"""Habit API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.db import get_session
from duohabit.models.users import User
from duohabit.repositories.habits import HabitRepository
from duohabit.schemas.habits import HabitCreate, HabitUpdate, HabitRead
from duohabit.services import habits as habits_service
from duohabit.auth import current_user

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("", response_model=HabitRead)
async def create_habit(
    habit_data: HabitCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Create a new habit."""
    repo = HabitRepository(session)
    return await habits_service.create_habit(repo, user.id, habit_data)


@router.get("", response_model=list[HabitRead])
async def get_habits(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Get all habits for current user."""
    repo = HabitRepository(session)
    return await habits_service.get_user_habits(repo, user.id)


@router.get("/{habit_id}", response_model=HabitRead)
async def get_habit(
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


@router.patch("/{habit_id}", response_model=HabitRead)
async def update_habit(
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


@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user)
):
    """Delete a habit."""
    repo = HabitRepository(session)
    try:
        await habits_service.delete_habit(repo, habit_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))