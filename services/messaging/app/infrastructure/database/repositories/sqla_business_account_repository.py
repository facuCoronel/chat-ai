from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.business_account_repository import IBusinessAccountRepository
from app.infrastructure.database.models import BusinessAccountORM


class SqlaBusinessAccountRepository(IBusinessAccountRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_external_ids(self) -> set[str]:
        stmt = select(BusinessAccountORM.external_id).where(BusinessAccountORM.is_active == True)
        result = await self._session.execute(stmt)
        return {row[0] for row in result.all()}
