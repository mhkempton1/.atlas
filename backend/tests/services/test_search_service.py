import pytest
from unittest.mock import MagicMock, patch
from services.search_service import SearchService

@pytest.fixture
def mock_chroma():
    with patch("services.search_service.chromadb") as mock:
        # Mock the client and collection
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Setup query return values structure
        mock_collection.query.return_value = {
            'ids': [['msg_123']],
            'distances': [[0.1]],
            'metadatas': [[{'subject': 'Test', 'sender': 'me'}]],
            'documents': [['Test content...']]
        }
        
        yield mock_collection

@pytest.fixture
def search_service(mock_chroma):
    # We need to re-instantiate the service to use the mock
    return SearchService()

def test_index_email(search_service, mock_chroma):
    email_data = {
        "subject": "Important Project",
        "sender": "boss@example.com",
        "body": "This is critical.",
        "message_id": "msg_123",
        "date": "2025-01-01"
    }
    
    result = search_service.index_email(email_data)
    
    assert result is True
    mock_chroma.upsert.assert_called_once()
    
def test_search(search_service, mock_chroma):
    results = search_service.search("project")
    
    assert len(results) == 1
    assert results[0]['id'] == 'msg_123'
    assert results[0]['score'] == 0.1
    mock_chroma.query.assert_called_once_with(
        query_texts=["project"],
        n_results=5
    )
