import pytest
from unittest.mock import AsyncMock, MagicMock

from app.adapters.controllers.webhook_controller import WebhookController
from app.application.dtos.message_dto import ReceiveMessageResponse
from app.domain.entities.message import Platform


WHATSAPP_TEXT_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WBA_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                    "display_phone_number": "16505555555",
                    "phone_number_id": "PHONE_ID",
                },
                "contacts": [{"profile": {"name": "John Doe"}, "wa_id": "16315551234"}],
                "messages": [{
                    "from": "16315551234",
                    "id": "wamid.ABC",
                    "timestamp": "1683229471",
                    "type": "text",
                    "text": {"body": "Hello"},
                }],
            },
            "field": "messages",
        }],
    }],
}

STATUS_UPDATE_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WBA_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "16505555555", "phone_number_id": "PHONE_ID"},
                "statuses": [{"id": "wamid.ABC", "status": "delivered", "timestamp": "1683229500"}],
            },
            "field": "messages",
        }],
    }],
}


@pytest.mark.asyncio
async def test_whatsapp_payload_is_handled():
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = ReceiveMessageResponse(
        message_id="msg-uuid",
        wamid="wamid.ABC",
        was_duplicate=False,
        platform=Platform.WHATSAPP.value,
    )

    controller = WebhookController(receive_message_uc=mock_uc)
    response = await controller.handle_incoming(WHATSAPP_TEXT_PAYLOAD)

    mock_uc.execute.assert_called_once()
    assert response is not None
    assert response.wamid == "wamid.ABC"


@pytest.mark.asyncio
async def test_unknown_platform_returns_none():
    mock_uc = AsyncMock()

    controller = WebhookController(receive_message_uc=mock_uc)
    response = await controller.handle_incoming({"object": "instagram_business_account"})

    assert response is None
    mock_uc.execute.assert_not_called()


@pytest.mark.asyncio
async def test_status_update_returns_none():
    mock_uc = AsyncMock()

    controller = WebhookController(receive_message_uc=mock_uc)
    response = await controller.handle_incoming(STATUS_UPDATE_PAYLOAD)

    assert response is None
    mock_uc.execute.assert_not_called()


@pytest.mark.asyncio
async def test_empty_payload_returns_none():
    mock_uc = AsyncMock()

    controller = WebhookController(receive_message_uc=mock_uc)
    response = await controller.handle_incoming({})

    assert response is None
    mock_uc.execute.assert_not_called()
