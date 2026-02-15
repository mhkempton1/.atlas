from typing import Dict, List, Optional, Any
from datetime import datetime
from services.gmail_provider import GmailProvider
from services.imap_provider import IMAPProvider
from services.smtp_provider import SMTPProvider
from core.config import settings

class CommunicationService:
    def __init__(self):
        smtp_provider = SMTPProvider()
        self.providers = {
            "google": GmailProvider(),
            "imap": IMAPProvider(sender=smtp_provider)
        }
        self.active_provider_name = settings.COMMUNICATION_PROVIDER if settings.COMMUNICATION_PROVIDER in self.providers else "google"

    @property
    def active_provider(self):
        return self.providers.get(self.active_provider_name)

    def set_provider(self, name: str):
        if name in self.providers:
            self.active_provider_name = name

    def sync_emails(self, last_sync_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        return self.active_provider.sync_emails(last_sync_timestamp)

    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.active_provider.send_email(recipient, subject, body, cc=cc, bcc=bcc)

    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        return self.active_provider.reply_to_email(remote_id, body, reply_all)

    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        return self.active_provider.forward_email(remote_id, to_address, note)

    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        return self.active_provider.trash_email(remote_id)

    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        return self.active_provider.archive_email(remote_id)

    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        return self.active_provider.mark_unread(remote_id)

    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        return self.active_provider.move_to_label(remote_id, label_name)

    def get_labels(self) -> List[Dict[str, Any]]:
        return self.active_provider.get_labels()

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event using the active provider."""
        if not hasattr(self.active_provider, 'create_event'):
            return {"error": f"Provider {self.active_provider_name} does not support event creation"}
        return self.active_provider.create_event(event_data)

    def sync_calendar(self) -> Dict[str, Any]:
        return self.active_provider.sync_calendar()

# Singleton
comm_service = CommunicationService()
