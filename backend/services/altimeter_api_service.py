# backend/services/altimeter_api_service.py
import aiohttp
import logging
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger("altimeter_api")

class AltimeterAPIService:
    """
    Real HTTP client for Altimeter construction management API.
    """
    def __init__(self):
        self.base_url = getattr(settings, "ALTIMETER_API_URL", "https://api.altimeter.com/v1")
        self.api_key = getattr(settings, "ALTIMETER_API_KEY", "")

        if not self.api_key:
            logger.warning("ALTIMETER_API_KEY not configured. API calls will fail.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in Altimeter."""
        url = f"{self.base_url}/tasks"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=task_data, headers=self._headers(), timeout=10) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        logger.info(f"Created Altimeter task: {result.get('id')}")
                        return result
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        raise Exception(f"Altimeter API returned {resp.status}: {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error creating task: {e}")
                raise

    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task in Altimeter."""
        url = f"{self.base_url}/tasks/{task_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(url, json=task_data, headers=self._headers(), timeout=10) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(f"Updated Altimeter task: {task_id}")
                        return result
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        raise Exception(f"Altimeter API returned {resp.status}: {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error updating task: {e}")
                raise

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a task from Altimeter by ID."""
        url = f"{self.base_url}/tasks/{task_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self._headers(), timeout=10) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    elif resp.status == 404:
                        logger.warning(f"Task {task_id} not found in Altimeter")
                        return None
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        raise Exception(f"Altimeter API returned {resp.status}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error fetching task: {e}")
                raise

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task in Altimeter."""
        url = f"{self.base_url}/tasks/{task_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.delete(url, headers=self._headers(), timeout=10) as resp:
                    if resp.status in [200, 204]:
                        logger.info(f"Deleted Altimeter task: {task_id}")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        return False
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error deleting task: {e}")
                return False

# Singleton instance
altimeter_api_service = AltimeterAPIService()
