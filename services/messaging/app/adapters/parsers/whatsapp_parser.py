from typing import Optional

from app.adapters.parsers.base_parser import IWebhookParser
from app.application.dtos.message_dto import ReceiveMessageRequest
from app.domain.entities.message import MessageType, Platform


class WhatsAppWebhookParser(IWebhookParser):
    """
    Translates a raw WhatsApp Cloud API webhook payload into a ReceiveMessageRequest.
    Handles only message events; returns None for status update payloads.
    """

    def can_parse(self, payload: dict) -> bool:
        return payload.get("object") == "whatsapp_business_account"

    def parse(self, payload: dict) -> Optional[ReceiveMessageRequest]:
        try:
            value = payload["entry"][0]["changes"][0]["value"]
        except (KeyError, IndexError):
            return None

        messages = value.get("messages")
        if not messages:
            return None

        msg = messages[0]
        contact = (value.get("contacts") or [{}])[0]

        raw_type = msg.get("type", "unknown")
        try:
            message_type = MessageType(raw_type)
        except ValueError:
            message_type = MessageType.UNKNOWN

        raw_text: Optional[str] = None
        if message_type == MessageType.TEXT:
            raw_text = msg.get("text", {}).get("body")

        media_id: Optional[str] = None
        if message_type == MessageType.AUDIO:
            media_id = msg.get("audio", {}).get("id")

        return ReceiveMessageRequest(
            wamid=msg["id"],
            platform=Platform.WHATSAPP,
            sender_id=msg["from"],
            sender_name=contact.get("profile", {}).get("name"),
            recipient_id=value["metadata"]["phone_number_id"],
            message_type=message_type,
            raw_text=raw_text,
            media_id=media_id,
            raw_payload=payload,
            received_at_unix=int(msg["timestamp"]),
        )
