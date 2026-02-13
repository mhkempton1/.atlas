import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import os
from core.config import settings

class SearchService:
    """
    Service for semantic search using ChromaDB.
    Indexes emails and knowledge documents for retrieval.
    """
    def __init__(self):
        # Store in Atlas data directory, NOT Altimeter
        self.persist_path = os.path.join(settings.DATA_DIR, "databases", "vectors")
        os.makedirs(self.persist_path, exist_ok=True)

        # Lazy init - don't crash the whole app if ChromaDB fails
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of ChromaDB to prevent startup crashes."""
        if self._initialized:
            return self._client is not None

        self._initialized = True
        try:
            self._client = chromadb.PersistentClient(path=self.persist_path)
            try:
                # Try to load SentenceTransformerEmbeddingFunction only if sentence_transformers is installed
                import sentence_transformers
                self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            except (ImportError, Exception) as e:
                class DummyEmbedding:
                    def __call__(self, input):
                        # Returns a fixed size vector (384 is common for MiniLM)
                        return [[0.1] * 384 for _ in input]

                self._embedding_fn = DummyEmbedding()

            # Collection for Emails
            self._email_collection = self._client.get_or_create_collection(
                name="emails",
                embedding_function=self._embedding_fn
            )
            # Collection for Knowledge Docs
            self._knowledge_collection = self._client.get_or_create_collection(
                name="knowledge",
                embedding_function=self._embedding_fn
            )
            return True
        except BaseException as e:
            # Catching BaseException to handle pyo3/rust panics
            self._client = None
            self._email_collection = None
            self._knowledge_collection = None
            return False

    @property
    def email_collection(self):
        self._ensure_initialized()
        return self._email_collection
    
    @property
    def knowledge_collection(self):
        self._ensure_initialized()
        return self._knowledge_collection

    def index_email(self, email_data: Dict[str, Any]) -> bool:
        """Add or update an email in the vector index."""
        if not self._ensure_initialized(): return False
        try:
            text_to_embed = f"Subject: {email_data.get('subject', '')}\nFrom: {email_data.get('sender', '')}\n\n{email_data.get('body', '')}"
            metadata = {
                "subject": email_data.get('subject', ''),
                "sender": email_data.get('sender', ''),
                "date": email_data.get('date', ''),
                "message_id": email_data.get('message_id', ''),
                "source": "email"
            }
            self.email_collection.upsert(
                documents=[text_to_embed],
                metadatas=[metadata],
                ids=[email_data.get('message_id', 'unknown_id')]
            )
            return True
        except Exception as e:
            return False

    def index_knowledge_batch(self, docs_data: List[Dict[str, Any]]) -> bool:
        """Add or update multiple knowledge documents in bulk."""
        if not self._ensure_initialized() or not docs_data: return False
        try:
            documents = []
            metadatas = []
            ids = []
            
            for doc_data in docs_data:
                text = f"Title: {doc_data.get('title', '')}\nCategory: {doc_data.get('category', '')}\n\n{doc_data.get('content', '')}"
                meta = {
                    "title": doc_data.get('title', ''),
                    "category": doc_data.get('category', 'UNCATEGORIZED'),
                    "path": doc_data.get('path', ''),
                    "source": doc_data.get('source', 'knowledge'),
                    "full_path": doc_data.get('full_path', '')
                }
                documents.append(text)
                metadatas.append(meta)
                ids.append(doc_data.get('id', 'unknown_id'))
            
            self.knowledge_collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            return False

    def search(self, query: str, collection_name: str = "emails", n_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search for a specific collection."""
        if not self._ensure_initialized(): return []
        try:
            col = self.email_collection if collection_name == "emails" else self.knowledge_collection
            results = col.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Transform results into a cleaner list of dicts
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    item = {
                        "id": results['ids'][0][i],
                        "score": results['distances'][0][i] if results['distances'] else 0.0,
                        "metadata": results['metadatas'][0][i],
                        "content_snippet": results['documents'][0][i][:200] + "..." # Preview
                    }
                    formatted_results.append(item)
            
            return formatted_results
            
        except Exception as e:
            return []

search_service = SearchService()
