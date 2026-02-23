import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock imports that might cause issues if dependencies aren't perfect
sys.modules['services.contact_persistence_service'] = MagicMock()
sys.modules['services.embedding_service'] = MagicMock()

from services.email_persistence_service import persist_email_to_database, clean_html
from database.models import Email

class TestEmailSanitization(unittest.TestCase):
    def test_clean_html_removes_scripts(self):
        malicious_html = '<script>alert("xss")</script><p>Hello</p>'
        cleaned = clean_html(malicious_html)
        self.assertNotIn('<script>', cleaned)
        self.assertIn('<p>Hello</p>', cleaned)
        # bleach escapes script content usually, let's just check script tag is gone or escaped
        self.assertTrue('&lt;script&gt;' in cleaned or 'script' not in cleaned)

    def test_clean_html_allows_safe_tags(self):
        safe_html = '<div class="content"><a href="http://example.com">Link</a></div>'
        cleaned = clean_html(safe_html)
        self.assertEqual(cleaned, safe_html)

    @patch('services.email_persistence_service.Email')
    @patch('services.email_persistence_service.datetime')
    def test_persist_email_sanitizes_body(self, mock_datetime, mock_email_cls):
        mock_db = MagicMock()
        # Mock query return None to trigger creation
        mock_db.query.return_value.filter.return_value.first.return_value = None

        email_data = {
            'subject': 'Test',
            'from_address': 'test@example.com',
            'body_html': '<img src=x onerror=alert(1)>'
        }

        # Mock Email instance
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance
        # Set email_id for return
        mock_email_instance.email_id = 1

        result = persist_email_to_database(email_data, mock_db)

        self.assertTrue(result['success'])
        # Verify body_html was sanitized
        sanitized_body = mock_email_instance.body_html
        print(f"Sanitized body: {sanitized_body}")
        self.assertNotIn('onerror', sanitized_body)
        self.assertIn('<img', sanitized_body)

if __name__ == '__main__':
    unittest.main()
