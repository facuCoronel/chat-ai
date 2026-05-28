from __future__ import annotations

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.conversation import Contact
from app.domain.entities.message import IncomingMessage, MessageType, Platform, SenderRole
from app.domain.repositories.conversation_repository import IConversationRepository
from app.infrastructure.database.models import MessageORM

_BUYER = SenderRole.BUYER.value

# Derive buyer phone from sender_role for historical messages (no conversation_id)
_buyer_phone = case(
    (MessageORM.sender_role == _BUYER, MessageORM.sender_id),
    else_=MessageORM.recipient_id,
)

# Unified contact expression: prefer customer_external_id when available (new msgs), fall back to role-derived
_contact_phone = case(
    (MessageORM.customer_external_id.isnot(None), MessageORM.customer_external_id),
    else_=_buyer_phone,
)


class SqlaConversationRepository(IConversationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_contacts(self, business_phone_id: str, platform: str) -> list[Contact]:
        # Filter messages that belong to this business account (new + historical)
        _biz_filter = or_(
            MessageORM.business_account_id == business_phone_id,
            and_(
                MessageORM.business_account_id.is_(None),
                or_(
                    MessageORM.sender_id == business_phone_id,
                    MessageORM.recipient_id == business_phone_id,
                ),
            ),
        )

        # Subquery 1: last message timestamp per contact
        last_sub = (
            select(
                _contact_phone.label("contact_id"),
                func.max(MessageORM.received_at).label("last_at"),
            )
            .where(MessageORM.platform == platform, _biz_filter)
            .group_by(_contact_phone)
            .subquery()
        )

        # Join to fetch the actual last message row per contact
        last_msg_stmt = (
            select(MessageORM)
            .join(
                last_sub,
                and_(
                    _contact_phone == last_sub.c.contact_id,
                    MessageORM.received_at == last_sub.c.last_at,
                    MessageORM.platform == platform,
                ),
            )
            .where(_biz_filter)
            .order_by(last_sub.c.last_at.desc())
        )

        # Subquery 2: most recent sender_name per buyer phone
        rn_sub = (
            select(
                MessageORM.sender_id,
                MessageORM.sender_name,
                func.row_number()
                .over(
                    partition_by=MessageORM.sender_id,
                    order_by=MessageORM.received_at.desc(),
                )
                .label("rn"),
            )
            .where(
                MessageORM.platform == platform,
                MessageORM.sender_role == _BUYER,
                MessageORM.sender_name.isnot(None),
            )
            .subquery()
        )
        name_stmt = select(rn_sub.c.sender_id, rn_sub.c.sender_name).where(rn_sub.c.rn == 1)

        rows = (await self._session.execute(last_msg_stmt)).scalars().all()
        name_rows = (await self._session.execute(name_stmt)).all()
        names: dict[str, str] = {r.sender_id: r.sender_name for r in name_rows}

        result: list[Contact] = []
        for r in rows:
            # Determine the contact_id for this row
            if r.customer_external_id is not None:
                contact_id = r.customer_external_id
            elif r.sender_role == _BUYER:
                contact_id = r.sender_id
            else:
                contact_id = r.recipient_id

            result.append(
                Contact(
                    contact_id=contact_id,
                    platform=Platform(r.platform),
                    name=names.get(contact_id),
                    last_message_text=r.raw_text,
                    last_message_at=r.received_at,
                    last_sender_role=SenderRole(r.sender_role),
                )
            )

        return result

    async def get_messages(
        self,
        contact_id: str,
        business_phone_id: str,
        platform: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IncomingMessage]:
        expected_conversation_id = f"{business_phone_id}_{contact_id}"

        stmt = (
            select(MessageORM)
            .where(
                or_(
                    # New messages: use conversation_id
                    MessageORM.conversation_id == expected_conversation_id,
                    # Historical messages: bidirectional sender/recipient match
                    and_(
                        MessageORM.conversation_id.is_(None),
                        MessageORM.platform == platform,
                        or_(
                            and_(
                                MessageORM.sender_id == contact_id,
                                MessageORM.recipient_id == business_phone_id,
                            ),
                            and_(
                                MessageORM.sender_id == business_phone_id,
                                MessageORM.recipient_id == contact_id,
                            ),
                        ),
                    ),
                )
            )
            .order_by(MessageORM.received_at.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]


def _to_entity(orm: MessageORM) -> IncomingMessage:
    return IncomingMessage(
        id=orm.id,
        wamid=orm.wamid,
        platform=Platform(orm.platform),
        sender_id=orm.sender_id,
        sender_name=orm.sender_name,
        recipient_id=orm.recipient_id,
        sender_role=SenderRole(orm.sender_role),
        message_type=MessageType(orm.message_type),
        raw_text=orm.raw_text,
        raw_payload=orm.raw_payload,
        received_at=orm.received_at,
        created_at=orm.created_at,
        conversation_id=orm.conversation_id,
        business_account_id=orm.business_account_id,
        customer_external_id=orm.customer_external_id,
    )
