from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.domain.entities.message import IncomingMessage


class IMessagePublisher(Protocol):
    """Output port: notifies external observers when a message is persisted."""

    async def publish(self, message: "IncomingMessage") -> None: ...
