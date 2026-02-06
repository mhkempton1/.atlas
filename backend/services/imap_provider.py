import imaplib
import email
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

            # Simple search: all messages
            # In a production environment, we'd search since last_sync_timestamp
            # For this implementation, we'll fetch the last 10-20 to verify decoupling
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                return {"synced": 0, "status": "search_failed"}

            message_ids = messages[0].split()
            # Most recent first
            message_ids.reverse()
            
            # Limit for demo/safety
            message_ids = message_ids[:20]

            for msg_id in message_ids:
                status, data = mail.fetch(msg_id, '(RFC822)')
                if status != 'OK': continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                if self._store_imap_email(msg, msg_id.decode(), db):
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
        
        # Check duplicate
        if db.query(Email).filter(
            (Email.remote_id == imap_uid) | 
            ((Email.message_id == message_id) & (Email.message_id.isnot(None)))
        ).first():
            return False

        # 2. Extract Body
        body_text, body_html = "", ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                try:
                    payload = part.get_payload(decode=True).decode()
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body_text += payload
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        body_html += payload
                except:
                    pass
        else:
            try:
                body_text = msg.get_payload(decode=True).decode()
            except:
                pass

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
            date_received=datetime.now(), # In production, parse msg['Date']
            is_read=False,
            synced_at=datetime.now(),
            category=category
        )
        db.add(email_obj)
        db.flush()

        # 5. Handle Attachments (Simplified)
        # TODO: Implement IMAP attachment saving

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

    # Stubs for other interface methods
    def send_email(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        from services.smtp_provider import SMTPProvider
        return SMTPProvider().send_email(recipient, subject, body)

    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        return {"success": False, "error": "IMAP Reply not implemented"}
    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        return {"success": False, "error": "IMAP Forward not implemented"}
    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        return {"success": False, "error": "IMAP Trash not implemented"}
    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        return {"success": False, "error": "IMAP Archive not implemented"}
    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        return {"success": False, "error": "IMAP Mark Unread not implemented"}
    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        return {"success": False, "error": "IMAP Move not implemented"}
    def get_labels(self) -> List[Dict[str, Any]]:
        return [{"id": "INBOX", "name": "INBOX"}]
    def sync_calendar(self) -> Dict[str, Any]:
        return {"synced": 0, "status": "not_supported"}
