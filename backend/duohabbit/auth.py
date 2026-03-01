"""Auth utilities."""

from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from duohabbit.config import settings
from duohabbit.db import get_session
from duohabbit.models.auth import AccessToken
from duohabbit.models.users import User, UserType
from duohabbit.schemas.auth import AccessTokenClaim
from duohabbit.services.users import UserManager


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, int], None]:
    """Dependency to get a user database adapter for fastapi-users."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_access_token_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyAccessTokenDatabase[AccessToken], None]:
    """Dependency to get an access token database adapter for fastapi-users."""
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, int] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Dependency to get a user manager for fastapi-users."""
    yield UserManager(user_db)


def get_db_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy[User, int, AccessToken]:
    """Dependency to get a database strategy for fastapi-users."""
    return DatabaseStrategy(access_token_db, lifetime_seconds=settings.session_lifetime)


auth_backend = AuthenticationBackend[User, int](
    name="db_bearer",
    transport=BearerTransport(tokenUrl="auth/login"),
    get_strategy=get_db_strategy,
)

_fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_user = _fastapi_users.current_user()
current_user_optional = _fastapi_users.current_user(optional=True)


def _claimize(user: User) -> AccessTokenClaim:
    """Get a claim from a full user."""
    return AccessTokenClaim(
        user_id=user.id,
        account_is_company=user.user_type == UserType.COMPANY,
        account_is_platform_admin=user.is_platform_admin,
    )


async def get_token_claim(
    user: User = Depends(current_user),
) -> AccessTokenClaim:
    """Use as a dependency to get the token claim from the request."""
    return _claimize(user)


async def get_token_claim_optional(
    user: User | None = Depends(current_user_optional),
) -> AccessTokenClaim | None:
    """Gets a token claim if there is one."""
    return _claimize(user) if user else None


login_router = _fastapi_users.get_auth_router(auth_backend)
