import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class RecurringTaskService:
    """
    Service for detecting recurring task patterns and generating 
    follow-up instances.
    """
    
    def detect_pattern(self, text: str) -> Optional[str]:
        """
        Detect if a task description implies recurrence.
        Returns pattern (e.g. "weekly", "daily") or None.
        """
        text = text.lower()
        if re.search(r'every day|daily', text):
            return "daily"
        if re.search(r'every week|weekly', text):
            return "weekly"
        if re.search(r'every month|monthly', text):
            return "monthly"
        
        day_match = re.search(r'every (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text)
        if day_match:
            return f"weekly:{day_match.group(1)}"
            
        return None

    def get_next_date(self, pattern: str, from_date: datetime) -> datetime:
        """
        Calculate the next occurrence date based on pattern.
        """
        if pattern == "daily":
            return from_date + timedelta(days=1)
        if pattern == "weekly":
            return from_date + timedelta(days=7)
        if pattern == "monthly":
            # Simple approximation: 30 days
            return from_date + timedelta(days=30)
        
        if pattern.startswith("weekly:"):
            return from_date + timedelta(days=7)
            
        return from_date + timedelta(days=1)

recurring_task_service = RecurringTaskService()
