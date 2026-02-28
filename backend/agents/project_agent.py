from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from agents.base import BaseAgent
from services.altimeter_service import altimeter_service
from services.search_service import search_service
from services.ai_service import ai_service
from database.database import SessionLocal
from database.models import Task

class ProjectAgent(BaseAgent):
    """
    Agent responsible for project assistance, including DaVinci's Safe Mode Procore Drafting.
    """
    def __init__(self):
        super().__init__("ProjectAgent")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle requests routed to the Project Agent.
        Supported actions: 'draft_daily_log'
        """
        action = context.get('action')
        project_id = context.get('project_id')
        user_prompt = context.get('user_prompt', '')
        
        if action == 'draft_daily_log':
            return await self.generate_daily_log_draft(project_id, user_prompt)
            
        return {"status": "error", "message": f"Unknown action: {action}"}

    async def generate_daily_log_draft(self, project_id: str, user_prompt: str) -> Dict[str, Any]:
        """
        Implements the DaVinci "Safe Mode" Drafter.
        Gathers context, writes a draft log, and saves it for manual review.
        """
        if not project_id:
            return {"status": "error", "message": "project_id is required."}

        # 1. Gather Project Context
        project_ctx = altimeter_service.load_project_context(project_id)
        if not project_ctx:
            return {"status": "error", "message": f"Could not load project context for {project_id}."}

        project_name = project_ctx.get('project', {}).get('name', 'Unknown')
        
        # 2. Gather Semantic Context (Emails/Logs past 48 hours)
        # Search the vector database for relevant project context
        recent_context = ""
        try:
             # Look for recent project emails
             query = f"Project {project_id} update"
             results = search_service.search(query, collection_name="emails", n_results=5)
             if results:
                 recent_context = "Recent Emails:\n"
                 for res in results:
                     recent_context += f"- {res.get('content_snippet', '')}\n"
        except Exception as e:
             print(f"Error fetching semantic context: {e}")
             
        # Add Altimeter recent activity 
        recent_activity = project_ctx.get('recent_activity', '')
        
        # 3. Prompt the LLM
        prompt = f'''
        You are the DaVinci AI Assistant.
        Your task is to draft a professional Daily Log formatted for submission into Procore.
        
        Project: {project_id} - {project_name}
        User Request: {user_prompt}
        
        Recent Activity Context:
        {recent_activity}
        {recent_context}
        
        Format the Daily Log with clear sections:
        - Work Performed Today
        - Schedule Updates
        - Safety Observations
        - Issues or Delays
        - Next Steps
        '''
        
        draft_content = await ai_service.generate_content(prompt)
        
        # 4. Safe Mode Output: Save as Pending Task
        db = SessionLocal()
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            title = f"Review Draft Daily Log for {project_id} ({today_str})"
            
            task = Task(
                title=title,
                description=f"Automated DaVinci Draft based on '{user_prompt}':\n\n{draft_content}\n\nPlease review, approve, and submit to Procore manually.",
                status="todo",
                priority="high",
                category="work",
                project_id=project_id,
                due_date=datetime.now(),
                created_from="ai_suggested",
                source="atlas_extracted"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            return {
                "status": "success", 
                "message": "Draft created in Safe Mode and added to tasks.", 
                "task_id": task.task_id
            }
            
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": f"Failed to save draft: {e}"}
        finally:
            db.close()

project_agent = ProjectAgent()
