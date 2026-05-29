import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.use_cases.reply_message import ReplyMessageUseCase
from app.domain.entities.message import MessageType, Platform


def _make_saved(wamid="wamid.SENT123", text="Hola"):
    saved = MagicMock()
    saved.id = "msg-uuid"
    saved.wamid = wamid
    saved.platform = Platform.WHATSAPP
    saved.sender_id = "PHONE_NUMBER_ID"
    saved.recipient_id = "5491112345678"
    saved.raw_text = text
    saved.sender_name = "Agent"
    saved.message_type = MessageType.TEXT
    saved.received_at = datetime.now(tz=timezone.utc)
    return saved


def _make_use_case(mock_wa, mock_repo, mock_business_repo, insight_generator=None, message_publisher=None):
    return ReplyMessageUseCase(
        whatsapp_client=mock_wa,
        repository=mock_repo,
        business_account_repo=mock_business_repo,
        insight_generator=insight_generator,
        message_publisher=message_publisher,
    )


@pytest.mark.asyncio
async def test_reply_sends_message_and_saves():
    mock_wa = AsyncMock()
    mock_wa.send_text.return_value = MagicMock(wamid="wamid.SENT123")
    mock_repo = AsyncMock()
    mock_repo.save.return_value = _make_saved()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_wa, mock_repo, mock_business_repo)
    response = await use_case.execute(to="5491112345678", text="Hola")

    mock_wa.send_text.assert_called_once()
    mock_repo.save.assert_called_once()
    assert response.was_duplicate is False
    assert response.wamid == "wamid.SENT123"
    assert response.platform == Platform.WHATSAPP.value


@pytest.mark.asyncio
async def test_reply_raises_when_no_business_accounts():
    mock_wa = AsyncMock()
    mock_repo = AsyncMock()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = set()

    use_case = _make_use_case(mock_wa, mock_repo, mock_business_repo)

    with pytest.raises(RuntimeError, match="No active business account"):
        await use_case.execute(to="5491112345678", text="Hola")

    mock_wa.send_text.assert_not_called()
    mock_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_reply_normalizes_argentine_phone():
    mock_wa = AsyncMock()
    mock_wa.send_text.return_value = MagicMock(wamid="wamid.X")
    mock_repo = AsyncMock()
    mock_repo.save.return_value = _make_saved()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_wa, mock_repo, mock_business_repo)
    # Argentine number without 9 → should be normalized to 549...
    await use_case.execute(to="541112345678", text="Hola")

    call_kwargs = mock_wa.send_text.call_args[1]
    # wa_api_phone strips the 9, so 549... → 54... for the API call
    assert call_kwargs["to"] == "541112345678"


@pytest.mark.asyncio
async def test_reply_with_message_publisher_creates_task():
    mock_wa = AsyncMock()
    mock_wa.send_text.return_value = MagicMock(wamid="wamid.X")
    mock_repo = AsyncMock()
    mock_repo.save.return_value = _make_saved()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}
    mock_publisher = AsyncMock()

    with patch("app.application.use_cases.reply_message.asyncio.create_task") as mock_create_task:
        use_case = _make_use_case(mock_wa, mock_repo, mock_business_repo, message_publisher=mock_publisher)
        await use_case.execute(to="5491112345678", text="Hola")

    mock_create_task.assert_called()


@pytest.mark.asyncio
async def test_reply_with_insight_generator_creates_task():
    mock_wa = AsyncMock()
    mock_wa.send_text.return_value = MagicMock(wamid="wamid.X")
    mock_repo = AsyncMock()
    mock_repo.save.return_value = _make_saved()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}
    mock_insight = AsyncMock()

    with patch("app.application.use_cases.reply_message.asyncio.create_task") as mock_create_task:
        use_case = _make_use_case(mock_wa, mock_repo, mock_business_repo, insight_generator=mock_insight)
        await use_case.execute(to="5491112345678", text="Hola")

    mock_create_task.assert_called()


@pytest.mark.asyncio
async def test_reply_without_optional_deps_does_not_create_tasks():
    mock_wa = AsyncMock()
    mock_wa.send_text.return_value = MagicMock(wamid="wamid.X")
    mock_repo = AsyncMock()
    mock_repo.save.return_value = _make_saved()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    with patch("app.application.use_cases.reply_message.asyncio.create_task") as mock_create_task:
        use_case = _make_use_case(mock_wa, mock_repo, mock_business_repo)
        await use_case.execute(to="5491112345678", text="Hola")

    mock_create_task.assert_not_called()
