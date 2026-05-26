from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.infrastructure.database.engine import get_session_factory
from app.infrastructure.database.repositories.sqla_message_repository import SqlaMessageRepository


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


async def get_receive_message_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> ReceiveMessageUseCase:
    repo = SqlaMessageRepository(session)
    return ReceiveMessageUseCase(repo)
