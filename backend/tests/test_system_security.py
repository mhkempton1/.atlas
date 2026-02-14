import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient

@pytest.fixture(scope="function")
def client():
    mock_mods = {
        "services.activity_service": MagicMock(),
        "services.altimeter_service": MagicMock(),
        "services.status_service": MagicMock(),
        "database": MagicMock(),
        "database.database": MagicMock()
    }
    # Setup mocks
    mock_mods["services.activity_service"].activity_service = MagicMock()
    mock_mods["services.altimeter_service"].altimeter_service = MagicMock()

    # Mock status service to return healthy
    async def mock_health():
        return {"status": "ok"}
    mock_mods["services.status_service"].get_health_status = mock_health

    # We use patch.dict to mock the modules for the duration of the test
    with patch.dict(sys.modules, mock_mods):
        # We need to reload/import router here to ensure it uses the mocks
        # But standard import caching might prevent reloading if it was already imported.
        # Since we run separate tests, and pytest might reuse modules...

        # To be safe, we rely on the fact that `api.system_routes` imports at top level are mocked.
        # AND the local imports inside functions will find the mocks in sys.modules because the patch is active.

        from api.system_routes import router

        app = FastAPI()
        app.include_router(router, prefix="/system")

        test_client = TestClient(app)
        yield test_client

def test_health_is_public(client):
    """
    /system/health should be accessible even from external IPs.
    """
    response = client.get("/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_control_is_protected(client):
    """
    /system/control/... should be protected (403 for external).
    """
    # By default, TestClient is local (allowed). We need to simulate external access.
    # We can override the dependency to force a failure, proving the route uses the dependency.
    from core.security import verify_local_request

    async def force_fail():
        raise HTTPException(status_code=403, detail="Access denied")

    client.app.dependency_overrides[verify_local_request] = force_fail

    response = client.post("/system/control/boot-silent")
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

    # Cleanup
    client.app.dependency_overrides = {}

def test_control_allowed_locally(client):
    """
    /system/control/... should be allowed for local requests.
    """
    # Mock subprocess to avoid actual execution
    with patch("subprocess.Popen") as mock_popen:
        response = client.post("/system/control/boot-silent")
        assert response.status_code == 200
        assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_verify_local_request_logic():
    """
    Unit test for the security logic.
    """
    mock_mods = {
        "services.activity_service": MagicMock(),
        "services.altimeter_service": MagicMock(),
        "services.status_service": MagicMock(),
        "database": MagicMock(),
        "database.database": MagicMock()
    }
    with patch.dict(sys.modules, mock_mods):
        from api.system_routes import verify_local_request
        from unittest.mock import Mock

        # Test Localhost IPv4
        req_local = Mock(spec=Request)
        req_local.client = Mock()
        req_local.client.host = "127.0.0.1"
        await verify_local_request(req_local) # Should pass

        # Test Localhost IPv6
        req_ipv6 = Mock(spec=Request)
        req_ipv6.client = Mock()
        req_ipv6.client.host = "::1"
        await verify_local_request(req_ipv6) # Should pass

        # Test External IP
        req_ext = Mock(spec=Request)
        req_ext.client = Mock()
        req_ext.client.host = "192.168.1.100"

        with pytest.raises(HTTPException) as exc:
            await verify_local_request(req_ext)
        assert exc.value.status_code == 403
