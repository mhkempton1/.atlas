import pytest
from unittest.mock import MagicMock, patch
from services.embedding_service import embedding_service

@pytest.fixture
def mock_ai_service():
    mock = MagicMock()
    with patch.object(embedding_service, 'ai_service', mock):
        yield mock

@pytest.fixture
def mock_search_service():
    mock = MagicMock()
    mock_collection = MagicMock()
    mock.email_collection = mock_collection
    with patch.object(embedding_service, 'search_service', mock):
        yield mock

def test_generate_email_embedding_new_success(mock_ai_service, mock_search_service):
    # Setup
    email_data = {
        "body": "word " * 60, # > 50 words
        "subject": "Test Subject",
        "sender": "test@example.com",
        "message_id": "msg123",
        "date": "2023-10-01"
    }

    # Mock non-existence
    mock_search_service.email_collection.get.return_value = {'ids': []}
    mock_ai_service.get_embedding.return_value = [0.1, 0.2, 0.3]

    # Execute
    result = embedding_service.generate_email_embedding(email_data)

    # Verify
    assert result is True
    mock_ai_service.get_embedding.assert_called_once()
    mock_search_service.email_collection.upsert.assert_called_once()

    # Verify arguments to upsert
    call_args = mock_search_service.email_collection.upsert.call_args[1]
    assert call_args['ids'] == ["msg123"]
    assert call_args['embeddings'] == [[0.1, 0.2, 0.3]]
    assert call_args['metadatas'][0]['subject'] == "Test Subject"

def test_generate_email_embedding_exists_update_only(mock_ai_service, mock_search_service):
    # Setup
    email_data = {
        "body": "word " * 60,
        "subject": "Updated Subject",
        "sender": "test@example.com",
        "message_id": "msg123",
        "date": "2023-10-02"
    }

    # Mock existence
    mock_search_service.email_collection.get.return_value = {
        'ids': ['msg123']
    }

    # Execute
    result = embedding_service.generate_email_embedding(email_data)

    # Verify
    assert result is True
    # Embedding should NOT be generated
    mock_ai_service.get_embedding.assert_not_called()
    # Upsert should NOT be called
    mock_search_service.email_collection.upsert.assert_not_called()
    # Update SHOULD be called
    mock_search_service.email_collection.update.assert_called_once()

    # Verify update args
    call_args = mock_search_service.email_collection.update.call_args[1]
    assert call_args['ids'] == ["msg123"]
    assert call_args['metadatas'][0]['subject'] == "Updated Subject"

def test_generate_email_embedding_short_body(mock_ai_service, mock_search_service):
    # Setup
    email_data = {
        "body": "Short body",
        "subject": "Test",
        "sender": "test@example.com",
        "message_id": "msg123"
    }

    # Execute
    result = embedding_service.generate_email_embedding(email_data)

    # Verify
    assert result is False
    mock_ai_service.get_embedding.assert_not_called()
    mock_search_service.email_collection.upsert.assert_not_called()
    mock_search_service.email_collection.get.assert_not_called() # Doesn't even check if short

def test_semantic_search_emails(mock_ai_service, mock_search_service):
    # Setup
    mock_ai_service.get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_search_service.email_collection.query.return_value = {
        'ids': [['msg1', 'msg2']],
        'distances': [[0.1, 0.2]],
        'metadatas': [[{'subject': 'S1'}, {'subject': 'S2'}]],
        'documents': [['Doc 1', 'Doc 2']]
    }

    # Execute
    results = embedding_service.semantic_search_emails("query", top_k=5)

    # Verify
    assert len(results) == 2
    assert results[0]['id'] == 'msg1'
    assert results[0]['score'] == 0.1
    mock_ai_service.get_embedding.assert_called_with("query")
    mock_search_service.email_collection.query.assert_called_once()
