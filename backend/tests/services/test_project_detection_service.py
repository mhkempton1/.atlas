import pytest
from unittest.mock import MagicMock, patch
import json
from services.project_detection_service import ProjectDetectionService
from services.email_persistence_service import persist_email_to_database
from database.models import Email

class TestProjectDetectionService:
    @pytest.fixture
    def service(self):
        return ProjectDetectionService()

    @pytest.fixture
    def mock_altimeter(self):
        mock = MagicMock()
        mock.get_project_details.side_effect = lambda pid: {
            "name": f"Project {pid}",
            "status": "Active"
        } if pid in ["25-0308", "25-0309"] else None
        return mock

    def test_detect_project_number_basic(self, service):
        text = "Please review 25-0308 regarding the foundation."
        assert service.detect_project_number_in_email(text) == ["25-0308"]

    def test_detect_project_number_variations(self, service):
        # 25-0308, 25 0309, 250310, Project 25-0311
        text = """
        Here are the project numbers:
        25-0308
        25 0309
        250310
        Project 25-0311
        """
        detected = service.detect_project_number_in_email(text)
        expected = ["25-0308", "25-0309", "25-0310", "25-0311"]
        assert sorted(detected) == sorted(expected)

    def test_detect_project_number_deduplication(self, service):
        text = "25-0308 and 25 0308 and 250308"
        assert service.detect_project_number_in_email(text) == ["25-0308"]

    def test_detect_project_number_no_match(self, service):
        text = "Call me at 555-0199 regarding year 2024."
        assert service.detect_project_number_in_email(text) == []

    def test_match_detected_projects_to_altimeter(self, service, mock_altimeter):
        project_numbers = ["25-0308", "25-0309", "25-9999"]
        matches = service.match_detected_projects_to_altimeter(project_numbers, mock_altimeter)

        assert len(matches) == 2
        match_numbers = [m["number"] for m in matches]
        assert "25-0308" in match_numbers
        assert "25-0309" in match_numbers
        assert "25-9999" not in match_numbers
        assert matches[0]["confidence"] == 1.0

    @patch("services.email_persistence_service.project_detection_service")
    @patch("services.email_persistence_service.altimeter_service")
    def test_persist_email_integration_single_project(self, mock_altimeter, mock_project_detection, db):
        # Setup mocks
        mock_project_detection.detect_project_number_in_email.return_value = ["25-0308"]
        mock_project_detection.match_detected_projects_to_altimeter.return_value = [{
            "number": "25-0308",
            "name": "Test Project",
            "status": "Active",
            "confidence": 1.0
        }]

        email_data = {
            "gmail_id": "g_proj_1",
            "subject": "Project 25-0308 Update",
            "body_text": "Please review.",
            "sender": "sender@test.com"
        }

        # Run persistence
        persist_email_to_database(email_data, db)

        # Verify
        email = db.query(Email).filter(Email.gmail_id == "g_proj_1").first()
        assert email.project_id == "25-0308"
        # Ensure labels are handled correctly (None or empty)
        assert not email.labels or "Multiple Projects Detected" not in email.labels

    @patch("services.email_persistence_service.project_detection_service")
    @patch("services.email_persistence_service.altimeter_service")
    def test_persist_email_integration_multiple_projects(self, mock_altimeter, mock_project_detection, db):
        # Setup mocks
        mock_project_detection.detect_project_number_in_email.return_value = ["25-0308", "25-0309"]
        mock_project_detection.match_detected_projects_to_altimeter.return_value = [
            {"number": "25-0308", "name": "P1", "status": "Active", "confidence": 1.0},
            {"number": "25-0309", "name": "P2", "status": "Active", "confidence": 1.0}
        ]

        email_data = {
            "gmail_id": "g_proj_multi",
            "subject": "Multiple Projects",
            "body_text": "25-0308 and 25-0309",
            "sender": "sender@test.com"
        }

        # Run persistence
        persist_email_to_database(email_data, db)

        # Verify
        email = db.query(Email).filter(Email.gmail_id == "g_proj_multi").first()
        assert email.project_id == "25-0308" # First one
        assert "Multiple Projects Detected" in email.labels
