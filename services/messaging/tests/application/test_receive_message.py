import pytest
from unittest.mock import AsyncMock

from app.application.dtos.message_dto import ReceiveMessageRequest, ReceiveMessageResponse
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.domain.entities.message import IncomingMessage, MessageType, Platform


def _make_request(**overrides) -> ReceiveMessageRequest:
    defaults = dict(
        wamid="wamid.ABC123",
        platform=Platform.WHATSAPP,
        sender_id="5491112345678",
        recipient_id="PHONE_NUMBER_ID",
        message_type=MessageType.TEXT,
        raw_payload={"object": "whatsapp_business_account"},
        received_at_unix=1683229471,
        sender_name="Test User",
        raw_text="Hello",
    )
    return ReceiveMessageRequest(**{**defaults, **overrides})


def _make_entity(request: ReceiveMessageRequest) -> IncomingMessage:
    from datetime import datetime, timezone
    return IncomingMessage(
        id="some-uuid",
        wamid=request.wamid,
        platform=request.platform,
        sender_id=request.sender_id,
        sender_name=request.sender_name,
        recipient_id=request.recipient_id,
        message_type=request.message_type,
        raw_text=request.raw_text,
        raw_payload=request.raw_payload,
        received_at=datetime.fromtimestamp(request.received_at_unix, tz=timezone.utc),
        created_at=datetime.now(tz=timezone.utc),
    )


@pytest.mark.asyncio
async def test_new_message_is_saved():
    request = _make_request()
    mock_repo = AsyncMock()
    mock_repo.exists_by_wamid.return_value = False
    mock_repo.save.return_value = _make_entity(request)
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {request.recipient_id}

    use_case = ReceiveMessageUseCase(mock_repo, mock_business_repo)
    response = await use_case.execute(request)

    mock_repo.exists_by_wamid.assert_called_once_with(request.wamid)
    mock_repo.save.assert_called_once()
    assert response.was_duplicate is False
    assert response.wamid == request.wamid
    assert response.platform == Platform.WHATSAPP.value


@pytest.mark.asyncio
async def test_duplicate_message_is_skipped():
    request = _make_request()
    mock_repo = AsyncMock()
    mock_repo.exists_by_wamid.return_value = True
    mock_business_repo = AsyncMock()

    use_case = ReceiveMessageUseCase(mock_repo, mock_business_repo)
    response = await use_case.execute(request)

    mock_repo.save.assert_not_called()
    assert response.was_duplicate is True
    assert response.wamid == request.wamid


@pytest.mark.asyncio
async def test_audio_media_id_is_passed_to_entity():
    request = _make_request(
        message_type=MessageType.AUDIO,
        raw_text=None,
        media_id="MEDIA_ID_123",
    )
    mock_repo = AsyncMock()
    mock_repo.exists_by_wamid.return_value = False
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {request.recipient_id}

    saved_entity = None

    async def capture_save(entity: IncomingMessage) -> IncomingMessage:
        nonlocal saved_entity
        saved_entity = entity
        return entity

    mock_repo.save.side_effect = capture_save

    use_case = ReceiveMessageUseCase(mock_repo, mock_business_repo)
    await use_case.execute(request)

    assert saved_entity is not None
    assert saved_entity.media_id == "MEDIA_ID_123"
    assert saved_entity.message_type == MessageType.AUDIO
    assert saved_entity.raw_text is None


@pytest.mark.asyncio
async def test_message_entity_fields_are_set_correctly():
    request = _make_request(raw_text="Hola mundo", message_type=MessageType.TEXT)
    mock_repo = AsyncMock()
    mock_repo.exists_by_wamid.return_value = False

    saved_entity = None

    async def capture_save(entity: IncomingMessage) -> IncomingMessage:
        nonlocal saved_entity
        saved_entity = entity
        return entity

    mock_repo.save.side_effect = capture_save
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {request.recipient_id}

    use_case = ReceiveMessageUseCase(mock_repo, mock_business_repo)
    await use_case.execute(request)

    assert saved_entity is not None
    assert saved_entity.wamid == "wamid.ABC123"
    assert saved_entity.platform == Platform.WHATSAPP
    assert saved_entity.raw_text == "Hola mundo"
    assert saved_entity.message_type == MessageType.TEXT
    assert saved_entity.id != ""
