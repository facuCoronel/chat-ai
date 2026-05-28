from __future__ import annotations

import re


def normalize_wa_phone(phone: str) -> str:
    """
    WhatsApp Cloud API delivers Argentine mobile numbers as 549XXXXXXXXXX (with 9).
    Normalize 54XXXXXXXXXX (12 digits, no 9) -> 549XXXXXXXXXX so conversation IDs
    are consistent regardless of whether the caller passes the number with or without 9.
    """
    if re.match(r'^54(?!9)\d{10}$', phone):
        return '549' + phone[2:]
    return phone


def build_conversation_data(
    business_account_ids: set[str],
    sender_id: str,
    recipient_id: str,
) -> tuple[str, str, str]:
    """
    Returns (conversation_id, business_account_id, customer_external_id).

    Raises ValueError if neither side belongs to a configured business account.
    """
    sender_id = normalize_wa_phone(sender_id)
    recipient_id = normalize_wa_phone(recipient_id)

    if sender_id in business_account_ids:
        business_account_id = sender_id
        customer_external_id = recipient_id
    elif recipient_id in business_account_ids:
        business_account_id = recipient_id
        customer_external_id = sender_id
    else:
        raise ValueError(
            "The message does not belong to any configured WhatsApp business account"
        )

    conversation_id = f"{business_account_id}_{customer_external_id}"
    return conversation_id, business_account_id, customer_external_id
