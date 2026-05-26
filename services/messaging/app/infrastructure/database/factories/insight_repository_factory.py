from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.repositories.insight_repository import IInsightRepository
from app.infrastructure.database.repositories.sqla_insight_repository import SqlaInsightRepository


class SqlaInsightRepositoryFactory:
    """Concrete implementation of IInsightRepositoryContextFactory.

    Creates a fresh AsyncSession per call, which is required for fire-and-forget
    background tasks that outlive the HTTP request scope.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def __call__(self) -> AsyncGenerator[IInsightRepository, None]:
        async with self._session_factory() as session:
            yield SqlaInsightRepository(session)
