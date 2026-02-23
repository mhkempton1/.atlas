import pytest
from fastapi import HTTPException
from core.security import verify_local_request
from unittest.mock import patch
from core.app import app

def test_system_control_security_allowed(client):
    # Override dependency to simulate successful local check
    app.dependency_overrides[verify_local_request] = lambda: True

    with patch("subprocess.Popen") as mock_popen:
        # Test VBS script execution
        response = client.post("/api/v1/system/control/boot-silent")
        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Action boot-silent triggered"}

        # Verify call args
        args, kwargs = mock_popen.call_args
        assert args[0] == ['wscript.exe', r"C:\Users\mhkem\Desktop\START_SYSTEM_SILENT.vbs"]
        # Ensure shell=True is NOT used
        assert kwargs.get('shell') is not True, "shell=True should not be used"

        # Test Batch file execution
        response = client.post("/api/v1/system/control/boot-all")
        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Action boot-all triggered"}

        # Verify call args for batch file
        args, kwargs = mock_popen.call_args
        assert args[0] == ['cmd.exe', '/c', r"C:\Users\mhkem\Desktop\START_SYSTEM_ALL.bat"]
        assert kwargs.get('shell') is not True, "shell=True should not be used"

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
