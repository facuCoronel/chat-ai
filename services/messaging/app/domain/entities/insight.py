from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from app.domain.entities.message import Platform, SenderRole


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class MainEmotion(str, Enum):
    ANGER = "anger"
    FRUSTRATION = "frustration"
    ANXIETY = "anxiety"
    CONFUSION = "confusion"
    SATISFACTION = "satisfaction"
    JOY = "joy"
    SADNESS = "sadness"
    URGENCY = "urgency"
    OTHER = "other"


class Intent(str, Enum):
    COMPLAINT = "complaint"
    QUESTION = "question"
    PURCHASE_INTENT = "purchase_intent"
    SUPPORT_REQUEST = "support_request"
    NEGOTIATION = "negotiation"
    CANCELLATION_RISK = "cancellation_risk"
    FOLLOW_UP = "follow_up"
    INFORMATION = "information"
    OTHER = "other"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CommercialRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MessageInsight:
    id: str
    message_id: str
    wamid: str
    platform: Platform
    sender_id: str
    recipient_id: str
    sender_role: SenderRole
    sentiment: Sentiment
    main_emotion: MainEmotion
    intent: Intent
    urgency: Urgency
    commercial_risk: CommercialRisk
    summary: str
    insights: list[str]
    keywords: list[str]
    raw_model_response: dict
    model_name: str
    prompt_version: str
    created_at: datetime
    sender_name: Optional[str] = None
    audio_transcription: Optional[str] = None
