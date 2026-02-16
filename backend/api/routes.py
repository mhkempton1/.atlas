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

# from services.google_service import google_service

class SendEmailRequest(BaseModel):
    recipient: str
    subject: str
    body: str

@router.post("/agents/send-email")
async def send_email_endpoint(request: SendEmailRequest):
    from services.communication_service import comm_service
    result = comm_service.send_email(request.recipient, request.subject, request.body)
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

from api.notification_routes import router as notification_router
router.include_router(notification_router, prefix="/notifications", tags=["Notifications"])

from api.dashboard_routes import router as dashboard_router
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

@router.post("/chat")
async def chat_assistant(request: dict):
    """
    Semantic intelligence chat bot.
    Now enhanced with:
    - RAG (Docs/Email)
    - SQL (Altimeter DB)
    - Strata Security
    """
    from services.search_service import search_service
    from services.ai_service import ai_service
    from services.altimeter_service import altimeter_service
    
    query = request.get("message", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Empty message")

    # Strata Level (Mocked to 5 for now as per previous context, but architected for dynamic)
    user_strata = 5

    # 1. RAG Search (Docs & Email)
    rag_context = ""
    knowledge_results = search_service.search(query, collection_name="knowledge", n_results=3)
    if knowledge_results:
        rag_context += "RELEVANT DOCUMENTS:\n"
        for res in knowledge_results:
            rag_context += f"- {res['metadata'].get('title')}: {res['content_snippet']}\n"

    email_results = search_service.search(query, collection_name="emails", n_results=2)
    if email_results:
        rag_context += "RELEVANT EMAILS:\n"
        for res in email_results:
            rag_context += f"- From {res['metadata'].get('sender')}: {res['content_snippet']}\n"

    # 2. Database Schema Injection
    schema_context = altimeter_service.get_db_schema(user_strata)

    # 3. Prompt Construction
    system_prompt = f"""
    You are Jules, the Atlas AI. You have access to the company's Knowledge Base and the Altimeter Project Database.

    USER QUERY: {query}

    CONTEXT (RAG):
    {rag_context}

    DATABASE ACCESS (SQL):
    {schema_context}

    INSTRUCTIONS:
    - If the user asks about data in the database (e.g. "How many active projects?", "Status of task X"), you can WRITE A SQL QUERY.
    - If you write a SQL query, format it exactly like this: SQL: SELECT * FROM ...
    - If the user asks to SEE a tool or view (e.g. "Show me the schedule", "Open tasks"), return a UI ACTION.
    - UI ACTION FORMAT: UI: render_task_list (or render_schedule)
    - If the answer is in the RAG context, summarize it.
    - If you don't know, say so.
    """

    # 4. First Pass: AI Reasoning
    response_text = await ai_service.generate_content(system_prompt, include_context=True, user_strata=user_strata)

    # 5. Tool Execution Loop (SQL or UI)
    stripped_resp = response_text.strip()

    if stripped_resp.startswith("SQL:"):
        sql_query = stripped_resp.replace("SQL:", "").strip()
        print(f"Executing AI SQL: {sql_query}")

        try:
            db_results = altimeter_service.execute_read_only_query(sql_query)

            # 6. Second Pass: Synthesize Data
            final_prompt = f"""
            The user asked: {query}
            You decided to run this SQL: {sql_query}
            Here are the results from the database:
            {db_results}
            Please formulate a natural language answer based on these results.
            """
            final_response = await ai_service.generate_content(final_prompt)
            return {"reply": final_response, "links": []}

        except Exception as e:
            return {"reply": f"I tried to query the database but encountered an error: {str(e)}", "links": []}

    if stripped_resp.startswith("UI:"):
        component = stripped_resp.replace("UI:", "").strip()
        return {
            "reply": f"Opening {component} view...",
            "ui_action": {"component": component, "props": {}}
        }

    # 6. Standard Response
    return {"reply": response_text, "links": [{"label": "Explore Library", "moduleId": "procedures"}]}

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
