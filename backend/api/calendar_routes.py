from fastapi import APIRouter, Depends, HTTPException, Query
from database.database import get_db
from database.models import CalendarEvent
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    attendees: Optional[str] = "[]"

@router.get("/events")
async def get_events(
    days: int = Query(default=14, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get upcoming calendar events for the next N days"""
    now = datetime.now()
    end = now + timedelta(days=days)

    events = db.query(CalendarEvent).filter(
        CalendarEvent.start_time >= now,
        CalendarEvent.start_time <= end
    ).order_by(CalendarEvent.start_time.asc()).all()

    return [
        {
            "event_id": e.id,
            "remote_event_id": e.google_calendar_id,
            "title": e.title,
            "description": e.description,
            "location": e.location,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "all_day": e.is_all_day,
            "attendees": e.attendees,
            "organizer": e.organizer,
            "status": e.status,
            "project_id": e.project_id
        }
        for e in events
    ]

@router.post("/events")
async def create_event(
    event: CalendarEventCreate,
    db: Session = Depends(get_db)
):
    """Create a new calendar event"""
    from services.communication_service import comm_service
    
    # 1. Create in local DB
    new_event = CalendarEvent(
        title=event.title,
        description=event.description,
        location=event.location,
        start_time=event.start_time,
        end_time=event.end_time,
        is_all_day=event.all_day,
        attendees=event.attendees,
        status="confirmed",
        synced_at=datetime.now()
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    # 2. Push to remote provider
    try:
        remote_result = comm_service.create_event(event.dict())
        if remote_result and "id" in remote_result:
            new_event.google_calendar_id = remote_result["id"]
            db.commit()
    except Exception as e:
        # We keep the local copy even if remote fail, but log it
        print(f"Remote sync failed: {e}")
        
    return {"status": "success", "event_id": new_event.id}

@router.get("/today")
async def get_today_events(db: Session = Depends(get_db)):
    """Get today's events"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    events = db.query(CalendarEvent).filter(
        CalendarEvent.start_time >= today_start,
        CalendarEvent.start_time < today_end
    ).order_by(CalendarEvent.start_time.asc()).all()

    return [
        {
            "event_id": e.id,
            "title": e.title,
            "location": e.location,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "all_day": e.is_all_day,
            "status": e.status,
            "attendees": e.attendees
        }
        for e in events
    ]

@router.post("/sync")
async def trigger_calendar_sync():
    """Manually trigger a calendar sync from the active provider"""
    from services.communication_service import comm_service
    result = comm_service.sync_calendar()
    return result
