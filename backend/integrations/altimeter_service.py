import httpx
import logging
import asyncio
from typing import Optional, Dict, List, Any
from core.config import settings

logger = logging.getLogger(__name__)

class AltimeterIntegrationService:
    def __init__(self):
        self.base_url = settings.ALTIMETER_API_URL
        self.token = settings.ALTIMETER_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Any]:
        url = f"{self.base_url}{endpoint}"
        retries = 3
        backoff = 1

        async with httpx.AsyncClient() as client:
            for attempt in range(retries + 1):
                try:
                    response = await client.request(
                        method,
                        url,
                        headers=self.headers,
                        json=data,
                        params=params,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    return response.json()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.error(f"Altimeter API Error ({method} {url}): {str(e)}")
                    if attempt < retries:
                        sleep_time = backoff * (2 ** attempt)
                        logger.info(f"Retrying in {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error("Max retries reached. Altimeter request failed.")
                        return None
                except Exception as e:
                    logger.error(f"Unexpected error calling Altimeter ({method} {url}): {str(e)}")
                    return None
        return None

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project details."""
        return await self._request("GET", f"/projects/{project_id}")

    async def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get full project context for AI processing."""
        return await self._request("GET", f"/projects/{project_id}/context")

    async def get_customers(self) -> Optional[List[Dict[str, Any]]]:
        """List all customers."""
        return await self._request("GET", "/customers")

    async def get_vendors(self) -> Optional[List[Dict[str, Any]]]:
        """List all vendors."""
        return await self._request("GET", "/vendors")

    async def get_project_contacts(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get team members and contacts for a project."""
        return await self._request("GET", f"/projects/{project_id}/contacts")

    async def sync_task_to_altimeter(self, task_object: Any) -> Optional[Dict[str, Any]]:
        """
        Create or update a task in Altimeter.
        task_object: An instance of backend.database.models.Task or similar object.
        """
        payload = {
            "title": getattr(task_object, "title", ""),
            "description": getattr(task_object, "description", ""),
            "status": getattr(task_object, "status", "open"),
            "priority": getattr(task_object, "priority", "medium"),
            "due_date": task_object.due_date.isoformat() if getattr(task_object, "due_date", None) else None,
            "assigned_to": getattr(task_object, "assigned_to", None),
            "source": "Atlas",
            "atlas_task_id": getattr(task_object, "task_id", None)
        }

        altimeter_id = getattr(task_object, "related_altimeter_task_id", None)

        if altimeter_id:
            return await self._request("PUT", f"/tasks/{altimeter_id}", data=payload)
        else:
            return await self._request("POST", "/tasks", data=payload)

altimeter_integration_service = AltimeterIntegrationService()
