import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from app.application.dtos.insight_dto import GenerateInsightRequest
from app.application.dtos.message_dto import ReceiveMessageRequest, ReceiveMessageResponse
from app.application.use_cases.generate_insight import _run_insight_safely
from app.domain.entities.message import IncomingMessage
from app.domain.repositories.message_repository import IMessageRepository

if TYPE_CHECKING:
    from app.application.ports.insight_generator import IInsightGenerator

logger = logging.getLogger(__name__)


class ReceiveMessageUseCase:
    """
    Application use case. Depends only on the domain layer.
    No FastAPI, no SQLAlchemy, no Pydantic.
    """

    def __init__(
        self,
        repository: IMessageRepository,
        insight_generator: Optional["IInsightGenerator"] = None,
    ) -> None:
        self._repo = repository
        self._insight_generator = insight_generator

    async def execute(
        self,
        request: ReceiveMessageRequest,
        sender_role: str = "buyer",
    ) -> ReceiveMessageResponse:
        if await self._repo.exists_by_wamid(request.wamid):
            return ReceiveMessageResponse(
                message_id="",
                wamid=request.wamid,
                was_duplicate=True,
                platform=request.platform.value,
            )

        message = IncomingMessage(
            id=str(uuid.uuid4()),
            wamid=request.wamid,
            platform=request.platform,
            sender_id=request.sender_id,
            sender_name=request.sender_name,
            recipient_id=request.recipient_id,
            message_type=request.message_type,
            raw_text=request.raw_text,
            raw_payload=request.raw_payload,
            received_at=datetime.fromtimestamp(request.received_at_unix, tz=timezone.utc),
            created_at=datetime.now(tz=timezone.utc),
        )

        saved = await self._repo.save(message)

        if self._insight_generator is not None:
            insight_request = GenerateInsightRequest(
                message_id=saved.id,
                wamid=saved.wamid,
                platform=saved.platform,
                sender_id=saved.sender_id,
                sender_role=sender_role,
                raw_text=saved.raw_text,
                message_type=saved.message_type,
                received_at=saved.received_at,
            )
            asyncio.create_task(
                _run_insight_safely(self._insight_generator, insight_request)
            )

        return ReceiveMessageResponse(
            message_id=saved.id,
            wamid=saved.wamid,
            was_duplicate=False,
            platform=saved.platform.value,
        )
