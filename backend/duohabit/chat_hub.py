"""
In-process registry of live chat WebSocket connections.

State lives in the process, so delivery works while the app runs as a single
uvicorn worker - which is what `fastapi dev` does. Scaling to several workers
means replacing the internals here with Redis pub/sub; routers and services
do not need to know about it.
"""

from collections import defaultdict
from typing import Any, Iterable

from fastapi import WebSocket

from duohabit.logger import logger


class ConnectionManager:
    """Keeps track of which sockets belong to which user."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept a socket and remember it for the user."""
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Forget a socket. Safe to call twice."""
        sockets = self._connections.get(user_id)
        if sockets is None:
            return

        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def broadcast(self, user_ids: Iterable[int], payload: dict[str, Any]) -> None:
        """
        Send a payload to every live socket of the given users.

        A dead socket must not stop delivery to everyone else, so failures are
        swallowed and the socket is dropped from the registry.
        """
        for user_id in set(user_ids):
            for websocket in list(self._connections.get(user_id, ())):
                try:
                    await websocket.send_json(payload)
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.debug("Dropping dead chat socket of user %s", user_id)
                    self.disconnect(user_id, websocket)


hub = ConnectionManager()
