from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WhatsAppSendResult:
    wamid: str


class IWhatsAppClient(ABC):
    @abstractmethod
    async def send_text(self, to: str, text: str) -> WhatsAppSendResult:
        """Send a text message and return the wamid assigned by Meta."""
        ...
