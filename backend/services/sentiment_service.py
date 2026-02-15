from services.ai_service import ai_service
from typing import Dict, Any

class SentimentService:
    """
    Service for analyzing sentiment of incoming emails using Gemini AI.
    """
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment, returning label and score.
        Labels: Positive, Neutral, Negative, Frustrated
        """
        prompt = f"""
        Analyze the sentiment of the following email text.
        Return ONLY a JSON object with:
        - label: "Positive", "Neutral", "Negative", or "Frustrated"
        - score: 0.0 to 1.0 (magnitude)
        - reasoning: "Short explanation"
        
        Text:
        {text[:2000]}
        """
        
        try:
            response = await ai_service.generate_content(prompt)
            # Clean possible markdown
            cleaned = response.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(cleaned)
        except Exception as e:
            print(f"[SentimentService] Error: {e}")
            return {"label": "Neutral", "score": 0.5, "reasoning": "Fallback due to error"}

sentiment_service = SentimentService()
