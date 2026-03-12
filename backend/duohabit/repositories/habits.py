"""Habit repository."""

from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from duohabit.models.habits import Habit, HabitCheck, HabitType


class HabitRepository:
    """Repository for habit operations."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
    
    async def create(
        self, 
        user_id: int, 
        title: str, 
        description: str | None = None,
        habit_type: HabitType = HabitType.DAILY
    ) -> Habit:
        """Create a new habit for user."""
        habit = Habit(
            user_id=user_id,
            title=title,
            description=description,
            habit_type=habit_type,
            current_streak=0,
            is_active=True
        )
        self._session.add(habit)
        await self._session.flush()
        await self._session.refresh(habit)
        return habit
    
    async def get_by_user(
        self, 
        user_id: int, 
        only_active: bool = True
    ) -> list[Habit]:
        """Get all habits for a user."""
        stmt = select(Habit).where(Habit.user_id == user_id)
        
        if only_active:
            stmt = stmt.where(Habit.is_active == True)
            
        stmt = stmt.order_by(Habit.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id(
        self, 
        habit_id: int, 
        user_id: int,
        load_checks: bool = False
    ) -> Habit | None:
        """Get a specific habit by ID (scoped to user)."""
        stmt = select(Habit).where(
            Habit.id == habit_id,
            Habit.user_id == user_id
        )
        
        if load_checks:
            stmt = stmt.options(selectinload(Habit.checks))
            
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update(self, habit: Habit, **kwargs) -> Habit:
        """Update habit fields."""
        kwargs.pop('user_id', None)
        
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
    
    async def archive(self, habit: Habit) -> Habit:
        """Archive habit (soft delete)."""
        habit.is_active = False
        await self._session.flush()
        await self._session.refresh(habit)
        return habit
    
    async def restore(self, habit: Habit) -> Habit:
        """Restore archived habit."""
        habit.is_active = True
        await self._session.flush()
        await self._session.refresh(habit)
        return habit
    
    # ========== CHECK METHODS ==========
    
    async def create_check(
        self, 
        habit_id: int, 
        check_date: date | None = None
    ) -> HabitCheck:
        """Create a new habit check."""
        if check_date is None:
            check_date = date.today()
        
        # Проверяем, нет ли уже чека на эту дату
        existing = await self.get_check_by_date(habit_id, check_date)
        if existing:
            raise ValueError(f"Check for {check_date} already exists")
        
        check = HabitCheck(
            habit_id=habit_id,
            check_date=check_date
        )
        self._session.add(check)
        await self._session.flush()
        await self._session.refresh(check)
        return check
    
    async def get_check_by_id(self, check_id: int) -> HabitCheck | None:
        """Get a specific check by ID."""
        stmt = select(HabitCheck).where(HabitCheck.id == check_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_check_by_date(
        self, 
        habit_id: int, 
        check_date: date
    ) -> HabitCheck | None:
        """Get check for specific habit and date."""
        stmt = select(HabitCheck).where(
            HabitCheck.habit_id == habit_id,
            HabitCheck.check_date == check_date
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_checks(
        self, 
        habit_id: int, 
        limit: int = 30,
        offset: int = 0
    ) -> list[HabitCheck]:
        """Get checks for a habit with pagination."""
        stmt = select(HabitCheck).where(
            HabitCheck.habit_id == habit_id
        ).order_by(
            HabitCheck.check_date.desc()
        ).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_checks_in_range(
        self,
        habit_id: int,
        start_date: date,
        end_date: date
    ) -> list[HabitCheck]:
        """Get checks for a habit within date range."""
        stmt = select(HabitCheck).where(
            HabitCheck.habit_id == habit_id,
            HabitCheck.check_date >= start_date,
            HabitCheck.check_date <= end_date
        ).order_by(HabitCheck.check_date)
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_check(self, check_id: int) -> None:
        """Delete a specific check."""
        check = await self.get_check_by_id(check_id)
        if check:
            await self._session.delete(check)
            await self._session.flush()
    
    async def delete_checks_by_habit(self, habit_id: int) -> None:
        """Delete all checks for a habit."""
        stmt = select(HabitCheck).where(HabitCheck.habit_id == habit_id)
        result = await self._session.execute(stmt)
        checks = result.scalars().all()
        
        for check in checks:
            await self._session.delete(check)
        
        await self._session.flush()
    
    # ========== STATS METHODS ==========
    
    async def get_stats(self, habit_id: int, user_id: int) -> dict:
        """Get habit statistics."""
        habit = await self.get_by_id(habit_id, user_id, load_checks=True)
        if not habit:
            return {}
        
        checks = sorted(habit.checks, key=lambda x: x.check_date)
        
        return {
            'total_checks': len(checks),
            'current_streak': habit.current_streak,
            'last_check': checks[-1].check_date if checks else None,
            'first_check': checks[0].check_date if checks else None,
            'habit_type': habit.habit_type.value
        }
    
    async def get_completion_rate(
        self,
        habit_id: int,
        days: int = 30
    ) -> float:
        """Get completion rate for last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        checks = await self.get_checks_in_range(habit_id, start_date, end_date)
        
        # Получаем привычку для определения типа
        stmt = select(Habit).where(Habit.id == habit_id)
        result = await self._session.execute(stmt)
        habit = result.scalar_one_or_none()
        
        if not habit:
            return 0.0
        
        # Расчет ожидаемого количества дней в зависимости от типа
        if habit.habit_type == HabitType.DAILY:
            expected = days
        elif habit.habit_type == HabitType.WEEKDAYS:
            # Подсчет рабочих дней (пн-пт) в диапазоне
            expected = sum(
                1 for i in range(days) 
                if (start_date + timedelta(days=i)).weekday() < 5
            )
        elif habit.habit_type == HabitType.WEEKLY:
            expected = days // 7
        else:  # MONTHLY
            expected = days // 30
        
        return (len(checks) / expected) * 100 if expected > 0 else 0