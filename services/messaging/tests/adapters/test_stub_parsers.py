import pytest

from app.adapters.parsers.facebook_parser import FacebookWebhookParser
from app.adapters.parsers.instagram_parser import InstagramWebhookParser


# --- FacebookWebhookParser ---

def test_facebook_parser_recognizes_page_payload():
    parser = FacebookWebhookParser()
    assert parser.can_parse({"object": "page"}) is True


def test_facebook_parser_rejects_non_page_payload():
    parser = FacebookWebhookParser()
    assert parser.can_parse({"object": "whatsapp_business_account"}) is False


def test_facebook_parser_parse_raises_not_implemented():
    parser = FacebookWebhookParser()
    with pytest.raises(NotImplementedError):
        parser.parse({"object": "page"})


# --- InstagramWebhookParser ---

def test_instagram_parser_recognizes_instagram_payload():
    parser = InstagramWebhookParser()
    assert parser.can_parse({"object": "instagram"}) is True


def test_instagram_parser_rejects_non_instagram_payload():
    parser = InstagramWebhookParser()
    assert parser.can_parse({"object": "whatsapp_business_account"}) is False


def test_instagram_parser_parse_raises_not_implemented():
    parser = InstagramWebhookParser()
    with pytest.raises(NotImplementedError):
        parser.parse({"object": "instagram"})
