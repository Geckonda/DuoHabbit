"""Business logic for users CRUD."""

from fastapi import UploadFile
from fastapi.requests import Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users import exceptions as fastapi_users_exceptions
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.schemas import BaseUserCreate
from pydantic import ValidationError

from duohabbit.models.users import User, UserType
from duohabbit.repositories.users import UnitOfWorkUserDB, UsersRepository
from duohabbit.schemas.auth import AccessTokenClaim
from duohabbit.schemas.common import PaginationParams
from duohabbit.schemas.users import (
    InternalUserNew,
    PersonProfile,
    UserNew,
    UserOut,
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    User manager for fastapi-users.
    Overrides the original create method to use our own transaction handling.
    Will be useful for hooking into fastapi-users processes.
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

    # Type ignores here because we know at least one of the profiles is set.
    profile = PersonProfile(
        first_name=user_model.person_profile.first_name,  # type: ignore[union-attr]
        last_name=user_model.person_profile.last_name,  # type: ignore[union-attr]
    )
    user_type_value = "person"

    include_private = request_context is not None and (
        request_context.account_is_platform_admin
        or request_context.user_id == user_model.id
    )

    return UserOut(
        user_id=user_model.id,
        user_type=user_type_value,
        user_profile=profile,
        email=user_model.email if include_private else None,
        is_platform_admin=user_model.is_platform_admin if include_private else None,
    )


async def get_users(
    repo: UsersRepository,
    request_context: AccessTokenClaim | None = None,
    pagination: PaginationParams | None = None,
) -> list[UserOut]:
    """Get all users."""
    user_models_result = await repo.get_users(
        pagination=pagination
    )
    user_models = list(user_models_result)

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

    # if request_context is None and user_model.user_type != UserType.COMPANY:
    #     raise Exception("Only companies can be viewed by unauthenticated users")

    return user_model_to_schema(user_model, request_context=request_context)


async def create_user(
    repo: UsersRepository,
    user_in: UserNew,
    claim_admin: bool | None,
    manager: UserManager,
) -> UserOut:
    """Create a new user and return the created user. Fails if the email is already in use."""
    if user_in.is_platform_admin and not claim_admin:
        raise Exception("Platform admins must be created by a platform admin")
    if user_in.is_platform_admin and user_in.user_type != "person":
        raise Exception("Platform admins must be people")
    # Repo checks for duplicates via DB constraints
    try:
        internal_model = InternalUserNew(
            email=user_in.email,
            is_platform_admin=user_in.is_platform_admin,
            user_type=user_in.user_type,
            user_profile=user_in.user_profile,
            password=user_in.password,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
    except ValidationError as exc:
        # Most commonly: invalid email (InternalUserNew inherits fastapi-users BaseUserCreate).
        raise Exception(f"Invalid user payload: {exc.errors()}") from exc
    try:
        created_user_model = await manager.create(internal_model)
    except fastapi_users_exceptions.UserAlreadyExists:
        raise Exception("Email already in use")
    await repo.add_profile(user_in, created_user_model)
    await repo.commit()
    # Treat the created user as "self" for response purposes (even if unauthenticated).
    created_user_claim = AccessTokenClaim(
        user_id=created_user_model.id,
        account_is_company=created_user_model.user_type == UserType.COMPANY,
        account_is_platform_admin=created_user_model.is_platform_admin,
    )
    return user_model_to_schema(created_user_model, request_context=created_user_claim)


async def set_user_avatar(
    user_id: int,
    file: UploadFile,
    repo: UsersRepository,
    token_claim: AccessTokenClaim
) -> UserOut:
    """Uploads and assigns a new avatar for the user."""

    if user_id != token_claim.user_id and not token_claim.account_is_platform_admin:
        raise Exception("Users can change only their own avatars.")

    if not file.content_type or file.content_type not in ALLOWED_TYPES:
        raise Exception("Only JPEG, PNG, GIF, and WebP images are allowed.")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise Exception(
            f"File too large. Maximum size is {MAX_SIZE // (1024*1024)}MB"
        )

    user = await repo.get_user(user_id)
    if not user:
        raise Exception("User not found")

    await repo.commit()
    await file.close()

    return user_model_to_schema(user, request_context=token_claim)
