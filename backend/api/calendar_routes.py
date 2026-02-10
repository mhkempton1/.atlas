from fastapi import APIRouter, Depends, HTTPException, Query
from database.database import get_db
from database.models import CalendarEvent
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

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
            "event_id": e.event_id,
            "remote_event_id": e.remote_event_id,
            "title": e.title,
            "description": e.description,
            "location": e.location,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "all_day": e.all_day,
            "attendees": e.attendees,
            "organizer": e.organizer,
            "status": e.status,
            "project_id": e.project_id
        }
        for e in events
    ]

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
            "event_id": e.event_id,
            "title": e.title,
            "location": e.location,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "all_day": e.all_day,
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
