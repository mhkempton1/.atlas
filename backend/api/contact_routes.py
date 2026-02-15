from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Contact
from services.contact_persistence_service import get_contact_by_email
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

router = APIRouter()

class ContactResponse(BaseModel):
    id: int
    email_address: str
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    relationship_type: Optional[str] = None
    email_count: int = 0
    last_contact_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    altimeter_customer_id: Optional[int] = None
    altimeter_vendor_id: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

@router.get("/search", response_model=Optional[ContactResponse])
async def search_contacts(q: str = Query(..., min_length=3), db: Session = Depends(get_db)):
    """
    Search for a contact by email address.
    Returns null if not found (frontend handles "Unknown Contact").
    """
    contact = get_contact_by_email(q, db)
    return contact
