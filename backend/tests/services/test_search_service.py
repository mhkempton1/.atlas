import pytest
from unittest.mock import MagicMock, patch
from services.search_service import SearchService

@pytest.fixture
def mock_chroma_setup():
    """Patches chromadb at the module level and returns the mock client and collection."""
    with patch("services.search_service.chromadb") as mock_chromadb:
        mock_client = MagicMock()
        mock_collection = MagicMock()

        # Setup basic structure
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        yield {
            'module': mock_chromadb,
            'client': mock_client,
            'collection': mock_collection
        }

@pytest.fixture
def search_service(mock_chroma_setup):
    """Returns a new SearchService instance using the mocked chromadb."""
    # Force re-initialization by creating a new instance
    service = SearchService()
    # Reset initialized state just in case (though new instance should be fresh)
    service._initialized = False
    return service

def test_initialization_success(search_service, mock_chroma_setup):
    """Test successful initialization of ChromaDB."""
    assert search_service._ensure_initialized() is True
    assert search_service._client == mock_chroma_setup['client']
    assert search_service._email_collection == mock_chroma_setup['collection']
    mock_chroma_setup['module'].PersistentClient.assert_called_once()

def test_initialization_failure(search_service, mock_chroma_setup):
    """Test initialization failure (e.g., ChromaDB crashes)."""
    mock_chroma_setup['module'].PersistentClient.side_effect = Exception("DB Crash")

    # Should handle exception and return False
    assert search_service._ensure_initialized() is False
    assert search_service._client is None

def test_index_email(search_service, mock_chroma_setup):
    """Test indexing a single email."""
    mock_collection = mock_chroma_setup['collection']

    email_data = {
        "subject": "Important Project",
        "sender": "boss@example.com",
        "body": "This is critical.",
        "message_id": "msg_123",
        "date": "2025-01-01"
    }
    
    result = search_service.index_email(email_data)
    
    assert result is True
    mock_collection.upsert.assert_called_once()

    # Verify call args
    call_args = mock_collection.upsert.call_args
    assert call_args is not None
    kwargs = call_args.kwargs
    
    assert kwargs['ids'] == ['msg_123']
    assert len(kwargs['documents']) == 1
    assert "Important Project" in kwargs['documents'][0]
    assert kwargs['metadatas'][0]['subject'] == "Important Project"

def test_index_email_failure(search_service, mock_chroma_setup):
    """Test email indexing failure."""
    mock_collection = mock_chroma_setup['collection']
    mock_collection.upsert.side_effect = Exception("Upsert failed")

    email_data = {"message_id": "123"}
    result = search_service.index_email(email_data)

    assert result is False

def test_index_knowledge_batch(search_service, mock_chroma_setup):
    """Test batch indexing of knowledge documents."""
    mock_collection = mock_chroma_setup['collection']

    docs = [
        {"id": "doc1", "title": "Guide 1", "content": "Content 1", "category": "Tech"},
        {"id": "doc2", "title": "Guide 2", "content": "Content 2", "category": "HR"}
    ]

    result = search_service.index_knowledge_batch(docs)

    assert result is True
    mock_collection.upsert.assert_called_once()
    kwargs = mock_collection.upsert.call_args.kwargs

    assert len(kwargs['ids']) == 2
    assert kwargs['ids'] == ["doc1", "doc2"]
    assert kwargs['metadatas'][0]['category'] == "Tech"
    assert kwargs['metadatas'][1]['category'] == "HR"

def test_search_success(search_service, mock_chroma_setup):
    """Test searching with results."""
    mock_collection = mock_chroma_setup['collection']

    # Mock query response
    mock_collection.query.return_value = {
        'ids': [['msg_123']],
        'distances': [[0.1]],
        'metadatas': [[{'subject': 'Test', 'sender': 'me'}]],
        'documents': [['Test content snippet...']]
    }

    results = search_service.search("test query")
    
    assert len(results) == 1
    item = results[0]
    assert item['id'] == 'msg_123'
    assert item['score'] == 0.1
    assert item['metadata']['subject'] == 'Test'
    assert "Test content snippet" in item['content_snippet']

    mock_collection.query.assert_called_once_with(
        query_texts=["test query"],
        n_results=5
    )

def test_search_empty(search_service, mock_chroma_setup):
    """Test searching with no results."""
    mock_collection = mock_chroma_setup['collection']

    # Chroma returns empty lists for no matches
    mock_collection.query.return_value = {
        'ids': [[]],
        'distances': [[]],
        'metadatas': [[]],
        'documents': [[]]
    }

    results = search_service.search("nonexistent")
    assert len(results) == 0

def test_search_failure(search_service, mock_chroma_setup):
    """Test search failure handling."""
    mock_collection = mock_chroma_setup['collection']
    mock_collection.query.side_effect = Exception("Search failed")

    results = search_service.search("crash")
    assert results == []

def test_dummy_embedding_fallback(search_service, mock_chroma_setup):
    """Test that DummyEmbedding is used if sentence_transformers is missing."""
    # We need to mock import failure specifically inside _ensure_initialized
    # But since that method does a local import, patching 'builtins.__import__' is tricky/risky.
    # Instead, we can inspect the _embedding_fn after initialization if we can force the ImportError path.
    # However, since we installed requirements, the import will succeed.
    # We can try to patch sys.modules to hide sentence_transformers.

    with patch.dict('sys.modules', {'sentence_transformers': None}):
        # Reset init state
        search_service._initialized = False
        search_service._client = None

        search_service._ensure_initialized()

        # Check if embedding function is the dummy one
        # The class is defined inside the method, so we check the name
        assert search_service._embedding_fn.__class__.__name__ == 'DummyEmbedding'

        # Verify dummy embedding works
        vector = search_service._embedding_fn(["test"])
        assert len(vector) == 1
        assert len(vector[0]) == 384
