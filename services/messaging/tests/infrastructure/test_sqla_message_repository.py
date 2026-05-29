import pytest
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.message import IncomingMessage, MessageType, Platform, SenderRole
from app.infrastructure.database.models import Base
from app.infrastructure.database.repositories.sqla_message_repository import SqlaMessageRepository


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def _make_message(**overrides) -> IncomingMessage:
    defaults = dict(
        id="msg-uuid-1",
        wamid="wamid.TEST123",
        platform=Platform.WHATSAPP,
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
        message_type=MessageType.TEXT,
        raw_payload={},
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        sender_role=SenderRole.BUYER,
    )
    return IncomingMessage(**{**defaults, **overrides})


@pytest.mark.asyncio
async def test_save_and_find_by_wamid(session):
    repo = SqlaMessageRepository(session)
    await repo.save(_make_message())

    found = await repo.find_by_wamid("wamid.TEST123")

    assert found is not None
    assert found.wamid == "wamid.TEST123"
    assert found.platform == Platform.WHATSAPP
    assert found.message_type == MessageType.TEXT
    assert found.media_id is None


@pytest.mark.asyncio
async def test_save_audio_message_persists_media_id(session):
    repo = SqlaMessageRepository(session)
    await repo.save(_make_message(
        id="msg-uuid-2",
        wamid="wamid.AUDIO123",
        message_type=MessageType.AUDIO,
        media_id="MEDIA_ID_ABC",
    ))

    found = await repo.find_by_wamid("wamid.AUDIO123")

    assert found is not None
    assert found.message_type == MessageType.AUDIO
    assert found.media_id == "MEDIA_ID_ABC"


@pytest.mark.asyncio
async def test_text_message_has_null_media_id(session):
    repo = SqlaMessageRepository(session)
    await repo.save(_make_message(message_type=MessageType.TEXT))

    found = await repo.find_by_wamid("wamid.TEST123")

    assert found is not None
    assert found.media_id is None


@pytest.mark.asyncio
async def test_exists_by_wamid_true_for_saved(session):
    repo = SqlaMessageRepository(session)
    await repo.save(_make_message())

    assert await repo.exists_by_wamid("wamid.TEST123") is True


@pytest.mark.asyncio
async def test_exists_by_wamid_false_for_unknown(session):
    repo = SqlaMessageRepository(session)

    assert await repo.exists_by_wamid("wamid.DOES_NOT_EXIST") is False


@pytest.mark.asyncio
async def test_find_by_wamid_returns_none_for_unknown(session):
    repo = SqlaMessageRepository(session)

    found = await repo.find_by_wamid("wamid.MISSING")

    assert found is None
