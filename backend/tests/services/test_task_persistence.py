import pytest
from unittest.mock import MagicMock
from services.task_persistence_service import TaskPersistenceService
from database.models import Task
import datetime

@pytest.fixture
def mock_db():
    return MagicMock()

def test_persist_task_to_database(mock_db):
    service = TaskPersistenceService()

    task_data = {
        "title": "Test Task",
        "description": "Description",
        "status": "open",
        "priority": "high",
        "project_id": "123",
        "email_id": 1,
        "source": "atlas_extracted",
        "assigned_to": "User1",
        "tags": ["tag1", "tag2"]
    }

    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    task = service.persist_task_to_database(task_data, mock_db)

    assert task.title == "Test Task"
    assert task.source == "atlas_extracted"
    assert task.assigned_to == "User1"
    assert task.tags == ["tag1", "tag2"]

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_update_task_status_completes_task(mock_db):
    service = TaskPersistenceService()

    mock_task = MagicMock(spec=Task)
    mock_task.task_id = 1
    mock_task.status = "open"
    mock_task.completed_at = None

    mock_db.query.return_value.filter.return_value.first.return_value = mock_task

    updated_task = service.update_task_status(1, "completed", mock_db)

    assert updated_task.status == "completed"
    assert updated_task.completed_at is not None
    mock_db.commit.assert_called_once()

def test_update_task_status_reopens_task(mock_db):
    service = TaskPersistenceService()

    mock_task = MagicMock(spec=Task)
    mock_task.task_id = 1
    mock_task.status = "completed"
    mock_task.completed_at = datetime.datetime.now()

    mock_db.query.return_value.filter.return_value.first.return_value = mock_task

    updated_task = service.update_task_status(1, "open", mock_db)

    assert updated_task.status == "open"
    assert updated_task.completed_at is None
    mock_db.commit.assert_called_once()

def test_get_tasks_by_status(mock_db):
    service = TaskPersistenceService()

    mock_db.query.return_value.filter.return_value.all.return_value = []

    tasks = service.get_tasks_by_status("open", mock_db)

    assert tasks == []
    mock_db.query.assert_called_once()

def test_get_tasks_by_email(mock_db):
    service = TaskPersistenceService()

    mock_db.query.return_value.filter.return_value.all.return_value = []

    tasks = service.get_tasks_by_email(1, mock_db)

    assert tasks == []
    mock_db.query.assert_called_once()
