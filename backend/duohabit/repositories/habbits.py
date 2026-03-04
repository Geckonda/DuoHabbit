"""Habit repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.models.habits import Habit


class HabitRepository:
    """Repository for habit operations."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, user_id: int, title: str, description: str | None = None) -> Habit:
        """Create a new habit for user."""
        habit = Habit(
            user_id=user_id,
            title=title,
            description=description
        )
        self._session.add(habit)
        await self._session.flush()
        await self._session.refresh(habit)
        return habit
    
    async def get_by_user(self, user_id: int) -> list[Habit]:
        """Get all habits for a user."""
        stmt = select(Habit).where(Habit.user_id == user_id).order_by(Habit.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id(self, habit_id: int, user_id: int) -> Habit | None:
        """Get a specific habit by ID (scoped to user)."""
        stmt = select(Habit).where(
            Habit.id == habit_id,
            Habit.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update(self, habit: Habit, **kwargs) -> Habit:
        """Update habit fields."""
        for key, value in kwargs.items():
            if hasattr(habit, key):
                setattr(habit, key, value)
        await self._session.flush()
        await self._session.refresh(habit)
        return habit
    
    async def delete(self, habit: Habit) -> None:
        """Delete a habit."""
        await self._session.delete(habit)
        await self._session.flush()