"""App entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from duohabit.auth import get_user_db, get_user_manager
from duohabit.config import settings
from duohabit.db import Base, engine, session_fact

from duohabit.repositories.users import UsersRepository
from duohabit.schemas.users import UserCreate
from duohabit.routers.auth import auth_router
from duohabit.routers.users import users_router
from duohabit.routers.habits import habits_router
from duohabit.routers.chat import chat_router
from duohabit.services.users import create_user
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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
    if await users_repo.get_user_by_email("admin@duohabit.com") is None:
        await create_user(
            users_repo,
            UserCreate(
                email="admin@duohabit.com",
                password="admin",
                username="duohabitAdmin",
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
    res_app.include_router(habits_router)
    res_app.include_router(chat_router)

    @res_app.get("/")
    def root() -> dict[str, str]:
        """Root endpoint to test if the app is running."""
        return {"message": "Running"}

    return res_app

app = create_app()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=[
    #     "http://localhost:5177",
    #     "http://localhost:5173",
    #     # Сюда добавишь прод домены
    #     "https://yourdomain.com",
    # ],
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE...)
    allow_headers=["*"],  # Разрешить все заголовки
    expose_headers=["*"],  # Какие заголовки отдавать клиенту
    max_age=600,  # Кэшировать preflight запросы на 10 минут
)
