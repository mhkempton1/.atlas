import sys
import os
import unittest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.altimeter_service import AltimeterService
from services.smtp_provider import SMTPProvider
from services.imap_provider import IMAPProvider

class TestEmailIntegration(unittest.TestCase):

    @patch('services.altimeter_service.AltimeterService.get_project_details')
    @patch('services.altimeter_service.AltimeterService._get_contact_info')
    @patch('services.altimeter_service.AltimeterService.get_active_phases')
    def test_altimeter_milestones(self, mock_phases, mock_contact, mock_project):
        mock_project.return_value = None
        mock_contact.return_value = None
        mock_phases.return_value = []

        service = AltimeterService()
        # Changed "Submit" to "Due" to match regex keywords
        context = service.get_context_for_email("test@example.com", "Subject", "Due by 12/25/2024 please.")
        milestones = context.get('suggested_milestones', [])
        self.assertTrue(len(milestones) > 0)
        self.assertEqual(milestones[0]['date_text'], '12/25/2024')

    @patch('services.smtp_provider.settings')
    @patch('smtplib.SMTP')
    def test_smtp_send(self, mock_smtp, mock_settings):
        # Configure settings mock
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        provider = SMTPProvider()
        # Mock connection
        server_mock = MagicMock()
        mock_smtp.return_value = server_mock

        provider.send_email(
            recipient="to@example.com",
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"]
        )

        # Verify login called
        server_mock.login.assert_called()

        # Verify send_message called with recipients
        args, kwargs = server_mock.send_message.call_args
        msg = args[0]
        recipients = kwargs.get('to_addrs')

        self.assertEqual(msg['To'], "to@example.com")
        self.assertEqual(msg['Cc'], "cc@example.com")
        self.assertIsNone(msg['Bcc']) # Bcc header should not be in msg

        # Recipients list should contain all
        self.assertIn("to@example.com", recipients)
        self.assertIn("cc@example.com", recipients)
        self.assertIn("bcc@example.com", recipients)

    @patch('services.imap_provider.settings')
    @patch('imaplib.IMAP4_SSL')
    @patch('services.imap_provider.SessionLocal')
    @patch('services.altimeter_service.altimeter_service')
    def test_imap_sync(self, mock_altimeter, mock_session, mock_imap, mock_settings):
        # Configure settings mock
        mock_settings.IMAP_HOST = "imap.example.com"
        mock_settings.IMAP_PORT = 993
        mock_settings.IMAP_USER = "user"
        mock_settings.IMAP_PASSWORD = "pass"

        provider = IMAPProvider()

        # Mock IMAP connection
        mail_mock = MagicMock()
        mock_imap.return_value = mail_mock

        # Mock Search
        mail_mock.uid.return_value = ('OK', [b'1 2'])

        # Mock DB
        db_mock = MagicMock()
        mock_session.return_value = db_mock
        # Mock query first() to return None (not exists)
        db_mock.query.return_value.filter.return_value.first.return_value = None

        # Mock Fetch
        # Return RFC822 content
        raw_email = b"From: sender@example.com\r\nSubject: Test\r\nMessage-ID: <123>\r\nDate: Wed, 25 Dec 2024 10:00:00 -0000\r\n\r\nHello"
        mail_mock.uid.side_effect = [
            ('OK', [b'1 2']), # search result
            ('OK', [(b'1 (RFC822 {50}', raw_email), b')']), # fetch 1
            ('OK', [(b'2 (RFC822 {50}', raw_email), b')'])  # fetch 2
        ]

        # Mock Altimeter
        mock_altimeter.get_context_for_email.return_value = {}

        result = provider.sync_emails()

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['synced'], 2)

        # Verify DB add called
        self.assertTrue(db_mock.add.called)

class TestIMAPProviderMethods(unittest.TestCase):
    @patch('services.imap_provider.imaplib.IMAP4_SSL')
    @patch('services.smtp_provider.SMTPProvider') # Patch the source class
    def test_reply_to_email(self, MockSMTPProvider, mock_imap):
        # Mock IMAP connection
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        # Mock fetch response
        mock_mail.uid.return_value = ('OK', [(b'123 (RFC822 {100})', b'Message-ID: <original@test.com>\r\nReferences: <ref1@test.com>\r\nSubject: Original Subject\r\nFrom: sender@test.com\r\n\r\nBody')])

        # Mock SMTP Provider instance
        mock_smtp_instance = MockSMTPProvider.return_value
        mock_smtp_instance.send_email.return_value = {"success": True}

        provider = IMAPProvider()
        # Ensure provider has connection (mocked) logic or bypass _connect if needed
        # _connect creates IMAP4_SSL, which is mocked

        # Test reply
        result = provider.reply_to_email("123", "Reply Body")

        # Verify
        self.assertTrue(result['success'])

        # Check if SMTPProvider.send_email was called
        mock_smtp_instance.send_email.assert_called_once()
        args, kwargs = mock_smtp_instance.send_email.call_args

        self.assertEqual(args[0], 'sender@test.com')
        self.assertEqual(args[1], 'Re: Original Subject')

        extra_headers = kwargs.get('extra_headers')
        self.assertIsNotNone(extra_headers)
        self.assertEqual(extra_headers['In-Reply-To'], '<original@test.com>')
        self.assertEqual(extra_headers['References'], '<ref1@test.com> <original@test.com>')

    @patch('services.imap_provider.imaplib.IMAP4_SSL')
    def test_trash_email(self, mock_imap):
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail

        # Mock folder list
        mock_mail.list.return_value = ('OK', [b'(\\HasNoChildren) "/" "Trash"'])

        provider = IMAPProvider()
        result = provider.trash_email("123")

        self.assertTrue(result['success'])
        # Check copy to Trash and flag Deleted
        mock_mail.uid.assert_any_call('copy', '123', 'Trash')
        mock_mail.uid.assert_any_call('store', '123', '+FLAGS', r'(\Deleted)')

class TestSMTPProviderExtra(unittest.TestCase):
    @patch('services.smtp_provider.smtplib.SMTP')
    def test_send_email_extra_headers(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        provider = SMTPProvider()
        provider.user = "user@test.com"
        provider.host = "smtp.test.com"

        extra_headers = {"X-Custom": "Value", "In-Reply-To": "<msgid>"}
        result = provider.send_email("to@test.com", "Subj", "Body", extra_headers=extra_headers)

        self.assertTrue(result['success'])
        mock_server.send_message.assert_called_once()
        args, _ = mock_server.send_message.call_args
        msg = args[0]

        self.assertEqual(msg['X-Custom'], 'Value')
        self.assertEqual(msg['In-Reply-To'], '<msgid>')

if __name__ == '__main__':
    unittest.main()
