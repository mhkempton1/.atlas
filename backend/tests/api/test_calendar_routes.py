import pytest
from datetime import datetime, timedelta

def test_get_calendar_events(client, db):
    from database.models import CalendarEvent

    event = CalendarEvent(
        google_calendar_id="gcal_test_001",
        title="Test Meeting",
        start_time=datetime.now() + timedelta(hours=2),
        end_time=datetime.now() + timedelta(hours=3),
        status="confirmed"
    )
    db.add(event)
    db.commit()

    response = client.get("/api/v1/calendar/events?days=7")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Meeting"

def test_get_today_events(client, db):
    from database.models import CalendarEvent

    event = CalendarEvent(
        google_calendar_id="gcal_today_001",
        title="Today's Standup",
        start_time=datetime.now().replace(hour=9, minute=0),
        end_time=datetime.now().replace(hour=9, minute=30),
        status="confirmed"
    )
    db.add(event)
    db.commit()

    response = client.get("/api/v1/calendar/today")
    assert response.status_code == 200

def test_get_events_empty(client):
    response = client.get("/api/v1/calendar/events?days=1")
    assert response.status_code == 200

def test_get_conflicts(client, db):
    from database.models import CalendarEvent
    from datetime import timezone

    # Setup overlapping events
    now = datetime.now(timezone.utc)

    e1 = CalendarEvent(
        google_calendar_id="conf_1",
        title="Conflict A",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        status="confirmed"
    )
    db.add(e1)

    e2 = CalendarEvent(
        google_calendar_id="conf_2",
        title="Conflict B",
        start_time=now + timedelta(hours=1, minutes=30),
        end_time=now + timedelta(hours=2, minutes=30),
        status="confirmed"
    )
    db.add(e2)
    db.commit()

    response = client.get("/api/v1/calendar/conflicts?days=7")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    c = data[0]
    titles = [c["event_1"]["title"], c["event_2"]["title"]]
    assert "Conflict A" in titles
    assert "Conflict B" in titles
