from __future__ import annotations


def build_conversation_data(
    business_account_ids: set[str],
    sender_id: str,
    recipient_id: str,
) -> tuple[str, str, str]:
    """
    Returns (conversation_id, business_account_id, customer_external_id).

    Raises ValueError if neither side belongs to a configured business account.
    """
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
