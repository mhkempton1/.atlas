import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Task
from services.task_sync_service import task_sync_service

# Setup test DB
engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)

@pytest.fixture(scope="module")
def db_engine():
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def test_sync_new_task(db):
    project_id = "P-123"
    alt_tasks = [{
        "id": "A-1",
        "project_id": project_id,
        "name": "New Task",
        "status": "In Progress",
        "updated_at": "2023-10-27T10:00:00Z"
    }]

    with patch("services.task_sync_service.altimeter_service.get_project_tasks", return_value=alt_tasks):
        task_sync_service.sync_tasks_from_altimeter(project_id, db)

    task = db.query(Task).filter(Task.related_altimeter_task_id == "A-1").first()
    assert task is not None
    assert task.title == "New Task"
    assert task.status == "in_progress"
    assert task.project_id == project_id

def test_sync_update_task(db):
    project_id = "P-123"
    # Create existing task
    task = Task(
        title="Old Title",
        status="open",
        project_id=project_id,
        related_altimeter_task_id="A-2",
        updated_at=datetime(2023, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
    )
    db.add(task)
    db.commit()

    alt_tasks = [{
        "id": "A-2",
        "project_id": project_id,
        "name": "New Title",
        "status": "Done",
        "updated_at": "2023-10-27T12:00:00Z" # Newer
    }]

    with patch("services.task_sync_service.altimeter_service.get_project_tasks", return_value=alt_tasks), \
         patch("services.task_sync_service.notification_service.push_notification") as mock_notify:

        task_sync_service.sync_tasks_from_altimeter(project_id, db)

        mock_notify.assert_called_once()

    db.refresh(task)
    assert task.title == "New Title"
    assert task.status == "done"

def test_sync_conflict_atlas_newer(db):
    project_id = "P-123"
    # Create existing task newer than Altimeter
    task = Task(
        title="Atlas Title",
        status="in_progress",
        project_id=project_id,
        related_altimeter_task_id="A-3",
        updated_at=datetime(2023, 10, 28, 10, 0, 0, tzinfo=timezone.utc)
    )
    db.add(task)
    db.commit()

    alt_tasks = [{
        "id": "A-3",
        "project_id": project_id,
        "name": "Altimeter Title",
        "status": "Done",
        "updated_at": "2023-10-27T12:00:00Z" # Older
    }]

    with patch("services.task_sync_service.altimeter_service.get_project_tasks", return_value=alt_tasks):
        task_sync_service.sync_tasks_from_altimeter(project_id, db)

    db.refresh(task)
    assert task.title == "Atlas Title" # Should not change
    assert task.status == "in_progress"
