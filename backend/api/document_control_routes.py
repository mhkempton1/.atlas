from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.document_control_service import document_control_service

router = APIRouter()

# Data Models
class DraftCreateRequest(BaseModel):
    title: str
    content: str
    section: Optional[str] = "GUIDELINES"

class DraftSaveRequest(BaseModel):
    path: str
    content: str

class PromoteRequest(BaseModel):
    path: str

class LockRequest(BaseModel):
    path: str
    approver: str

# Routes

@router.get("/list")
async def list_documents():
    """List all documents (Draft, Review, Locked)"""
    return document_control_service.get_all_documents()

@router.get("/content")
async def get_content(path: str):
    """Get content of a specific document"""
    content = document_control_service.get_document_content(path)
    if content is None:
         raise HTTPException(status_code=404, detail="Document not found")
    return {"content": content}

@router.post("/draft/create")
async def create_draft(req: DraftCreateRequest):
    try:
        return document_control_service.create_draft(req.title, req.content, req.section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/draft/save")
async def save_draft(req: DraftSaveRequest):
    try:
        return document_control_service.save_draft(req.path, req.content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Draft not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/draft")
async def delete_draft(path: str):
    try:
        return document_control_service.delete_draft(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Draft not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promote")
async def promote_draft(req: PromoteRequest):
    try:
        return document_control_service.promote_to_review(req.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lock")
async def lock_document(req: LockRequest):
    try:
        return document_control_service.lock_document(req.path, req.approver)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demote")
async def demote_draft(req: PromoteRequest):
    try:
        return document_control_service.demote_to_draft(req.path)
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ImportRequest(BaseModel):
    path: str
    section: Optional[str] = "GUIDELINES"

@router.post("/import")
async def import_document(req: ImportRequest):
    try:
        return document_control_service.import_to_review(req.path, req.section)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Source file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Comment System ---

class CommentRequest(BaseModel):
    path: str
    author: str
    content: str
    comment_type: Optional[str] = "general"  # general, issue, suggestion, approval

class ResolveCommentRequest(BaseModel):
    resolver: str

@router.post("/comment")
async def add_comment(req: CommentRequest):
    try:
        return document_control_service.add_comment(req.path, req.author, req.content, req.comment_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comments")
async def get_comments(path: str):
    try:
        return document_control_service.get_comments(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/comment/{comment_id}/resolve")
async def resolve_comment(comment_id: int, req: ResolveCommentRequest):
    try:
        return document_control_service.resolve_comment(comment_id, req.resolver)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/review-summary")
async def get_review_summary(path: str):
    try:
        return document_control_service.get_review_summary(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
