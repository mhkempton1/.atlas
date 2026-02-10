from services.communication_provider import CommunicationProvider
from services.google_service import GoogleService
from typing import Dict, List, Optional, Any
from datetime import datetime

class GmailProvider(CommunicationProvider):
    """
    Gmail-specific implementation of the CommunicationProvider interface.
    """
    def __init__(self):
        # We reuse the existing GoogleService but adapt it to the interface
        self.service = GoogleService()

    def sync_emails(self, last_sync_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        return self.service.sync_emails(last_sync_timestamp)

    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.service.send_email(recipient, subject, body, cc=cc, bcc=bcc)

    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        return self.service.reply_to_email(remote_id, body, reply_all)

    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        return self.service.forward_email(remote_id, to_address, note)

    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        return self.service.trash_email(remote_id)

    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        return self.service.archive_email(remote_id)

    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        return self.service.mark_unread(remote_id)

    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        return self.service.move_to_label(remote_id, label_name)

    def get_labels(self) -> List[Dict[str, Any]]:
        return self.service.get_labels()

    def sync_calendar(self) -> Dict[str, Any]:
        return self.service.sync_calendar()
