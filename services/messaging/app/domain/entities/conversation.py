from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.message import Platform, SenderRole


@dataclass
class Contact:
    contact_id: str
    platform: Platform
    last_message_at: datetime
    last_sender_role: SenderRole
    name: Optional[str] = None
    last_message_text: Optional[str] = None
