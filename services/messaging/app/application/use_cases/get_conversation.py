from __future__ import annotations

from app.application.dtos.conversation_dto import ConversationMessageResponse
from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.domain.repositories.conversation_repository import IConversationRepository


class GetConversationUseCase:

    def __init__(
        self,
        repo: IConversationRepository,
        business_account_repo: IBusinessAccountRepository,
    ) -> None:
        self._repo = repo
        self._business_account_repo = business_account_repo

    async def execute(
        self,
        contact_id: str,
        platform: str = "whatsapp",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationMessageResponse]:
        business_ids = await self._business_account_repo.get_active_external_ids()
        business_phone_id = next(iter(business_ids), None) if business_ids else None
        if not business_phone_id:
            return []

        messages = await self._repo.get_messages(
            contact_id=contact_id,
            business_phone_id=business_phone_id,
            platform=platform,
            limit=limit,
            offset=offset,
        )
        return [
            ConversationMessageResponse(
                id=m.id,
                wamid=m.wamid,
                sender_role=m.sender_role.value,
                sender_name=m.sender_name,
                message_type=m.message_type.value,
                raw_text=m.raw_text,
                received_at=m.received_at.isoformat(),
            )
            for m in messages
        ]
