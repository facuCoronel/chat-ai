import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.list_contacts import ListContactsUseCase
from app.domain.entities.message import Platform, SenderRole


def _make_contact(contact_id="5491112345678", name="Test User"):
    contact = MagicMock()
    contact.contact_id = contact_id
    contact.platform.value = Platform.WHATSAPP.value
    contact.name = name
    contact.last_message_text = "Hola"
    contact.last_message_at.isoformat.return_value = "2025-01-01T00:00:00+00:00"
    contact.last_sender_role.value = SenderRole.BUYER.value
    return contact


def _make_use_case(mock_repo, mock_business_repo):
    return ListContactsUseCase(repo=mock_repo, business_account_repo=mock_business_repo)


@pytest.mark.asyncio
async def test_returns_empty_when_no_business_accounts():
    mock_repo = AsyncMock()
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = set()

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute()

    assert result == []
    mock_repo.list_contacts.assert_not_called()


@pytest.mark.asyncio
async def test_returns_mapped_contacts():
    c1 = _make_contact(contact_id="5491112345678", name="Alice")
    c2 = _make_contact(contact_id="5491198765432", name="Bob")
    mock_repo = AsyncMock()
    mock_repo.list_contacts.return_value = [c1, c2]
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute()

    assert len(result) == 2
    assert result[0].contact_id == "5491112345678"
    assert result[0].name == "Alice"
    assert result[1].contact_id == "5491198765432"
    assert result[1].name == "Bob"


@pytest.mark.asyncio
async def test_returns_empty_when_no_contacts():
    mock_repo = AsyncMock()
    mock_repo.list_contacts.return_value = []
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute()

    assert result == []


@pytest.mark.asyncio
async def test_passes_business_phone_id_and_platform_to_repo():
    mock_repo = AsyncMock()
    mock_repo.list_contacts.return_value = []
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    await use_case.execute(platform="whatsapp")

    mock_repo.list_contacts.assert_called_once_with("PHONE_NUMBER_ID", "whatsapp")


@pytest.mark.asyncio
async def test_contact_fields_mapped_to_dto():
    contact = _make_contact()
    mock_repo = AsyncMock()
    mock_repo.list_contacts.return_value = [contact]
    mock_business_repo = AsyncMock()
    mock_business_repo.get_active_external_ids.return_value = {"PHONE_NUMBER_ID"}

    use_case = _make_use_case(mock_repo, mock_business_repo)
    result = await use_case.execute()

    dto = result[0]
    assert dto.contact_id == "5491112345678"
    assert dto.platform == Platform.WHATSAPP.value
    assert dto.last_message_at == "2025-01-01T00:00:00+00:00"
    assert dto.last_sender_role == SenderRole.BUYER.value
