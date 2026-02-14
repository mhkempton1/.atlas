import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from services.scheduler_service import scheduler_service
from database.models import Task, CalendarEvent, Email
from sqlalchemy.orm import Session

@pytest.fixture
def patch_session(db):
    """
    Patch SchedulerService.SessionLocal to use the test 'db' session.
    """
    mock_session = MagicMock(wraps=db)
    mock_session.commit = db.flush
    mock_session.close = lambda: None

    # We also need to patch the SessionLocal imported inside methods
    # Since imports happen inside methods, we patch where it is imported FROM.
    # But wait, 'from database.database import SessionLocal'.
    # So we patch 'database.database.SessionLocal'.

    def get_session():
        return mock_session

    with patch("database.database.SessionLocal", side_effect=get_session):
        yield

@pytest.fixture
def mock_dependencies():
    """Mock external dependencies used in scheduler service."""
    # We patch the service instances in their respective modules
    with patch("services.document_control_service.document_control_service") as mock_docs, \
         patch("services.altimeter_service.altimeter_service") as mock_alt:

        mock_docs.get_all_documents.return_value = {
            "draft": ["d1", "d2"],
            "review": ["r1"]
        }

        mock_alt.list_projects.return_value = ["p1", "p2"]
        mock_alt.get_upcoming_milestones.return_value = [
            {
                "id": "m1",
                "title": "Milestone 1",
                "altimeter_project_id": "25-001",
                "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "project_name": "Project Alpha"
            }
        ]
        yield mock_docs, mock_alt

def test_get_my_schedule(db, patch_session, mock_dependencies):
    """Test aggregation of schedule items."""
    # 1. Create Calendar Event
    event = CalendarEvent(
        event_id=1, # Integer PK
        remote_event_id="g1",
        title="Meeting",
        start_time=datetime.now() + timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=2),
        status="confirmed",
        project_id="25-001"
    )
    db.add(event)

    # 2. Create Task
    now = datetime.now()
    task = Task(
        title="Coding",
        status="todo",
        priority="high",
        due_date=now + timedelta(days=1),
        original_due_date=now
    )
    db.add(task)
    db.flush() # ensure IDs are generated

    # Run
    schedule = scheduler_service.get_my_schedule("user")

    # Assert
    assert len(schedule) >= 3 # 1 event, 1 task, 1 milestone (mocked)

    types = [item["type"] for item in schedule]
    assert "calendar" in types
    assert "task" in types
    assert "altimeter" in types

    # Check event
    cal_item = next(i for i in schedule if i["type"] == "calendar")
    assert cal_item["name"] == "Meeting"
    assert cal_item["status"] == "Confirmed"

    # Check task
    task_item = next(i for i in schedule if i["type"] == "task")
    assert task_item["name"] == "Coding"
    assert task_item["status"] == "Prioritized" # high priority
    assert task_item["deviation"] == 1

@pytest.mark.asyncio
async def test_get_dashboard_stats(db, patch_session, mock_dependencies):
    """Test dashboard stats calculation."""
    # Add some data
    db.add(Task(title="T1", status="todo"))
    db.add(Task(title="T2", status="done"))
    db.add(Email(message_id="e1", is_read=False))
    db.add(Email(message_id="e2", is_read=True))
    db.add(CalendarEvent(
        event_id=2,
        remote_event_id="g2",
        title="Future",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1)
    ))
    db.flush()

    stats = await scheduler_service.get_dashboard_stats()

    assert stats["drafts"] == 2
    assert stats["reviews"] == 1
    assert stats["pending_tasks"] == 1 # T1 only
    assert stats["inbox_total"] == 2
    assert stats["inbox_unread"] == 1
    assert stats["upcoming_events"] == 1
    assert stats["active_projects"] == 2
