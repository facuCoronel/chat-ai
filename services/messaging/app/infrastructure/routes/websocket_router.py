from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.infrastructure.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/messages")
async def websocket_messages(ws: WebSocket) -> None:
    """Real-time stream of all incoming and outgoing messages."""
    await connection_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(ws)
