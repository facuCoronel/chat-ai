from __future__ import annotations

from app.application.dtos.conversation_dto import ContactResponse
from app.domain.repositories.conversation_repository import IConversationRepository


class ListContactsUseCase:

    def __init__(self, repo: IConversationRepository, phone_number_id: str) -> None:
        self._repo = repo
        self._phone_number_id = phone_number_id

    async def execute(self, platform: str = "whatsapp") -> list[ContactResponse]:
        contacts = await self._repo.list_contacts(self._phone_number_id, platform)
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
