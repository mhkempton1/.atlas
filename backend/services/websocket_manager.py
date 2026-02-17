# backend/services/websocket_manager.py
from fastapi import WebSocket
from typing import List, Dict, Any
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger("websocket_manager")

class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts sync status updates to connected clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_sync_status(self, entity_type: str, entity_id: int, status: str):
        """
        Broadcast sync status to all connected clients.

        Args:
            entity_type: Type of entity ('task', 'email', etc.)
            entity_id: Database ID of the entity
            status: Sync status ('syncing', 'synced', 'error', 'conflict')
        """
        message = {
            "type": "sync_status",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.debug(f"Broadcast to client: {message}")
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for dead in dead_connections:
            await self.disconnect(dead)

        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connections")

# Singleton instance
ws_manager = WebSocketManager()
