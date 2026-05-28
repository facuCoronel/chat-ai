from __future__ import annotations

from app.application.dtos.conversation_dto import ContactResponse
from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.domain.repositories.conversation_repository import IConversationRepository


class ListContactsUseCase:

    def __init__(
        self,
        repo: IConversationRepository,
        business_account_repo: IBusinessAccountRepository,
    ) -> None:
        self._repo = repo
        self._business_account_repo = business_account_repo

    async def execute(self, platform: str = "whatsapp") -> list[ContactResponse]:
        business_ids = await self._business_account_repo.get_active_external_ids()
        # Use the first active account. When multi-account is needed, the caller
        # will pass a specific business_account_id.
        business_phone_id = next(iter(business_ids), None) if business_ids else None
        if not business_phone_id:
            return []

        contacts = await self._repo.list_contacts(business_phone_id, platform)
        return [
            ContactResponse(
                contact_id=c.contact_id,
                platform=c.platform.value,
                name=c.name,
                last_message_text=c.last_message_text,
                last_message_at=c.last_message_at.isoformat(),
                last_sender_role=c.last_sender_role.value,
            )
            for c in contacts
        ]
