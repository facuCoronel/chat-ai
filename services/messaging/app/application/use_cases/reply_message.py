from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.application._background import run_insight_safely
from app.application.dtos.insight_dto import GenerateInsightRequest
from app.application.dtos.message_dto import ReceiveMessageResponse
from app.domain.entities.message import IncomingMessage, MessageType, Platform, SenderRole
from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.domain.repositories.message_repository import IMessageRepository
from app.domain.services.conversation_builder import build_conversation_data, normalize_wa_phone

if TYPE_CHECKING:
    from app.application.ports.insight_generator import IInsightGenerator
    from app.application.ports.message_publisher import IMessagePublisher
    from app.domain.services.whatsapp_client import IWhatsAppClient

logger = logging.getLogger(__name__)


class ReplyMessageUseCase:
    """Sends a text reply via WhatsApp and records it as a seller message."""

    def __init__(
        self,
        whatsapp_client: "IWhatsAppClient",
        repository: IMessageRepository,
        business_account_repo: IBusinessAccountRepository,
        insight_generator: Optional["IInsightGenerator"] = None,
        message_publisher: Optional["IMessagePublisher"] = None,
    ) -> None:
        self._wa = whatsapp_client
        self._repo = repository
        self._business_account_repo = business_account_repo
        self._insight_generator = insight_generator
        self._message_publisher = message_publisher

    async def execute(
        self,
        to: str,
        text: str,
        sender_name: Optional[str] = None,
        platform: Platform = Platform.WHATSAPP,
    ) -> ReceiveMessageResponse:
        business_ids = await self._business_account_repo.get_active_external_ids()
        if not business_ids:
            raise RuntimeError("No active business account configured in business_accounts table")

        # With one active account, use it directly.
        # When multiple accounts exist, the caller should pass a from_account_id (future).
        business_account_id = next(iter(business_ids))
        customer_external_id = normalize_wa_phone(to)
        conversation_id = f"{business_account_id}_{customer_external_id}"

        result = await self._wa.send_text(to=customer_external_id, text=text, phone_number_id=business_account_id)

        message = IncomingMessage(
            id=str(uuid.uuid4()),
            wamid=result.wamid,
            platform=platform,
            sender_id=business_account_id,
            recipient_id=customer_external_id,
            sender_role=SenderRole.SELLER,
            message_type=MessageType.TEXT,
            raw_text=text,
            raw_payload={},
            received_at=datetime.now(tz=timezone.utc),
            created_at=datetime.now(tz=timezone.utc),
            sender_name=sender_name,
            conversation_id=conversation_id,
            business_account_id=business_account_id,
            customer_external_id=customer_external_id,
        )

        saved = await self._repo.save(message)

        if self._message_publisher is not None:
            asyncio.create_task(self._message_publisher.publish(saved))

        if self._insight_generator is not None:
            insight_request = GenerateInsightRequest(
                message_id=saved.id,
                wamid=saved.wamid,
                platform=saved.platform,
                sender_id=saved.sender_id,
                recipient_id=saved.recipient_id,
                sender_role=SenderRole.SELLER.value,
                sender_name=saved.sender_name,
                raw_text=saved.raw_text,
                message_type=saved.message_type,
                received_at=saved.received_at,
            )
            asyncio.create_task(run_insight_safely(self._insight_generator, insight_request))

        return ReceiveMessageResponse(
            message_id=saved.id,
            wamid=saved.wamid,
            was_duplicate=False,
            platform=saved.platform.value,
        )
