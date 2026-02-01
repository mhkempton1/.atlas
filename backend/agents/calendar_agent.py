from typing import Dict, Any, List, Optional
from agents.base import BaseAgent
from services.ai_service import ai_service
import json
import datetime

class CalendarAgent(BaseAgent):
    """
    Agent responsible for extracting scheduling details from email content.
    """
    
    def __init__(self):
        super().__init__(agent_name="CalendarAgent")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email and extract calendar event details.
        """
        subject = context.get('subject', '')
        sender = context.get('sender', '')
        body = context.get('body', '')
        current_time = datetime.datetime.now().isoformat()
        
        # Construct Prompt
        prompt = f"""
        You are an AI Scheduling Assistant.
        Analyze the following email and extract event details for a calendar entry.
        
        Current Date/Time: {current_time}
        
        Email Context:
        From: {sender}
        Subject: {subject}
        Body:
        {body}
        
        Instructions:
        1. Identify if this email discusses a meeting, appointment, or deadline.
        2. Extract a clear Event Title.
        3. Infer Start and End times in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). 
           - If no duration is specified, assume 1 hour.
           - If no date is specified, return null.
        4. Identify the Location (physical or virtual/link).
        5. List Attendees (names/emails found).
        6. Return the result as a STRICT JSON object.
        
        JSON Schema:
        {{
            "is_event": true/false,
            "event": {{
                "title": "Meeting Title",
                "start_time": "ISO_TIMESTAMP" or null,
                "end_time": "ISO_TIMESTAMP" or null,
                "location": "Location string",
                "description": "Agenda or notes...",
                "attendees": ["email1", "email2"]
            }}
        }}
        
        If it's not an event, set "is_event" to false and "event" to null.
        Do not include markdown formatting (```json). Just the raw JSON string.
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
                event_data = json.loads(cleaned_text)
            except json.JSONDecodeError as je:
                print(f"[CalendarAgent] JSON Parse Error: {je}")
                return {
                    "status": "error",
                    "error": f"Failed to parse AI response as JSON: {str(je)}",
                    "raw_response": response_text
                }
            
            # Enhance with metadata
            if isinstance(event_data, dict) and event_data.get("is_event"):
                event_data["source"] = "email"
                event_data["source_id"] = context.get("message_id")
                
            return {
                "status": "success",
                "data": event_data
            }
            
        except Exception as e:
            print(f"[CalendarAgent] Error processing request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "raw_response": locals().get('response_text', 'No response')
            }

calendar_agent = CalendarAgent()
