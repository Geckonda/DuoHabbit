"""Habit business logic."""

from datetime import date, timedelta
from sqlalchemy import select
from duohabit.repositories.habits import HabitRepository
from duohabit.schemas.habits import (
    HabitCreate, 
    HabitUpdate, 
    HabitRead,
    HabitCheckCreate,
    HabitCheckRead,
    HabitWithChecks,
    HabitStats,
    HabitType
)
from duohabit.models.habits import HabitCheck


async def create_habit(
    repo: HabitRepository,
    user_id: int,
    habit_data: HabitCreate
) -> HabitRead:
    """Create a new habit."""
    habit = await repo.create(
        user_id=user_id,
        title=habit_data.title,
        description=habit_data.description,
        habit_type=habit_data.habit_type
    )
    return HabitRead.model_validate(habit)


async def get_user_habits(
    repo: HabitRepository,
    user_id: int,
    only_active: bool = True
) -> list[HabitRead]:
    """Get all habits for a user."""
    habits = await repo.get_by_user(user_id, only_active=only_active)
    return [HabitRead.model_validate(h) for h in habits]


async def get_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int,
    with_checks: bool = False
) -> HabitRead | HabitWithChecks:
    """Get a specific habit."""
    habit = await repo.get_by_id(habit_id, user_id, load_checks=with_checks)
    if not habit:
        raise Exception("Habit not found")
    
    if with_checks:
        recent_checks = sorted(habit.checks, key=lambda x: x.check_date, reverse=True)[:30]
        return HabitWithChecks(
            **HabitRead.model_validate(habit).model_dump(),
            recent_checks=[HabitCheckRead.model_validate(c) for c in recent_checks],
            total_checks=len(habit.checks),
            last_check_date=habit.checks[-1].check_date if habit.checks else None
        )
    
    return HabitRead.model_validate(habit)


async def update_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int,
    habit_data: HabitUpdate
) -> HabitRead:
    """Update a habit."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    
    update_data = habit_data.model_dump(exclude_unset=True)
    updated = await repo.update(habit, **update_data)
    return HabitRead.model_validate(updated)


async def delete_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> None:
    """Delete a habit."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    await repo.delete(habit)


async def archive_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> HabitRead:
    """Archive a habit (soft delete)."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    archived = await repo.archive(habit)
    return HabitRead.model_validate(archived)


async def restore_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> HabitRead:
    """Restore an archived habit."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    restored = await repo.restore(habit)
    return HabitRead.model_validate(restored)


# ========== HABIT CHECKS (через тот же репозиторий) ==========

async def check_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int,
    check_date: date | None = None
) -> dict:
    """Mark habit as done for today or specific date."""
    
    # Проверяем привычку
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    
    if not habit.is_active:
        raise Exception("Cannot check archived habit")
    
    # Создаем чек через репозиторий
    try:
        check = await repo.create_check(habit_id, check_date)
    except ValueError as e:
        raise Exception(str(e))
    
    # Пересчитываем стрик
    new_streak = await _calculate_streak(repo, habit_id)
    
    # Обновляем стрик в привычке
    if new_streak != habit.current_streak:
        await repo.update(habit, current_streak=new_streak)
    
    return {
        "checked": True,
        "check_date": check.check_date.isoformat(),
        "current_streak": new_streak,
        "message": f"Streak: {new_streak} days! 🔥"
    }


async def get_habit_checks(
    repo: HabitRepository,
    habit_id: int,
    user_id: int,
    limit: int = 30
) -> list[HabitCheckRead]:
    """Get last N checks for a habit."""
    # Проверяем, что привычка принадлежит юзеру
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    
    checks = await repo.get_checks(habit_id, limit)
    return [HabitCheckRead.model_validate(c) for c in checks]


async def delete_check(
    repo: HabitRepository,
    check_id: int,
    user_id: int
) -> None:
    """Delete a check."""
    # Получаем чек и проверяем доступ
    check = await repo.get_check_by_id(check_id)
    if not check:
        raise Exception("Check not found")
    
    # Проверяем, что привычка принадлежит юзеру
    habit = await repo.get_by_id(check.habit_id, user_id)
    if not habit:
        raise Exception("Access denied")
    
    await repo.delete_check(check_id)
    
    # Пересчитываем стрик
    new_streak = await _calculate_streak(repo, check.habit_id)
    await repo.update(habit, current_streak=new_streak)


# ========== STREAK LOGIC ==========

async def _calculate_streak(
    repo: HabitRepository,
    habit_id: int
) -> int:
    """Calculate current streak for a habit."""
    checks = await repo.get_checks(habit_id, limit=100)
    if not checks:
        return 0
    
    sorted_checks = sorted(checks, key=lambda x: x.check_date, reverse=True)
    
    streak = 0
    current_date = date.today()
    
    for check in sorted_checks:
        if check.check_date == current_date:
            streak += 1
            current_date = current_date - timedelta(days=1)
        else:
            break
    
    return streak


async def get_habit_stats(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> HabitStats:
    """Get detailed statistics for a habit."""
    habit = await repo.get_by_id(habit_id, user_id, load_checks=True)
    if not habit:
        raise Exception("Habit not found")
    
    checks = sorted(habit.checks, key=lambda x: x.check_date)
    
    if checks:
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_checks = [c for c in checks if c.check_date >= thirty_days_ago]
        
        if habit.habit_type == HabitType.DAILY:
            expected = 30
        elif habit.habit_type == HabitType.WEEKDAYS:
            expected = 22
        elif habit.habit_type == HabitType.WEEKLY:
            expected = 4
        else:  # MONTHLY
            expected = 1
        
        completion_rate = (len(recent_checks) / expected) * 100 if expected > 0 else 0
    else:
        completion_rate = 0
    
    return HabitStats(
        habit_id=habit.id,
        title=habit.title,
        total_checks=len(checks),
        current_streak=habit.current_streak,
        last_check=checks[-1].check_date if checks else None,
        first_check=checks[0].check_date if checks else None,
        habit_type=habit.habit_type,
        completion_rate=round(completion_rate, 2)
    )