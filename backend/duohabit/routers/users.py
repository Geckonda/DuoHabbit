"""Users endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import (
    get_token_claim,
    get_token_claim_optional,
    get_user_manager,
)
from duohabit.db import get_session
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.users import UserCreate, UserOut, UserSelfUpdate, UserUpdate
from duohabit.schemas.common import PaginationParams
from duohabit.services.users import (
    UserManager,
    create_user,
    get_user,
    get_users,
    update_user,
)

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/", response_model=list[UserOut], response_model_exclude_none=True)
async def get_users_endpoint(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim | None = Depends(get_token_claim_optional),
) -> list[UserOut]:
    """
    Get all users.
    Authenticated users can get any users.
    Unauthenticated users will only receive company profiles on the platform.
    Supports pagination with offset and limit query parameters.
    """
    return await get_users(UsersRepository(session), token_claim, pagination)


@users_router.get("/me", response_model=UserOut, response_model_exclude_none=True)
async def get_current_user_endpoint(
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> UserOut:
    """
    Get the currently authenticated user's profile.
    Requires authentication.
    """
    return await get_user(UsersRepository(session), token_claim.user_id, token_claim)


@users_router.patch("/me", response_model=UserOut, response_model_exclude_none=True)
async def update_current_user_endpoint(
    user_in: UserSelfUpdate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
    manager: UserManager = Depends(get_user_manager),
) -> UserOut:
    """
    Update the currently authenticated user's own profile (username, timezone only).
    Requires authentication. Cannot change email, password, or admin status here.
    """
    update_data = user_in.model_dump(exclude_unset=True)
    return await update_user(
        UsersRepository(session),
        token_claim.user_id,
        UserUpdate(**update_data),
        token_claim,
        manager,
    )


@users_router.get(
    "/{user_id}", response_model=UserOut, response_model_exclude_none=True
)
async def get_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim | None = Depends(get_token_claim_optional),
) -> UserOut:
    """
    Get a single user by ID.
    Authenticated users can get any users.
    Unauthenticated users can only get company profiles.
    """
    return await get_user(UsersRepository(session), user_id, token_claim)


@users_router.post("/", status_code=201, response_model=UserOut)
async def create_user_endpoint(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim | None = Depends(get_token_claim_optional),
    manager: UserManager = Depends(get_user_manager),
) -> UserOut:
    """
    Register a new user.
    No authentication required to create a non-admin user,
    but required with admin privileges to create an admin user.
    Fails if the email is already in use.
    """
    return await create_user(
        UsersRepository(session),
        user_in,
        None if token_claim is None else token_claim.account_is_platform_admin,
        manager,
    )