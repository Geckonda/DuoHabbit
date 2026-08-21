"""Business logic for users CRUD."""

from fastapi.requests import Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users import exceptions as fastapi_users_exceptions
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.schemas import BaseUserCreate

from duohabit.models.users import User
from duohabit.repositories.users import UnitOfWorkUserDB, UsersRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.common import PaginationParams
from duohabit.schemas.users import (
    UserCreate,
    UserOut,
    UserUpdate,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    User manager for fastapi-users.
    Overrides the original create method to use our own transaction handling.
    """

    async def create(
        self,
        user_create: BaseUserCreate,
        safe: bool = False,
        request: Request | None = None,
    ) -> User:
        # We definitely use an SQLAlchemyUserDatabase
        adapter: SQLAlchemyUserDatabase[User, int] = self.user_db  # type: ignore[assignment]
        new_adapter = UnitOfWorkUserDB(adapter.session, User)
        try:
            self.user_db = new_adapter
            result = await super().create(user_create, safe, request)
        finally:
            self.user_db = adapter
        return result


def user_model_to_schema(
    user_model: User, request_context: AccessTokenClaim | None = None
) -> UserOut:
    """Convert SQLAlchemy User model to Pydantic schema."""

    include_private = request_context is not None and (
        request_context.account_is_platform_admin
        or request_context.user_id == user_model.id
    )

    return UserOut(
        id=user_model.id,  # fastapi-users BaseUser использует id, не user_id
        email=user_model.email if include_private else None,
        username=user_model.username,
        is_platform_admin=user_model.is_platform_admin if include_private else None,
        is_active=user_model.is_active,
        is_superuser=user_model.is_superuser,
        is_verified=user_model.is_verified,
        timezone=user_model.timezone if include_private else None,
    )


async def get_users(
    repo: UsersRepository,
    request_context: AccessTokenClaim | None = None,
    pagination: PaginationParams | None = None,
) -> list[UserOut]:
    """Get all users."""
    user_models = await repo.get_users(pagination=pagination)

    return [
        user_model_to_schema(user, request_context=request_context)
        for user in user_models
    ]


async def get_user(
    repo: UsersRepository,
    target_user_id: int,
    request_context: AccessTokenClaim | None = None,
) -> UserOut:
    """Return a single user by ID."""
    user_model = await repo.get_user(target_user_id)

    if user_model is None:
        raise Exception("User not found")

    return user_model_to_schema(user_model, request_context=request_context)


async def create_user(
    repo: UsersRepository,
    user_in: UserCreate,
    claim_admin: bool | None,
    manager: UserManager,
) -> UserOut:
    """Create a new user and return the created user."""

    # Проверка прав на создание админа
    if user_in.is_platform_admin and not claim_admin:
        raise Exception("Platform admins must be created by a platform admin")

    # Проверка уникальности email через БД
    try:
        created_user_model = await manager.create(user_in)
    except fastapi_users_exceptions.UserAlreadyExists:
        raise Exception("Email already in use")

    await repo.commit()

    # Для ответа используем claim создателя
    created_user_claim = AccessTokenClaim(
        user_id=created_user_model.id,
        account_is_platform_admin=created_user_model.is_platform_admin,
    )

    return user_model_to_schema(created_user_model, request_context=created_user_claim)


async def update_user(
    repo: UsersRepository,
    user_id: int,
    user_update: UserUpdate,
    request_context: AccessTokenClaim,
    manager: UserManager,
) -> UserOut:
    """Update a user."""

    # Проверка прав
    if (
        user_id != request_context.user_id
        and not request_context.account_is_platform_admin
    ):
        raise Exception("You can only update your own profile")

    # Получаем пользователя
    user = await repo.get_user(user_id)
    if not user:
        raise Exception("User not found")

    # Обновляем через fastapi-users manager
    updated_user = await manager.update(user_update, user)
    await repo.commit()

    return user_model_to_schema(updated_user, request_context=request_context)
