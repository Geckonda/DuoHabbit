"""Shared pytest fixtures: an isolated in-memory SQLite backend for the FastAPI app."""

# pylint: disable=wrong-import-position,redefined-outer-name
# Settings() requires these env vars to even import; dummy values are enough since the
# real engine() (postgres) is never touched in tests -- get_session is overridden below.
# The fixtures below also legitimately take other fixtures as same-named parameters,
# which is the standard pytest pattern pylint's redefined-outer-name doesn't recognize.

import os
from typing import AsyncGenerator

os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("TESTING", "true")

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from duohabit.auth import get_token_claim
from duohabit.db import Base, get_session
from duohabit.main import create_app
from duohabit.models.users import User
from duohabit.schemas.auth import AccessTokenClaim


@pytest_asyncio.fixture(loop_scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A fresh in-memory SQLite database per test, with all app tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_fact = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_fact() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def app(db_session: AsyncSession) -> FastAPI:
    """The FastAPI app with its DB dependency pointed at the test session."""
    fastapi_app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    return fastapi_app


@pytest_asyncio.fixture(loop_scope="session")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """An HTTP client wired to the test app, for router-level tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def as_user(app: FastAPI, user_id: int, is_platform_admin: bool = False) -> None:
    """Bypass real bearer-token auth in router tests: force the caller's identity."""

    async def _override() -> AccessTokenClaim:
        return AccessTokenClaim(
            user_id=user_id, account_is_platform_admin=is_platform_admin
        )

    app.dependency_overrides[get_token_claim] = _override


async def make_user(session: AsyncSession, username: str, email: str) -> User:
    """Create a bare User row for tests (no password hashing needed)."""
    user = User(email=email, hashed_password="x", username=username)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user
