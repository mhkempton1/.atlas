from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.search_service import search_service

router = APIRouter()

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

class IndexRequest(BaseModel):
    subject: str
    sender: str
    body: str
    message_id: str
    date: Optional[str] = None

@router.get("/", response_model=SearchResponse)
async def search_emails(q: str = Query(..., min_length=3)):
    """
    Semantic search for emails.
    """
    results = search_service.search(q)
    return {"results": results}

@router.post("/index")
async def manual_index(request: IndexRequest):
    """
    Manually index an email (mostly for testing/admin).
    """
    success = search_service.index_email(request.model_dump())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index email")
    return {"status": "indexed", "id": request.message_id}
