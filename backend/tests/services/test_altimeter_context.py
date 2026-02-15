import pytest
from unittest.mock import MagicMock, patch
from services.altimeter_service import AltimeterService
import time

@pytest.fixture
def altimeter_service():
    return AltimeterService()

def test_load_project_context_success(altimeter_service):
    """Test successful API call and caching."""
    project_id = "25-0001"
    mock_data = {
        "name": "Test Project",
        "customer": "Test Customer",
        "status": "Active"
    }

    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value.__enter__.return_value
        mock_instance.get.return_value.status_code = 200
        mock_instance.get.return_value.json.return_value = mock_data

        # First call: Should hit API
        result = altimeter_service.load_project_context(project_id)

        assert result == mock_data
        assert project_id in altimeter_service.project_context_cache
        mock_instance.get.assert_called_once()

        # Second call: Should use cache
        mock_instance.get.reset_mock()
        result_cached = altimeter_service.load_project_context(project_id)
        assert result_cached == mock_data
        mock_instance.get.assert_not_called()

def test_load_project_context_api_error(altimeter_service):
    """Test API error handling."""
    project_id = "25-0002"

    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value.__enter__.return_value
        mock_instance.get.return_value.status_code = 500
        mock_instance.get.return_value.text = "Internal Server Error"

        result = altimeter_service.load_project_context(project_id)

        assert result is None
        assert project_id not in altimeter_service.project_context_cache

def test_load_project_context_expired_cache(altimeter_service):
    """Test that expired cache triggers new API call."""
    project_id = "25-0003"
    mock_data_old = {"name": "Old Name"}
    mock_data_new = {"name": "New Name"}

    # Manually populate cache with old timestamp
    altimeter_service.project_context_cache[project_id] = {
        "timestamp": time.time() - 7201, # Expired (2 hours + 1 second)
        "data": mock_data_old
    }

    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value.__enter__.return_value
        mock_instance.get.return_value.status_code = 200
        mock_instance.get.return_value.json.return_value = mock_data_new

        result = altimeter_service.load_project_context(project_id)

        assert result == mock_data_new
        assert altimeter_service.project_context_cache[project_id]["data"] == mock_data_new
        mock_instance.get.assert_called_once()

def test_load_project_context_connection_error(altimeter_service):
    """Test connection error handling."""
    project_id = "25-0004"

    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value.__enter__.return_value
        mock_instance.get.side_effect = Exception("Connection refused")

        result = altimeter_service.load_project_context(project_id)

        assert result is None
