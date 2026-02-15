from sqlalchemy.orm import Session
from database.models import CalendarEvent
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class CalendarPersistenceService:
    def persist_calendar_event(self, event_data: Dict[str, Any], db: Session) -> CalendarEvent:
        """
        Persists a calendar event to the database.

        Args:
            event_data: A dictionary containing event data.
                        Required keys: google_calendar_id, title, start_time, end_time
            db: The database session.

        Returns:
            The persisted CalendarEvent object.
        """
        google_id = event_data.get('google_calendar_id')

        # Helper to ensure tz-aware
        def ensure_tz(dt):
            if isinstance(dt, str):
                try:
                    # Handle Z suffix
                    if dt.endswith('Z'):
                        dt = dt[:-1] + '+00:00'
                    return datetime.fromisoformat(dt)
                except:
                    return None
            if dt and dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        start_time = ensure_tz(event_data.get('start_time'))
        end_time = ensure_tz(event_data.get('end_time'))

        # Prepare update data
        update_data = {
            "title": event_data.get('title'),
            "description": event_data.get('description'),
            "start_time": start_time,
            "end_time": end_time,
            "location": event_data.get('location'),
            "is_all_day": event_data.get('is_all_day', False),
            "status": event_data.get('status', 'confirmed'),
            "attendees": event_data.get('attendees'),
            "organizer": event_data.get('organizer'),
            "calendar_id": event_data.get('calendar_id'),
            "project_id": event_data.get('project_id'),
            "is_recurring": event_data.get('is_recurring', False),
            "recurrence_rule": event_data.get('recurrence_rule'),
            "related_email_id": event_data.get('related_email_id'),
            "is_declined": event_data.get('is_declined', False),
            "synced_at": datetime.now(timezone.utc)
        }

        existing_event = None
        if google_id:
            existing_event = db.query(CalendarEvent).filter(CalendarEvent.google_calendar_id == google_id).first()

        if existing_event:
            # Update
            for key, value in update_data.items():
                setattr(existing_event, key, value)
            return existing_event
        else:
            # Create
            new_event = CalendarEvent(
                google_calendar_id=google_id,
                **update_data
            )
            db.add(new_event)
            db.flush() # Flush to get ID
            return new_event

    def detect_conflicts(self, check_date: datetime, db: Session) -> List[CalendarEvent]:
        """
        Detects conflicting events (overlaps) for a specific date.

        Args:
            check_date: The date to check for conflicts (datetime object).
            db: The database session.

        Returns:
            A list of CalendarEvent objects that are part of an overlap on the given date.
        """
        # Ensure check_date is tz-aware or strip it for comparison if stored as naive (sqlite usually naive or consistent)
        # But our models use DateTime(timezone=True).
        if check_date.tzinfo is None:
            check_date = check_date.replace(tzinfo=timezone.utc)

        start_of_day = check_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = check_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Fetch events for the day
        events = db.query(CalendarEvent).filter(
            CalendarEvent.start_time >= start_of_day,
            CalendarEvent.start_time <= end_of_day,
            CalendarEvent.status == 'confirmed',
            CalendarEvent.is_all_day == False
        ).order_by(CalendarEvent.start_time).all()

        conflicting_events = set()
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                e1 = events[i]
                e2 = events[j]

                # Check overlap: Start1 < End2 and Start2 < End1
                if e1.start_time < e2.end_time and e2.start_time < e1.end_time:
                    conflicting_events.add(e1)
                    conflicting_events.add(e2)

        return list(conflicting_events)

    def get_conflicts(self, start_date: datetime, end_date: datetime, db: Session) -> List[Dict[str, Any]]:
        """
        Detects conflicting events (overlaps) within a date range.

        Args:
            start_date: The start of the range.
            end_date: The end of the range.
            db: The database session.

        Returns:
            A list of dictionaries, each containing 'event_1', 'event_2', and 'overlap_time'.
        """
        # Ensure aware
        if start_date.tzinfo is None: start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None: end_date = end_date.replace(tzinfo=timezone.utc)

        events = db.query(CalendarEvent).filter(
            CalendarEvent.end_time > start_date,
            CalendarEvent.start_time < end_date,
            CalendarEvent.status == 'confirmed',
            CalendarEvent.is_all_day == False,
            CalendarEvent.is_declined == False
        ).order_by(CalendarEvent.start_time).all()

        conflicts = []
        processed_pairs = set()

        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                e1 = events[i]
                e2 = events[j]

                # Check overlap: Start1 < End2 and Start2 < End1
                if e1.start_time < e2.end_time and e2.start_time < e1.end_time:
                    # Create a unique key for the pair to avoid duplicates if revisited
                    pair_key = tuple(sorted([e1.id, e2.id]))
                    if pair_key not in processed_pairs:
                        processed_pairs.add(pair_key)

                        overlap_start = max(e1.start_time, e2.start_time)
                        overlap_end = min(e1.end_time, e2.end_time)

                        conflicts.append({
                            "event_1": e1,
                            "event_2": e2,
                            "overlap_start": overlap_start,
                            "overlap_end": overlap_end
                        })

        return conflicts

calendar_persistence_service = CalendarPersistenceService()
