import uuid
import pytest
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.insight import (
    CommercialRisk,
    Intent,
    MainEmotion,
    MessageInsight,
    Sentiment,
    Urgency,
)
from app.domain.entities.message import Platform, SenderRole
from app.infrastructure.database.models import Base
from app.infrastructure.database.repositories.sqla_insight_repository import SqlaInsightRepository


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def _make_insight(**overrides) -> MessageInsight:
    defaults = dict(
        id=str(uuid.uuid4()),
        message_id="msg-uuid",
        wamid="wamid.TEST123",
        platform=Platform.WHATSAPP,
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
        sender_role=SenderRole.BUYER,
        sentiment=Sentiment.NEUTRAL,
        main_emotion=MainEmotion.OTHER,
        intent=Intent.INFORMATION,
        urgency=Urgency.LOW,
        commercial_risk=CommercialRisk.LOW,
        summary="Test summary",
        recommended_action="No action needed",
        insights=["Test insight"],
        raw_model_response={"response": "raw"},
        model_name="llama3",
        prompt_version="v1",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    return MessageInsight(**{**defaults, **overrides})


@pytest.mark.asyncio
async def test_save_and_find_by_wamid(session):
    repo = SqlaInsightRepository(session)
    await repo.save(_make_insight())

    found = await repo.find_by_wamid("wamid.TEST123")

    assert found is not None
    assert found.wamid == "wamid.TEST123"
    assert found.sentiment == Sentiment.NEUTRAL
    assert found.audio_transcription is None


@pytest.mark.asyncio
async def test_save_audio_insight_persists_transcription(session):
    repo = SqlaInsightRepository(session)
    await repo.save(_make_insight(
        wamid="wamid.AUDIO123",
        audio_transcription="Hola, quiero cancelar mi pedido",
    ))

    found = await repo.find_by_wamid("wamid.AUDIO123")

    assert found is not None
    assert found.audio_transcription == "Hola, quiero cancelar mi pedido"


@pytest.mark.asyncio
async def test_text_insight_has_null_transcription(session):
    repo = SqlaInsightRepository(session)
    await repo.save(_make_insight())

    found = await repo.find_by_wamid("wamid.TEST123")

    assert found is not None
    assert found.audio_transcription is None


@pytest.mark.asyncio
async def test_find_by_message_id(session):
    repo = SqlaInsightRepository(session)
    await repo.save(_make_insight(message_id="specific-msg-uuid"))

    found = await repo.find_by_message_id("specific-msg-uuid")

    assert found is not None
    assert found.message_id == "specific-msg-uuid"


@pytest.mark.asyncio
async def test_find_recent_by_conversation_returns_history(session):
    repo = SqlaInsightRepository(session)

    for i in range(3):
        await repo.save(_make_insight(
            id=str(uuid.uuid4()),
            wamid=f"wamid.CONV{i}",
            message_id=f"msg-{i}",
        ))

    results = await repo.find_recent_by_conversation(
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
        platform="whatsapp",
        limit=10,
    )

    assert len(results) == 3


@pytest.mark.asyncio
async def test_find_recent_by_conversation_respects_limit(session):
    repo = SqlaInsightRepository(session)

    for i in range(5):
        await repo.save(_make_insight(
            id=str(uuid.uuid4()),
            wamid=f"wamid.LIM{i}",
            message_id=f"msg-lim-{i}",
        ))

    results = await repo.find_recent_by_conversation(
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
        platform="whatsapp",
        limit=3,
    )

    assert len(results) == 3
