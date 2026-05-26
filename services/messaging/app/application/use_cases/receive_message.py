import uuid
from datetime import datetime, timezone

from app.application.dtos.message_dto import ReceiveMessageRequest, ReceiveMessageResponse
from app.domain.entities.message import IncomingMessage
from app.domain.repositories.message_repository import IMessageRepository


class ReceiveMessageUseCase:
    """
    Application use case. Depends only on the domain layer.
    No FastAPI, no SQLAlchemy, no Pydantic.
    """

    def __init__(self, repository: IMessageRepository) -> None:
        self._repo = repository

    async def execute(self, request: ReceiveMessageRequest) -> ReceiveMessageResponse:
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

        return ReceiveMessageResponse(
            message_id=saved.id,
            wamid=saved.wamid,
            was_duplicate=False,
            platform=saved.platform.value,
        )
