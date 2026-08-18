import asyncio
import logging
from typing import Dict, List

from fastapi.websockets import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections grouped by job ID.

    Methods are async and use an asyncio.Lock to ensure safe concurrent
    access from multiple tasks.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """Register a websocket under a given job_id.

        Does not call `websocket.accept()` here; the caller should accept
        the connection before registering if needed.
        """
        async with self._lock:
            if job_id not in self._connections:
                self._connections[job_id] = []
            self._connections[job_id].append(websocket)
            logger.debug("WebSocket connected for job_id=%s (total=%d)", job_id, len(self._connections[job_id]))

    async def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """Remove a websocket from the list for job_id."""
        async with self._lock:
            conns = self._connections.get(job_id)
            if not conns:
                return
            try:
                conns.remove(websocket)
            except ValueError:
                # websocket not present; ignore
                return
            if not conns:
                # remove the key when no connections remain
                self._connections.pop(job_id, None)
            logger.debug("WebSocket disconnected for job_id=%s (remaining=%d)", job_id, len(conns))

    async def broadcast(self, job_id: str, message: dict) -> None:
        """Send JSON `message` to all websockets registered under `job_id`.

        Silently drops any connection that raises an exception while sending.
        """
        # Copy the list under lock so we can send without holding the lock.
        async with self._lock:
            conns = list(self._connections.get(job_id, []))

        if not conns:
            return

        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                # On any error, try to remove the websocket from registry.
                logger.debug("Dropping websocket for job_id=%s due to send error", job_id, exc_info=True)
                async with self._lock:
                    stored = self._connections.get(job_id)
                    if stored and ws in stored:
                        try:
                            stored.remove(ws)
                        except ValueError:
                            pass
                    if stored is not None and not stored:
                        self._connections.pop(job_id, None)


# Module level instance to import elsewhere
manager = ConnectionManager()
