import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from services.scheduler_service import scheduler_service
from database.models import Task, CalendarEvent, Email

@pytest.fixture
def mock_session_local(db):
    """
    Patch SessionLocal in scheduler_service to use the test session.
    Prevent the service from closing the session, so we can verify data.
    """
    original_close = db.close
    db.close = lambda: None

    # We patch database.database.SessionLocal because the service imports it
    with patch("database.database.SessionLocal", return_value=db):
        yield db

    db.close = original_close

@pytest.fixture
def mock_altimeter_service():
    with patch("services.altimeter_service.altimeter_service") as m:
        yield m

@pytest.fixture
def mock_document_control_service():
    with patch("services.document_control_service.document_control_service") as m:
        yield m

def test_get_my_schedule(mock_session_local, mock_altimeter_service):
    db = mock_session_local
    today = datetime.now()

    # 1. Calendar Event (Today + 1h)
    event = CalendarEvent(
        title="Meeting",
        start_time=today + timedelta(hours=1),
        end_time=today + timedelta(hours=2),
        status="confirmed",
        provider_type="google",
        remote_event_id="evt1"
    )
    db.add(event)

    # 2. Task (Due tomorrow)
    task = Task(
        title="Coding",
        status="in_progress",
        priority="high",
        due_date=today + timedelta(days=1),
        original_due_date=today
    )
    db.add(task)
    db.commit()

    # 3. Mock Altimeter
    mock_altimeter_service.get_upcoming_milestones.return_value = [
        {
            "id": "m1",
            "title": "Milestone 1",
            "altimeter_project_id": "p1",
            "due_date": "2024-01-01",
            "project_name": "Project X"
        }
    ]

    # Run
    schedule = scheduler_service.get_my_schedule("EMP005")

    # Verify
    assert len(schedule) == 3

    types = [item["type"] for item in schedule]
    assert "calendar" in types
    assert "task" in types
    assert "altimeter" in types

    cal_item = next(i for i in schedule if i["type"] == "calendar")
    assert cal_item["name"] == "Meeting"

    task_item = next(i for i in schedule if i["type"] == "task")
    assert task_item["name"] == "Coding"
    assert task_item["status"] == "Prioritized" # high priority -> Prioritized

    alt_item = next(i for i in schedule if i["type"] == "altimeter")
    assert alt_item["name"] == "Milestone 1"

@pytest.mark.asyncio
async def test_get_dashboard_stats(mock_session_local, mock_altimeter_service, mock_document_control_service):
    db = mock_session_local
    today = datetime.now()

    # Setup Data
    # 1. Pending Task
    t1 = Task(title="T1", status="todo", priority="medium")
    db.add(t1)
    # 2. High Priority Task
    t2 = Task(title="T2", status="todo", priority="high")
    db.add(t2)
    # 3. Upcoming Event
    e1 = CalendarEvent(
        title="E1",
        start_time=today + timedelta(hours=1),
        end_time=today + timedelta(hours=2),
        provider_type="google",
        remote_event_id="evt2"
    )
    db.add(e1)
    # 4. Email
    email = Email(
        subject="S1",
        is_read=False,
        from_address="a@b.c",
        body_text="b",
        date_received=today,
        remote_id="msg1"
    )
    db.add(email)

    db.commit()

    # Mocks
    mock_document_control_service.get_all_documents.return_value = {
        "draft": ["d1", "d2"],
        "review": ["r1"]
    }

    mock_altimeter_service.list_projects.return_value = ["p1", "p2", "p3"]

    # Run
    stats = await scheduler_service.get_dashboard_stats()

    # Verify
    assert stats["drafts"] == 2
    assert stats["reviews"] == 1
    assert stats["pending_tasks"] == 2 # T1, T2
    assert stats["high_priority_tasks"] == 1 # T2
    assert stats["upcoming_events"] == 1
    assert stats["inbox_total"] == 1
    assert stats["inbox_unread"] == 1
    assert stats["active_projects"] == 3
