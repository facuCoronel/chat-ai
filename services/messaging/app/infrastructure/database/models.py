import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BusinessAccountORM(Base):
    __tablename__ = "business_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_business_accounts_external_id", "external_id", unique=True),
    )


class InsightORM(Base):
    __tablename__ = "message_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(String(36), nullable=False)
    wamid: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False, server_default="")
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    main_emotion: Mapped[str] = mapped_column(String(30), nullable=False)
    intent: Mapped[str] = mapped_column(String(30), nullable=False)
    urgency: Mapped[str] = mapped_column(String(10), nullable=False)
    commercial_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    summary: Mapped[str] = mapped_column(String(1024), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(1024), nullable=False)
    insights: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_model_response: Mapped[dict] = mapped_column(JSON, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_message_insights_message_id", "message_id"),
        Index("ix_message_insights_wamid", "wamid"),
        Index("ix_message_insights_sentiment", "sentiment"),
        Index("ix_message_insights_intent", "intent"),
        Index("ix_message_insights_commercial_risk", "commercial_risk"),
        Index("ix_message_insights_created_at", "created_at"),
    )


class MessageORM(Base):
    __tablename__ = "incoming_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wamid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="buyer")
    message_type: Mapped[str] = mapped_column(String(30), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    customer_external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_incoming_messages_platform", "platform"),
        Index("ix_incoming_messages_sender_id", "sender_id"),
        Index("ix_incoming_messages_received_at", "received_at"),
        Index("ix_incoming_messages_conversation_id", "conversation_id"),
        Index("ix_incoming_messages_customer_external_id", "customer_external_id"),
    )
