from typing import Dict, Any
from agents.base import BaseAgent
from services.ai_service import ai_service
from services.altimeter_service import altimeter_service
from services.search_service import search_service
import json

class DraftAgent(BaseAgent):
    """
    Agent responsible for drafting email responses and content.
    Now enhanced with "The Lens" - Altimeter Context.
    """
    
    def __init__(self):
        super().__init__(agent_name="DraftAgent")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a draft based on email context + Company Data.
        """
        subject = context.get('subject', '')
        sender = context.get('sender', '')
        body = context.get('body', '')
        instructions = context.get('instructions', 'Draft a professional response.')
        
        # 1. Apply "The Lens": Get Context from Altimeter
        # Who is this? What project is this? What is their role?
        altimeter_context = altimeter_service.get_context_for_email(sender, subject)
        
        project_info = "Unknown Project"
        if altimeter_context.get("project"):
            p = altimeter_context["project"]
            project_info = f"{p.get('name')} (#{p.get('number')}) - Status: {p.get('status')}"

        # 2. Apply "The Lens": Knowledge Search
        # Check procedures/SOPs/Safety talks relevant to the query
        knowledge_results = search_service.search(f"{subject} {body}", collection_name="knowledge", n_results=3)
        knowledge_context_str = ""
        if knowledge_results:
            knowledge_context_str = "\nRELEVANT PROCEDURES & SOPS:\n"
            for res in knowledge_results:
                meta = res.get('metadata', {})
                knowledge_context_str += f"- {meta.get('title')} ({meta.get('category')}): {res.get('content_snippet')}\n"

        # 3. Construct the Prompt with "The Lens"
        file_context_str = altimeter_context.get("file_context", "")
        role_info = altimeter_context.get("company_role", "Unknown Role")

        prompt = f"""
        You are Atlas, a personal AI assistant for a Construction Electrical Contractor (Davis Electric).
        Your goal is to be the "Chief of Staff" - applying company context to every interaction.
        
        Incoming Email:
        ----------------
        From: {sender}
        Subject: {subject}
        Body: 
        {body}
        ----------------

        PROJECT INTELLIGENCE (The Lens):
        Project: {project_info}
        Identified Sender Role: {role_info}

        DEEP CONTEXT (Extracted from Project Files):
        {file_context_str}
        
        {knowledge_context_str}

        User Instructions: 
        {instructions}
        
        GUIDELINES:
        - Use the DEEP CONTEXT to answer specific questions about status, contacts, or scope.
        - IMPORTANT: If RELEVANT PROCEDURES are provided, ensure the draft aligns with company SOPs and safety protocols.
        - If the context lists a "Customer Contact" and the sender matches, treat them as the Client.
        - If the context lists "Outstanding Items", check if the email relates, and mention them if relevant.
        - Tone: Professional, Competent, Proactive. We don't just answer; we solve.
        
        Task:
        1. Draft the email response.
        2. If applicable, add a separate "Internal Note" to the user about things they should check (e.g., "Check budget code X", "Notify Project Manager Y").
        """
        
        # 3. Generate Content
        generated_content = await ai_service.generate_content(prompt)
        
        return {
            "draft_text": generated_content,
            "context_used": altimeter_context,
            "status": "generated",
            "model": "gemini-2.0-flash"
        }

draft_agent = DraftAgent()
