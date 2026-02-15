from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.altimeter_service import altimeter_service

router = APIRouter()

@router.get("/{project_id}/context", response_model=Dict[str, Any])
async def get_project_context(project_id: str):
    """
    Get full project context from Altimeter.
    """
    context = altimeter_service.load_project_context(project_id)
    if not context:
        raise HTTPException(status_code=404, detail="Project context not found or Altimeter unavailable")
    return context
