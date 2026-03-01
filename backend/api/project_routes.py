from fastapi import APIRouter, HTTPException, Depends
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

from pydantic import BaseModel

class DraftLogRequest(BaseModel):
    prompt: str

@router.post("/{project_id}/draft-daily-log", response_model=Dict[str, Any])
async def draft_daily_log_for_project(project_id: str, request: DraftLogRequest):
    """
    Trigger the Project Agent to generate a Safe Mode Daily Log draft.
    """
    from agents.project_agent import project_agent
    
    result = await project_agent.process({
        "action": "draft_daily_log",
        "project_id": project_id,
        "user_prompt": request.prompt
    })
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    return result

