from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from email.mime.text import MIMEText
import base64
import os
from typing import List, Optional
from core.config import settings
from services.activity_service import activity_service
import email.utils
from datetime import datetime, timedelta, timezone
from database.database import get_db
from database.models import Email, EmailAttachment, CalendarEvent
from services.email_persistence_service import persist_email_to_database
from services.calendar_persistence_service import calendar_persistence_service

# Updated Scopes for Email + Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

class GoogleService:
    """
    Service for interacting with Google APIs (Gmail, Calendar).
    Handles authentication and synchronization.
    """
    def __init__(self):
        self.gmail_service = None
        self.calendar_service = None

    def authenticate(self):
        """OAuth 2.0 authentication with Google for multiple services"""
        creds = None
        
        # Check .vault first, then config
        vault_path = os.path.join(os.path.expanduser("~"), ".vault")
        config_dir = "config"
        
        possible_token_paths = [
            os.path.join(vault_path, 'google_token.json'), # Generic name preferred
            os.path.join(vault_path, 'gmail_token.json'),  # Legacy
            os.path.join(config_dir, 'google_token.json'),
            os.path.join(config_dir, 'gmail_token.json')
        ]
        
        possible_creds_paths = [
            os.path.join(vault_path, 'credentials.json'),  # Generic name preferred
            os.path.join(vault_path, 'gmail_credentials.json'),
            os.path.join(config_dir, 'credentials.json'),
            os.path.join(config_dir, 'gmail_credentials.json')
        ]
        
        # Find first existing
        token_path = next((p for p in possible_token_paths if os.path.exists(p)), possible_token_paths[0])
        creds_path = next((p for p in possible_creds_paths if os.path.exists(p)), possible_creds_paths[0])

        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                # Verify scopes match - force re-auth if scopes changed
                if creds and not set(SCOPES).issubset(set(creds.scopes or [])):
                    creds = None
            except Exception:
                creds = None

        # Refresh or Login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    creds = None
            
            if not creds:
                if os.path.exists(creds_path):
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    return

            # Save token
            # Use the path we found it at, or the first preference
            save_path = token_path if os.path.exists(token_path) else possible_token_paths[0]
            
            try:
                with open(save_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                pass

        # Build Services
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        self.calendar_service = build('calendar', 'v3', credentials=creds)

    # --- Gmail Methods ---
    def sync_emails(self, last_sync_timestamp=None):
        if not self.gmail_service:
            self.authenticate()
            if not self.gmail_service: raise Exception("Gmail service unavailable")

        from database.database import SessionLocal
        db = SessionLocal()
        
        if last_sync_timestamp:
            query = f"after:{int(last_sync_timestamp.timestamp())}"
        else:
            query = "newer_than:30d"

        synced_count = 0
        errors = []
        status = "success"

        try:
            results = self.gmail_service.users().messages().list(userId='me', q=query, maxResults=100).execute()
            messages = results.get('messages', [])

            for msg_ref in messages:
                try:
                    message = self.gmail_service.users().messages().get(userId='me', id=msg_ref['id'], format='full').execute()

                    email_data = self._extract_email_data(message)
                    result = persist_email_to_database(email_data, db)

                    if result["success"]:
                        if result["action"] == "created": # Only count new emails
                            synced_count += 1
                    else:
                        errors.append(f"Failed to persist {msg_ref['id']}: {result.get('error')}")
                except Exception as e:
                    errors.append(f"Failed to process {msg_ref['id']}: {str(e)}")

            if errors:
                status = "partial" if synced_count > 0 else "failed"

            if synced_count > 0:
                activity_service.log_activity(
                    type="email",
                    action="Inbox Sync",
                    target=f"{synced_count} new emails",
                    details=f"Synced {synced_count} emails from Gmail API."
                )
                
            return {
                'synced': synced_count,
                'timestamp': datetime.now(),
                'status': status,
                'errors': errors
            }

        except Exception as e:
            raise Exception(f"Email sync failed: {e}")
        finally:
            db.close()

    def _extract_email_data(self, message):
        """Extract email data from Gmail message for persistence."""
        payload = message.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}
        remote_id = message['id']
        message_id = headers.get('Message-ID')

        body_text, body_html = self._extract_body(payload)
        
        # Real-time Classification via Altimeter
        from services.altimeter_service import altimeter_service
        context = altimeter_service.get_context_for_email(
            headers.get('From', ''), 
            headers.get('Subject', ''),
            body_text
        )
        
        category = None
        if context.get('is_proposal'):
            category = 'proposal'
        elif context.get('is_daily_log'):
            category = 'daily_log'

        attachments = []
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    # Download and get path
                    att_path = self._download_attachment(part, remote_id)
                    if att_path:
                        attachments.append({
                            'filename': part['filename'],
                            'mime_type': part.get('mimeType'),
                            'storage_path': att_path
                        })

        return {
            'gmail_id': remote_id,
            'remote_id': remote_id,
            'message_id': message_id or f"atlas-{remote_id}",
            'thread_id': message.get('threadId'),
            'provider_type': 'google',
            'from_address': headers.get('From'),
            'sender': headers.get('From'), # persist_email_to_database uses 'sender'
            'subject': headers.get('Subject'),
            'body_text': body_text,
            'body_html': body_html,
            'snippet': message.get('snippet', '')[:200],
            'date_received': self._parse_date(headers.get('Date')),
            'is_read': 'UNREAD' not in message.get('labelIds', []),
            'is_unread': 'UNREAD' in message.get('labelIds', []),
            'category': category,
            'attachments': attachments,
            'labels': message.get('labelIds', [])
        }
                    self._download_attachment(part, email.email_id, message['id'], db)
                    
        # Index in Vector DB
        try:
            from services.embedding_service import embedding_service
            embedding_service.generate_email_embedding({
                "subject": email.subject,
                "sender": email.from_address,
                "body": email.body_text or email.body_html,
                "message_id": email.message_id,
                "date": email.date_received.isoformat() if email.date_received else None
            })
        except Exception as e:
            pass

        return True

    def _extract_body(self, payload):
        # ... (Same helper)
        body_text, body_html = "", ""
        if 'body' in payload and payload['body'].get('data'):
             data = payload['body']['data']
             try:
                 decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                 if payload.get('mimeType') == 'text/html': body_html = decoded
                 else: body_text = decoded
             except: pass
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('body', {}).get('data'):
                    sub_text, sub_html = self._extract_body(part) # Recursive call works if method handles dict
                    # Actually _extract_body expects payload (dict).
                    # Fix: self call logic.
                    # Simplified here:
                    if part['mimeType'] == 'text/plain':
                        try: body_text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        except: pass
                    elif part['mimeType'] == 'text/html':
                        try: body_html += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        except: pass
                if part.get('parts'):
                     t, h = self._extract_body(part)
                     body_text += t
                     body_html += h
        return body_text, body_html

    def _download_attachment(self, part, remote_id):
        if not self.gmail_service: return None
        att_id = part['body'].get('attachmentId')
        if not att_id: return None
        try:
            att = self.gmail_service.users().messages().attachments().get(userId='me', messageId=remote_id, id=att_id).execute()
            data = base64.urlsafe_b64decode(att['data'])
            # Use remote_id (Gmail ID) for path as email_id is not yet available
            path = f"data/files/attachments/{remote_id}/{part['filename']}"
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'wb') as f: f.write(data)
            return path
        except:
            return None

    def _parse_date(self, date_str):
        if not date_str: return datetime.now()
        try: return datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(date_str)))
        except: return datetime.now()

    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> dict:
        """Reply to an email using Gmail API, maintaining thread context"""
        if not self.gmail_service:
            self.authenticate()

        try:
            # Get the original message for headers
            original = self.gmail_service.users().messages().get(
                userId='me', id=remote_id, format='metadata',
                metadataHeaders=['From', 'To', 'Cc', 'Subject', 'Message-ID', 'References', 'In-Reply-To']
            ).execute()

            headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
            thread_id = original.get('threadId')

            # Build reply
            msg = MIMEText(body)
            msg['to'] = headers.get('From', '')  # Reply to sender
            if reply_all and headers.get('Cc'):
                msg['cc'] = headers['Cc']
            subject = headers.get('Subject', '')
            if not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"
            msg['Subject'] = subject
            msg['In-Reply-To'] = headers.get('Message-ID', '')
            msg['References'] = f"{headers.get('References', '')} {headers.get('Message-ID', '')}".strip()

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw, 'threadId': thread_id}
            ).execute()

            return {'success': True, 'message_id': result.get('id'), 'thread_id': thread_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def forward_email(self, gmail_id: str, to_address: str, note: str = "") -> dict:
        """Forward an email to a new recipient"""
        if not self.gmail_service:
            self.authenticate()

        try:
            # Get original message
            original = self.gmail_service.users().messages().get(
                userId='me', id=gmail_id, format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
            body_text, body_html = self._extract_body(original.get('payload', {}))

            # Build forward
            forward_body = f"{note}\n\n---------- Forwarded message ----------\nFrom: {headers.get('From', '')}\nDate: {headers.get('Date', '')}\nSubject: {headers.get('Subject', '')}\n\n{body_text}"

            msg = MIMEText(forward_body)
            msg['to'] = to_address
            msg['subject'] = f"Fwd: {headers.get('Subject', '')}"

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            result = self.gmail_service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()

            return {'success': True, 'message_id': result.get('id')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trash_email(self, gmail_id: str) -> dict:
        """Move email to Gmail trash"""
        if not self.gmail_service:
            self.authenticate()
        try:
            self.gmail_service.users().messages().trash(userId='me', id=gmail_id).execute()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def archive_email(self, gmail_id: str) -> dict:
        """Archive email (remove INBOX label)"""
        if not self.gmail_service:
            self.authenticate()
        try:
            self.gmail_service.users().messages().modify(
                userId='me', id=gmail_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def mark_unread(self, gmail_id: str) -> dict:
        """Mark email as unread"""
        if not self.gmail_service:
            self.authenticate()
        try:
            self.gmail_service.users().messages().modify(
                userId='me', id=gmail_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def move_to_label(self, gmail_id: str, label_name: str) -> dict:
        """Move email to a Gmail label/folder"""
        if not self.gmail_service:
            self.authenticate()
        try:
            # Get or create label
            labels = self.gmail_service.users().labels().list(userId='me').execute()
            label_id = None
            for label in labels.get('labels', []):
                if label['name'].lower() == label_name.lower():
                    label_id = label['id']
                    break

            if not label_id:
                # Create the label
                new_label = self.gmail_service.users().labels().create(
                    userId='me',
                    body={'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
                ).execute()
                label_id = new_label['id']

            # Move: add new label, remove INBOX
            self.gmail_service.users().messages().modify(
                userId='me', id=gmail_id,
                body={'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}
            ).execute()

            return {'success': True, 'label_id': label_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_labels(self) -> list:
        """Get all Gmail labels/folders"""
        if not self.gmail_service:
            self.authenticate()
        try:
            result = self.gmail_service.users().labels().list(userId='me').execute()
            return [{'id': l['id'], 'name': l['name'], 'type': l['type']}
                    for l in result.get('labels', [])]
        except Exception as e:
            return []

    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, extra_headers: Optional[dict] = None) -> dict:
        if not self.gmail_service: self.authenticate()
        msg = MIMEText(body)
        msg['To'] = recipient
        msg['From'] = 'me'
        msg['Subject'] = subject
        if cc:
            msg['Cc'] = ', '.join(cc)
        if bcc:
            msg['Bcc'] = ', '.join(bcc)

        if extra_headers:
            for k, v in extra_headers.items():
                msg[k] = v

        raw = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')}
        return self.gmail_service.users().messages().send(userId='me', body=raw).execute()

    # --- Calendar Methods ---
    def sync_calendar(self):
        """Sync future events from primary calendar"""
        if not self.calendar_service:
            self.authenticate()
            if not self.calendar_service: raise Exception("Calendar service unavailable")

        db = next(get_db())
        
        # Sync from now
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z") # Ensure Z suffix for Google API
        
        try:
            events_result = self.calendar_service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=50, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            synced_count = 0
            for event in events:
                if self._store_event(event, db):
                    synced_count += 1
            
            db.commit()
            
            if synced_count > 0:
                activity_service.log_activity(
                    type="calendar",
                    action="Calendar Sync",
                    target=f"{synced_count} events updated",
                    details=f"Synchronized {synced_count} calendar events with Google Calendar."
                )

            return {'synced': synced_count, 'timestamp': datetime.now()}
            
        except Exception as e:
            db.rollback()
            if "Calendar usage limits exceeded" in str(e) or "API has not been used" in str(e):
                return {'synced': 0, 'error': 'API_DISABLED'}
            raise Exception(f"Calendar sync failed: {e}")

    def _store_event(self, event, db):
        # Extract fields for persistence
        start = event.get('start', {})
        end = event.get('end', {})
        
        start_time = start.get('dateTime', start.get('date'))
        end_time = end.get('dateTime', end.get('date'))
        is_all_day = 'dateTime' not in start
        
        event_data = {
            "google_calendar_id": event['id'],
            "title": event.get('summary'),
            "description": event.get('description'),
            "start_time": start_time,
            "end_time": end_time,
            "location": event.get('location'),
            "is_all_day": is_all_day,
            "status": event.get('status'),
            "attendees": event.get('attendees'),
            "organizer": event.get('organizer', {}).get('email'),
            "calendar_id": "primary",
            "is_recurring": 'recurringEventId' in event or 'recurrence' in event,
            "recurrence_rule": "\n".join(event.get('recurrence', [])) if event.get('recurrence') else None
        }
        
        calendar_persistence_service.persist_calendar_event(event_data, db)
        return True

    def create_event(self, event_data: dict) -> dict:
        """Create an event in the primary Google Calendar."""
        if not self.calendar_service:
            self.authenticate()
            if not self.calendar_service: raise Exception("Calendar service unavailable")

        # Format for Google API
        attendees = []
        import json
        try:
            raw_attendees = event_data.get('attendees', '[]')
            if isinstance(raw_attendees, str):
                attendee_list = json.loads(raw_attendees)
            else:
                attendee_list = raw_attendees
            attendees = [{'email': a} if isinstance(a, str) else a for a in attendee_list]
        except: pass

        body = {
            'summary': event_data['title'],
            'location': event_data.get('location'),
            'description': event_data.get('description'),
            'start': {
                'dateTime': event_data['start_time'].isoformat() if hasattr(event_data['start_time'], 'isoformat') else event_data['start_time'],
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event_data['end_time'].isoformat() if hasattr(event_data['end_time'], 'isoformat') else event_data['end_time'],
                'timeZone': 'UTC',
            },
            'attendees': attendees,
        }

        try:
            event = self.calendar_service.events().insert(calendarId='primary', body=body).execute()
            return event
        except Exception as e:
            raise Exception(f"Google Calendar event creation failed: {e}")

# Singleton
google_service = GoogleService()
# Alias for backward compatibility
gmail_service = google_service
