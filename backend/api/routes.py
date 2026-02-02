from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.draft_agent import draft_agent

router = APIRouter()

class DraftRequest(BaseModel):
    subject: str
    sender: str
    body: str
    instructions: Optional[str] = "Reply professionally"

class DraftResponse(BaseModel):
    draft_text: str
    status: str
    model: str
    detected_context: Optional[dict] = None

@router.get("/health")
async def health_check():
    """Health check for API prefix compatibility"""
    from services.status_service import get_health_status
    return await get_health_status()

@router.post("/agents/draft", response_model=DraftResponse)
async def generate_draft_endpoint(request: DraftRequest):
    try:
        context = {
            "subject": request.subject,
            "sender": request.sender,
            "body": request.body,
            "instructions": request.instructions
        }
        
        result = await draft_agent.process(context)
        
        return DraftResponse(
            draft_text=result.get("draft_text", ""),
            status=result.get("status", "error"),
            model=result.get("model", "unknown"),
            detected_context=result.get("context_used", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from services.google_service import google_service

class SendEmailRequest(BaseModel):
    recipient: str
    subject: str
    body: str

@router.post("/agents/send-email")
async def send_email_endpoint(request: SendEmailRequest):
    result = google_service.send_email(request.recipient, request.subject, request.body)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result



# --- Router Includes ---

from api.document_control_routes import router as doc_router
router.include_router(doc_router, prefix="/docs", tags=["Document Control"])

from api.email_routes import router as email_router
router.include_router(email_router, prefix="/email", tags=["Email"])

from api.calendar_routes import router as calendar_router
router.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])

from api.task_routes import router as task_router
router.include_router(task_router, prefix="/tasks", tags=["Tasks"])

from api.system_routes import router as system_router
router.include_router(system_router, prefix="/system", tags=["System"])

from api.knowledge_routes import router as knowledge_router
router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])

from api.search_routes import router as search_router
router.include_router(search_router, prefix="/search", tags=["Search"])

from api.weather_routes import router as weather_router
router.include_router(weather_router, prefix="/weather", tags=["Weather"])

from api.reporting_routes import router as reporting_router
router.include_router(reporting_router, prefix="/reporting", tags=["Reporting"])

from api.foreman_routes import router as foreman_router
router.include_router(foreman_router, prefix="/foreman", tags=["Foreman Protocol"])

@router.post("/chat")
async def chat_assistant(request: dict):
    """Semantic intelligence chat bot"""
    from services.search_service import search_service
    
    query = request.get("message", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Empty message")

    # 1. Search Knowledge Base (Highest Priority)
    knowledge_results = search_service.search(query, collection_name="knowledge", n_results=3)
    
    if knowledge_results and knowledge_results[0]["score"] < 0.8: # Threshold for high confidence (lower score is better)
        best_match = knowledge_results[0]
        meta = best_match["metadata"]
        snippet = best_match["content_snippet"]
        
        reply = f"Based on our internal documents (**{meta.get('title', 'Unknown')}**), here is what I found:\n\n{snippet}\n\nWould you like to view the full document?"
        links = [{"label": f"View {meta.get('title')}", "moduleId": "procedures", "path": meta.get('path')}]
        return {"reply": reply, "links": links}

    # 2. Search Emails (Secondary Priority)
    email_results = search_service.search(query, collection_name="emails", n_results=2)
    if email_results and email_results[0]["score"] < 0.7:
        best_email = email_results[0]
        meta = best_email["metadata"]
        reply = f"I found a relevant communication from **{meta.get('sender')}** regarding '{meta.get('subject')}'. \n\nSnippet: {best_email['content_snippet']}"
        links = [{"label": "Go to Inbox", "moduleId": "email"}]
        return {"reply": reply, "links": links}

    # 3. Fallback to general conversational response
    return {
        "reply": "I couldn't find a specific policy or email matching that query in my active knowledge core. Try rephrasing, or ask about specific categories like 'safety', 'payroll', or 'engineering'.",
        "links": [{"label": "Explore Library", "moduleId": "procedures"}]
    }

# --- Dashboard & Scheduler Routes ---
from services.scheduler_service import SchedulerService
scheduler_service = SchedulerService()

@router.get("/dashboard/status")
async def get_dashboard_status():
    """Proxy Altimeter System Health"""
    return await scheduler_service.get_system_health()

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Fetch high-level system stats"""
    return await scheduler_service.get_dashboard_stats()

@router.get("/dashboard/schedule")
async def get_my_schedule(employee_id: Optional[str] = "EMP005"): # Default to Admin for demo
    """Fetch Schedule from Altimeter"""
    return scheduler_service.get_my_schedule(employee_id)

@router.get("/dashboard/oracle")
async def get_oracle_feed():
    """
    The Oracle Protocol: Returns predictive Mission Intel.
    Combines Active Phases + Weather Context + Knowledge Base.
    """
    from services.altimeter_service import altimeter_service, intelligence_bridge
    from services.weather_service import weather_service

    # 1. Get Context
    active_phases = altimeter_service.get_active_phases()
    weather_data = None
    try:
        # Get weather for default location
        weather_data = await weather_service.get_weather()
    except:
        pass # Fail gracefully if weather service is down

    # 2. Predict Intelligence
    mission_intel = intelligence_bridge.predict_mission_intel(active_phases, weather_data)

    return mission_intel
