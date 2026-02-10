import pytest
from fastapi import HTTPException
from core.security import verify_local_request
from unittest.mock import patch
from core.app import app

def test_system_control_security_allowed(client):
    # Override dependency to simulate successful local check
    app.dependency_overrides[verify_local_request] = lambda: True

    with patch("subprocess.Popen") as mock_popen:
        response = client.post("/api/v1/system/control/boot-silent")
        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Action boot-silent triggered"}

    app.dependency_overrides.clear()

def test_system_control_security_denied(client):
    # Override dependency to simulate failure (remote request)
    def mock_verify_denied():
        raise HTTPException(status_code=403, detail="Access denied")

    app.dependency_overrides[verify_local_request] = mock_verify_denied

    response = client.post("/api/v1/system/control/boot-silent")
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

    app.dependency_overrides.clear()
