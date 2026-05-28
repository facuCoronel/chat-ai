from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class SenderRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    UNKNOWN = "unknown"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    CONTACTS = "contacts"
    STICKER = "sticker"
    REACTION = "reaction"
    UNKNOWN = "unknown"


@dataclass
class IncomingMessage:
    """
    Enterprise entity. Platform-agnostic. Zero framework or ORM imports.
    wamid is used as the universal idempotency key across all Meta platforms.
    """
    id: str
    wamid: str
    platform: Platform
    sender_id: str
    recipient_id: str
    message_type: MessageType
    raw_payload: dict
    received_at: datetime
    created_at: datetime
    sender_role: SenderRole = SenderRole.UNKNOWN
    sender_name: Optional[str] = None
    raw_text: Optional[str] = None
    conversation_id: Optional[str] = None
    business_account_id: Optional[str] = None
    customer_external_id: Optional[str] = None
