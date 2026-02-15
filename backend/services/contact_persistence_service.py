from sqlalchemy.orm import Session
from database.models import Contact
from datetime import datetime, timezone
import email.utils

def get_contact_by_email(email_address: str, db: Session):
    """
    Retrieve a contact by email address.
    """
    if not email_address:
        return None
    return db.query(Contact).filter(Contact.email_address == email_address.lower()).first()

def persist_contact_to_database(contact_data: dict, db: Session):
    """
    Persist a contact object to the database.
    Updates if exists, creates if new.
    """
    email_address = contact_data.get('email_address')
    if not email_address:
        return None

    email_address = email_address.lower()
    contact_data['email_address'] = email_address

    existing_contact = get_contact_by_email(email_address, db)

    if existing_contact:
        # Update existing
        for key, value in contact_data.items():
            if hasattr(existing_contact, key) and value is not None:
                setattr(existing_contact, key, value)

        try:
            db.commit()
            db.refresh(existing_contact)
            return existing_contact
        except Exception as e:
            db.rollback()
            raise e
    else:
        # Create new
        new_contact = Contact(**contact_data)
        try:
            db.add(new_contact)
            db.commit()
            db.refresh(new_contact)
            return new_contact
        except Exception as e:
            db.rollback()
            raise e

def update_contact_from_email(email_input: str, db: Session):
    """
    Update or create a contact based on an email address string (e.g., "Name <email>").

    Args:
        email_input: Email string (e.g. "John Doe <john@example.com>" or just "john@example.com")
        db: Database session
    """
    if not email_input:
        return None

    # Parse name and email
    name, email_address = email.utils.parseaddr(email_input)

    if not email_address:
        # Fallback if parseaddr fails or returns empty but input might be just email
        if '@' in email_input:
            email_address = email_input.strip()
        else:
            return None # Invalid email

    # Normalize email
    email_address = email_address.lower()

    existing_contact = get_contact_by_email(email_address, db)

    if existing_contact:
        # Increment count and update last_contact_date
        existing_contact.email_count += 1
        existing_contact.last_contact_date = datetime.now(timezone.utc)

        # Update name if missing in DB but present in email
        if not existing_contact.name and name:
            existing_contact.name = name

        try:
            db.commit()
            db.refresh(existing_contact)
            return existing_contact
        except Exception as e:
            db.rollback()
            print(f"Error updating contact {email_address}: {e}")
            return None
    else:
        # Create new contact
        new_contact = Contact(
            email_address=email_address,
            name=name,
            first_contact_date=datetime.now(timezone.utc),
            last_contact_date=datetime.now(timezone.utc),
            email_count=1
        )
        try:
            db.add(new_contact)
            db.commit()
            db.refresh(new_contact)
            return new_contact
        except Exception as e:
            db.rollback()
            print(f"Error creating contact {email_address}: {e}")
            return None
