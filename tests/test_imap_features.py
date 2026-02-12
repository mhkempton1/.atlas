import sys
import os
import unittest
from unittest.mock import MagicMock, patch, ANY
import email

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.imap_provider import IMAPProvider
from services.smtp_provider import SMTPProvider
from core.config import settings

class TestIMAPFeatures(unittest.TestCase):

    def setUp(self):
        # Ensure settings are mocked or set
        settings.IMAP_HOST = "imap.test.com"
        settings.IMAP_USER = "user@test.com"
        settings.IMAP_PASSWORD = "password"
        settings.SMTP_HOST = "smtp.test.com"
        settings.SMTP_USER = "user@test.com"
        settings.SMTP_PASSWORD = "password"

    @patch('imaplib.IMAP4_SSL')
    def test_get_labels(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap

        # Mock LIST response
        # Standard format: (Flags) "Delimiter" "Name"
        # Example: (\HasNoChildren) "/" "INBOX"
        mock_imap.list.return_value = ('OK', [
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "Trash"',
            b'(\\HasChildren) "/" "Work/Project"',
        ])

        provider = IMAPProvider()
        labels = provider.get_labels()

        self.assertEqual(len(labels), 3)
        self.assertEqual(labels[0]['name'], 'INBOX')
        self.assertEqual(labels[1]['name'], 'Trash')
        self.assertEqual(labels[2]['name'], 'Work/Project')

    @patch('imaplib.IMAP4_SSL')
    def test_mark_unread(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap

        provider = IMAPProvider()
        result = provider.mark_unread("123")

        self.assertTrue(result['success'])
        mock_imap.select.assert_called_with("INBOX")
        mock_imap.uid.assert_called_with('STORE', '123', '-FLAGS', '(\\Seen)')

    @patch('imaplib.IMAP4_SSL')
    def test_move_to_label(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap
        mock_imap.uid.return_value = ('OK', [b'Success']) # For COPY

        provider = IMAPProvider()
        result = provider.move_to_label("123", "Archive")

        self.assertTrue(result['success'])
        # Verify COPY
        mock_imap.uid.assert_any_call('COPY', '123', 'Archive')
        # Verify STORE \Deleted
        mock_imap.uid.assert_any_call('STORE', '123', '+FLAGS', '(\\Deleted)')
        # Verify EXPUNGE
        mock_imap.expunge.assert_called()

    @patch('services.smtp_provider.smtplib.SMTP')
    @patch('imaplib.IMAP4_SSL')
    def test_reply_to_email(self, mock_imap_cls, mock_smtp_cls):
        # Mock IMAP to return original email
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap

        raw_email = (
            b"From: sender@example.com\r\n"
            b"To: me@example.com\r\n"
            b"Subject: Original Subject\r\n"
            b"Message-ID: <orig-msg-id>\r\n"
            b"Date: Wed, 25 Dec 2024 10:00:00 -0000\r\n"
            b"\r\n"
            b"Original Body Text"
        )

        # mock FETCH response for _get_original_email
        mock_imap.uid.return_value = ('OK', [(b'1 (RFC822 {100}', raw_email), b')'])

        # Mock SMTP
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp

        smtp_provider = SMTPProvider()
        provider = IMAPProvider(sender=smtp_provider)

        result = provider.reply_to_email("123", "My Reply Body")

        self.assertTrue(result['success'])

        # Verify SMTP send_message called
        mock_smtp.send_message.assert_called()
        args, kwargs = mock_smtp.send_message.call_args
        msg = args[0]

        self.assertEqual(msg['Subject'], "Re: Original Subject")
        self.assertEqual(msg['To'], "sender@example.com")
        self.assertEqual(msg['In-Reply-To'], "<orig-msg-id>")
        self.assertIn("<orig-msg-id>", msg['References'])

        # Helper to get text content from MIME
        def get_text(msg):
            if msg.is_multipart():
                return get_text(msg.get_payload()[0])
            return msg.get_payload()

        body_content = get_text(msg)
        self.assertIn("My Reply Body", body_content)
        self.assertIn("> Original Body Text", body_content)

    @patch('services.smtp_provider.smtplib.SMTP')
    @patch('imaplib.IMAP4_SSL')
    def test_forward_email(self, mock_imap_cls, mock_smtp_cls):
        # Mock IMAP
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap

        raw_email = (
            b"From: sender@example.com\r\n"
            b"Subject: Important Info\r\n"
            b"Date: Wed, 25 Dec 2024 10:00:00 -0000\r\n"
            b"\r\n"
            b"Secret Info"
        )
        mock_imap.uid.return_value = ('OK', [(b'1 (RFC822 {100}', raw_email), b')'])

        # Mock SMTP
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp

        smtp_provider = SMTPProvider()
        provider = IMAPProvider(sender=smtp_provider)
        result = provider.forward_email("123", "new@example.com", "FYI")

        self.assertTrue(result['success'])

        mock_smtp.send_message.assert_called()
        args, kwargs = mock_smtp.send_message.call_args
        msg = args[0]

        self.assertEqual(msg['Subject'], "Fwd: Important Info")
        self.assertEqual(msg['To'], "new@example.com")

        def get_text(msg):
            if msg.is_multipart():
                return get_text(msg.get_payload()[0])
            return msg.get_payload()

        body_content = get_text(msg)
        self.assertIn("FYI", body_content)
        self.assertIn("---------- Forwarded message ----------", body_content)
        self.assertIn("Secret Info", body_content)

if __name__ == '__main__':
    unittest.main()
