"""Habit API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from duohabit.db import get_session
from duohabit.models.users import User
from duohabit.repositories.habits import HabitRepository
from duohabit.schemas.habits import (
    HabitCreate, 
    HabitUpdate, 
    HabitRead,
    HabitCheckRead,
    HabitWithChecks,
    HabitStats
)
from duohabit.services.habits import (
    create_habit,
    get_habit,
    update_habit,
    archive_habit,
    get_habit_checks,
    get_habit_stats,
    get_user_habits,
    restore_habit,
    delete_check,
    delete_habit,
    check_habit
)
from duohabit.auth import get_token_claim
from duohabit.schemas.auth import AccessTokenClaim

habits_router = APIRouter(prefix="/habits", tags=["Habits"])


@habits_router.post("", response_model=HabitRead)
async def create_habit_endpoint(
    habit_data: HabitCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Create a new habit."""
    return await create_habit(
        repo=HabitRepository(session),
        user_id=token_claim.user_id,
        habit_data=habit_data
    )


@habits_router.get("", response_model=list[HabitRead])
async def get_habits_endpoint(
    only_active: bool = Query(True, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Get all habits for current user."""
    return await get_user_habits(
        repo=HabitRepository(session),
        user_id=token_claim.user_id,
        only_active=only_active
    )


@habits_router.get("/{habit_id}", response_model=HabitRead)
async def get_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Get a specific habit."""
    return await get_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id
    )


@habits_router.get("/{habit_id}/details", response_model=HabitWithChecks)
async def get_habit_with_checks_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Get a specific habit with its recent checks."""
    return await get_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
        with_checks=True
    )


@habits_router.patch("/{habit_id}", response_model=HabitRead)
async def update_habit_endpoint(
    habit_id: int,
    habit_data: HabitUpdate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Update a habit."""
    return await update_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
        habit_data=habit_data
    )


@habits_router.delete("/{habit_id}", status_code=204)
async def delete_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Delete a habit permanently."""
    await delete_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id
    )


# ========== ARCHIVE / RESTORE ==========

@habits_router.post("/{habit_id}/archive", response_model=HabitRead)
async def archive_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Archive a habit (soft delete)."""
    return await archive_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id
    )


@habits_router.post("/{habit_id}/restore", response_model=HabitRead)
async def restore_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Restore an archived habit."""
    return await restore_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id
    )


# ========== HABIT CHECKS ==========

@habits_router.post("/{habit_id}/check")
async def check_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Mark habit as done for today or specific date."""
    return await check_habit(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id
    )


@habits_router.get("/{habit_id}/checks", response_model=list[HabitCheckRead])
async def get_habit_checks_endpoint(
    habit_id: int,
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Get last N checks for a habit."""
    return await get_habit_checks(
        repo=HabitRepository(session),
        habit_id=habit_id,
        user_id=token_claim.user_id,
        limit=limit
    )


@habits_router.delete("/checks/{check_id}", status_code=204)
async def delete_check_endpoint(
    check_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim)
):
    """Delete a specific check."""
    await delete_check(
        repo=HabitRepository(session),
        check_id=check_id,
        user_id=token_claim.user_id
    )


# ========== STATISTICS ==========

# @habits_router.get("/{habit_id}/stats", response_model=HabitStats)
# async def get_habit_stats_endpoint(
#     habit_id: int,
#     session: AsyncSession = Depends(get_session),
#     user: User = Depends(current_user)
# ):
#     """Get detailed statistics for a habit."""
#     repo = HabitRepository(session)
#     try:
#         return await habits_service.get_habit_stats(repo, habit_id, user.id)
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=str(e))


# @habits_router.get("/{habit_id}/completion-rate")
# async def get_completion_rate_endpoint(
#     habit_id: int,
#     days: int = Query(30, ge=7, le=365),
#     session: AsyncSession = Depends(get_session),
#     user: User = Depends(current_user)
# ):
#     """Get habit completion rate for last N days."""
#     repo = HabitRepository(session)
#     try:
#         # Проверяем доступ
#         habit = await repo.get_by_id(habit_id, user.id)
#         if not habit:
#             raise HTTPException(status_code=404, detail="Habit not found")
        
#         rate = await repo.get_completion_rate(habit_id, days)
#         return {
#             "habit_id": habit_id,
#             "days": days,
#             "completion_rate": round(rate, 2),
#             "habit_type": habit.habit_type.value
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))