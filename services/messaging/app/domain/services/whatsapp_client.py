from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WhatsAppSendResult:
    wamid: str


class IWhatsAppClient(ABC):
    @abstractmethod
    async def send_text(self, to: str, text: str, phone_number_id: str) -> WhatsAppSendResult:
        """Send a text message from phone_number_id and return the wamid assigned by Meta."""
        ...

    @abstractmethod
    async def download_media(self, media_id: str) -> bytes:
        """Download media bytes from Meta CDN using the media_id."""
        ...
