from typing import Optional
import asyncio
try:
    from google import genai
except ImportError:
    genai = None
from core.config import settings

class GeminiService:
    """
    Service for interacting with Google Gemini AI.
    """
    def __init__(self):
        """Initialize the Gemini Service."""
        # Initialize Gemini if key is present
        if settings.GEMINI_API_KEY and genai:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model_name = 'gemini-2.0-flash'
        else:
            self.client = None
            self.model_name = None

    async def generate_content(self, prompt: str, max_retries: int = 3, include_context: bool = False, user_strata: int = 1) -> Optional[str]:
        """
        Generate content using Gemini AI.

        Args:
            prompt: The prompt to send to the AI.
            max_retries: Maximum number of retries in case of failure.
            include_context: Whether to include system context in the prompt.
            user_strata: The user's strata level for context customization.

        Returns:
            The generated content as a string, or an error message.
        """
        if not self.client:
            return "AI Service Unavailable: Missing API Key"
        
        from services.altimeter_service import altimeter_service
        from services.learning_service import learning_service

        final_prompt = prompt
        
        # Inject Context (Oracle + Strata + Learning)
        if include_context:
            context_str = "\n\n[SYSTEM CONTEXT]\n"

            # 1. Strata Permissions
            permissions = settings.STRATA_PERMISSIONS.get(user_strata, [])
            context_str += f"User Access Level: Strata {user_strata} (Permissions: {', '.join(permissions)})\n"

            # 2. Learning Core (Shadow Tester Feedback)
            lessons = learning_service.get_lessons()
            context_str += f"Lessons Learned:\n{lessons}\n"

            # 3. Active Projects (Filtered by Strata if needed - implemented in list_projects?)
            try:
                projects = altimeter_service.list_projects()
                active_projects = [p['name'] for p in projects[:3]]
                context_str += f"Active Projects: {', '.join(active_projects)}\n"
            except Exception:
                pass

            final_prompt += context_str

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
                    await asyncio.sleep(wait_time)
                    continue
                
                if is_rate_limit:
                    return "ERROR_RATE_LIMIT_EXCEEDED"
                
                return f"Error generating content: {error_msg}"

# Singleton instance
ai_service = GeminiService()
