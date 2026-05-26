from typing import Optional

from app.adapters.parsers.base_parser import IWebhookParser
from app.adapters.parsers.whatsapp_parser import WhatsAppWebhookParser
from app.application.dtos.message_dto import ReceiveMessageResponse
from app.application.use_cases.receive_message import ReceiveMessageUseCase


class WebhookController:
    """
    Interface adapter. Delegates to the matching parser and the use case.
    Never imports FastAPI or SQLAlchemy.

    To add Instagram/Facebook: register the new parser in _parsers — nothing else changes.
    """

    def __init__(self, receive_message_uc: ReceiveMessageUseCase) -> None:
        self._receive_message_uc = receive_message_uc
        self._parsers: list[IWebhookParser] = [
            WhatsAppWebhookParser(),
            # InstagramWebhookParser(),  # uncomment when ready
            # FacebookWebhookParser(),   # uncomment when ready
        ]

    async def handle_incoming(self, raw_payload: dict) -> Optional[ReceiveMessageResponse]:
        for parser in self._parsers:
            if parser.can_parse(raw_payload):
                request = parser.parse(raw_payload)
                if request is None:
                    return None
                return await self._receive_message_uc.execute(request)
        return None
