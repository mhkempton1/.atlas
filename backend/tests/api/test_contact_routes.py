import pytest
from datetime import datetime, timezone, timedelta
from database.models import Contact, Email

def test_list_contacts(client, db):
    # Setup
    contact1 = Contact(email_address="alice@example.com", name="Alice", email_count=5)
    contact2 = Contact(email_address="bob@example.com", name="Bob", email_count=2)
    db.add(contact1)
    db.add(contact2)
    db.commit()

    response = client.get("/api/v1/contacts")
    assert response.status_code == 200
    data = response.json()
    # Note: DB might have other contacts from other tests if not cleaned properly,
    # but conftest says it uses transaction rollback or drop/create.
    # We should filter or just check existence.
    emails = [c["email_address"] for c in data]
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails

def test_get_contact(client, db):
    # Setup
    contact = Contact(email_address="charlie@example.com", name="Charlie")
    db.add(contact)
    db.commit()
    db.refresh(contact)

    response = client.get(f"/api/v1/contacts/{contact.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email_address"] == "charlie@example.com"
    assert data["name"] == "Charlie"

def test_get_contact_not_found(client, db):
    response = client.get("/api/v1/contacts/999999")
    assert response.status_code == 404

def test_search_contacts(client, db):
    # Setup
    contact1 = Contact(email_address="dave@example.com", name="Dave")
    contact2 = Contact(email_address="eve@example.com", name="Eve")
    db.add(contact1)
    db.add(contact2)
    db.commit()

    # Search by name
    response = client.get("/api/v1/contacts/search?q=Dave")
    assert response.status_code == 200
    data = response.json()
    found_names = [c["name"] for c in data]
    assert "Dave" in found_names
    assert "Eve" not in found_names

    # Search by email
    response = client.get("/api/v1/contacts/search?q=eve@")
    assert response.status_code == 200
    data = response.json()
    found_emails = [c["email_address"] for c in data]
    assert "eve@example.com" in found_emails

def test_get_contact_emails_threaded(client, db):
    # Setup
    contact = Contact(email_address="frank@example.com", name="Frank")
    db.add(contact)
    db.commit()
    db.refresh(contact)

    # Email 1: From Frank, Thread A, Older
    email1 = Email(
        subject="Thread A - Old",
        sender="frank@example.com",
        from_address="frank@example.com",
        date_received=datetime.now(timezone.utc) - timedelta(days=2),
        thread_id="thread_a",
        recipients=["me@example.com"]
    )

    # Email 2: From Frank, Thread A, Newer
    email2 = Email(
        subject="Thread A - New",
        sender="frank@example.com",
        from_address="frank@example.com",
        date_received=datetime.now(timezone.utc) - timedelta(days=1),
        thread_id="thread_a",
        recipients=["me@example.com"]
    )

    # Email 3: To Frank, Thread B
    email3 = Email(
        subject="Thread B",
        sender="me@example.com",
        from_address="me@example.com",
        date_received=datetime.now(timezone.utc),
        thread_id="thread_b",
        recipients=["frank@example.com"],
        to_addresses=["frank@example.com"]
    )

    # Email 4: Unrelated
    email4 = Email(
        subject="Unrelated",
        sender="stranger@example.com",
        from_address="stranger@example.com",
        recipients=["me@example.com"],
        date_received=datetime.now(timezone.utc),
        thread_id="thread_c"
    )

    db.add(email1)
    db.add(email2)
    db.add(email3)
    db.add(email4)
    db.commit()

    response = client.get(f"/api/v1/contacts/{contact.id}/emails")
    assert response.status_code == 200
    data = response.json()

    # Should see 2 emails (one per thread involving Frank)
    # Thread A (should pick email2 as it is newer) and Thread B
    assert len(data) == 2

    # Sort order: Thread B (today) -> Thread A (yesterday)
    # Note: data[0] is most recent
    assert data[0]["thread_id"] == "thread_b"
    assert data[1]["thread_id"] == "thread_a"

    # Check if we got the latest email for Thread A
    # Wait, 'Thread A - New' is newer than 'Thread A - Old'.
    # And 'Thread B' is today (newest).

    # Verify content of the thread items
    subjects = {d["thread_id"]: d["subject"] for d in data}
    assert subjects["thread_a"] == "Thread A - New"
    assert subjects["thread_b"] == "Thread B"

def test_get_contact_emails_mixed_threading(client, db):
    # Setup
    contact = Contact(email_address="grace@example.com", name="Grace")
    db.add(contact)
    db.commit()
    db.refresh(contact)

    # Threaded Email (Newest overall)
    email1 = Email(
        subject="Threaded 1",
        sender="grace@example.com",
        date_received=datetime.now(timezone.utc),
        thread_id="thread_x",
        recipients=["me@example.com"]
    )

    # Threaded Email (Older)
    email2 = Email(
        subject="Threaded 1 Old",
        sender="grace@example.com",
        date_received=datetime.now(timezone.utc) - timedelta(days=2),
        thread_id="thread_x",
        recipients=["me@example.com"]
    )

    # Unthreaded Email (Middle)
    email3 = Email(
        subject="Unthreaded",
        sender="grace@example.com",
        date_received=datetime.now(timezone.utc) - timedelta(days=1),
        thread_id=None,
        recipients=["me@example.com"]
    )

    db.add(email1)
    db.add(email2)
    db.add(email3)
    db.commit()

    response = client.get(f"/api/v1/contacts/{contact.id}/emails")
    assert response.status_code == 200
    data = response.json()

    # Expect: Threaded 1 (newest), Unthreaded (middle)
    # Threaded 1 Old should be hidden by Threaded 1
    assert len(data) == 2

    # Order: email1 (Threaded 1), email3 (Unthreaded)
    assert data[0]["subject"] == "Threaded 1"
    assert data[1]["subject"] == "Unthreaded"
