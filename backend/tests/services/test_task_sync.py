import pytest
from unittest.mock import MagicMock, patch
from services.altimeter_service import AltimeterService
from services.task_sync_service import TaskSyncService
from database.models import Task, TaskSyncLog
import datetime
import os
import sqlite3

# --- Integration Test for AltimeterService ---

def test_altimeter_service_sync_task():
    # Ensure we are using the dummy DB
    # We can instantiate a new service or use the singleton if we are sure about the path
    service = AltimeterService()

    # Verify DB connection points to our dummy DB
    expected_db_path = os.path.join(os.path.expanduser("~"), ".altimeter", "database", "altimeter.db")
    # Assert path matches (handling potential differences in absolute path resolution)
    assert os.path.abspath(service.db_path) == os.path.abspath(expected_db_path)
    assert os.path.exists(service.db_path)

    task_data = {
        "title": "Integration Test Task",
        "description": "Testing sync",
        "priority": "high",
        "status": "todo",
        "due_date": "2023-12-31",
        "project_id": "25-0001" # Matches the dummy project I inserted
    }

    new_id = service.sync_task_to_altimeter(task_data)
    assert new_id is not None

    # Verify insertion
    conn = sqlite3.connect(expected_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    # id, project_id, name, description, priority, status, due_date ...
    # Schema: id, project_id, name, description, priority, status, due_date, ...
    # Indices: 0, 1,          2,    3,           4,        5,       6
    assert row[1] == "25-0001"
    assert row[2] == "Integration Test Task"
    assert row[3] == "Testing sync"
    assert row[4] == 3 # high -> 3
    assert row[5] == "Open" # todo -> Open

# --- Unit Test for TaskSyncService ---

@patch("services.task_sync_service.altimeter_service")
def test_create_altimeter_task_from_atlas(mock_alt_service):
    mock_alt_service.sync_task_to_altimeter.return_value = "999"

    mock_db = MagicMock()

    # Mock Atlas Task
    mock_task = Task(
        task_id=1,
        title="Atlas Task",
        description="Description",
        status="in_progress",
        priority="medium",
        due_date=datetime.datetime(2023, 10, 10, 10, 0, 0),
        project_id="25-0001"
    )

    # Setup query return
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_task
    mock_db.query.return_value = mock_query

    service = TaskSyncService()
    result = service.create_altimeter_task_from_atlas(1, None, mock_db)

    assert result["status"] == "success"
    assert result["altimeter_task_id"] == "999"

    # Verify AltimeterService called with correct data
    mock_alt_service.sync_task_to_altimeter.assert_called_once()
    call_args = mock_alt_service.sync_task_to_altimeter.call_args[0][0]
    assert call_args["title"] == "Atlas Task"
    assert call_args["priority"] == "medium"
    assert call_args["project_id"] == "25-0001"

    # Verify Task Updated
    assert mock_task.related_altimeter_task_id == "999"

    # Verify SyncLog created
    mock_db.add.assert_called_once()
    added_obj = mock_db.add.call_args[0][0]
    assert isinstance(added_obj, TaskSyncLog)
    assert added_obj.atlas_task_id == 1
    assert added_obj.altimeter_task_id == "999"
    assert added_obj.sync_direction == "atlas_to_altimeter"

    mock_db.commit.assert_called_once()
