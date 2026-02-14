import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from services.learning_service import learning_service
from database.models import Learning

@pytest.fixture
def mock_session_local(db):
    """
    Patch SessionLocal in learning_service to return the test db session (wrapped).
    This ensures that when learning_service creates a new session, it gets our test session.
    """
    # Patch the class/function SessionLocal in the service module
    with patch("services.learning_service.SessionLocal") as mock:
        # We need to mock close() to do nothing (so the fixture can handle cleanup),
        # and commit() to flush() (to preserve the transaction for rollback).

        # Wrap the db session to intercept close and commit
        mock_session = MagicMock(wraps=db)
        mock_session.close.side_effect = lambda: None
        mock_session.commit.side_effect = db.flush # Use flush instead of commit to keep transaction open for rollback

        mock.return_value = mock_session
        yield mock_session

def test_record_lesson_creates_new(mock_session_local):
    # Act
    learning_service.record_lesson("Topic A", "Insight A", "Source A")

    # Assert
    # Verify it's in the DB
    lesson = mock_session_local.query(Learning).filter_by(topic="Topic A").first()
    assert lesson is not None
    assert lesson.insight == "Insight A"
    assert lesson.source == "Source A"

def test_record_lesson_deduplicates(mock_session_local):
    # Setup - insert existing with old timestamp
    old_time = datetime.now() - timedelta(days=1)
    l1 = Learning(topic="Topic B", insight="Insight B", source="Old Source", created_at=old_time)
    mock_session_local.add(l1)
    mock_session_local.flush()
    mock_session_local.refresh(l1)

    initial_created_at = l1.created_at

    # Act
    learning_service.record_lesson("Topic B", "Insight B", "New Source")

    # Assert
    mock_session_local.expire_all() # Force reload from DB
    l1_reloaded = mock_session_local.query(Learning).filter_by(topic="Topic B").first()

    assert l1_reloaded.created_at > initial_created_at
    # Source should NOT be updated based on requirements ("update timestamp only")
    # But checking implementation:
    # existing.created_at = datetime.now()
    # db.commit()
    # It doesn't update source.
    assert l1_reloaded.source == "Old Source"

def test_get_recent_lessons(mock_session_local):
    # Setup
    t1 = datetime.now()
    t2 = datetime.now() - timedelta(hours=1)
    l1 = Learning(topic="T1", insight="I1", source="S1", created_at=t1)
    l2 = Learning(topic="T2", insight="I2", source="S2", created_at=t2)
    mock_session_local.add(l1)
    mock_session_local.add(l2)
    mock_session_local.flush()

    # Act
    lessons = learning_service.get_recent_lessons(limit=10)

    # Assert
    assert len(lessons) == 2
    assert lessons[0]["topic"] == "T1"
    assert lessons[1]["topic"] == "T2"

def test_ai_service_integration():
    from services.ai_service import ai_service

    # Mock learning_service within ai_service context
    with patch("services.learning_service.learning_service") as mock_ls:
        mock_ls.get_recent_lessons.return_value = [
             {"topic": "T_AI", "insight": "I_AI", "source": "S_AI", "created_at": "2023-01-01T00:00:00"}
        ]

        context = ai_service._build_context(user_strata=1)

        assert "Previous learnings:" in context
        assert "- 2023-01-01T00:00:00: [T_AI] I_AI" in context
