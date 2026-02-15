import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from services.contact_unification_service import import_customers_from_altimeter, import_vendors_from_altimeter
from database.models import Contact

class TestContactUnificationService(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)

    @patch('services.contact_unification_service.altimeter_service')
    def test_import_customers_new(self, mock_altimeter_service):
        # Setup mock data
        mock_customers = [
            {
                "email": "cust@example.com",
                "company_name": "Test Company",
                "phone": "123-456-7890",
                "title": "Manager",
                "contact_name": "John Doe",
                "customer_id": 101
            }
        ]
        mock_altimeter_service.get_customers.return_value = mock_customers

        # Mock DB query to return empty list
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        stats = import_customers_from_altimeter(self.mock_db)

        # Verify
        self.assertEqual(stats["imported"], 1)
        self.assertEqual(stats["updated"], 0)
        self.assertEqual(stats["errors"], 0)

        # Check if db.add was called with correct object
        self.mock_db.add.assert_called_once()
        added_contact = self.mock_db.add.call_args[0][0]
        self.assertIsInstance(added_contact, Contact)
        self.assertEqual(added_contact.email_address, "cust@example.com")
        self.assertEqual(added_contact.relationship_type, "customer")
        self.assertEqual(added_contact.altimeter_customer_id, 101)

    @patch('services.contact_unification_service.altimeter_service')
    def test_import_customers_update(self, mock_altimeter_service):
        # Setup mock data
        mock_customers = [
            {
                "email": "existing@example.com",
                "company_name": "New Company Name",
                "phone": "987-654-3210",
                "customer_id": 102
            }
        ]
        mock_altimeter_service.get_customers.return_value = mock_customers

        # Mock DB query to return existing contact
        existing_contact = MagicMock(spec=Contact)
        existing_contact.email_address = "existing@example.com"
        existing_contact.company = "Old Company"
        existing_contact.phone = "000-000-0000"
        existing_contact.relationship_type = None

        # Mock .all() return value
        self.mock_db.query.return_value.filter.return_value.all.return_value = [existing_contact]

        # Execute
        stats = import_customers_from_altimeter(self.mock_db)

        # Verify
        self.assertEqual(stats["imported"], 0)
        self.assertEqual(stats["updated"], 1)

        self.assertEqual(existing_contact.company, "New Company Name")
        self.assertEqual(existing_contact.phone, "987-654-3210")
        self.assertEqual(existing_contact.altimeter_customer_id, 102)
        # Ensure relationship type is set
        self.assertEqual(existing_contact.relationship_type, "customer")

    @patch('services.contact_unification_service.altimeter_service')
    def test_import_vendors_new(self, mock_altimeter_service):
        mock_vendors = [
            {
                "email": "vendor@example.com",
                "company_name": "Vendor Inc",
                "vendor_id": 201
            }
        ]
        mock_altimeter_service.get_vendors.return_value = mock_vendors
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        stats = import_vendors_from_altimeter(self.mock_db)

        self.assertEqual(stats["imported"], 1)
        self.mock_db.add.assert_called_once()
        added_contact = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_contact.relationship_type, "vendor")
        self.assertEqual(added_contact.altimeter_vendor_id, 201)
