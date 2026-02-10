from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()

class DailyLogDraftRequest(BaseModel):
    project_id: str
    checklist_items: List[Dict[str, Any]] # [{"step": "...", "completed": True}, ...]
    weather_summary: Optional[str] = None
    notes: Optional[str] = ""

@router.post("/daily-log/draft")
async def draft_daily_log(request: DailyLogDraftRequest):
    """
    Foreman Protocol: Auto-drafts a daily log entry based on completed work.
    Stores it in a 'Pending Audit' state (mocked for now).
    """

    # 1. Synthesize Log Text
    completed_steps = [i['step'] for i in request.checklist_items if i.get('completed')]

    log_body = f"DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}\n"
    log_body += f"Project: {request.project_id}\n\n"

    if request.weather_summary:
        log_body += f"Weather Conditions: {request.weather_summary}\n\n"

    log_body += "WORK PERFORMED:\n"
    if completed_steps:
        for step in completed_steps:
            log_body += f"- {step}\n"
    else:
        log_body += "- No checklist items marked complete.\n"

    if request.notes:
        log_body += f"\nNOTES:\n{request.notes}"

    # 2. Store (Mocked - in real system, would save to 'daily_logs' with status='draft')
    # For prototype, we just return the drafted text so frontend can show it in the modal

    return {
        "status": "draft_created",
        "preview": log_body,
        "requires_audit": True
    }

class FeedbackRequest(BaseModel):
    source_context: str
    corrected_content: str
    user_comment: Optional[str] = ""

@router.post("/learning/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Active Learning: Capture user corrections to improve future AI outputs.
    """
    from services.learning_service import learning_service

    learning_service.save_correction(
        request.source_context,
        request.corrected_content,
        request.user_comment
    )
    return {"status": "success", "message": "Feedback recorded in Learning Core."}
