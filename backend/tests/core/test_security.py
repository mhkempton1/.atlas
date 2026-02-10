import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
from core.security import verify_local_request

@pytest.mark.asyncio
async def test_verify_local_request_allowed():
    """Test that local IPs are allowed."""
    allowed_hosts = ["127.0.0.1", "::1", "localhost", "testclient"]

    for host in allowed_hosts:
        mock_request = MagicMock()
        mock_request.client.host = host

        # Should not raise exception
        result = await verify_local_request(mock_request)
        assert result is True

@pytest.mark.asyncio
async def test_verify_local_request_denied():
    """Test that remote IPs are denied."""
    denied_hosts = ["192.168.1.5", "10.0.0.1", "8.8.8.8"]

    for host in denied_hosts:
        mock_request = MagicMock()
        mock_request.client.host = host

        with pytest.raises(HTTPException) as exc_info:
            await verify_local_request(mock_request)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

@pytest.mark.asyncio
async def test_verify_local_request_no_client():
    """Test behavior when request.client is None."""
    mock_request = MagicMock()
    mock_request.client = None

    with pytest.raises(HTTPException) as exc_info:
        await verify_local_request(mock_request)

    assert exc_info.value.status_code == 403
