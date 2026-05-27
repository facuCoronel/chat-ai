from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.use_cases.get_conversation import GetConversationUseCase
from app.application.use_cases.list_contacts import ListContactsUseCase
from app.infrastructure.dependencies import get_get_conversation_use_case, get_list_contacts_use_case

router = APIRouter()


@router.get("/contacts")
async def list_contacts(
    platform: str = Query(default="whatsapp"),
    use_case: ListContactsUseCase = Depends(get_list_contacts_use_case),
):
    """Returns all contacts grouped by buyer, ordered by most recent message."""
    contacts = await use_case.execute(platform=platform)
    return [vars(c) for c in contacts]


@router.get("/conversations/{contact_id}")
async def get_conversation(
    contact_id: str,
    platform: str = Query(default="whatsapp"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    use_case: GetConversationUseCase = Depends(get_get_conversation_use_case),
):
    """Returns all messages in a conversation with a specific contact."""
    messages = await use_case.execute(
        contact_id=contact_id,
        platform=platform,
        limit=limit,
        offset=offset,
    )
    return [vars(m) for m in messages]
