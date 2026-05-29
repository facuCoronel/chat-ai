import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from app.application._background import run_insight_safely
from app.application.dtos.insight_dto import GenerateInsightRequest
from app.application.dtos.message_dto import ReceiveMessageRequest, ReceiveMessageResponse
from app.domain.entities.message import IncomingMessage, SenderRole
from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.domain.repositories.message_repository import IMessageRepository
from app.domain.services.conversation_builder import build_conversation_data

if TYPE_CHECKING:
    from app.application.ports.insight_generator import IInsightGenerator
    from app.application.ports.message_publisher import IMessagePublisher

logger = logging.getLogger(__name__)


class ReceiveMessageUseCase:
    """
    Application use case. Depends only on the domain layer.
    No FastAPI, no SQLAlchemy, no Pydantic.
    """

    def __init__(
        self,
        repository: IMessageRepository,
        business_account_repo: IBusinessAccountRepository,
        insight_generator: Optional["IInsightGenerator"] = None,
        message_publisher: Optional["IMessagePublisher"] = None,
    ) -> None:
        self._repo = repository
        self._business_account_repo = business_account_repo
        self._insight_generator = insight_generator
        self._message_publisher = message_publisher

    async def execute(
        self,
        request: ReceiveMessageRequest,
        sender_role: SenderRole = SenderRole.BUYER,
    ) -> ReceiveMessageResponse:
        if await self._repo.exists_by_wamid(request.wamid):
            return ReceiveMessageResponse(
                message_id="",
                wamid=request.wamid,
                was_duplicate=True,
                platform=request.platform.value,
            )

        business_ids = await self._business_account_repo.get_active_external_ids()
        try:
            conversation_id, business_account_id, customer_external_id = build_conversation_data(
                business_ids, request.sender_id, request.recipient_id
            )
        except ValueError:
            logger.warning(
                "Rejected incoming message wamid=%s: no matching business account (sender=%s recipient=%s)",
                request.wamid,
                request.sender_id,
                request.recipient_id,
            )
            return ReceiveMessageResponse(
                message_id="",
                wamid=request.wamid,
                was_duplicate=False,
                platform=request.platform.value,
            )

        message = IncomingMessage(
            id=str(uuid.uuid4()),
            wamid=request.wamid,
            platform=request.platform,
            sender_id=request.sender_id,
            sender_name=request.sender_name,
            recipient_id=request.recipient_id,
            sender_role=sender_role,
            message_type=request.message_type,
            raw_text=request.raw_text,
            media_id=request.media_id,
            raw_payload=request.raw_payload,
            received_at=datetime.fromtimestamp(request.received_at_unix, tz=timezone.utc),
            created_at=datetime.now(tz=timezone.utc),
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
                sender_role=sender_role.value,
                sender_name=saved.sender_name,
                raw_text=saved.raw_text,
                media_id=saved.media_id,
                message_type=saved.message_type,
                received_at=saved.received_at,
            )
            asyncio.create_task(
                run_insight_safely(self._insight_generator, insight_request)
            )

        return ReceiveMessageResponse(
            message_id=saved.id,
            wamid=saved.wamid,
            was_duplicate=False,
            platform=saved.platform.value,
        )
