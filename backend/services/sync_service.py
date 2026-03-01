from typing import Dict, Any, Optional
from datetime import datetime
from services.communication_service import comm_service

class SyncService:
    """
    Dedicated service for orchestrating synchronization tasks.
    Wraps the communication_service to ensure full context linking and vector ingestion.
    """
    
    def __init__(self):
        pass

    def sync_recent_emails(self, last_sync_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Syncs recent emails and ensures they are persisted and ingested into ChromaDB.
        """
        # The communication service handles the fetch from provider (Gmail/IMAP)
        # The persistence layer handles Altimeter linking and ChromaDB embedding.
        result = comm_service.sync_emails(last_sync_timestamp)
        return result

sync_service = SyncService()
