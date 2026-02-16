import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from unittest.mock import AsyncMock, patch

from database.database import Base
from database.models import Task, SyncQueue
from services.altimeter_sync_service import AltimeterSyncService
from services.altimeter_api_service import AltimeterAPIService

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_api():
    return AsyncMock(spec=AltimeterAPIService)

@pytest.fixture
def sync_service(mock_api):
    service = AltimeterSyncService()
    with patch('services.altimeter_sync_service.altimeter_api_service', mock_api):
        yield service

@pytest.mark.asyncio
async def test_integration_push_flow(sync_service, test_db, mock_api):
    # 1. Create Task
    task = Task(title="Integration Task", status="open")
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)

    # 2. Enqueue Push
    item = sync_service.enqueue_task(test_db, task.task_id, 'push')
    assert item.status == 'pending'

    # 3. Process Queue
    mock_api.create_task.return_value = {"id": "remote_999", "title": "Integration Task"}

    await sync_service._process_item(item, test_db)

    # 4. Verify
    test_db.refresh(item)
    test_db.refresh(task)

    assert item.status == 'synced'
    assert task.remote_id == "remote_999"
    assert task.sync_status == 'synced'
    mock_api.create_task.assert_called_once()

@pytest.mark.asyncio
async def test_integration_pull_flow(sync_service, test_db, mock_api):
    # 1. Create Task with remote ID
    task = Task(title="Old Title", status="open", remote_id="remote_888")
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)

    # 2. Enqueue Pull
    item = sync_service.enqueue_task(test_db, task.task_id, 'pull')

    # 3. Process Queue
    mock_api.get_task.return_value = {
        "id": "remote_888",
        "title": "New Remote Title",
        "description": "Updated Desc",
        "status": "in_progress"
    }

    await sync_service._process_item(item, test_db)

    # 4. Verify
    test_db.refresh(task)
    assert task.title == "New Remote Title"
    assert task.description == "Updated Desc"
    assert task.status == "in_progress"
    assert task.sync_status == 'synced'
