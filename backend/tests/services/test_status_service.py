import pytest
from unittest.mock import patch, MagicMock
from services.status_service import get_health_status
import services.status_service as status_module
import time

@pytest.fixture
def mock_dependencies():
    with patch("services.scheduler_service.scheduler_service") as mock_scheduler, \
         patch("services.altimeter_service.altimeter_service") as mock_altimeter, \
         patch("services.notification_service.notification_service") as mock_notif, \
         patch("services.status_service.SessionLocal") as mock_session_local:

        # Mock SessionLocal to raise error (simulate DB down) to cause degradation
        mock_session_local.side_effect = Exception("DB Down")

        # Mock Altimeter to be healthy so we only fail on DB
        mock_altimeter.check_health.return_value = {"status": "connected"}

        # Mock Scheduler to be healthy
        async def mock_health():
            return {"status": "online", "services": {"s1": "Online"}}
        mock_scheduler.get_system_health.side_effect = mock_health

        yield mock_notif

@pytest.mark.asyncio
async def test_health_notification_rate_limit(mock_dependencies):
    mock_notif = mock_dependencies

    # Reset the global variable for testing
    status_module._last_degradation_notification_time = 0

    # First call: Should be degraded (DB down) and push notification
    status = await get_health_status()
    assert status["status"] == "degraded"
    mock_notif.push_notification.assert_called_once()

    # Reset mock to check next call
    mock_notif.push_notification.reset_mock()

    # Second call immediately: Should be degraded but NO notification
    status = await get_health_status()
    assert status["status"] == "degraded"
    mock_notif.push_notification.assert_not_called()

@pytest.mark.asyncio
async def test_health_notification_rate_limit_expiry(mock_dependencies):
    mock_notif = mock_dependencies
    status_module._last_degradation_notification_time = 0

    # 1. Trigger notification
    await get_health_status()
    mock_notif.push_notification.assert_called_once()
    mock_notif.push_notification.reset_mock()

    # 2. Simulate 6 minutes passing
    current_time = time.time()
    future_time = current_time + 360

    # Patch time.time to return future_time
    with patch("services.status_service.time.time", return_value=future_time):
        await get_health_status()
        mock_notif.push_notification.assert_called_once()
