from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.application.dtos.message_dto import ReceiveMessageRequest, ReceiveMessageResponse
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.domain.entities.message import MessageType, Platform

if TYPE_CHECKING:
    from app.domain.services.whatsapp_client import IWhatsAppClient


class ReplyMessageUseCase:
    """Sends a text reply via WhatsApp and records it as a seller message for insight generation."""

    def __init__(
        self,
        whatsapp_client: "IWhatsAppClient",
        receive_uc: ReceiveMessageUseCase,
        phone_number_id: str,
    ) -> None:
        self._wa = whatsapp_client
        self._receive_uc = receive_uc
        self._phone_number_id = phone_number_id

    async def execute(
        self,
        to: str,
        text: str,
        sender_name: Optional[str] = None,
        platform: Platform = Platform.WHATSAPP,
    ) -> ReceiveMessageResponse:
        result = await self._wa.send_text(to=to, text=text)

        request = ReceiveMessageRequest(
            wamid=result.wamid,
            platform=platform,
            sender_id=self._phone_number_id,
            recipient_id=to,
            message_type=MessageType.TEXT,
            raw_text=text,
            raw_payload={},
            received_at_unix=int(datetime.now(timezone.utc).timestamp()),
            sender_name=sender_name,
        )
        return await self._receive_uc.execute(request, sender_role="seller")
