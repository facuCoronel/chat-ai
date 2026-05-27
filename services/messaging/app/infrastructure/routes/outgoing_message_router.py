from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.dtos.message_dto import ReceiveMessageRequest
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.domain.entities.message import MessageType, Platform, SenderRole
from app.infrastructure.dependencies import get_receive_message_use_case

logger = logging.getLogger(__name__)

router = APIRouter()


class OutgoingMessagePayload(BaseModel):
    platform: str
    sender_id: str
    recipient_id: str
    message_type: str
    raw_text: Optional[str] = None
    raw_payload: dict[str, Any] = {}
    wamid_local: str = ""
    sender_name: Optional[str] = None


@router.post("/messages/outgoing", status_code=200)
async def record_outgoing_message(
    payload: OutgoingMessagePayload,
    use_case: ReceiveMessageUseCase = Depends(get_receive_message_use_case),
):
    """Records a seller message sent externally (e.g. from another service) and triggers insight generation."""
    request = ReceiveMessageRequest(
        wamid=payload.wamid_local or str(uuid.uuid4()),
        platform=Platform(payload.platform),
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        message_type=MessageType(payload.message_type),
        raw_text=payload.raw_text,
        raw_payload=payload.raw_payload,
        received_at_unix=int(datetime.now(timezone.utc).timestamp()),
        sender_name=payload.sender_name,
    )
    response = await use_case.execute(request, sender_role=SenderRole.SELLER)
    logger.info(
        "outgoing message recorded wamid=%s was_duplicate=%s",
        response.wamid,
        response.was_duplicate,
    )
    return {
        "message_id": response.message_id,
        "wamid": response.wamid,
        "was_duplicate": response.was_duplicate,
    }
