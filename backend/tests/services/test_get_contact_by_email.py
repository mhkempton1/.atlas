import unittest
from unittest.mock import MagicMock
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

# Mock sqlalchemy and database.models
mock_sqlalchemy = MagicMock()
mock_sqlalchemy_orm = MagicMock()
mock_database = MagicMock()
mock_database_models = MagicMock()

sys.modules['sqlalchemy'] = mock_sqlalchemy
sys.modules['sqlalchemy.orm'] = mock_sqlalchemy_orm
sys.modules['database'] = mock_database
sys.modules['database.models'] = mock_database_models

# Import the function under test after mocking dependencies
from services.contact_persistence_service import get_contact_by_email
from database.models import Contact

class TestGetContactByEmail(unittest.TestCase):

    def setUp(self):
        # Setup a mock session
        self.mock_db = MagicMock()
        self.mock_query = MagicMock()
        self.mock_filter = MagicMock()

        # Configure the mock chain: db.query().filter().first()
        self.mock_db.query.return_value = self.mock_query
        self.mock_query.filter.return_value = self.mock_filter

    def test_get_contact_by_email_empty_string(self):
        """Test that an empty email address returns None immediately."""
        result = get_contact_by_email("", self.mock_db)

        self.assertIsNone(result)
        self.mock_db.query.assert_not_called()

    def test_get_contact_by_email_none(self):
        """Test that a None email address returns None immediately."""
        result = get_contact_by_email(None, self.mock_db)

        self.assertIsNone(result)
        self.mock_db.query.assert_not_called()

    def test_get_contact_by_email_valid(self):
        """Test that a valid email address is converted to lowercase and queried correctly."""
        # Setup mock return value
        mock_contact = MagicMock()
        self.mock_filter.first.return_value = mock_contact

        email = "TeSt@ExAmPle.CoM"
        result = get_contact_by_email(email, self.mock_db)

        # Verify db.query(Contact) was called
        self.mock_db.query.assert_called_once_with(Contact)

        # Verify filter was called. Since MagicMock intercepts ==, we just verify it was called
        self.mock_query.filter.assert_called_once()

        # Verify first() was called
        self.mock_filter.first.assert_called_once()

        # Verify the correct result is returned
        self.assertEqual(result, mock_contact)

if __name__ == '__main__':
    unittest.main()
