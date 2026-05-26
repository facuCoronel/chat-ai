from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from app.infrastructure.config import get_settings
from app.infrastructure.database.models import Base

_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.LOG_LEVEL == "DEBUG",
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


async def create_tables() -> None:
    """Create all tables. Use Alembic in production instead."""
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
