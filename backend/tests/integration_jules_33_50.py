import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.urgency_service import urgency_service
from services.contact_service import contact_service
from services.date_parsing_service import date_parsing_service
from services.recurring_task_service import recurring_task_service
from services.notification_service import notification_service

class JulesIntegrationTests(unittest.IsolatedAsyncioTestCase):
    
    def test_urgency_scoring(self):
        """Verify keyword-based urgency scoring."""
        email_data = {
            "subject": "URGENT: Site Safety Violation",
            "body": "Please respond ASAP regarding the safety issue.",
            "date_received": "2026-02-15T23:30:00", # Late night
            "sentiment": "negative"
        }
        score = urgency_service.calculate_urgency(email_data)
        self.assertGreater(score, 70)
        print(f"✓ Urgency Test Passed: Score {score}")

    def test_date_parsing(self):
        """Verify relative date extraction."""
        text = "This needs to be done by Friday."
        # Friday depends on when test is run, but we check if it returns a date string
        deadline = date_parsing_service.parse_deadline_from_text(text)
        self.assertIsNotNone(deadline)
        self.assertTrue(len(deadline) == 10) # YYYY-MM-DD
        print(f"✓ Date Parsing Test Passed: {deadline}")

    def test_recurring_recognition(self):
        """Verify recurrence pattern detection."""
        patterns = {
            "Send weekly report": "weekly",
            "Check daily logs": "daily",
            "Every Monday meeting": "weekly:monday"
        }
        for text, expected in patterns.items():
            pattern = recurring_task_service.detect_pattern(text)
            self.assertEqual(pattern, expected)
        print("✓ Recurring Task Test Passed")

    def test_vip_ranking(self):
        """Verify contact importance logic."""
        mock_contact = MagicMock()
        mock_contact.role = "President"
        mock_contact.email_count = 50
        mock_contact.last_contact_date = None
        
        score = contact_service.calculate_importance(mock_contact, MagicMock())
        self.assertGreater(score, 50)
        print(f"✓ VIP Ranking Test Passed: Score {score}")

    def test_smart_notifications(self):
        """Verify notification rules."""
        data = {
            "subject": "Immediate Action Required",
            "urgency_score": 90,
            "sentiment_label": "Frustrated"
        }
        # Mock push_notification to avoid DB insert in unit test
        with patch.object(notification_service, 'push_notification') as mock_push:
            notification_service.push_smart_notification(data)
            mock_push.assert_called_once()
            _, kwargs = mock_push.call_args
            self.assertEqual(kwargs.get("priority"), "critical")
        print("✓ Smart Notification Test Passed")

if __name__ == "__main__":
    unittest.main()
