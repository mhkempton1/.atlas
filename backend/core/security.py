from fastapi import HTTPException, Request, status
from typing import List

async def verify_local_request(request: Request):
    """
    Verifies that the request originates from localhost.
    Raises 403 Forbidden if the request is remote.
    """
    # Allow testclient for testing
    allowed_hosts: List[str] = ["127.0.0.1", "::1", "localhost", "testclient"]

    client_host = request.client.host if request.client else None

    if client_host not in allowed_hosts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Remote access to this endpoint is restricted."
        )
    return True
