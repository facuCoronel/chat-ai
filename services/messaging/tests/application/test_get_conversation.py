import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.get_conversation import GetConversationUseCase
from app.domain.entities.message import MessageType, SenderRole


def _make_message(wamid="wamid.ABC", text="Hola", sender_role=SenderRole.BUYER):
    msg = MagicMock()
    msg.id = "msg-uuid"
    msg.wamid = wamid
    msg.sender_role.value = sender_role.value
    msg.sender_name = "Test User"
    msg.message_type.value = MessageType.TEXT.value
    msg.raw_text = text
    msg.received_at.isoformat.return_value = "2025-01-01T00:00:00+00:00"
    return msg


def _make_use_case(mock_repo, mock_business_repo):
    return GetConversationUseCase(repo=mock_repo, business_account_repo=mock_business_repo)


@pytest.mark.asyncio
async def test_returns_empty_when_no_business_accounts():
    mock_repo = AsyncMock()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = set()

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute(contact_id="5491112345678")

    assert result == []
    mock_repo.get_messages.assert_not_called()


@pytest.mark.asyncio
async def test_returns_mapped_messages():
    msg1 = _make_message(wamid="wamid.1", text="Hola")
    msg2 = _make_message(wamid="wamid.2", text="Chau", sender_role=SenderRole.SELLER)
    mock_repo = AsyncMock()
    mock_repo.get_messages.return_value = [msg1, msg2]
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute(contact_id="5491112345678")

    assert len(result) == 2
    assert result[0].wamid == "wamid.1"
    assert result[0].raw_text == "Hola"
    assert result[1].wamid == "wamid.2"
    assert result[1].sender_role == SenderRole.SELLER.value


@pytest.mark.asyncio
async def test_returns_empty_when_no_messages():
    mock_repo = AsyncMock()
    mock_repo.get_messages.return_value = []
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute(contact_id="5491112345678")

    assert result == []


@pytest.mark.asyncio
async def test_passes_correct_params_to_repo():
    mock_repo = AsyncMock()
    mock_repo.get_messages.return_value = []
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    await use_case.execute(contact_id="5491112345678", platform="whatsapp", limit=20, offset=5)

    mock_repo.get_messages.assert_called_once_with(
        contact_id="5491112345678",
        business_phone_id="PHONE_NUMBER_ID",
        platform="whatsapp",
        limit=20,
        offset=5,
    )


@pytest.mark.asyncio
async def test_message_fields_mapped_to_dto():
    msg = _make_message()
    mock_repo = AsyncMock()
    mock_repo.get_messages.return_value = [msg]
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute(contact_id="5491112345678")

    dto = result[0]
    assert dto.id == "msg-uuid"
    assert dto.wamid == "wamid.ABC"
    assert dto.sender_name == "Test User"
    assert dto.received_at == "2025-01-01T00:00:00+00:00"
