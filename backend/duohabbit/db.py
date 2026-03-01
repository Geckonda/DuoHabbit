"""Database connection utilities."""

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from duohabbit.config import settings


@lru_cache()
def engine() -> AsyncEngine:
    """Get the database engine."""
    return create_async_engine(settings.get_postgres_url())


@lru_cache()
def session_fact() -> async_sessionmaker[AsyncSession]:
    """Get the database sessionmaker."""
    return async_sessionmaker(
        bind=engine(), expire_on_commit=False, class_=AsyncSession
    )


class Base(
    DeclarativeBase
):  # pylint: disable=too-few-public-methods  # Intentional shim
    """Base class for all models."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    Closed automatically.
    """
    session: AsyncSession = session_fact()()
    try:
        yield session
    finally:
        await session.close()
