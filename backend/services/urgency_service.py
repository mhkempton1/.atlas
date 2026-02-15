import re
from typing import Dict, Any
from datetime import datetime

class UrgencyService:
    """
    Service for calculating the urgency of incoming emails based on 
    keywords, metadata, and timing.
    """
    
    def __init__(self):
        self.urgent_keywords = {
            "critical": 40,
            "emergency": 50,
            "asap": 30,
            "immediate": 35,
            "urgent": 35,
            "deadline": 25,
            "delay": 20,
            "stop work": 60,
            "important": 15,
            "action required": 20,
            "due today": 45,
            "as soon as possible": 30
        }
        
    def calculate_urgency(self, email_data: Dict[str, Any]) -> int:
        """
        Calculate urgency score from 0 to 100.
        """
        score = 0
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        full_text = f"{subject} {body}"
        
        # 1. Keyword Scoring
        for kw, points in self.urgent_keywords.items():
            if kw in full_text:
                # Extra weight for subject line
                if kw in subject:
                    score += points * 1.5
                else:
                    score += points
        
        # 2. Timing Analysis (Quiet Hours / Late Work)
        # Emails sent very late might be high pressure
        try:
            date_str = email_data.get('date_received')
            if date_str:
                dt = datetime.fromisoformat(date_str)
                # If between 10 PM and 5 AM
                if dt.hour >= 22 or dt.hour <= 5:
                    score += 15
        except:
            pass
            
        # 3. Sentiment Adjustment (If provided)
        # Note: Sentiment service will call this later or adjust.
        # For now, just placeholder for metadata sentiment
        if email_data.get('sentiment') == 'negative':
            score += 10
            
        # Cap score at 100
        return min(int(score), 100)

urgency_service = UrgencyService()
