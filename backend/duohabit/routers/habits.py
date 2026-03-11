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
from duohabit.services import habits as habits_service
from duohabit.auth import current_user

habits_router = APIRouter(prefix="/habits", tags=["Habits"])


# ========== BASIC CRUD ==========

@habits_router.post("", response_model=HabitRead)
async def create_habit_endpoint(
    habit_data: HabitCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Create a new habit."""
    repo = HabitRepository(session)
    return await habits_service.create_habit(repo, user.id, habit_data)


@habits_router.get("", response_model=list[HabitRead])
async def get_habits_endpoint(
    only_active: bool = Query(True, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get all habits for current user."""
    repo = HabitRepository(session)
    return await habits_service.get_user_habits(repo, user.id, only_active=only_active)


@habits_router.get("/{habit_id}", response_model=HabitRead)
async def get_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get a specific habit."""
    repo = HabitRepository(session)
    try:
        return await habits_service.get_habit(repo, habit_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@habits_router.get("/{habit_id}/details", response_model=HabitWithChecks)
async def get_habit_with_checks_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get a specific habit with its recent checks."""
    repo = HabitRepository(session)
    try:
        return await habits_service.get_habit(repo, habit_id, user.id, with_checks=True)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@habits_router.patch("/{habit_id}", response_model=HabitRead)
async def update_habit_endpoint(
    habit_id: int,
    habit_data: HabitUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Update a habit."""
    repo = HabitRepository(session)
    try:
        return await habits_service.update_habit(repo, habit_id, user.id, habit_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@habits_router.delete("/{habit_id}", status_code=204)
async def delete_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Delete a habit permanently."""
    repo = HabitRepository(session)
    try:
        await habits_service.delete_habit(repo, habit_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== ARCHIVE / RESTORE ==========

@habits_router.post("/{habit_id}/archive", response_model=HabitRead)
async def archive_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Archive a habit (soft delete)."""
    repo = HabitRepository(session)
    try:
        return await habits_service.archive_habit(repo, habit_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@habits_router.post("/{habit_id}/restore", response_model=HabitRead)
async def restore_habit_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Restore an archived habit."""
    repo = HabitRepository(session)
    try:
        return await habits_service.restore_habit(repo, habit_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== HABIT CHECKS ==========

@habits_router.post("/{habit_id}/check")
async def check_habit_endpoint(
    habit_id: int,
    check_date: date | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Mark habit as done for today or specific date."""
    repo = HabitRepository(session)
    try:
        result = await habits_service.check_habit(
            repo, habit_id, user.id, check_date
        )
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@habits_router.get("/{habit_id}/checks", response_model=list[HabitCheckRead])
async def get_habit_checks_endpoint(
    habit_id: int,
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get last N checks for a habit."""
    repo = HabitRepository(session)
    try:
        return await habits_service.get_habit_checks(repo, habit_id, user.id, limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@habits_router.delete("/checks/{check_id}", status_code=204)
async def delete_check_endpoint(
    check_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Delete a specific check."""
    repo = HabitRepository(session)
    try:
        await habits_service.delete_check(repo, check_id, user.id)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== STATISTICS ==========

@habits_router.get("/{habit_id}/stats", response_model=HabitStats)
async def get_habit_stats_endpoint(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get detailed statistics for a habit."""
    repo = HabitRepository(session)
    try:
        return await habits_service.get_habit_stats(repo, habit_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@habits_router.get("/{habit_id}/completion-rate")
async def get_completion_rate_endpoint(
    habit_id: int,
    days: int = Query(30, ge=7, le=365),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get habit completion rate for last N days."""
    repo = HabitRepository(session)
    try:
        # Проверяем доступ
        habit = await repo.get_by_id(habit_id, user.id)
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        rate = await repo.get_completion_rate(habit_id, days)
        return {
            "habit_id": habit_id,
            "days": days,
            "completion_rate": round(rate, 2),
            "habit_type": habit.habit_type.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))