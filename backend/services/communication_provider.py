from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

class CommunicationProvider(ABC):
    """
    Abstract Base Class for communication providers (Gmail, IMAP, Outlook, Internal).
    """

    @abstractmethod
    def sync_emails(self, last_sync_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def reply_to_email(self, remote_id: str, body: str, reply_all: bool = False) -> Dict[str, Any]:
        pass

    @abstractmethod
    def forward_email(self, remote_id: str, to_address: str, note: str = "") -> Dict[str, Any]:
        pass

    @abstractmethod
    def trash_email(self, remote_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def archive_email(self, remote_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def mark_unread(self, remote_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def move_to_label(self, remote_id: str, label_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_labels(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def sync_calendar(self) -> Dict[str, Any]:
        pass
