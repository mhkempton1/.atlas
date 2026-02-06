from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from email.mime.text import MIMEText
import base64
import os
from core.config import settings
from services.activity_service import activity_service
import email.utils
from datetime import datetime, timedelta
from database.database import get_db
from database.models import Email, EmailAttachment, Contact, CalendarEvent

# Updated Scopes for Email + Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

class GoogleService:
    def __init__(self):
        self.gmail_service = None
        self.calendar_service = None
        
        try:
            self.authenticate()
        except Exception as e:
            print(f"Google Auth Error: {e}")

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
                    print("Scopes changed, re-authenticating...")
                    creds = None
            except Exception:
                creds = None

        # Refresh or Login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    print("Token expired and refresh failed. Re-authenticating...")
                    creds = None
            
            if not creds:
                if os.path.exists(creds_path):
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    print("Opening browser for authentication...")
                    creds = flow.run_local_server(port=0)
                else:
                    print(f"No credentials found. Searching: {possible_creds_paths}")
                    return

            # Save token
            # Use the path we found it at, or the first preference
            save_path = token_path if os.path.exists(token_path) else possible_token_paths[0]
            
            try:
                with open(save_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Failed to save token to {save_path}: {e}")

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
        
        # Logic same as before...
        if last_sync_timestamp:
            query = f"after:{int(last_sync_timestamp.timestamp())}"
        else:
            query = "newer_than:30d"

        try:
            results = self.gmail_service.users().messages().list(userId='me', q=query, maxResults=100).execute()
            messages = results.get('messages', [])
            synced_count = 0

            for msg_ref in messages:
                try:
                    message = self.gmail_service.users().messages().get(userId='me', id=msg_ref['id'], format='full').execute()
                    if self._store_email(message, db):
                        synced_count += 1
                except Exception as e:
                    print(f"Failed to sync email {msg_ref['id']}: {e}")

            db.commit()
            
            if synced_count > 0:
                activity_service.log_activity(
                    type="email",
                    action="Inbox Sync",
                    target=f"{synced_count} new emails",
                    details=f"Synced {synced_count} emails from Gmail API."
                )
                
            return {'synced': synced_count, 'timestamp': datetime.now()}

        except Exception as e:
            db.rollback()
            raise Exception(f"Email sync failed: {e}")
        finally:
            db.close()

    def _store_email(self, message, db):
        payload = message.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}

        # Check duplicate by Remote ID or Message ID
        message_id = headers.get('Message-ID')
        if db.query(Email).filter(
            (Email.remote_id == message['id']) | 
            ((Email.message_id == message_id) & (Email.message_id.isnot(None)))
        ).first():
            return False
        
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

        email = Email(
            message_id=message_id or f"atlas-{message['id']}",
            remote_id=message['id'],
            thread_id=message.get('threadId'),
            provider_type='google',
            from_address=headers.get('From'),
            subject=headers.get('Subject'),
            body_text=body_text, 
            body_html=body_html,
            snippet=message.get('snippet', '')[:200],
            date_received=self._parse_date(headers.get('Date')),
            is_read='UNREAD' not in message.get('labelIds', []),
            synced_at=datetime.now(),
            category=category 
        )
        db.add(email)
        db.flush()
        
        # Attachments
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    self._download_attachment(part, email.email_id, message['id'], db)
                    
        # Index in Vector DB
        try:
            from services.search_service import search_service
            search_service.index_email({
                "subject": email.subject,
                "sender": email.from_address,
                "body": email.body_text or email.body_html,
                "message_id": email.message_id,
                "date": email.date_received.isoformat() if email.date_received else None
            })
        except Exception as e:
            print(f"Failed to index email {email.message_id}: {e}")

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

    def _download_attachment(self, part, email_id, remote_id, db):
        # ... (Same helper)
        if not self.gmail_service: return
        att_id = part['body'].get('attachmentId')
        if not att_id: return
        try:
            att = self.gmail_service.users().messages().attachments().get(userId='me', messageId=remote_id, id=att_id).execute()
            data = base64.urlsafe_b64decode(att['data'])
            path = f"data/files/attachments/{email_id}/{part['filename']}"
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'wb') as f: f.write(data)
            db.add(EmailAttachment(email_id=email_id, filename=part['filename'], file_path=path))
        except: pass

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
            msg['subject'] = headers.get('Subject', '')
            if not msg['subject'].lower().startswith('re:'):
                msg['subject'] = f"Re: {msg['subject']}"
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

    def send_email(self, recipient, subject, body):
        if not self.gmail_service: self.authenticate()
        msg = MIMEText(body)
        msg['to'], msg['from'], msg['subject'] = recipient, 'me', subject
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
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
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
                print(f"Calendar API warning: {e}")
                return {'synced': 0, 'error': 'API_DISABLED'}
            raise Exception(f"Calendar sync failed: {e}")

    def _store_event(self, event, db):
        remote_id = event['id']
        existing = db.query(CalendarEvent).filter_by(remote_event_id=remote_id).first()
        
        # Parse times
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        # Handle date-only (all day)
        is_all_day = 'T' not in str(start) if start else False
        
        # Convert to datetime object if string
        # Simple parser for ISO format needed if not using dateutil
        # For now, storing as string might be safer if DB allows, but DB expects DateTime.
        # We need a robust parser.
        
        def parse_iso(dt_str):
            if not dt_str: return None
            try:
                # Remove Z and handle offsets if possible, or use simplified
                if 'T' in dt_str:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else: 
                     return datetime.fromisoformat(dt_str) # Date only
            except:
                return datetime.now()

        start_dt = parse_iso(start)
        end_dt = parse_iso(end)

        if existing:
            # Update
            existing.title = event.get('summary')
            existing.description = event.get('description')
            existing.location = event.get('location')
            existing.start_time = start_dt
            existing.end_time = end_dt
            existing.status = event.get('status')
            existing.synced_at = datetime.now()
            return True
        else:
            # Create
            new_event = CalendarEvent(
                remote_event_id=remote_id,
                provider_type='google',
                calendar_id='primary',
                title=event.get('summary'),
                description=event.get('description'),
                location=event.get('location'),
                start_time=start_dt,
                end_time=end_dt,
                all_day=is_all_day,
                status=event.get('status'),
                organizer=event.get('organizer', {}).get('email'),
                synced_at=datetime.now()
            )
            db.add(new_event)
            db.flush()
            return True

# Singleton
google_service = GoogleService()
# Alias for backward compatibility
gmail_service = google_service
