from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.insight import MessageInsight


class IInsightRepository(ABC):
    @abstractmethod
    async def save(self, insight: MessageInsight) -> MessageInsight: ...

    @abstractmethod
    async def find_by_message_id(self, message_id: str) -> Optional[MessageInsight]: ...

    @abstractmethod
    async def find_by_wamid(self, wamid: str) -> Optional[MessageInsight]: ...

    @abstractmethod
    async def find_recent_by_conversation(
        self, sender_id: str, recipient_id: str, platform: str, limit: int
    ) -> list[MessageInsight]: ...
