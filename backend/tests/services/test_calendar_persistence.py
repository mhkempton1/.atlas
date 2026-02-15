import pytest
from datetime import datetime, timedelta, timezone
from services.calendar_persistence_service import calendar_persistence_service
from database.models import CalendarEvent

def test_persist_calendar_event_create(db):
    event_data = {
        "google_calendar_id": "test_id_1",
        "title": "Test Event",
        "start_time": datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc),
        "end_time": datetime(2023, 10, 27, 11, 0, 0, tzinfo=timezone.utc),
        "description": "Test Description",
        "location": "Test Location",
        "is_all_day": False
    }

    event = calendar_persistence_service.persist_calendar_event(event_data, db)

    assert event.id is not None
    assert event.google_calendar_id == "test_id_1"
    assert event.title == "Test Event"
    assert event.start_time == event_data["start_time"]

    # Check DB
    db_event = db.query(CalendarEvent).filter_by(google_calendar_id="test_id_1").first()
    assert db_event is not None
    assert db_event.title == "Test Event"

def test_persist_calendar_event_update(db):
    # Create initial event
    event_data = {
        "google_calendar_id": "test_id_2",
        "title": "Initial Title",
        "start_time": datetime(2023, 10, 28, 10, 0, 0, tzinfo=timezone.utc),
        "end_time": datetime(2023, 10, 28, 11, 0, 0, tzinfo=timezone.utc),
    }
    calendar_persistence_service.persist_calendar_event(event_data, db)

    # Update
    update_data = event_data.copy()
    update_data["title"] = "Updated Title"
    update_data["description"] = "Added Description"

    event = calendar_persistence_service.persist_calendar_event(update_data, db)

    assert event.title == "Updated Title"
    assert event.description == "Added Description"

    # Check DB
    db_event = db.query(CalendarEvent).filter_by(google_calendar_id="test_id_2").first()
    assert db_event.title == "Updated Title"

def test_detect_conflicts(db):
    base_time = datetime(2023, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Event 1: 10:00 - 11:00
    e1_data = {
        "google_calendar_id": "c1",
        "title": "Conflict 1",
        "start_time": base_time,
        "end_time": base_time + timedelta(hours=1)
    }
    calendar_persistence_service.persist_calendar_event(e1_data, db)

    # Event 2: 10:30 - 11:30 (Overlaps with 1)
    e2_data = {
        "google_calendar_id": "c2",
        "title": "Conflict 2",
        "start_time": base_time + timedelta(minutes=30),
        "end_time": base_time + timedelta(hours=1, minutes=30)
    }
    calendar_persistence_service.persist_calendar_event(e2_data, db)

    # Event 3: 12:00 - 13:00 (No overlap)
    e3_data = {
        "google_calendar_id": "c3",
        "title": "No Conflict",
        "start_time": base_time + timedelta(hours=2),
        "end_time": base_time + timedelta(hours=3)
    }
    calendar_persistence_service.persist_calendar_event(e3_data, db)

    conflicts = calendar_persistence_service.detect_conflicts(base_time, db)

    # Conflicts should return overlapping events
    # c1 overlaps c2. c2 overlaps c1.
    # So we expect 2 events.

    assert len(conflicts) == 2
    ids = [e.google_calendar_id for e in conflicts]
    assert "c1" in ids
    assert "c2" in ids
    assert "c3" not in ids

def test_detect_conflicts_no_overlap(db):
    base_time = datetime(2023, 11, 2, 10, 0, 0, tzinfo=timezone.utc)

    # Event 1: 10:00 - 11:00
    e1_data = {
        "google_calendar_id": "no_c1",
        "title": "Event 1",
        "start_time": base_time,
        "end_time": base_time + timedelta(hours=1)
    }
    calendar_persistence_service.persist_calendar_event(e1_data, db)

    # Event 2: 11:00 - 12:00 (Adjacent, not overlapping)
    e2_data = {
        "google_calendar_id": "no_c2",
        "title": "Event 2",
        "start_time": base_time + timedelta(hours=1),
        "end_time": base_time + timedelta(hours=2)
    }
    calendar_persistence_service.persist_calendar_event(e2_data, db)

    conflicts = calendar_persistence_service.detect_conflicts(base_time, db)
    assert len(conflicts) == 0
