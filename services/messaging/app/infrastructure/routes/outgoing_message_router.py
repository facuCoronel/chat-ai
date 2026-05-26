from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.dtos.insight_dto import RecordOutgoingMessageRequest
from app.application.use_cases.record_outgoing_message import RecordOutgoingMessageUseCase
from app.domain.entities.message import MessageType, Platform
from app.infrastructure.dependencies import get_record_outgoing_use_case

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


@router.post("/messages/outgoing", status_code=200)
async def record_outgoing_message(
    payload: OutgoingMessagePayload,
    use_case: RecordOutgoingMessageUseCase = Depends(get_record_outgoing_use_case),
):
    """Records a seller/agent outgoing message and triggers insight generation.

    WhatsApp status webhooks do not include message text, so outgoing messages
    must be registered explicitly at send time via this endpoint.
    """
    request = RecordOutgoingMessageRequest(
        platform=Platform(payload.platform),
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        message_type=MessageType(payload.message_type),
        raw_text=payload.raw_text,
        raw_payload=payload.raw_payload,
        wamid_local=payload.wamid_local,
    )
    response = await use_case.execute(request)
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
