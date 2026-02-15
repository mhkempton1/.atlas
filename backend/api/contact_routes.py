from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from database.database import get_db
from database.models import Contact
from services.contact_unification_service import get_all_emails_with_contact
from api.email_routes import EmailResponse
from pydantic import BaseModel, ConfigDict
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
    is_starred: bool = False
    tags: Optional[list] = None
    notes: Optional[str] = None
    last_contact_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[ContactResponse])
async def list_contacts(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all contacts with email count"""
    contacts = db.query(Contact).limit(limit).offset(offset).all()
    return contacts

@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search contacts by name or email"""
    search_term = f"%{q}%"
    contacts = db.query(Contact).filter(
        or_(
            Contact.name.ilike(search_term),
            Contact.email_address.ilike(search_term)
        )
    ).limit(limit).all()
    return contacts

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get contact details"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.get("/{contact_id}/emails", response_model=List[EmailResponse])
async def get_contact_emails(
    contact_id: int,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    """Get threaded emails for a contact"""
    # Verify contact exists first
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    emails = get_all_emails_with_contact(contact_id, db, page, per_page)
    return emails
