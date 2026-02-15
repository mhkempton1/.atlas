from fastapi import APIRouter, Depends, HTTPException
from database.database import get_db
from database.models import Notification
from sqlalchemy.orm import Session
from typing import List, Optional
from services.notification_service import notification_service
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    priority: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

@router.get("/list", response_model=List[NotificationResponse])
async def get_notifications(unread_only: bool = True, db: Session = Depends(get_db)):
    """Get notifications list."""
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    return query.order_by(Notification.created_at.desc()).limit(50).all()

@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int):
    """Mark notification as read."""
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}

@router.delete("/clear")
async def clear_notifications():
    """Clear all notifications."""
    count = notification_service.clear_all()
    return {"success": True, "cleared_count": count}
