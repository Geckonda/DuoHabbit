"""Habit repository: Habit, HabitMember (per-participant streak state), HabitCheck."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.models.habits import Habit, HabitCheck, HabitMember


class HabitRepository:
    """Repository for habit, membership, and check operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    # ========== HABIT METHODS ==========

    async def create(
        self,
        creator_id: int,
        title: str,
        description: str | None,
        habit_type: str,
        allowed_misses: int = 0,
        group_id: int | None = None,
    ) -> Habit:
        """Create a new habit, personal (group_id=None) or belonging to a group."""
        habit = Habit(
            group_id=group_id,
            creator_id=creator_id,
            title=title,
            description=description,
            habit_type=habit_type,
            allowed_misses=allowed_misses,
            is_active=True,
        )
        self._session.add(habit)
        await self._session.flush()
        await self._session.refresh(habit)
        return habit

    async def get_by_id(self, habit_id: int) -> Habit | None:
        """Get a habit by id."""
        stmt = select(Habit).where(Habit.id == habit_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_group(
        self, group_id: int, only_active: bool = True
    ) -> list[Habit]:
        """Get all habits belonging to a group."""
        stmt = select(Habit).where(Habit.group_id == group_id)
        if only_active:
            stmt = stmt.where(Habit.is_active == True)
        stmt = stmt.order_by(Habit.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_personal_habits(
        self, user_id: int, only_active: bool = True
    ) -> list[Habit]:
        """Get personal (group_id is None) habits owned by a user."""
        stmt = select(Habit).where(
            Habit.group_id.is_(None), Habit.creator_id == user_id
        )
        if only_active:
            stmt = stmt.where(Habit.is_active == True)
        stmt = stmt.order_by(Habit.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, habit: Habit, **kwargs: Any) -> Habit:
        """Update habit fields."""
        kwargs.pop("group_id", None)
        kwargs.pop("creator_id", None)
        kwargs.pop("habit_type", None)
        for key, value in kwargs.items():
            if hasattr(habit, key):
                setattr(habit, key, value)
        await self._session.flush()
        await self._session.refresh(habit)
        return habit

    async def delete(self, habit: Habit) -> None:
        """Delete a habit (cascades to members and checks)."""
        await self._session.delete(habit)
        await self._session.flush()

    async def archive(self, habit: Habit) -> Habit:
        """Archive a habit (soft delete)."""
        habit.is_active = False
        await self._session.flush()
        await self._session.refresh(habit)
        return habit

    async def restore(self, habit: Habit) -> Habit:
        """Restore an archived habit."""
        habit.is_active = True
        await self._session.flush()
        await self._session.refresh(habit)
        return habit

    # ========== HABIT MEMBER METHODS ==========

    async def add_member(
        self,
        habit_id: int,
        user_id: int,
        misses_remaining: int,
        last_resolved_period_key: str,
    ) -> HabitMember:
        """Create a fresh per-member streak row (new join, or first member of a personal habit)."""
        member = HabitMember(
            habit_id=habit_id,
            user_id=user_id,
            current_streak=0,
            misses_remaining=misses_remaining,
            last_resolved_period_key=last_resolved_period_key,
            is_active=True,
        )
        self._session.add(member)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError("User already participates in this habit") from exc
        await self._session.refresh(member)
        return member

    async def get_member(self, habit_id: int, user_id: int) -> HabitMember | None:
        """Get a (possibly inactive) member row for a user on a habit."""
        stmt = select(HabitMember).where(
            HabitMember.habit_id == habit_id, HabitMember.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_members(self, habit_id: int) -> list[HabitMember]:
        """List active member-streak rows for a habit."""
        stmt = select(HabitMember).where(
            HabitMember.habit_id == habit_id, HabitMember.is_active == True
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_min_active_streak(self, habit_id: int) -> int:
        """The habit's displayed streak: MIN(current_streak) over active members (0 if none)."""
        stmt = select(func.min(HabitMember.current_streak)).where(
            HabitMember.habit_id == habit_id, HabitMember.is_active == True
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return int(value) if value is not None else 0

    async def update_member(self, member: HabitMember, **kwargs: Any) -> HabitMember:
        """Update a member's streak/grace fields."""
        kwargs.pop("habit_id", None)
        kwargs.pop("user_id", None)
        for key, value in kwargs.items():
            if hasattr(member, key):
                setattr(member, key, value)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def deactivate_member(
        self, member: HabitMember, removed_at: datetime
    ) -> HabitMember:
        """Soft-remove a member's participation (they left/were removed from the group)."""
        member.is_active = False
        member.removed_at = removed_at
        await self._session.flush()
        await self._session.refresh(member)
        return member

    # ========== CHECK METHODS ==========

    async def create_check(
        self, habit_id: int, user_id: int, check_date: date, period_key: str
    ) -> HabitCheck:
        """Record a member's check-in for a period."""
        check = HabitCheck(
            habit_id=habit_id,
            user_id=user_id,
            check_date=check_date,
            period_key=period_key,
        )
        self._session.add(check)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError("Already checked in for this period") from exc
        await self._session.refresh(check)
        return check

    async def get_check(
        self, habit_id: int, user_id: int, period_key: str
    ) -> HabitCheck | None:
        """Get a specific member's check for a period, if any."""
        stmt = select(HabitCheck).where(
            HabitCheck.habit_id == habit_id,
            HabitCheck.user_id == user_id,
            HabitCheck.period_key == period_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_checks_for_habit_period(
        self, habit_id: int, period_key: str
    ) -> list[HabitCheck]:
        """Get all members' checks recorded for a period of a habit."""
        stmt = select(HabitCheck).where(
            HabitCheck.habit_id == habit_id, HabitCheck.period_key == period_key
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_checks_for_user(
        self, habit_id: int, user_id: int, limit: int = 30
    ) -> list[HabitCheck]:
        """Get a member's recent checks for a habit."""
        stmt = (
            select(HabitCheck)
            .where(HabitCheck.habit_id == habit_id, HabitCheck.user_id == user_id)
            .order_by(HabitCheck.check_date.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
