from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from services.knowledge_service import knowledge_service
from services.search_service import search_service

router = APIRouter()

@router.get("/docs", response_model=List[Dict[str, Any]])
async def get_knowledge_documents():
    """
    Get all available knowledge documents (deduplicated).
    """
    return knowledge_service.get_all_documents()

@router.get("/content")
async def get_document_content(path: str = Query(...)):
    """
    Get full content of a specific document.
    Supports both absolute paths and relative paths.
    """
    # 1. Try resolving as relative path if a known document exists
    content = knowledge_service.get_document_content(path)
    
    # 2. If not found, search for it in the aggregated doc list
    if content is None:
        all_docs = knowledge_service.get_all_documents()
        found = next((d for d in all_docs if d['path'] == path or d['title'].lower() == path.lower()), None)
        if found:
            content = knowledge_service.get_document_content(found['full_path'])

    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"content": content}

@router.get("/search")
async def search_knowledge(q: str = Query(..., min_length=3)):
    """
    Semantic search across knowledge base.
    """
    results = search_service.search(q, collection_name="knowledge")
    return results

@router.post("/reindex")
async def reindex_knowledge_base(background_tasks: BackgroundTasks):
    """
    Trigger manual reindexing and deduplication as a background task.
    """
    try:
        # Run the heavy work in background
        background_tasks.add_task(knowledge_service.reindex_knowledge)
        return {
            "status": "accepted", 
            "message": "Knowledge Base reindexing started in background. Systems remain operational."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing trigger failed: {str(e)}")
