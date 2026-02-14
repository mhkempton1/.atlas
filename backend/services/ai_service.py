from typing import Optional
import asyncio
import json
import time
import datetime
import os
try:
    from google import genai
except ImportError:
    genai = None
from core.config import settings

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_FILE = os.path.join(LOG_DIR, "ai_audit_log.jsonl")

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

    def _log_audit(self, prompt: str, response: str, model: str, tokens_used: Optional[int], latency_ms: float, status: str, error_message: Optional[str] = None):
        """
        Log AI audit entry.
        """
        if os.environ.get("TEST"):
            return

        try:
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)

            # Log rotation
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 50 * 1024 * 1024:
                rotated_file = LOG_FILE.replace(".jsonl", ".1.jsonl")
                os.replace(LOG_FILE, rotated_file)

            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "prompt": prompt,
                "response": response,
                "model": model,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "status": status
            }
            if error_message:
                entry["error_message"] = error_message

            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Fallback print if logging fails
            print(f"Failed to write to AI audit log: {e}")

    def _build_context(self, user_strata: int) -> str:
        """
        Build system context string.
        """
        from services.altimeter_service import altimeter_service
        from services.learning_service import learning_service

        context_str = "\n\n[SYSTEM CONTEXT]\n"

        # 1. Strata Permissions
        permissions = settings.STRATA_PERMISSIONS.get(user_strata, [])
        context_str += f"User Access Level: Strata {user_strata} (Permissions: {', '.join(permissions)})\n"

        # 2. Learning Core (Shadow Tester Feedback)
        try:
            recent_lessons = learning_service.get_recent_lessons(limit=5)
            if recent_lessons:
                lessons_str = "\n".join([f"- {l['created_at']}: [{l['topic']}] {l['insight']}" for l in recent_lessons])
                context_str += f"Previous learnings:\n{lessons_str}\n"
            else:
                context_str += "Previous learnings: None\n"
        except Exception:
            context_str += "Previous learnings: Unavailable\n"

        # 3. Active Projects
        try:
            projects = altimeter_service.list_projects()
            active_projects = [p['name'] for p in projects[:3]]
            context_str += f"Active Projects: {', '.join(active_projects)}\n"
        except Exception:
            pass

        return context_str

    async def generate_content(
        self,
        prompt: str,
        max_retries: int = 3,
        include_context: bool = False,
        user_strata: int = 1,
        json_mode: bool = False
    ) -> Optional[str]:
        """
        Generate content using Gemini AI.

        Args:
            prompt: The prompt to send to the AI.
            max_retries: Maximum number of retries in case of failure.
            include_context: Whether to include system context in the prompt.
            user_strata: The user's strata level for context customization.
            json_mode: Whether to enforce JSON output structure.

        Returns:
            The generated content as a string, or an error message.
        """
        if not self.client:
            return "AI Service Unavailable: Missing API Key"

        final_prompt = prompt
        
        # Inject Context
        if include_context:
            final_prompt += self._build_context(user_strata)

        config = {}
        if json_mode:
            config["response_mime_type"] = "application/json"

        start_time = time.time()

        for attempt in range(max_retries + 1):
            try:
                # The new SDK is synchronous by default, but we wrap it in async for the service interface
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=final_prompt,
                    config=config
                )

                # Log success
                tokens_used = None
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    tokens_used = response.usage_metadata.total_token_count

                self._log_audit(
                    prompt=final_prompt,
                    response=response.text,
                    model=self.model_name,
                    tokens_used=tokens_used,
                    latency_ms=(time.time() - start_time) * 1000,
                    status="success"
                )

                return response.text
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg
                
                if is_rate_limit and attempt < max_retries:
                    wait_time = (2 ** attempt) + 1
                    await asyncio.sleep(wait_time)
                    continue
                
                latency_ms = (time.time() - start_time) * 1000
                if is_rate_limit:
                    self._log_audit(
                        prompt=final_prompt,
                        response="ERROR_RATE_LIMIT_EXCEEDED",
                        model=self.model_name,
                        tokens_used=None,
                        latency_ms=latency_ms,
                        status="error",
                        error_message="Rate limit exceeded"
                    )
                    return "ERROR_RATE_LIMIT_EXCEEDED"
                
                self._log_audit(
                    prompt=final_prompt,
                    response=f"Error generating content: {error_msg}",
                    model=self.model_name,
                    tokens_used=None,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=error_msg
                )
                return f"Error generating content: {error_msg}"

# Singleton instance
ai_service = GeminiService()
