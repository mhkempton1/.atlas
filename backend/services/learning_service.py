from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Learning
from datetime import datetime
from typing import List, Dict, Any

class LearningService:
    def get_recent_lessons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the database for the most recent learned patterns.
        Returns list of {topic, insight, source, created_at}.
        """
        db: Session = SessionLocal()
        try:
            lessons = db.query(Learning).order_by(Learning.created_at.desc()).limit(limit).all()
            return [
                {
                    "topic": l.topic,
                    "insight": l.insight,
                    "source": l.source,
                    "created_at": l.created_at.isoformat() if l.created_at else None
                }
                for l in lessons
            ]
        finally:
            db.close()

    def record_lesson(self, topic: str, insight: str, source: str):
        """
        Persist a new learning record to the database.
        Deduplicate: if same topic+insight exists, update timestamp only.
        """
        db: Session = SessionLocal()
        try:
            existing = db.query(Learning).filter(
                Learning.topic == topic,
                Learning.insight == insight
            ).first()

            if existing:
                # Update timestamp to bring it to top of recent list
                existing.created_at = datetime.now()
                # Also update updated_at if needed, though usually handled by model hook.
                # But we explicitly want to "refresh" the lesson.
                db.commit()
            else:
                new_lesson = Learning(
                    topic=topic,
                    insight=insight,
                    source=source
                )
                db.add(new_lesson)
                db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Legacy/Helper for AI Service context injection, maintaining backward compatibility if needed
    def get_lessons(self) -> str:
        """Retrieve aggregated lessons formatted for context injection."""
        lessons = self.get_recent_lessons(limit=5)
        if not lessons:
            return "No historical lessons learned yet."

        # Format similar to previous implementation for consistency
        return "\n".join([f"- {l['created_at']}: [{l['topic']}] {l['insight']}" for l in lessons])

learning_service = LearningService()
