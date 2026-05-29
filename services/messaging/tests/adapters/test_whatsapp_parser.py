import pytest

from app.adapters.parsers.whatsapp_parser import WhatsAppWebhookParser
from app.domain.entities.message import MessageType, Platform


SAMPLE_AUDIO_PAYLOAD = {
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
                    "id": "wamid.AUDIO123",
                    "timestamp": "1683229471",
                    "type": "audio",
                    "audio": {
                        "id": "MEDIA_ID_123",
                        "mime_type": "audio/ogg; codecs=opus",
                    },
                }],
            },
            "field": "messages",
        }],
    }],
}

SAMPLE_TEXT_PAYLOAD = {
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


def test_can_parse_whatsapp_payload():
    parser = WhatsAppWebhookParser()
    assert parser.can_parse(SAMPLE_TEXT_PAYLOAD) is True


def test_cannot_parse_non_whatsapp_payload():
    parser = WhatsAppWebhookParser()
    assert parser.can_parse({"object": "instagram"}) is False


def test_parses_text_message_correctly():
    parser = WhatsAppWebhookParser()
    request = parser.parse(SAMPLE_TEXT_PAYLOAD)

    assert request is not None
    assert request.wamid == "wamid.ABC"
    assert request.platform == Platform.WHATSAPP
    assert request.sender_id == "16315551234"
    assert request.recipient_id == "PHONE_ID"
    assert request.message_type == MessageType.TEXT
    assert request.raw_text == "Hello"
    assert request.sender_name == "John Doe"
    assert request.received_at_unix == 1683229471


def test_status_update_returns_none():
    parser = WhatsAppWebhookParser()
    result = parser.parse(STATUS_UPDATE_PAYLOAD)
    assert result is None


def test_parses_audio_message_extracts_media_id():
    parser = WhatsAppWebhookParser()
    request = parser.parse(SAMPLE_AUDIO_PAYLOAD)

    assert request is not None
    assert request.message_type == MessageType.AUDIO
    assert request.media_id == "MEDIA_ID_123"
    assert request.raw_text is None
    assert request.wamid == "wamid.AUDIO123"


def test_text_message_has_no_media_id():
    parser = WhatsAppWebhookParser()
    request = parser.parse(SAMPLE_TEXT_PAYLOAD)

    assert request is not None
    assert request.media_id is None
