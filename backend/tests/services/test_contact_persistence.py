import pytest
from datetime import datetime, timezone
from services.contact_persistence_service import update_contact_from_email, persist_contact_to_database, get_contact_by_email
from database.models import Contact

def test_get_contact_by_email(db):
    # Setup
    contact = Contact(email_address="test@example.com", name="Test User")
    db.add(contact)
    db.commit()

    # Test
    result = get_contact_by_email("test@example.com", db)
    assert result is not None
    assert result.email_address == "test@example.com"
    assert result.name == "Test User"

    # Test not found
    result = get_contact_by_email("unknown@example.com", db)
    assert result is None

def test_persist_contact_to_database_create(db):
    data = {"email_address": "new@example.com", "name": "New User", "company": "Acme"}

    result = persist_contact_to_database(data, db)

    assert result is not None
    assert result.email_address == "new@example.com"
    assert result.name == "New User"
    assert result.company == "Acme"

    # Verify in DB
    contact = db.query(Contact).filter(Contact.email_address == "new@example.com").first()
    assert contact is not None

def test_persist_contact_to_database_update(db):
    # Setup
    contact = Contact(email_address="existing@example.com", name="Old Name")
    db.add(contact)
    db.commit()

    data = {"email_address": "existing@example.com", "name": "New Name", "company": "Acme"}

    result = persist_contact_to_database(data, db)

    assert result.name == "New Name"
    assert result.company == "Acme"

    # Verify in DB
    updated = db.query(Contact).filter(Contact.email_address == "existing@example.com").first()
    assert updated.name == "New Name"
    assert updated.company == "Acme"

def test_update_contact_from_email_new(db):
    email_input = "John Doe <john@example.com>"

    result = update_contact_from_email(email_input, db)

    assert result is not None
    assert result.email_address == "john@example.com"
    assert result.name == "John Doe"
    assert result.email_count == 1
    assert result.first_contact_date is not None
    assert result.last_contact_date is not None

def test_update_contact_from_email_existing(db):
    # Setup
    contact = Contact(
        email_address="john@example.com",
        name="John Doe",
        email_count=5,
        last_contact_date=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )
    db.add(contact)
    db.commit()

    email_input = "John Updated <john@example.com>"

    result = update_contact_from_email(email_input, db)

    assert result.email_count == 6
    # Avoid timezone offset issues with SQLite
    if result.last_contact_date.tzinfo:
        assert result.last_contact_date > datetime(2020, 1, 1, tzinfo=timezone.utc)
    else:
        assert result.last_contact_date > datetime(2020, 1, 1)

    # Name should NOT be updated if it already exists
    assert result.name == "John Doe"

def test_update_contact_from_email_existing_no_name(db):
    # Setup
    contact = Contact(
        email_address="john@example.com",
        name=None,
        email_count=5
    )
    db.add(contact)
    db.commit()

    email_input = "John New <john@example.com>"

    result = update_contact_from_email(email_input, db)

    assert result.name == "John New"
    assert result.email_count == 6
