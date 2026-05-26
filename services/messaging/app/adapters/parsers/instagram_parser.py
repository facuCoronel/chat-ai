from typing import Optional

from app.adapters.parsers.base_parser import IWebhookParser
from app.application.dtos.message_dto import ReceiveMessageRequest
from app.domain.entities.message import MessageType, Platform


class InstagramWebhookParser(IWebhookParser):
    """
    Stub parser for Instagram Messaging webhooks.
    Instagram webhook payloads use object == "instagram".
    """

    def can_parse(self, payload: dict) -> bool:
        return payload.get("object") == "instagram"

    def parse(self, payload: dict) -> Optional[ReceiveMessageRequest]:
        # TODO: implement when Instagram integration is activated
        raise NotImplementedError("Instagram parser not yet implemented")
