import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone

from services.altimeter_sync_service import AltimeterSyncService
from database.models import Task, SyncQueue
from services.altimeter_api_service import AltimeterAPIService

@pytest.fixture
def mock_db():
    session = MagicMock()
    return session

@pytest.fixture
def mock_api():
    return AsyncMock(spec=AltimeterAPIService)

@pytest.fixture
def sync_service(mock_api):
    service = AltimeterSyncService()
    # Patch the global api service used inside the class
    with patch('services.altimeter_sync_service.altimeter_api_service', mock_api):
        yield service

@pytest.mark.asyncio
async def test_enqueue_task(sync_service, mock_db):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = None # No existing item

    # Act
    item = sync_service.enqueue_task(mock_db, 123, 'push')

    # Assert
    assert item.entity_id == 123
    assert item.direction == 'push'
    assert item.status == 'pending'
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_process_item_push_new(sync_service, mock_db, mock_api):
    # Setup
    item = SyncQueue(id=1, entity_type='task', entity_id=101, direction='push', status='pending')
    task = Task(task_id=101, title="Test Task", status="open", remote_id=None, priority="medium", description="desc", project_id="24-1234", due_date=None)

    mock_db.query.return_value.filter.return_value.first.return_value = task
    mock_api.create_task.return_value = {"id": "remote_123"}

    # Act
    await sync_service._process_item(item, mock_db)

    # Assert
    assert item.status == 'synced'
    assert task.remote_id == "remote_123"
    assert task.sync_status == 'synced'
    mock_api.create_task.assert_called_once()
    mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_process_item_push_update(sync_service, mock_db, mock_api):
    # Setup
    item = SyncQueue(id=1, entity_type='task', entity_id=101, direction='push', status='pending')
    task = Task(task_id=101, title="Test Task", status="open", remote_id="remote_123", priority="medium", description=None, project_id=None, due_date=None)

    mock_db.query.return_value.filter.return_value.first.return_value = task
    mock_api.update_task.return_value = {"id": "remote_123"}

    # Act
    await sync_service._process_item(item, mock_db)

    # Assert
    assert item.status == 'synced'
    mock_api.update_task.assert_called_once()

@pytest.mark.asyncio
async def test_process_item_failed_retry(sync_service, mock_db, mock_api):
    # Setup
    item = SyncQueue(id=1, entity_type='task', entity_id=101, direction='push', status='pending', retry_count=0)
    task = Task(task_id=101, title="Test Task", remote_id=None)

    mock_db.query.return_value.filter.return_value.first.return_value = task
    mock_api.create_task.side_effect = Exception("API Error")

    # Act
    await sync_service._process_item(item, mock_db)

    # Assert
    assert item.status == 'retry'
    assert item.retry_count == 1
    assert item.error_message == "API Error"
    mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_process_item_failed_max_retries(sync_service, mock_db, mock_api):
    # Setup
    item = SyncQueue(id=1, entity_type='task', entity_id=101, direction='push', status='retry', retry_count=2)
    task = Task(task_id=101, title="Test Task", remote_id=None)

    mock_db.query.return_value.filter.return_value.first.return_value = task
    mock_api.create_task.side_effect = Exception("API Error")

    # Act
    await sync_service._process_item(item, mock_db)

    # Assert
    assert item.status == 'failed'
    assert item.retry_count == 3
    mock_db.commit.assert_called()
