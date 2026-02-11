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
    def __init__(self, sender: Optional[CommunicationProvider] = None):
        self.sender = sender
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
        body_text, body_html = self._extract_body_from_msg(msg)

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

    def _extract_body_from_msg(self, msg):
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

        return extract_parts(msg)

    def _get_original_email(self, remote_id: str):
        """Fetch full original email from IMAP for context."""
        if not self.host or not self.user: return None
        try:
            mail = self._connect()
            mail.select("INBOX")
            status, data = mail.uid('fetch', remote_id, '(RFC822)')
            if status != 'OK' or not data or not data[0]:
                mail.logout()
                return None

            # data[0] is usually (uid, content)
            raw_email = data[0][1]
            if not raw_email:
                 mail.logout()
                 return None

            msg = email.message_from_bytes(raw_email)
            mail.logout()
            return msg
        except Exception as e:
            print(f"IMAP Fetch Error: {e}")
            return None

    # Stubs for other interface methods
    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if self.sender:
            return self.sender.send_email(recipient, subject, body, cc=cc, bcc=bcc, extra_headers=extra_headers)
        return {"success": False, "error": "No sender configured for IMAP provider"}

    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        msg = self._get_original_email(remote_id)
        if not msg:
            return {"success": False, "error": "Could not fetch original email"}

        try:
            # Extract headers
            orig_subject = self._decode_mime_header(msg.get('Subject', ''))
            orig_from = msg.get('Reply-To') or msg.get('From')
            orig_message_id = msg.get('Message-ID', '')
            orig_refs = msg.get('References', '')
            orig_date = msg.get('Date', '')

            # Construct new headers
            new_subject = orig_subject
            if not new_subject.lower().startswith('re:'):
                new_subject = f"Re: {new_subject}"

            extra_headers = {
                'In-Reply-To': orig_message_id,
                'References': f"{orig_refs} {orig_message_id}".strip()
            }

            # Determine recipients
            to_addr = email.utils.parseaddr(orig_from)[1]
            cc_addrs = []
            if reply_all:
                # Add original To and Cc to Cc list, excluding self
                orig_to = msg.get_all('To', [])
                orig_cc = msg.get_all('Cc', [])
                all_recipients = email.utils.getaddresses(orig_to + orig_cc)
                for name, addr in all_recipients:
                    if addr.lower() != self.user.lower() and addr.lower() != to_addr.lower():
                        cc_addrs.append(addr)

            # Construct body with quote
            orig_text, _ = self._extract_body_from_msg(msg)
            full_body = f"{body}\n\nOn {orig_date}, {orig_from} wrote:\n> " + orig_text.replace('\n', '\n> ')

            return self.send_email(to_addr, new_subject, full_body, cc=cc_addrs, extra_headers=extra_headers)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        msg = self._get_original_email(remote_id)
        if not msg:
            return {"success": False, "error": "Could not fetch original email"}

        try:
            orig_subject = self._decode_mime_header(msg.get('Subject', ''))
            orig_from = msg.get('From')
            orig_date = msg.get('Date')

            new_subject = f"Fwd: {orig_subject}"

            orig_text, _ = self._extract_body_from_msg(msg)
            full_body = f"{note}\n\n---------- Forwarded message ----------\nFrom: {orig_from}\nDate: {orig_date}\nSubject: {orig_subject}\n\n{orig_text}"

            return self.send_email(to_address, new_subject, full_body)
        except Exception as e:
            return {"success": False, "error": str(e)}
    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        return self.move_to_label(remote_id, "Trash")

    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        return self.move_to_label(remote_id, "Archive")

    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        if not self.host or not self.user:
             return {"success": False, "error": "Not configured"}
        try:
            mail = self._connect()
            mail.select("INBOX")
            mail.uid('STORE', remote_id, '-FLAGS', '(\\Seen)')
            mail.logout()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        if not self.host or not self.user:
            return {"success": False, "error": "Not configured"}

        try:
            mail = self._connect()
            mail.select("INBOX")

            # Simple quoting for mailbox name
            mailbox = label_name
            if ' ' in mailbox and not mailbox.startswith('"'):
                mailbox = f'"{mailbox}"'

            # COPY
            result = mail.uid('COPY', remote_id, mailbox)
            if result[0] != 'OK':
                mail.logout()
                return {"success": False, "error": f"COPY failed: {result}"}

            # Mark Deleted in source
            mail.uid('STORE', remote_id, '+FLAGS', '(\\Deleted)')
            mail.expunge()

            mail.logout()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_labels(self) -> List[Dict[str, Any]]:
        if not self.host or not self.user: return []
        try:
            mail = self._connect()
            status, folders = mail.list()
            mail.logout()

            labels = []
            import shlex
            if status == 'OK':
                for folder in folders:
                    if not folder: continue
                    try:
                        f_str = folder.decode()
                        # Parse standard IMAP list response: (Flags) "Delimiter" "Name"
                        parts = f_str.split(')')
                        if len(parts) < 2: continue

                        rest = parts[1].strip()
                        tokens = shlex.split(rest)
                        if tokens:
                            name = tokens[-1]
                            labels.append({"id": name, "name": name})
                    except: continue

            return labels if labels else [{"id": "INBOX", "name": "INBOX"}]
        except Exception:
            return [{"id": "INBOX", "name": "INBOX"}]
    def sync_calendar(self) -> Dict[str, Any]:
        return {"synced": 0, "status": "not_supported"}
