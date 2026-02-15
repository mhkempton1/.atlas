from typing import List, Dict, Any, Optional
from database.database import SessionLocal
from database.models import Contact, Email
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import datetime

class ContactService:
    """
    Service for managing contacts and calculating VIP rankings.
    """
    
    def list_contacts(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """List all contacts."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            contacts = db.query(Contact).all()
            return [
                {
                    "contact_id": c.contact_id,
                    "name": c.name,
                    "email": c.email_address,
                    "company": c.company,
                    "role": c.role,
                    "category": c.category,
                    "email_count": c.email_count,
                    "importance_score": self.calculate_importance(c, db)
                }
                for c in contacts
            ]
        finally:
            if close_db: db.close()

    def calculate_importance(self, contact: Contact, db: Session) -> int:
        """
        Calculate importance score (0-100).
        """
        score = 0
        
        # 1. Email Volume (up to 40 points)
        score += min(contact.email_count or 0, 40)
        
        # 2. Role Keywords (up to 30 points)
        role = (contact.role or "").lower()
        if any(kw in role for kw in ["director", "vp", "manager", "head"]):
            score += 20
        if any(kw in role for kw in ["ceo", "owner", "president"]):
            score += 30
            
        # 3. Recency (up to 30 points)
        if contact.last_contact_date:
            days_since = (datetime.datetime.now() - contact.last_contact_date).days
            if days_since < 7:
                score += 30
            elif days_since < 30:
                score += 15
                
        return min(score, 100)

    def get_vip_contacts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return the top ranked contacts.
        """
        contacts = self.list_contacts()
        contacts.sort(key=lambda x: x["importance_score"], reverse=True)
        return contacts[:limit]

    def calculate_health(self, contact_id: int, db: Session) -> Dict[str, Any]:
        """
        Assess contact health based on activity gap.
        """
        contact = db.query(Contact).filter(Contact.contact_id == contact_id).first()
        if not contact: return {"score": 0, "status": "unknown"}
        
        if not contact.last_contact_date: 
            return {"score": 30, "status": "stale", "days": "N/A"}
            
        days_since = (datetime.datetime.now() - contact.last_contact_date).days
        
        if days_since < 14:
            return {"score": 100, "status": "healthy", "days": days_since}
        elif days_since < 30:
            return {"score": 70, "status": "good", "days": days_since}
        elif days_since < 60:
            return {"score": 40, "status": "re-engage", "days": days_since}
        else:
            return {"score": 10, "status": "stale", "days": days_since}

    def get_at_risk_contacts(self) -> List[Dict[str, Any]]:
        """Find contacts that haven't been touched in a long time."""
        db = SessionLocal()
        try:
            contacts = db.query(Contact).all()
            at_risk = []
            for c in contacts:
                health = self.calculate_health(c.contact_id, db)
                if health["score"] < 50:
                    at_risk.append({
                        "name": c.name,
                        "email": c.email_address,
                        "health": health
                    })
            return at_risk
        finally:
            db.close()

contact_service = ContactService()
