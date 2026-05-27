from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.conversation import Contact
from app.domain.entities.message import IncomingMessage


class IConversationRepository(ABC):

    @abstractmethod
    async def list_contacts(self, business_phone_id: str, platform: str) -> list[Contact]: ...

    @abstractmethod
    async def get_messages(
        self,
        contact_id: str,
        business_phone_id: str,
        platform: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IncomingMessage]: ...
