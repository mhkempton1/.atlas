from typing import Dict, Any, List
from agents.base import BaseAgent
from services.ai_service import ai_service
import json
import datetime

class TaskAgent(BaseAgent):
    """
    Agent responsible for extracting actionable tasks from email content.
    """
    
    def __init__(self):
        super().__init__(agent_name="TaskAgent")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email and extract tasks.
        """
        subject = context.get('subject', '')
        sender = context.get('sender', '')
        body = context.get('body', '')
        
        # Construct Prompt
        prompt = f"""
        You are an AI Task extraction assistant for a Construction Project Manager.
        Analyze the following {context.get('type', 'email')} and extract actionable tasks.
        
        Context Source: {context.get('type', 'Unknown')}
        Subject/Title: {subject}
        From/Organizer: {sender}
        Content:
        {body}
        
        Instructions:
        1. Identify clear, actionable tasks.
        2. Assign a priority (High, Medium, Low).
        3. Infer a due date if mentioned (use YYYY-MM-DD format). If no year is specified, assume 2026.
        4. Extract a concise title and detailed description.
        5. For Calendar events, consider location ({context.get('location', 'N/A')}) and timing ({context.get('start_time', 'N/A')}).
        6. Return the result as a STRICT JSON object with a key "tasks" containing a list of task objects.
        
        JSON Schema:
        {{
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
        
        If no tasks are found, return {{"tasks": []}}.
        Do not include markdown formatting. Just the raw JSON string.
        """
        
        try:
            # Generate
            response_text = await ai_service.generate_content(prompt)
            
            if response_text == "ERROR_RATE_LIMIT_EXCEEDED":
                return {
                    "status": "error",
                    "error": "AI Rate limit exceeded. Please try again later."
                }

            if not response_text:
                return {
                    "status": "error",
                    "error": "AI Service returned empty response."
                }

            # Clean potential markdown
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                task_data = json.loads(cleaned_text)
            except json.JSONDecodeError as je:
                print(f"[TaskAgent] JSON Parse Error: {je}")
                return {
                    "status": "error",
                    "error": f"Failed to parse AI response as JSON: {str(je)}",
                    "raw_response": response_text
                }
            
            # Ensure task_data is a dict and has "tasks" key
            if not isinstance(task_data, dict) or "tasks" not in task_data:
                task_data = {"tasks": []}
            
            # Enhance with metadata
            for task in task_data.get("tasks", []):
                task["source"] = "email"
                task["source_id"] = context.get("message_id")
                task["created_at"] = datetime.datetime.now().isoformat()
                
            return {
                "status": "success",
                "data": task_data
            }
            
        except Exception as e:
            print(f"[TaskAgent] Error processing request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "raw_response": locals().get('response_text', 'No response')
            }

task_agent = TaskAgent()
