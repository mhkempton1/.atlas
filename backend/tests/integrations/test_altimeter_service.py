import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from integrations.altimeter_service import AltimeterIntegrationService, altimeter_integration_service
from core.config import settings
import httpx

@pytest.fixture
def mock_settings():
    original_url = settings.ALTIMETER_API_URL
    original_token = settings.ALTIMETER_API_TOKEN
    settings.ALTIMETER_API_URL = "http://test-altimeter.com"
    settings.ALTIMETER_API_TOKEN = "test-token"
    # Re-initialize service with new settings since __init__ reads them once
    global altimeter_integration_service
    altimeter_integration_service = AltimeterIntegrationService()
    yield settings
    settings.ALTIMETER_API_URL = original_url
    settings.ALTIMETER_API_TOKEN = original_token

@pytest.mark.asyncio
async def test_get_project_success(mock_settings):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "Test Project"}
        mock_request.return_value = mock_response

        result = await altimeter_integration_service.get_project("123")

        assert result == {"id": "123", "name": "Test Project"}
        mock_request.assert_called_with(
            "GET",
            "http://test-altimeter.com/projects/123",
            headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
            json=None,
            params=None,
            timeout=10.0
        )

@pytest.mark.asyncio
async def test_get_customers_success(mock_settings):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Customer A"}]
        mock_request.return_value = mock_response

        result = await altimeter_integration_service.get_customers()

        assert result == [{"id": 1, "name": "Customer A"}]
        mock_request.assert_called_with(
            "GET",
            "http://test-altimeter.com/customers",
            headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
            json=None,
            params=None,
            timeout=10.0
        )

@pytest.mark.asyncio
async def test_retry_logic(mock_settings):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}

        # mock_request.side_effect = [
        #     httpx.RequestError("Connection failed", request=MagicMock()),
        #     httpx.RequestError("Connection failed", request=MagicMock()),
        #     httpx.RequestError("Connection failed", request=MagicMock()),
        #     mock_response_success
        # ]
        # The above logic is slightly flawed because httpx.RequestError needs to be raised, not returned if we set side_effect on the coro result.
        # But since we are mocking request() which returns a Coroutine, setting side_effect on the mock itself works if it's an AsyncMock?
        # AsyncMock side_effect iterates. If item is Exception, it raises it.

        mock_request.side_effect = [
            httpx.RequestError("Connection failed 1", request=MagicMock()),
            httpx.RequestError("Connection failed 2", request=MagicMock()),
            httpx.RequestError("Connection failed 3", request=MagicMock()),
            mock_response_success
        ]

        # Patch asyncio.sleep to speed up tests
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await altimeter_integration_service._request("GET", "/test")

            assert result == {"success": True}
            assert mock_request.call_count == 4
            assert mock_sleep.call_count == 3
            # Check backoff times: 1, 2, 4
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)
            mock_sleep.assert_any_call(4)

@pytest.mark.asyncio
async def test_failure_after_retries(mock_settings):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = httpx.RequestError("Connection failed", request=MagicMock())

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await altimeter_integration_service._request("GET", "/test")

            assert result is None
            assert mock_request.call_count == 4 # Initial + 3 retries

@pytest.mark.asyncio
async def test_sync_task_create(mock_settings):
    task = MagicMock()
    task.title = "New Task"
    task.description = "Desc"
    task.status = "open"
    task.priority = "high"
    task.due_date = MagicMock()
    task.due_date.isoformat.return_value = "2023-01-01"
    task.assigned_to = "user@example.com"
    task.task_id = 101
    task.related_altimeter_task_id = None

    with patch("integrations.altimeter_service.AltimeterIntegrationService._request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": "alt-123"}

        result = await altimeter_integration_service.sync_task_to_altimeter(task)

        assert result == {"id": "alt-123"}
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == "/tasks"
        assert kwargs['data']['title'] == "New Task"

@pytest.mark.asyncio
async def test_sync_task_update(mock_settings):
    task = MagicMock()
    task.title = "Update Task"
    task.related_altimeter_task_id = "alt-999"
    task.due_date = None # Handle None date

    with patch("integrations.altimeter_service.AltimeterIntegrationService._request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": "alt-999"}

        result = await altimeter_integration_service.sync_task_to_altimeter(task)

        assert result == {"id": "alt-999"}
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "PUT"
        assert args[1] == "/tasks/alt-999"
        assert kwargs['data']['title'] == "Update Task"
        assert kwargs['data']['due_date'] is None
