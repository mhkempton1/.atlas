from typing import Dict, Any, Optional
try:
    from google import genai
except ImportError:
    genai = None
from core.config import settings

class GeminiService:
    def __init__(self):
        # Initialize Gemini if key is present
        if settings.GEMINI_API_KEY and genai:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model_name = 'gemini-2.0-flash'
        else:
            self.client = None
            self.model_name = None
            if not genai:
                print("Warning: google-genai package not found.")
            else:
                print("Warning: GEMINI_API_KEY not found. AI features will be limited.")

    async def generate_content(self, prompt: str, max_retries: int = 3, include_context: bool = False) -> Optional[str]:
        if not self.client:
            return "AI Service Unavailable: Missing API Key"
        
        import asyncio
        import time
        from services.altimeter_service import altimeter_service

        final_prompt = prompt
        
        # Inject Altimeter Context (The Oracle Protocol)
        if include_context:
            try:
                projects = altimeter_service.list_projects()
                active_projects = [p['name'] for p in projects[:3]]
                context_str = f"\n\n[SYSTEM CONTEXT: ACTIVE PROJECTS -> {', '.join(active_projects)}]"
                final_prompt += context_str
            except Exception as e:
                print(f"Context injection failed: {e}")

        for attempt in range(max_retries + 1):
            try:
                # The new SDK is synchronous by default, but we wrap it in async for the service interface
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=final_prompt
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
                
                if is_rate_limit and attempt < max_retries:
                    wait_time = (2 ** attempt) + 1
                    print(f"Gemini Rate Limit (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                
                if is_rate_limit:
                    print(f"Gemini Rate Limit Exceeded after {max_retries} retries: {error_msg}")
                    return "ERROR_RATE_LIMIT_EXCEEDED"
                
                print(f"Gemini API Error: {e}")
                return f"Error generating content: {error_msg}"

# Singleton instance
ai_service = GeminiService()
