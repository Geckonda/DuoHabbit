"""Habit API routes: personal habits (group habits are also served here by id, see routers/groups.py
for group-scoped listing/creation)."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import get_token_claim
from duohabit.db import get_session
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.habits import (
    HabitCheckinStatus,
    HabitCheckRead,
    HabitCreate,
    HabitRead,
    HabitUpdate,
    HabitWithChecks,
)
from duohabit.services.habits import (
    archive_habit,
    check_in,
    create_habit,
    delete_habit,
    get_checkin_status,
    get_habit,
    get_my_checks,
    get_user_habits,
    restore_habit,
    update_habit,
)

habits_router = APIRouter(prefix="/habits", tags=["Habits"])


@habits_router.post("", response_model=HabitRead)
async def create_habit_endpoint(
    habit_data: HabitCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitRead:
    """Create a new personal habit."""
    return await create_habit(
        repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        user_id=token_claim.user_id,
        habit_data=habit_data,
    )


@habits_router.get("", response_model=list[HabitRead])
async def get_habits_endpoint(
    only_active: bool = Query(True, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[HabitRead]:
    """Get the caller's personal habits (group habits: see GET /groups/{id}/habits)."""
    return await get_user_habits(
        repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        user_id=token_claim.user_id,
        only_active=only_active,
    )


@habits_router.get("/{habit_id}", response_model=HabitRead)
async def get_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitRead:
    """Get a specific habit (personal or group -- any active participant may view)."""
    return await get_habit(
        repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
    )


@habits_router.get("/{habit_id}/details", response_model=HabitWithChecks)
async def get_habit_with_checks_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitWithChecks:
    """Get a specific habit with the caller's recent checks."""
    return await get_habit(
        repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
        with_checks=True,
    )


@habits_router.patch("/{habit_id}", response_model=HabitRead)
async def update_habit_endpoint(
    habit_id: int,
    habit_data: HabitUpdate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitRead:
    """Update a habit (creator only)."""
    return await update_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
        habit_data=habit_data,
    )


@habits_router.delete("/{habit_id}", status_code=204)
async def delete_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Delete a habit permanently (creator only)."""
    await delete_habit(
        repo=HabitRepository(session), habit_id=habit_id, user_id=token_claim.user_id
    )


# ========== ARCHIVE / RESTORE ==========


@habits_router.post("/{habit_id}/archive", response_model=HabitRead)
async def archive_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitRead:
    """Archive a habit (creator only)."""
    return await archive_habit(
        repo=HabitRepository(session), habit_id=habit_id, user_id=token_claim.user_id
    )


@habits_router.post("/{habit_id}/restore", response_model=HabitRead)
async def restore_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitRead:
    """Restore an archived habit (creator only)."""
    return await restore_habit(
        repo=HabitRepository(session), habit_id=habit_id, user_id=token_claim.user_id
    )


# ========== CHECK-INS ==========


@habits_router.post("/{habit_id}/check")
async def check_in_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> dict[str, Any]:
    """Check in on a habit for today, in the caller's own timezone. No backfill."""
    return await check_in(
        repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
    )


@habits_router.get("/{habit_id}/checks", response_model=list[HabitCheckRead])
async def get_habit_checks_endpoint(
    habit_id: int,
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[HabitCheckRead]:
    """Get the caller's last N checks for a habit."""
    return await get_my_checks(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
        limit=limit,
    )


@habits_router.get("/{habit_id}/checks/status", response_model=HabitCheckinStatus)
async def get_checkin_status_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitCheckinStatus:
    """See who has and hasn't checked in for their own current period."""
    return await get_checkin_status(
        repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
    )
