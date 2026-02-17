import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Mock modules that might be missing or troublesome
search_service_module_mock = MagicMock()
# The code does: from services.search_service import search_service
# So the module mock must have a 'search_service' attribute.
search_service_instance_mock = MagicMock()
search_service_module_mock.search_service = search_service_instance_mock
sys.modules['services.search_service'] = search_service_module_mock

sys.modules['services.altimeter_service'] = MagicMock()
sys.modules['services.document_control_service'] = MagicMock()
sys.modules['services.google_service'] = MagicMock()
# database.database is used inside functions, so we might not need to mock it if we don't call those functions
# But if it was imported at top level we would need to mock it.
# It is imported inside sync_emails_job, which is not called at import time.

from services.scheduler_service import scheduler_service

@pytest.mark.asyncio
async def test_get_system_health_optimization():
    # Setup mocks
    search_service_instance_mock._ensure_initialized.return_value = True

    # We need to verify httpx usage.
    with patch('services.scheduler_service.httpx.AsyncClient') as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        # Run
        health = await scheduler_service.get_system_health()

        # Check result
        assert health['status'] == 'online'
        assert health['services']['altimeter'] == 'Online'

        # Verify it used httpx
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert "https://api.altimeter.com/v1/api/system/health" in args[0]
        assert kwargs.get('timeout') == 1

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_get_system_health_optimization())
