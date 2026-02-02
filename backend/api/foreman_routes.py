from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.altimeter_service import altimeter_service

router = APIRouter()

class BriefingRequest(BaseModel):
    phase_id: str
    sop_content: str

@router.post("/briefing")
async def generate_briefing(request: BriefingRequest):
    """
    Foreman Protocol: Generate a mission briefing based on Phase and SOP.
    """
    try:
        return await altimeter_service.generate_mission_briefing(request.phase_id, request.sop_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
