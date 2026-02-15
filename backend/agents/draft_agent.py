from typing import Dict, Any
from agents.base import BaseAgent
from services.ai_service import ai_service
from services.altimeter_service import altimeter_service
from services.knowledge_service import knowledge_service
import json

class DraftAgent(BaseAgent):
    """
    Agent responsible for drafting email responses and content.
    Enhanced with Company Intelligence (Templates, Guidelines, Skills).
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
        
        # 1. Altimeter Context (Project/Role)
        altimeter_context = altimeter_service.get_context_for_email(sender, subject)
        project_info = "Unknown"
        if altimeter_context.get("project"):
            p = altimeter_context["project"]
            project_info = f"{p.get('name')} (#{p.get('number')})"

        # 2. Knowledge Search (Templates/Guidelines/Skills)
        knowledge_context = ""
        try:
            results = knowledge_service.search_all_knowledge(f"{subject} {body[:200]}", top_k=2)
            
            if results.get("templates"):
                knowledge_context += "\nRECOMMENDED TEMPLATE:\n"
                for res in results["templates"]:
                    knowledge_context += f"Template: {res['metadata'].get('title')}\n{res.get('content_snippet', '')}\n"
                    
            if results.get("guidelines"):
                knowledge_context += "\nMANAGEMENT GUIDELINES:\n"
                for res in results["guidelines"]:
                    knowledge_context += f"- {res['metadata'].get('title')}: {res.get('content_snippet', '')}\n"
                    
            if results.get("skills"):
                knowledge_context += "\nTECHNICAL SKILLS/SOPS:\n"
                for res in results["skills"]:
                    knowledge_context += f"- {res['metadata'].get('title')}: {res.get('content_snippet', '')}\n"
        except Exception as e:
            print(f"[DraftAgent] Knowledge Search Error: {e}")

        # 3. Construct Prompt
        prompt = f"""
        You are Atlas, a personal AI assistant for Davis Electric.
        Draft a response to the following email using company context and knowledge.
        
        Email Context:
        - From: {sender}
        - Subject: {subject}
        - Content: {body}
        
        Project: {project_info}
        Sender Role: {altimeter_context.get('company_role', 'Unknown')}
        
        {knowledge_context}
        
        User Instructions: {instructions}
        
        IMPORTANT:
        - If a TEMPLATE is provided, use its structure/tone.
        - If GUIDELINES are provided, adhere to the management rules.
        - If SKILLS/SOPS are provided, ensure technical accuracy.
        - Tone: Professional, Competent, Proactive.
        """
        
        generated_content = await ai_service.generate_content(prompt)
        
        return {
            "draft_text": generated_content,
            "context_used": altimeter_context,
            "status": "generated",
            "model": "gemini-2.0-flash"
        }

draft_agent = DraftAgent()
