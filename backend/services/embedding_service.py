from typing import Dict, Any, List, Optional
from services.ai_service import ai_service
from services.search_service import search_service

class EmbeddingService:
    """
    Service for generating embeddings and semantic search for emails.
    """
    def __init__(self):
        self.ai_service = ai_service
        self.search_service = search_service

    def generate_email_embedding(self, email_data: Dict[str, Any]) -> bool:
        """
        Generate embedding for email if body > 50 words and store in ChromaDB.

        Args:
            email_data: Dictionary containing email fields:
                        - body (or body_text/body_html)
                        - subject
                        - sender
                        - date
                        - message_id
        """
        body = email_data.get('body') or email_data.get('body_text') or email_data.get('body_html') or ""

        # Word count check
        word_count = len(body.split())
        if word_count <= 50:
            return False

        msg_id = email_data.get('message_id', 'unknown_id')

        # Check if already exists (to avoid re-embedding cost)
        try:
            if not self.search_service.email_collection:
                return False

            existing = self.search_service.email_collection.get(ids=[msg_id])
            if existing and existing.get('ids') and len(existing['ids']) > 0:
                # Update metadata only
                metadata = {
                    "subject": email_data.get('subject', ''),
                    "sender": email_data.get('sender', ''),
                    "date": email_data.get('date', ''),
                    "message_id": msg_id,
                    "source": "email"
                }
                self.search_service.email_collection.update(
                    ids=[msg_id],
                    metadatas=[metadata]
                )
                return True
        except Exception as e:
            print(f"Error checking/updating existing embedding: {e}")
            # Continue to upsert if check fails (fallback)

        # Generate embedding
        # Combine subject and body for better context
        text_to_embed = f"Subject: {email_data.get('subject', '')}\nFrom: {email_data.get('sender', '')}\n\n{body}"

        embedding = self.ai_service.get_embedding(text_to_embed)
        if not embedding:
            return False

        # Store in ChromaDB
        try:
            # Metadata
            metadata = {
                "subject": email_data.get('subject', ''),
                "sender": email_data.get('sender', ''),
                "date": email_data.get('date', ''),
                "message_id": msg_id,
                "source": "email"
            }

            # Upsert
            # Use search_service's collection.
            # Note: Providing 'embeddings' overrides the collection's embedding function.
            self.search_service.email_collection.upsert(
                ids=[msg_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[text_to_embed]
            )
            return True
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False

    def semantic_search_emails(self, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for emails.
        """
        embedding = self.ai_service.get_embedding(query_text)
        if not embedding:
            return []

        try:
            if not self.search_service.email_collection:
                return []

            results = self.search_service.email_collection.query(
                query_embeddings=[embedding],
                n_results=top_k
            )

            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    item = {
                        "id": results['ids'][0][i],
                        "score": results['distances'][0][i] if results['distances'] else 0.0,
                        "metadata": results['metadatas'][0][i],
                        "content_snippet": results['documents'][0][i][:200] + "..." if results['documents'] and results['documents'][0] else ""
                    }
                    formatted_results.append(item)
            return formatted_results
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []

embedding_service = EmbeddingService()
