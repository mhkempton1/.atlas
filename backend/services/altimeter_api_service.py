import httpx
from typing import Dict, Any, Optional
from core.config import settings

class AltimeterAPIService:
    """
    Service for HTTP communication with Altimeter API.
    """
    def __init__(self):
        self.base_url = settings.ALTIMETER_API_URL.rstrip("/")
        self.api_key = getattr(settings, "ALTIMETER_API_KEY", "")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    async def check_health(self) -> bool:
        """Check if Altimeter API is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/health", headers=self.headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task in Altimeter."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/tasks",
                json=task_data,
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def update_task(self, remote_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task in Altimeter."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(
                f"{self.base_url}/tasks/{remote_id}",
                json=task_data,
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_task(self, remote_id: str) -> bool:
        """Delete a task in Altimeter."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                f"{self.base_url}/tasks/{remote_id}",
                headers=self.headers
            )
            if resp.status_code == 404:
                return True # Already deleted
            resp.raise_for_status()
            return True

    async def get_task(self, remote_id: str) -> Optional[Dict[str, Any]]:
        """Get a task from Altimeter."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/tasks/{remote_id}",
                    headers=self.headers
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return None

altimeter_api_service = AltimeterAPIService()
