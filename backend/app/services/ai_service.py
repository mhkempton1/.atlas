import os
import google.generativeai as genai

class GeminiService:
    """Service to interact with Google Gemini API"""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    async def generate_response(self, prompt: str) -> str:
        if not self.is_available():
            return "AI Service Unavailable (Missing Key)"
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"
