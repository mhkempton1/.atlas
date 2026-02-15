from typing import Dict, Any, List
from agents.base import BaseAgent
from services.ai_service import ai_service
from services.knowledge_service import knowledge_service
from services.date_parsing_service import date_parsing_service
import json
import datetime

class TaskAgent(BaseAgent):
    """
    Agent responsible for extracting actionable tasks and categorizing 
    emails using construction domain knowledge.
    """
    
    def __init__(self):
        super().__init__(agent_name="TaskAgent")
        self.categories = [
            "Safety",       # Inspection, compliance, OSHA
            "Financial",    # Invoices, draw requests, change orders
            "Schedule",     # Milestones, delays, updates
            "Material",     # Submittals, lead times, delivery
            "Quality",      # Punch list, specs, defects
            "Communication" # General coordination
        ]
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email, extract tasks, and categorize.
        """
        subject = context.get('subject', '')
        sender = context.get('sender', '')
        body = context.get('body', '')
        
        # 1. Integrate Knowledge Search
        knowledge_context = ""
        try:
            knowledge_results = knowledge_service.search_all_knowledge(f"{subject} {body[:200]}", top_k=2)
            
            if knowledge_results.get("skills"):
                knowledge_context += "\nRelevant Skills/Procedures:\n"
                for skill in knowledge_results["skills"]:
                    knowledge_context += f"- {skill['metadata'].get('title', 'Unknown')}: {skill.get('content_snippet', '')}\n"
            
            if knowledge_results.get("guidelines"):
                knowledge_context += "\nManagement Guidelines:\n"
                for guide in knowledge_results["guidelines"]:
                    knowledge_context += f"- {guide['metadata'].get('title', 'Unknown')}: {guide.get('content_snippet', '')}\n"
        except Exception as e:
            print(f"[TaskAgent] Knowledge Search Failed: {e}")

        # 2. Construct Prompt
        prompt = f"""
        You are an AI Task extraction and categorization assistant for a Construction Project Manager.
        Analyze the following {context.get('type', 'email')} and provide actionable insights.
        
        Context Source: {context.get('type', 'Unknown')}
        Subject: {subject}
        From: {sender}
        Content:
        {body}
        
        {knowledge_context}
        
        Instructions:
        1. Categorize this communication into one of: {", ".join(self.categories)}.
        2. Identify clear, actionable tasks.
        3. Assign a priority (High, Medium, Low).
        4. Infer a due date if mentioned (use YYYY-MM-DD format). Assume year 2026 if not specified.
        5. Return the result as a STRICT JSON object.
        
        JSON Schema:
        {{
            "category": "Selected Category",
            "summary": "One sentence summary",
            "tasks": [
                {{
                    "title": "Short Task Title",
                    "description": "Detailed explanation...",
                    "priority": "High|Medium|Low",
                    "due_date": "YYYY-MM-DD" or null,
                    "confidence": 0.0-1.0
                }}
            ]
        }}
        
        If no tasks are found, return {{"category": "...", "summary": "...", "tasks": []}}.
        Do not include markdown formatting. Just the raw JSON string.
        """
        
        try:
            # Generate
            response_text = await ai_service.generate_content(prompt)
            
            if response_text == "ERROR_RATE_LIMIT_EXCEEDED":
                return {"status": "error", "error": "AI Rate limit exceeded."}

            if not response_text:
                return {"status": "error", "error": "AI Service returned empty response."}

            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(cleaned_text)
            except json.JSONDecodeError as je:
                print(f"[TaskAgent] JSON Parse Error: {je}")
                return {"status": "error", "error": f"Failed to parse AI response: {str(je)}"}
            
            # 3. Post-Process: Relative Date Parsing
            # If AI didn't find a due_date, we try to parse it from the body
            for task in data.get("tasks", []):
                if not task.get("due_date"):
                    task["due_date"] = date_parsing_service.parse_deadline_from_text(body)
                
                # Enhance with metadata
                task["source"] = "email"
                task["source_id"] = context.get("message_id")
                task["created_at"] = datetime.datetime.now().isoformat()
                
            return {
                "status": "success",
                "data": data
            }
            
        except Exception as e:
            print(f"[TaskAgent] Error: {e}")
            return {"status": "error", "error": str(e)}

task_agent = TaskAgent()
