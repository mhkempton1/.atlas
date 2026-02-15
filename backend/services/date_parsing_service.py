import re
from datetime import datetime, timedelta
from typing import Optional

class DateParsingService:
    """
    Service for extracting dates and deadlines from natural language text.
    Focuses on relative dates common in construction (e.g., "by Friday", "next Tuesday").
    """
    
    def __init__(self):
        self.days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, 
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
    def parse_deadline_from_text(self, text: str, reference_date: Optional[datetime] = None) -> Optional[str]:
        """
        Attempt to parse a deadline from text. 
        Returns YYYY-MM-DD or None.
        """
        if not text:
            return None
            
        now = reference_date or datetime.now()
        text = text.lower().strip()
        
        # 1. Direct Regex for YYYY-MM-DD
        iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if iso_match:
            return iso_match.group(0)
            
        # 2. Key phrases
        if "today" in text:
            return now.strftime("%Y-%m-%d")
        if "tomorrow" in text:
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")
        if "eod" in text or "end of day" in text:
             return now.strftime("%Y-%m-%d")
             
        # 3. Day of week (e.g. "by Friday", "due Tuesday")
        for day_name, day_num in self.days_map.items():
            if f" {day_name}" in f" {text}" or f"{day_name} " in f"{text} ":
                # Find the next occurrence of this day
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0: # Already passed this week or IS today
                    days_ahead += 7
                
                target_date = now + timedelta(days=days_ahead)
                
                # Check for "next" modifier
                if f"next {day_name}" in text:
                    target_date += timedelta(days=7)
                    
                return target_date.strftime("%Y-%m-%d")
                
        # 4. "in X days"
        in_days_match = re.search(r'in (\d+) days?', text)
        if in_days_match:
            days = int(in_days_match.group(1))
            return (now + timedelta(days=days)).strftime("%Y-%m-%d")
            
        return None

date_parsing_service = DateParsingService()
