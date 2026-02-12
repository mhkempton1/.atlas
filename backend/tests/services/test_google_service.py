import pytest
from unittest.mock import MagicMock, patch
from services.google_service import GoogleService
from database.models import Email, CalendarEvent
from datetime import datetime
import base64
import email

@pytest.fixture
def google_service_instance():
    # Patch authenticate to avoid real auth during init
    with patch.object(GoogleService, 'authenticate', return_value=None), \
         patch('services.search_service.search_service') as mock_search, \
         patch('services.altimeter_service.altimeter_service') as mock_altimeter:

        service = GoogleService()

        # Setup Gmail Service Mock Chain
        # service.gmail_service.users().messages().get().execute()
        gmail_mock = MagicMock()
        users_mock = MagicMock()
        messages_mock = MagicMock()
        labels_mock = MagicMock()

        gmail_mock.users.return_value = users_mock
        users_mock.messages.return_value = messages_mock
        users_mock.labels.return_value = labels_mock

        service.gmail_service = gmail_mock
        service.calendar_service = MagicMock()

        # Mock Altimeter response
        mock_altimeter.get_context_for_email.return_value = {}

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

def test_extract_body_recursive(google_service_instance):
    """Test extracting body from nested multipart/mixed structure."""
    payload = {
        'mimeType': 'multipart/mixed',
        'parts': [
            {
                'mimeType': 'multipart/alternative',
                'parts': [
                     {'mimeType': 'text/plain', 'body': {'data': 'VGV4dA=='}}, # Text
                     {'mimeType': 'text/html', 'body': {'data': 'SFRNTA=='}}   # HTML
                ]
            },
            {
                'mimeType': 'application/pdf',
                'filename': 'doc.pdf'
            }
        ]
    }
    body_text, body_html = google_service_instance._extract_body(payload)
    assert body_text == "Text"
    assert body_html == "HTML"

def test_store_email_duplicate(google_service_instance, db):
    # Mock message
    message = {
        'id': 'msg123',
        'threadId': 'thread123',
        'payload': {'headers': []}
    }
    
    # Add existing email to DB
    existing_email = Email(remote_id='msg123', message_id='id123')
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
    
    stored = db.query(Email).filter_by(remote_id='msg_new').first()
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
    
    stored = db.query(CalendarEvent).filter_by(remote_event_id='event123').first()
    assert stored is not None
    assert stored.title == 'Meeting'
    assert stored.organizer == 'boss@example.com'

def test_sync_calendar_date_only(google_service_instance, db):
    """Test storage of all-day events (date only, no time)."""
    event_data = {
        'id': 'event_allday',
        'summary': 'Holiday',
        'start': {'date': '2026-01-01'},
        'end': {'date': '2026-01-02'},
        'status': 'confirmed'
    }

    result = google_service_instance._store_event(event_data, db)
    assert result is True

    stored = db.query(CalendarEvent).filter_by(remote_event_id='event_allday').first()
    assert stored is not None
    assert stored.all_day is True
    # Verify date parsing matches local or UTC midnight
    assert stored.start_time.year == 2026
    assert stored.start_time.month == 1
    assert stored.start_time.day == 1

def test_parse_date_robustness(google_service_instance):
    # Valid date
    dt = google_service_instance._parse_date('Mon, 26 Jan 2026 10:00:00 +0000')
    assert dt.year == 2026
    assert dt.month == 1
    
    # Invalid date should return current date (soft fail)
    dt_fail = google_service_instance._parse_date('invalid date')
    assert isinstance(dt_fail, datetime)

def test_reply_to_email(google_service_instance):
    """Test reply_to_email calls Gmail API correctly."""
    # Mock return of original message
    mock_messages = google_service_instance.gmail_service.users().messages()
    mock_messages.get().execute.return_value = {
        'threadId': 't1',
        'payload': {'headers': [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'Subject', 'value': 'Topic'},
            {'name': 'Message-ID', 'value': '<original@id>'}
        ]}
    }

    mock_messages.send().execute.return_value = {'id': 'new_msg_id'}

    result = google_service_instance.reply_to_email('msg_id', 'Reply body')

    assert result['success'] is True
    assert result['message_id'] == 'new_msg_id'

    # Verify get called
    mock_messages.get.assert_called_with(
        userId='me', id='msg_id', format='metadata',
        metadataHeaders=['From', 'To', 'Cc', 'Subject', 'Message-ID', 'References', 'In-Reply-To']
    )

    # Verify send called
    send_call_args = mock_messages.send.call_args[1]
    assert send_call_args['userId'] == 'me'
    assert send_call_args['body']['threadId'] == 't1'

    # Decode sent raw message to check headers
    raw = base64.urlsafe_b64decode(send_call_args['body']['raw'])
    msg = email.message_from_bytes(raw)

    assert msg['Subject'] == 'Re: Topic'
    assert msg['To'] == 'sender@example.com'
    assert msg['In-Reply-To'] == '<original@id>'

def test_forward_email(google_service_instance):
    """Test forward_email constructs correct body and subject."""
    mock_messages = google_service_instance.gmail_service.users().messages()

    # Mock original message
    mock_messages.get().execute.return_value = {
        'payload': {
            'headers': [{'name': 'Subject', 'value': 'Original Subject'}],
            'body': {'data': 'T3JpZ2luYWw='} # "Original"
        }
    }
    
    result = google_service_instance.forward_email('msg_id', 'recipient@test.com', 'Look at this')
    
    assert result['success'] is True

    send_call_args = mock_messages.send.call_args[1]
    raw = base64.urlsafe_b64decode(send_call_args['body']['raw'])
    msg = email.message_from_bytes(raw)

    assert msg['Subject'] == 'Fwd: Original Subject'
    assert msg['To'] == 'recipient@test.com'
    assert 'Look at this' in str(msg)

def test_trash_email(google_service_instance):
    """Test moving to trash."""
    result = google_service_instance.trash_email('msg_id')
    assert result['success'] is True

    google_service_instance.gmail_service.users().messages().trash.assert_called_with(
        userId='me', id='msg_id'
    )

def test_mark_unread(google_service_instance):
    """Test marking email as unread."""
    result = google_service_instance.mark_unread('msg_id')
    assert result['success'] is True

    google_service_instance.gmail_service.users().messages().modify.assert_called_with(
        userId='me', id='msg_id',
        body={'addLabelIds': ['UNREAD']}
    )

def test_move_to_label_create_new(google_service_instance):
    """Test moving email to a new label (creates label first)."""
    mock_labels = google_service_instance.gmail_service.users().labels()
    mock_messages = google_service_instance.gmail_service.users().messages()

    # Mock existing labels (target not found)
    mock_labels.list().execute.return_value = {'labels': [{'name': 'Existing', 'id': 'l1'}]}

    # Mock creation
    mock_labels.create().execute.return_value = {'id': 'new_label_id'}

    result = google_service_instance.move_to_label('msg_id', 'New Label')

    assert result['success'] is True

    # Verify creation
    mock_labels.create.assert_called()

    # Verify move
    mock_messages.modify.assert_called_with(
        userId='me', id='msg_id',
        body={'addLabelIds': ['new_label_id'], 'removeLabelIds': ['INBOX']}
    )
