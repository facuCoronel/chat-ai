from typing import Optional

from app.adapters.parsers.base_parser import IWebhookParser
from app.application.dtos.message_dto import ReceiveMessageRequest
from app.domain.entities.message import MessageType, Platform


class FacebookWebhookParser(IWebhookParser):
    """
    Stub parser for Facebook Messenger webhooks.
    Facebook webhook payloads use object == "page".
    """

    def can_parse(self, payload: dict) -> bool:
        return payload.get("object") == "page"

    def parse(self, payload: dict) -> Optional[ReceiveMessageRequest]:
        # TODO: implement when Facebook integration is activated
        raise NotImplementedError("Facebook parser not yet implemented")
