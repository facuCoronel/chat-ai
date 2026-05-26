from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.application.dtos.insight_dto import RecordOutgoingMessageRequest
from app.application.dtos.message_dto import ReceiveMessageRequest, ReceiveMessageResponse
from app.application.use_cases.receive_message import ReceiveMessageUseCase


class RecordOutgoingMessageUseCase:
    """Records seller/agent outgoing messages for persistence and insight generation.

    WhatsApp Cloud API status webhooks do not include message text for outgoing messages,
    so seller messages must be registered explicitly at send time via this use case.
    """

    def __init__(self, receive_uc: ReceiveMessageUseCase) -> None:
        self._receive_uc = receive_uc

    async def execute(self, request: RecordOutgoingMessageRequest) -> ReceiveMessageResponse:
        wamid = request.wamid_local or str(uuid.uuid4())
        receive_req = ReceiveMessageRequest(
            wamid=wamid,
            platform=request.platform,
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            message_type=request.message_type,
            raw_text=request.raw_text,
            raw_payload=request.raw_payload,
            received_at_unix=int(datetime.now(timezone.utc).timestamp()),
        )
        return await self._receive_uc.execute(receive_req, sender_role="seller")
