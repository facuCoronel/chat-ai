from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.message import IncomingMessage


class IMessageRepository(ABC):
    """
    Defined in the domain layer. Implemented in infrastructure.
    The Dependency Rule: infrastructure depends on this, never the reverse.
    """

    @abstractmethod
    async def save(self, message: IncomingMessage) -> IncomingMessage:
        """Persist a new message and return the saved entity."""
        ...

    @abstractmethod
    async def find_by_wamid(self, wamid: str) -> Optional[IncomingMessage]:
        """Return stored message or None."""
        ...

    @abstractmethod
    async def exists_by_wamid(self, wamid: str) -> bool:
        """Fast idempotency check without loading the full entity."""
        ...
