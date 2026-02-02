import os
import json
from datetime import datetime
from typing import List, Dict, Any
from core.config import settings

class LearningService:
    def __init__(self):
        self.learning_path = os.path.join(settings.DATA_DIR, "learning_core.json")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.learning_path):
            with open(self.learning_path, 'w') as f:
                json.dump({"lessons": [], "last_updated": None}, f)

    def get_lessons(self) -> str:
        """Retrieve aggregated lessons for context injection."""
        try:
            with open(self.learning_path, 'r') as f:
                data = json.load(f)

            lessons = data.get("lessons", [])
            if not lessons:
                return "No historical lessons learned yet."

            # Return most recent 5 lessons
            recent = sorted(lessons, key=lambda x: x['date'], reverse=True)[:5]
            return "\n".join([f"- {l['date']}: {l['lesson']}" for l in recent])
        except Exception as e:
            print(f"Error reading learning core: {e}")
            return "Error retrieving lessons."

    def save_lesson(self, lesson: str, context: str = "Self-Audit"):
        """Save a new lesson to the core."""
        try:
            with open(self.learning_path, 'r') as f:
                data = json.load(f)

            data["lessons"].append({
                "date": datetime.now().isoformat(),
                "lesson": lesson,
                "context": context
            })
            data["last_updated"] = datetime.now().isoformat()

            with open(self.learning_path, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"Lesson saved: {lesson}")
        except Exception as e:
            print(f"Error saving lesson: {e}")

    async def run_self_audit(self):
        """
        The Shadow Tester: Compares predictions vs reality.
        For MVP, this mocks the comparison logic but establishes the pipeline.
        """
        from services.ai_service import ai_service

        # 1. Fetch Yesterday's Prediction (Mocked for now as we just started)
        prediction = "Predicted: Rough-in completion by 5 PM."

        # 2. Fetch Actual Log (Mocked)
        actual = "Actual: Rough-in completed at 6:30 PM due to missing conduit bender."

        # 3. Generate Lesson
        prompt = f"""
        Analyze the discrepancy between prediction and reality.
        {prediction}
        {actual}

        Output a single sentence 'Lesson Learned' for future improvement.
        """

        lesson = await ai_service.generate_content(prompt)
        if lesson:
            self.save_lesson(lesson.strip(), "Daily Self-Audit")

learning_service = LearningService()
