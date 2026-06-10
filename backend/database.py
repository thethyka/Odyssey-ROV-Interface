# backend/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from backend.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# NullPool under tests: each TestClient runs on its own event loop, and an
# asyncpg connection is bound to the loop that opened it, so a pooled
# connection reused on a later test's loop deadlocks. See Settings.testing.
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool if settings.testing else None,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped database session."""
    async with async_session_factory() as session:
        yield session
