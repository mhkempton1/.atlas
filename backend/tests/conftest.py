import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

print(f"DEBUG: backend_dir={backend_dir}")
print(f"DEBUG: sys.path={sys.path}")

from core.app import app
from database.database import Base, get_db
from core.config import settings
from services.ai_service import ai_service
from services.google_service import google_service

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_atlas.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_ai_service(monkeypatch):
    mock = AsyncMock()
    mock.generate_content.return_value = "Mocked AI Response"
    monkeypatch.setattr("services.ai_service.ai_service", mock)
    # Also monkeypatch where it's imported in other modules if necessary, 
    # but since it's a singleton imported, monkeypatching the service module might be enough 
    # if they import 'ai_service' from 'services.ai_service'.
    return mock

@pytest.fixture
def mock_google_service(monkeypatch):
    mock = MagicMock()
    mock.send_email.return_value = {"success": True, "message_id": "mock_id"}
    mock.sync_emails.return_value = {"success": True, "count": 5}
    mock.sync_calendar.return_value = {"success": True, "count": 2}
    monkeypatch.setattr("services.google_service.google_service", mock)
    monkeypatch.setattr("api.routes.google_service", mock)
    return mock

@pytest.fixture
def mock_draft_agent(monkeypatch):
    mock = AsyncMock()
    mock.process.return_value = {
        "draft_text": "API Mocked Draft",
        "status": "generated",
        "model": "gemini-2.0-flash",
        "context_used": {"test": "context"}
    }
    monkeypatch.setattr("agents.draft_agent.draft_agent", mock)
    monkeypatch.setattr("api.routes.draft_agent", mock)
    return mock

@pytest.fixture
def temp_onedrive(tmp_path, monkeypatch):
    """Mock OneDrive path for document control tests"""
    mock_path = tmp_path / "OneDrive"
    mock_path.mkdir()
    (mock_path / "GUIDELINES").mkdir()
    (mock_path / "GUIDELINES" / "DRAFTS").mkdir()
    (mock_path / "GUIDELINES" / "REVIEW").mkdir()
    (mock_path / "GUIDELINES" / "LOCKED").mkdir()
    (mock_path / "GUIDELINES" / "ARCHIVE").mkdir()
    
    # Update settings
    monkeypatch.setattr(settings, "ONEDRIVE_PATH", str(mock_path))
    
    # Update the service singletons
    from services.document_control_service import document_control_service
    from services.knowledge_service import knowledge_service
    
    monkeypatch.setattr(document_control_service, "root_path", str(mock_path))
    monkeypatch.setattr(knowledge_service, "sources", {
        "obsidian": str(tmp_path / "Obsidian"),
        "onedrive": str(mock_path)
    })
    
    # Create extra directories
    (tmp_path / "Obsidian").mkdir()
    (mock_path / "PROJECTS").mkdir()
    (mock_path / "SKILLS").mkdir()
    (mock_path / "TRAINING").mkdir()

    return mock_path
