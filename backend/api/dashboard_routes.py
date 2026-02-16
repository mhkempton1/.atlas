from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import Task, Email, CalendarEvent
from database.database import get_db
from services.weather_service import weather_service

router = APIRouter()

@router.get("/my-day")
async def get_my_day_summary(db: Session = Depends(get_db)):
    """
    Unified 'My Day' executive summary.
    Aggregates tasks, high-priority emails, and schedule.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        # 1. Tasks: Due today or Overdue
        tasks_query = db.query(Task).filter(
            Task.due_date <= today_str,
            Task.status != 'completed'
        ).order_by(Task.priority.desc(), Task.due_date).limit(10).all()

        my_tasks = [
            {
                "task_id": t.task_id,
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None
            }
            for t in tasks_query
        ]

        # 2. Urgent Emails (Score > 70)
        emails_query = db.query(Email).filter(
            Email.urgency_score > 70,
            Email.is_read == False
        ).order_by(Email.urgency_score.desc()).limit(10).all()

        urgent_emails = [
            {
                "email_id": e.email_id,
                "subject": e.subject,
                "from_address": e.from_address or e.sender,
                "from_name": e.from_address or e.sender,
                "urgency_score": e.urgency_score,
                "date_received": e.date_received.isoformat() if e.date_received else None
            }
            for e in emails_query
        ]

        # 3. Calendar: Next 24 hours
        tomorrow = now + timedelta(days=1)
        events_query = db.query(CalendarEvent).filter(
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= tomorrow
        ).order_by(CalendarEvent.start_time).limit(10).all()

        upcoming_events = [
            {
                "event_id": e.event_id,
                "summary": e.summary or e.title,
                "title": e.title,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "location": e.location
            }
            for e in events_query
        ]
        
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
