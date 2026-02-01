import pytest
from unittest.mock import MagicMock, patch
from services.google_service import GoogleService
from database.models import Email, CalendarEvent
from datetime import datetime

@pytest.fixture
def google_service_instance():
    # Patch authenticate to avoid real auth during init
    with patch.object(GoogleService, 'authenticate', return_value=None), \
         patch('services.search_service.search_service') as mock_search:
        service = GoogleService()
        service.gmail_service = MagicMock()
        service.calendar_service = MagicMock()
        yield service

def test_extract_body_plain_text(google_service_instance):
    payload = {
        'mimeType': 'text/plain',
        'body': {'data': 'SGVsbG8gV29ybGQ='}  # "Hello World" in base64url
    }
    body_text, body_html = google_service_instance._extract_body(payload)
    assert body_text == "Hello World"
    assert body_html == ""

def test_extract_body_multipart(google_service_instance):
    payload = {
        'mimeType': 'multipart/alternative',
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {'data': 'UGxhaW4gdGV4dA=='} # "Plain text"
            },
            {
                'mimeType': 'text/html',
                'body': {'data': 'PGgxPkh0bWw8L2gxPg=='} # "<h1>Html</h1>"
            }
        ]
    }
    body_text, body_html = google_service_instance._extract_body(payload)
    assert body_text == "Plain text"
    assert body_html == "<h1>Html</h1>"

def test_store_email_duplicate(google_service_instance, db):
    # Mock message
    message = {
        'id': 'msg123',
        'threadId': 'thread123',
        'payload': {'headers': []}
    }
    
    # Add existing email to DB
    existing_email = Email(gmail_id='msg123', message_id='id123')
    db.add(existing_email)
    db.commit()
    
    result = google_service_instance._store_email(message, db)
    assert result is False

def test_store_email_success(google_service_instance, db):
    message = {
        'id': 'msg_new',
        'threadId': 'thread_new',
        'snippet': 'This is a snippet',
        'labelIds': ['INBOX', 'UNREAD'],
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'Subject', 'value': 'Test Subject'},
                {'name': 'Date', 'value': 'Mon, 26 Jan 2026 10:00:00 +0000'},
                {'name': 'Message-ID', 'value': '<new_id@msg>'}
            ],
            'mimeType': 'text/plain',
            'body': {'data': 'VGVzdCBCb2R5'} # "Test Body"
        }
    }
    
    result = google_service_instance._store_email(message, db)
    assert result is True
    
    stored = db.query(Email).filter_by(gmail_id='msg_new').first()
    assert stored is not None
    assert stored.subject == 'Test Subject'
    assert stored.from_address == 'test@example.com'
    assert stored.is_read is False

def test_sync_calendar_storage(google_service_instance, db):
    event_data = {
        'id': 'event123',
        'summary': 'Meeting',
        'description': 'Important meeting',
        'start': {'dateTime': '2026-01-26T12:00:00Z'},
        'end': {'dateTime': '2026-01-26T13:00:00Z'},
        'status': 'confirmed',
        'organizer': {'email': 'boss@example.com'}
    }
    
    result = google_service_instance._store_event(event_data, db)
    assert result is True
    
    stored = db.query(CalendarEvent).filter_by(google_event_id='event123').first()
    assert stored is not None
    assert stored.title == 'Meeting'
    assert stored.organizer == 'boss@example.com'

def test_parse_date_robustness(google_service_instance):
    # Valid date
    dt = google_service_instance._parse_date('Mon, 26 Jan 2026 10:00:00 +0000')
    assert dt.year == 2026
    assert dt.month == 1
    
    # Invalid date should return current date (soft fail)
    dt_fail = google_service_instance._parse_date('invalid date')
    assert isinstance(dt_fail, datetime)

def test_store_email_missing_message_id(google_service_instance, db):
    message = {
        'id': 'msg_no_id',
        'threadId': 'thread_no_id',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'Subject', 'value': 'No Message-ID'},
                {'name': 'Date', 'value': 'Mon, 26 Jan 2026 10:00:00 +0000'}
            ],
            'mimeType': 'text/plain',
            'body': {'data': 'VGVzdCBCb2R5'}
        }
    }
    
    result = google_service_instance._store_email(message, db)
    assert result is True
    
    stored = db.query(Email).filter_by(gmail_id='msg_no_id').first()
    assert stored is not None
    assert stored.message_id.startswith('atlas-')
