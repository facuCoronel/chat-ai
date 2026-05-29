import pytest

from app.domain.services.conversation_builder import (
    build_conversation_data,
    normalize_wa_phone,
    wa_api_phone,
)


# --- normalize_wa_phone ---

def test_normalize_adds_9_to_argentine_number_without_9():
    assert normalize_wa_phone("541112345678") == "5491112345678"


def test_normalize_leaves_argentine_number_with_9_unchanged():
    assert normalize_wa_phone("5491112345678") == "5491112345678"


def test_normalize_leaves_non_argentine_number_unchanged():
    assert normalize_wa_phone("16315551234") == "16315551234"


def test_normalize_leaves_already_normalized_short_number_unchanged():
    assert normalize_wa_phone("1234567890") == "1234567890"


# --- wa_api_phone ---

def test_wa_api_strips_9_from_argentine_number():
    assert wa_api_phone("5491112345678") == "541112345678"


def test_wa_api_leaves_number_without_9_unchanged():
    assert wa_api_phone("541112345678") == "541112345678"


def test_wa_api_leaves_non_argentine_number_unchanged():
    assert wa_api_phone("16315551234") == "16315551234"


# --- build_conversation_data ---

def test_build_when_sender_is_business():
    conversation_id, biz_id, customer_id = build_conversation_data(
        business_account_ids={"PHONE_ID"},
        sender_id="PHONE_ID",
        recipient_id="5491112345678",
    )
    assert biz_id == "PHONE_ID"
    assert customer_id == "5491112345678"
    assert conversation_id == "PHONE_ID_5491112345678"


def test_build_when_recipient_is_business():
    conversation_id, biz_id, customer_id = build_conversation_data(
        business_account_ids={"PHONE_ID"},
        sender_id="5491112345678",
        recipient_id="PHONE_ID",
    )
    assert biz_id == "PHONE_ID"
    assert customer_id == "5491112345678"
    assert conversation_id == "PHONE_ID_5491112345678"


def test_build_raises_when_neither_side_is_business():
    with pytest.raises(ValueError, match="does not belong to any configured"):
        build_conversation_data(
            business_account_ids={"PHONE_ID"},
            sender_id="5491111111111",
            recipient_id="5491222222222",
        )


def test_build_normalizes_argentine_sender():
    _, _, customer_id = build_conversation_data(
        business_account_ids={"PHONE_ID"},
        sender_id="PHONE_ID",
        recipient_id="541112345678",  # without 9
    )
    assert customer_id == "5491112345678"  # normalized with 9
