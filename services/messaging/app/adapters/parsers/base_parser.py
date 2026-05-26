from abc import ABC, abstractmethod
from typing import Optional

from app.application.dtos.message_dto import ReceiveMessageRequest


class IWebhookParser(ABC):
    """
    Parser interface defined in the adapters layer.
    One implementation per Meta platform (WhatsApp, Instagram, Facebook).
    Adding a new platform = new class implementing this interface, registered in the controller.
    """

    @abstractmethod
    def can_parse(self, payload: dict) -> bool:
        """Return True if this parser handles the given webhook payload."""
        ...

    @abstractmethod
    def parse(self, payload: dict) -> Optional[ReceiveMessageRequest]:
        """
        Extract the incoming message from the payload and return a ReceiveMessageRequest.
        Return None if the payload contains no message events (e.g. status updates).
        """
        ...
