from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.message import IncomingMessage, MessageType, Platform
from app.domain.repositories.message_repository import IMessageRepository
from app.infrastructure.database.models import MessageORM


class SqlaMessageRepository(IMessageRepository):
    """
    SQLAlchemy implementation of IMessageRepository.
    Translates between the domain entity and the ORM model.
    The domain entity never knows this class exists.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: IncomingMessage) -> IncomingMessage:
        orm = _to_orm(message)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_entity(orm)

    async def find_by_wamid(self, wamid: str) -> Optional[IncomingMessage]:
        result = await self._session.execute(
            select(MessageORM).where(MessageORM.wamid == wamid)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def exists_by_wamid(self, wamid: str) -> bool:
        result = await self._session.execute(
            select(MessageORM.id).where(MessageORM.wamid == wamid)
        )
        return result.scalar_one_or_none() is not None


def _to_orm(entity: IncomingMessage) -> MessageORM:
    return MessageORM(
        id=entity.id,
        wamid=entity.wamid,
        platform=entity.platform.value,
        sender_id=entity.sender_id,
        sender_name=entity.sender_name,
        recipient_id=entity.recipient_id,
        message_type=entity.message_type.value,
        raw_text=entity.raw_text,
        raw_payload=entity.raw_payload,
        received_at=entity.received_at,
        created_at=entity.created_at,
    )


def _to_entity(orm: MessageORM) -> IncomingMessage:
    return IncomingMessage(
        id=orm.id,
        wamid=orm.wamid,
        platform=Platform(orm.platform),
        sender_id=orm.sender_id,
        sender_name=orm.sender_name,
        recipient_id=orm.recipient_id,
        message_type=MessageType(orm.message_type),
        raw_text=orm.raw_text,
        raw_payload=orm.raw_payload,
        received_at=orm.received_at,
        created_at=orm.created_at,
    )
