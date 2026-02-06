import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from services.communication_provider import CommunicationProvider
from typing import Dict, List, Optional, Any
from core.config import settings

class SMTPProvider(CommunicationProvider):
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD

    def send_email(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        if not self.host or not self.user:
            return {"success": False, "error": "SMTP Not configured"}

        try:
            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
            server.quit()

            return {"success": True}
        except Exception as e:
            print(f"SMTP Send Error: {e}")
            return {"success": False, "error": str(e)}

    # Stubs for other interface methods
    def sync_emails(self, last_sync_timestamp: Optional[Any] = None) -> Dict[str, Any]:
        return {"synced": 0, "status": "send_only_provider"}
    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        return {"success": False, "error": "SMTP Reply not implemented"}
    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        return {"success": False, "error": "SMTP Forward not implemented"}
    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        return {"success": False, "error": "N/A for SMTP"}
    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        return {"success": False, "error": "N/A for SMTP"}
    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        return {"success": False, "error": "N/A for SMTP"}
    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        return {"success": False, "error": "N/A for SMTP"}
    def get_labels(self) -> List[Dict[str, Any]]:
        return []
    def sync_calendar(self) -> Dict[str, Any]:
        return {"synced": 0, "status": "not_supported"}
