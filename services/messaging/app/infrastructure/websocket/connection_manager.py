from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket

if TYPE_CHECKING:
    from app.domain.entities.message import IncomingMessage

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Infrastructure adapter. Implements IMessagePublisher and manages active WebSocket connections.
    Singleton — instantiated once at module level and injected via DI.
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("ws connected total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)
        logger.info("ws disconnected total=%d", len(self._connections))

    async def publish(self, message: "IncomingMessage") -> None:
        if not self._connections:
            return
        payload = json.dumps({
            "event": "message",
            "data": {
                "id": message.id,
                "wamid": message.wamid,
                "platform": message.platform.value,
                "sender_id": message.sender_id,
                "recipient_id": message.recipient_id,
                "sender_role": message.sender_role.value,
                "sender_name": message.sender_name,
                "message_type": message.message_type.value,
                "raw_text": message.raw_text,
                "received_at": message.received_at.isoformat(),
            },
        })
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


connection_manager = WebSocketConnectionManager()
