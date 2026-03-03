"""App entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from duohabbit.auth import get_user_db, get_user_manager
from duohabbit.config import settings
from duohabbit.db import Base, engine, session_fact

from duohabbit.repositories.users import UsersRepository
from duohabbit.schemas.users import UserCreate
from duohabbit.routers.auth import auth_router
from duohabbit.routers.users import users_router
from duohabbit.services.users import create_user
from fastapi import FastAPI


async def init_db() -> None:
    """Initialize the database."""
    if settings.testing:
        return
    async with engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = session_fact()()
    users_repo = UsersRepository(session)
    user_db = await anext(get_user_db(session))
    manager = await anext(get_user_manager(user_db))
    if await users_repo.get_user_by_email("admin@duohabbit.com") is None:
        await create_user(
            users_repo,
            UserCreate(
                email="admin@duohabbit.com",
                password="admin",
                username="duohabbitAdmin",
                is_platform_admin=True,
            ),
            True,
            manager,
        )
    await session.commit()
    await session.close()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan for the app."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """
    Create the app.
    """
    res_app = FastAPI(lifespan=lifespan)
    res_app.include_router(auth_router)
    res_app.include_router(users_router)

    @res_app.get("/")
    def root() -> dict[str, str]:
        """Root endpoint to test if the app is running."""
        return {"message": "Running"}

    return res_app

app = create_app()