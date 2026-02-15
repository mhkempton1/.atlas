from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from services.calendar_service import calendar_service

class SchedulingSuggestionService:
    """
    Service for analyzing calendar availability and suggesting 
    optimal meeting slots.
    """
    
    def __init__(self):
        self.work_start = time(9, 0)
        self.work_end = time(17, 0)
        
    def suggest_meeting_slots(self, duration_minutes: int = 30, days_ahead: int = 3) -> List[Dict[str, Any]]:
        """
        Find available slots in the user's schedule.
        """
        suggestions = []
        now = datetime.now()
        
        # 1. Get existing events
        existing_events = calendar_service.list_events()
        
        for i in range(1, days_ahead + 1):
            date_to_check = (now + timedelta(days=i)).date()
            
            # Start checking from 9 AM
            current_time = datetime.combine(date_to_check, self.work_start)
            end_of_day = datetime.combine(date_to_check, self.work_end)
            
            while current_time + timedelta(minutes=duration_minutes) <= end_of_day:
                next_check = current_time + timedelta(minutes=duration_minutes)
                
                # Check if current_time to next_check is free
                is_free = True
                for event in existing_events:
                    try:
                        e_start = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00')).replace(tzinfo=None)
                        e_end = datetime.fromisoformat(event["end_time"].replace('Z', '+00:00')).replace(tzinfo=None)
                        
                        # Overlap logic
                        if not (next_check <= e_start or current_time >= e_end):
                            is_free = False
                            # Skip to next event end
                            current_time = e_end
                            break
                    except:
                        continue
                
                if is_free:
                    suggestions.append({
                        "start": current_time.isoformat(),
                        "end": next_check.isoformat(),
                        "label": current_time.strftime("%A, %b %d at %I:%M %p")
                    })
                    if len(suggestions) >= 5: return suggestions
                    
                    # Move forward
                    current_time += timedelta(minutes=duration_minutes)
                
                if not is_free and current_time < end_of_day:
                    # current_time was already advanced in the overlap logic
                    pass
                else:
                    current_time += timedelta(minutes=15) # Small padding
            
            if len(suggestions) >= 3: break
                
        return suggestions[:3]

scheduling_suggestion_service = SchedulingSuggestionService()
