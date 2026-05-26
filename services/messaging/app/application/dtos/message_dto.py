from dataclasses import dataclass
from typing import Optional

from app.domain.entities.message import Platform, MessageType


@dataclass
class ReceiveMessageRequest:
    """
    Input boundary DTO. Plain dataclass — no framework types.
    Crosses the use case boundary inward from the adapters layer.
    """
    wamid: str
    platform: Platform
    sender_id: str
    recipient_id: str
    message_type: MessageType
    raw_payload: dict
    received_at_unix: int
    sender_name: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class ReceiveMessageResponse:
    """
    Output boundary DTO. Returned by the interactor to the adapters layer.
    """
    message_id: str
    wamid: str
    was_duplicate: bool
    platform: str
