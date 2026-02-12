import pytest
from datetime import datetime, timedelta

def test_get_calendar_events(client, db):
    from database.models import CalendarEvent

    event = CalendarEvent(
        remote_event_id="gcal_test_001",
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
        remote_event_id="gcal_today_001",
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
