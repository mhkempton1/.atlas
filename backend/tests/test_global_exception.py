import pytest
from fastapi.testclient import TestClient
from core.app import app

# Set raise_server_exceptions=False to allow the exception handler to return a response
client = TestClient(app, raise_server_exceptions=False)

def test_global_exception_handler():
    # Add a temporary route to trigger an error
    @app.get("/test_error_route_for_verification")
    def trigger_error():
        raise ValueError("This is a test error")

    response = client.get("/test_error_route_for_verification")

    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "Internal Server Error"
    assert data["message"] == "This is a test error"
    assert "correlation_id" in data
    assert "timestamp" in data
