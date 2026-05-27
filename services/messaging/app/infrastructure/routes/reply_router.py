from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.use_cases.reply_message import ReplyMessageUseCase
from app.infrastructure.dependencies import get_reply_use_case

logger = logging.getLogger(__name__)

router = APIRouter()


class ReplyPayload(BaseModel):
    to: str
    text: str
    sender_name: Optional[str] = None


@router.post("/messages/reply", status_code=200)
async def reply_message(
    payload: ReplyPayload,
    use_case: ReplyMessageUseCase = Depends(get_reply_use_case),
):
    """Send a WhatsApp text reply and register the seller insight."""
    response = await use_case.execute(
        to=payload.to,
        text=payload.text,
        sender_name=payload.sender_name,
    )
    logger.info("reply sent and recorded wamid=%s to=%s", response.wamid, payload.to)
    return {
        "message_id": response.message_id,
        "wamid": response.wamid,
        "was_duplicate": response.was_duplicate,
    }
