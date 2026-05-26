from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.entities.message import MessageType, Platform


@dataclass
class GenerateInsightRequest:
    """Input DTO for GenerateInsightUseCase. No framework types."""

    message_id: str
    wamid: str
    platform: Platform
    sender_id: str
    sender_role: str
    message_type: MessageType
    received_at: datetime
    raw_text: Optional[str] = None


@dataclass
class GenerateInsightResponse:
    """Output DTO returned by GenerateInsightUseCase."""

    message_id: str
    wamid: str
    was_skipped: bool
    insight_id: str = ""
    sentiment: str = ""
    intent: str = ""
    urgency: str = ""
    commercial_risk: str = ""


@dataclass
class RecordOutgoingMessageRequest:
    """Input DTO for RecordOutgoingMessageUseCase (seller messages)."""

    platform: Platform
    sender_id: str
    recipient_id: str
    message_type: MessageType
    raw_payload: dict
    wamid_local: str = ""
    raw_text: Optional[str] = None
