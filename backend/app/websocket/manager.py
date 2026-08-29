"""In-process WebSocket connection manager for real-time alert broadcast."""
import asyncio
import contextlib
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Called once at app startup so sync code can schedule onto this loop."""
        self._loop = loop

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.active.append(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self.active:
                self.active.remove(ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in list(self.active):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


manager = ConnectionManager()


def broadcast_sync(message: dict[str, Any]) -> None:
    """Fire-and-forget broadcast callable from sync request handlers/threads.

    FastAPI runs sync endpoints in a threadpool, so we schedule the coroutine onto
    the main event loop captured at startup (thread-safe). No-op if no loop/clients.
    """
    loop = manager._loop
    if loop is None or not manager.active:
        return
    with contextlib.suppress(RuntimeError):
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), loop)
