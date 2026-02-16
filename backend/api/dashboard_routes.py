from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
from services.task_service import task_service
from services.calendar_service import calendar_service
from services.email_service import email_service
from services.weather_service import weather_service
from services.urgency_service import urgency_service

router = APIRouter()

@router.get("/my-day")
async def get_my_day_summary():
    """
    Unified 'My Day' executive summary.
    Aggregates tasks, high-priority emails, and schedule.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        # 1. Tasks: Due today or Overdue
        all_tasks = task_service.list_tasks()
        my_tasks = [
            t for t in all_tasks 
            if t.get("due_date") and (t["due_date"] <= today_str) and not t.get("completed")
        ]
        
        # 2. Urgent Emails (Score > 70)
        all_emails = email_service.list_emails(limit=20)
        urgent_emails = [
            e for e in all_emails 
            if (e.get("urgency_score") or 0) > 70 and not e.get("is_read")
        ]
        
        # 3. Calendar: Next 24 hours
        events = calendar_service.list_events()
        upcoming_events = []
        for event in events:
            start_time = event.get("start_time")
            if start_time:
                try:
                    event_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if now <= event_dt <= (now + timedelta(days=1)):
                        upcoming_events.append(event)
                except:
                    pass
        
        # 4. Weather Context
        weather = None
        try:
            weather = await weather_service.get_weather()
        except:
            pass

        return {
            "date": today_str,
            "tasks": my_tasks,
            "urgent_emails": urgent_emails,
            "upcoming_events": upcoming_events,
            "weather": weather,
            "summary_intel": f"You have {len(my_tasks)} tasks and {len(upcoming_events)} events today."
        }
        
    except Exception as e:
        print(f"[Dashboard] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
