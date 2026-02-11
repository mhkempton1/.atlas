import imaplib
import email
import email.utils
from email.header import decode_header
import base64
import os
from datetime import datetime
from services.communication_provider import CommunicationProvider
from typing import Dict, List, Optional, Any
from core.config import settings
from database.database import SessionLocal
from database.models import Email, EmailAttachment

class IMAPProvider(CommunicationProvider):
    def __init__(self):
        self.host = settings.IMAP_HOST
        self.port = settings.IMAP_PORT
        self.user = settings.IMAP_USER
        self.password = settings.IMAP_PASSWORD

    def _connect(self):
        mail = imaplib.IMAP4_SSL(self.host, self.port)
        mail.login(self.user, self.password)
        return mail

    def sync_emails(self, last_sync_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        if not self.host or not self.user:
            return {"synced": 0, "status": "not_configured"}

        db = SessionLocal()
        synced_count = 0
        try:
            mail = self._connect()
            mail.select("INBOX")

            search_criteria = 'ALL'
            if last_sync_timestamp:
                date_str = last_sync_timestamp.strftime("%d-%b-%Y")
                search_criteria = f'(SINCE "{date_str}")'

            # Use UID search for robustness
            status, messages = mail.uid('search', None, search_criteria)
            if status != 'OK':
                return {"synced": 0, "status": "search_failed"}

            uids = messages[0].split()

            # Process newer emails first (if possible, though logic iterates all)
            # Optimization: Check if UID exists in DB before fetching
            
            for uid in uids:
                uid_str = uid.decode()

                # Fast check existence
                exists = db.query(Email).filter(
                    Email.remote_id == uid_str,
                    Email.provider_type == 'imap'
                ).first()
                if exists:
                    continue

                status, data = mail.uid('fetch', uid, '(RFC822)')
                if status != 'OK': continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                if self._store_imap_email(msg, uid_str, db):
                    synced_count += 1

            db.commit()
            mail.logout()
            return {"synced": synced_count, "status": "success"}
        except Exception as e:
            db.rollback()
            print(f"IMAP Sync Error: {e}")
            return {"synced": 0, "status": "error", "error": str(e)}
        finally:
            db.close()

    def _store_imap_email(self, msg, imap_uid, db):
        # 1. Parse Headers
        subject = self._decode_mime_header(msg['Subject'])
        from_raw = msg.get('From')
        message_id = msg.get('Message-ID')
        date_str = msg.get('Date')

        # Check duplicate by Message-ID (if UID check passed but message exists)
        if message_id and db.query(Email).filter(Email.message_id == message_id).first():
            return False

        # Parse Date
        date_received = datetime.now()
        if date_str:
            try:
                date_tuple = email.utils.parsedate_tz(date_str)
                if date_tuple:
                    date_received = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            except: pass

        # 2. Extract Body
        body_text, body_html = "", ""

        def extract_parts(message_part):
            text, html = "", ""
            if message_part.is_multipart():
                for part in message_part.get_payload():
                    t, h = extract_parts(part)
                    text += t
                    html += h
            else:
                content_type = message_part.get_content_type()
                disposition = str(message_part.get("Content-Disposition"))

                if "attachment" not in disposition:
                    try:
                        payload = message_part.get_payload(decode=True)
                        charset = message_part.get_content_charset() or 'utf-8'
                        decoded = payload.decode(charset, errors='replace')
                        if content_type == "text/plain":
                            text += decoded
                        elif content_type == "text/html":
                            html += decoded
                    except: pass
            return text, html

        body_text, body_html = extract_parts(msg)

        # 3. Context Bridge via Altimeter
        from services.altimeter_service import altimeter_service
        context = altimeter_service.get_context_for_email(from_raw, subject, body_text)
        
        category = None
        if context.get('is_proposal'): category = 'proposal'
        elif context.get('is_daily_log'): category = 'daily_log'

        # 4. Save to DB
        email_obj = Email(
            message_id=message_id or f"imap-{imap_uid}",
            remote_id=imap_uid,
            provider_type='imap',
            from_address=from_raw,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            snippet=body_text[:200] if body_text else "",
            date_received=date_received,
            is_read=False,
            synced_at=datetime.now(),
            category=category
        )
        db.add(email_obj)
        db.flush()

        # 5. Handle Attachments (Metadata Only)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart': continue
                if part.get('Content-Disposition') is None: continue

                filename = part.get_filename()
                if filename:
                    filename = self._decode_mime_header(filename)
                    # Skip saving content, capture metadata
                    payload = part.get_payload(decode=True)
                    file_size = len(payload) if payload else 0

                    att = EmailAttachment(
                        email_id=email_obj.email_id,
                        filename=filename,
                        file_size=file_size,
                        mime_type=part.get_content_type(),
                        file_path="skipped_in_imap_phase"
                    )
                    db.add(att)

        # 6. Index
        try:
            from services.search_service import search_service
            search_service.index_email({
                "subject": email_obj.subject,
                "sender": email_obj.from_address,
                "body": email_obj.body_text or email_obj.body_html,
                "message_id": email_obj.message_id,
                "date": email_obj.date_received.isoformat()
            })
        except: pass

        return True

    def _decode_mime_header(self, header):
        if not header: return ""
        decoded = decode_header(header)
        result = ""
        for s, encoding in decoded:
            if isinstance(s, bytes):
                result += s.decode(encoding or 'utf-8')
            else:
                result += s
        return result

    def _get_email_details(self, remote_id: str) -> Dict[str, str]:
        """
        Helper to get subject, from, message-id from DB or IMAP.
        """
        db = SessionLocal()
        try:
            email_obj = db.query(Email).filter(Email.remote_id == remote_id, Email.provider_type == 'imap').first()
            if email_obj:
                return {
                    "subject": email_obj.subject,
                    "from": email_obj.from_address,
                    "message_id": email_obj.message_id
                }

            # Fallback to IMAP
            mail = self._connect()
            mail.select("INBOX")
            status, data = mail.uid('fetch', remote_id, '(BODY[HEADER.FIELDS (SUBJECT FROM MESSAGE-ID)])')
            mail.logout()

            if status == 'OK' and data and data[0]:
                raw_headers = data[0][1]
                if isinstance(raw_headers, bytes):
                    msg = email.message_from_bytes(raw_headers)
                    return {
                        "subject": self._decode_mime_header(msg['Subject']),
                        "from": msg['From'],
                        "message_id": msg['Message-ID']
                    }
            return {}
        except Exception as e:
            print(f"Error fetching email details: {e}")
            return {}
        finally:
            db.close()

    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        from services.smtp_provider import SMTPProvider
        return SMTPProvider().send_email(recipient, subject, body, cc=cc, bcc=bcc, extra_headers=extra_headers)

    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        details = self._get_email_details(remote_id)
        if not details.get("from"):
            return {"success": False, "error": "Original email not found"}

        orig_subject = details["subject"]
        orig_from = details["from"]
        orig_msg_id = details["message_id"]

        new_subject = f"Re: {orig_subject}" if not orig_subject.lower().startswith("re:") else orig_subject

        # Extract email from "Name <email>" if needed, but SMTP usually handles it.
        # However, for safety:
        recipient_addr = email.utils.parseaddr(orig_from)[1]

        extra_headers = {}
        if orig_msg_id:
            extra_headers['In-Reply-To'] = orig_msg_id
            extra_headers['References'] = orig_msg_id

        return self.send_email(recipient_addr, new_subject, body, extra_headers=extra_headers)

    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        details = self._get_email_details(remote_id)
        if not details.get("subject"):
            return {"success": False, "error": "Original email not found"}

        orig_subject = details["subject"]
        new_subject = f"Fwd: {orig_subject}" if not orig_subject.lower().startswith("fwd:") else orig_subject

        # In a real forward, we would attach the original email or quote the body.
        # Since _get_email_details doesn't return body, we might need to fetch it if we want to quote it.
        # For this MVP, we will just send the note with the subject.
        # OPTIONAL: Fetch body to append.

        # Let's try to fetch body for better UX
        full_body = note

        # ... Fetching body logic skipped for brevity/complexity in this iteration unless critical.
        # Task says "Finish the logic", implies working forward. A forward without content is empty.
        # I should try to fetch body.

        db = SessionLocal()
        try:
            email_obj = db.query(Email).filter(Email.remote_id == remote_id, Email.provider_type == 'imap').first()
            if email_obj:
                full_body += f"\n\n--- Forwarded message ---\nFrom: {email_obj.from_address}\nDate: {email_obj.date_received}\nSubject: {email_obj.subject}\n\n{email_obj.body_text}"
        except:
            pass
        finally:
            db.close()

        return self.send_email(to_address, new_subject, full_body)

    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        return self.move_to_label(remote_id, "Trash")

    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        return self.move_to_label(remote_id, "Archive")

    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        try:
            mail = self._connect()
            mail.select("INBOX")
            mail.uid('STORE', remote_id, '-FLAGS', '(\Seen)')
            mail.logout()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        try:
            mail = self._connect()
            mail.select("INBOX")

            # Check if destination exists (optional, but good practice).
            # If not, create? Or fail? Standard IMAP folders usually exist.
            # Assuming it exists.

            result = mail.uid('COPY', remote_id, label_name)
            if result[0] == 'OK':
                mail.uid('STORE', remote_id, '+FLAGS', '(\Deleted)')
                mail.expunge()
                mail.logout()
                return {"success": True}
            else:
                # If COPY failed (e.g. folder doesn't exist), try creating it?
                # For now, return error.
                mail.logout()
                return {"success": False, "error": f"Copy failed: {result}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_labels(self) -> List[Dict[str, Any]]:
        try:
            mail = self._connect()
            status, folders = mail.list()
            mail.logout()

            labels = []
            if status == 'OK':
                for folder in folders:
                    # folder is bytes: b'(\HasNoChildren) "/" "INBOX"'
                    # Parse name.
                    name = folder.decode().split(' "')[-1].strip('"')
                    labels.append({"id": name, "name": name})
            return labels
        except Exception as e:
            print(f"IMAP List Error: {e}")
            return [{"id": "INBOX", "name": "INBOX"}]

    def sync_calendar(self) -> Dict[str, Any]:
        return {"synced": 0, "status": "not_supported"}
