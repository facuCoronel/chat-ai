from __future__ import annotations

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.conversation import Contact
from app.domain.entities.message import IncomingMessage, MessageType, Platform, SenderRole
from app.domain.repositories.conversation_repository import IConversationRepository
from app.infrastructure.database.models import MessageORM

_BUYER = SenderRole.BUYER.value

# Expression: phone number of the buyer side of the conversation
_buyer_phone = case(
    (MessageORM.sender_role == _BUYER, MessageORM.sender_id),
    else_=MessageORM.recipient_id,
)


class SqlaConversationRepository(IConversationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_contacts(self, business_phone_id: str, platform: str) -> list[Contact]:
        _involves_business = or_(
            MessageORM.sender_id == business_phone_id,
            MessageORM.recipient_id == business_phone_id,
        )

        # Subquery 1: last message timestamp per contact
        last_sub = (
            select(
                _buyer_phone.label("contact_id"),
                func.max(MessageORM.received_at).label("last_at"),
            )
            .where(MessageORM.platform == platform, _involves_business)
            .group_by(_buyer_phone)
            .subquery()
        )

        # Join to fetch the actual last message row per contact
        last_msg_stmt = (
            select(MessageORM)
            .join(
                last_sub,
                and_(
                    case(
                        (MessageORM.sender_role == _BUYER, MessageORM.sender_id),
                        else_=MessageORM.recipient_id,
                    ) == last_sub.c.contact_id,
                    MessageORM.received_at == last_sub.c.last_at,
                    MessageORM.platform == platform,
                    _involves_business,
                ),
            )
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
                _involves_business,
            )
            .subquery()
        )
        name_stmt = select(rn_sub.c.sender_id, rn_sub.c.sender_name).where(rn_sub.c.rn == 1)

        rows = (await self._session.execute(last_msg_stmt)).scalars().all()
        name_rows = (await self._session.execute(name_stmt)).all()
        names: dict[str, str] = {r.sender_id: r.sender_name for r in name_rows}

        return [
            Contact(
                contact_id=r.sender_id if r.sender_role == _BUYER else r.recipient_id,
                platform=Platform(r.platform),
                name=names.get(r.sender_id if r.sender_role == _BUYER else r.recipient_id),
                last_message_text=r.raw_text,
                last_message_at=r.received_at,
                last_sender_role=SenderRole(r.sender_role),
            )
            for r in rows
        ]

    async def get_messages(
        self,
        contact_id: str,
        business_phone_id: str,
        platform: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IncomingMessage]:
        stmt = (
            select(MessageORM)
            .where(
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
    )
