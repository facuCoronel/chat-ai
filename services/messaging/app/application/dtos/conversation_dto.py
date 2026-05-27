from dataclasses import dataclass
from typing import Optional


@dataclass
class ContactResponse:
    contact_id: str
    platform: str
    last_message_at: str
    last_sender_role: str
    name: Optional[str] = None
    last_message_text: Optional[str] = None


@dataclass
class ConversationMessageResponse:
    id: str
    wamid: str
    sender_role: str
    message_type: str
    received_at: str
    sender_name: Optional[str] = None
    raw_text: Optional[str] = None
