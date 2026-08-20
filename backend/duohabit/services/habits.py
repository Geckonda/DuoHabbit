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
from duohabit.models.habits import Habit, HabitType, HabitCheck


def habit_model_to_schema(habit_model: Habit, checks: list[HabitCheck] | None = None) -> HabitRead | HabitWithChecks:
    if checks:
        return HabitWithChecks(
            title=habit_model.title,
            description=habit_model.description,
            is_active=habit_model.is_active,
            is_private=habit_model.is_private,
            habit_type=HabitType(habit_model.habit_type),
            id=habit_model.id,
            user_id=habit_model.user_id,
            current_streak=habit_model.current_streak,
            recent_checks=checks
        )
    else:
        return HabitRead(
            id=habit_model.id,
            user_id=habit_model.user_id,
            title=habit_model.title,
            description=habit_model.description,
            is_active=habit_model.is_active,
            is_private=habit_model.is_private,
            habit_type=HabitType(habit_model.habit_type),
            current_streak=habit_model.current_streak
        )


def habit_check_model_to_schema(habit_check_model: HabitCheck) -> HabitCheckRead:
    return HabitCheckRead(
        habit_id=habit_check_model.habit_id,
        check_date=habit_check_model.check_date,
        id=habit_check_model.id,
        created_at=habit_check_model.created_at
    )


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
    
    await repo.commit()

    return habit_model_to_schema(habit)


async def get_user_habits(
    repo: HabitRepository,
    user_id: int,
    only_active: bool = True
) -> list[HabitRead]:
    """Get all habits for a user."""
    habits = await repo.get_by_user(user_id, only_active=only_active)
    return [habit_model_to_schema(h) for h in habits]


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
    
    if habit.user_id != user_id:
        raise Exception("User can show only his habits.")
    
    if with_checks:
        recent_checks = sorted(habit.checks, key=lambda x: x.check_date, reverse=True)[:30]
        checks = [habit_check_model_to_schema(ch) for ch in recent_checks]

        return habit_model_to_schema(habit, checks)
    
    return habit_model_to_schema(habit)


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

    if habit.user_id != user_id:
        raise Exception("User can edit only his habits.")
    
    update_data = habit_data.model_dump(exclude_unset=True)
    updated = await repo.update(habit, **update_data)

    await repo.commit()
    
    return habit_model_to_schema(updated)


async def delete_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> None:
    """Delete a habit."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    if habit.user_id != user_id:
        raise Exception("User can delete only his habits.")
    await repo.delete(habit)
    await repo.commit()


async def archive_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> HabitRead:
    """Archive a habit (soft delete)."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    if habit.user_id != user_id:
        raise Exception("User can archive only his habits.")
    archived = await repo.archive(habit)
    await repo.commit()
    return habit_model_to_schema(archived)


async def restore_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> HabitRead:
    """Restore an archived habit."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    if habit.user_id != user_id:
        raise Exception("User can archive only his habits.")
    restored = await repo.restore(habit)
    await repo.commit()
    return habit_model_to_schema(restored)


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
    
    if habit.user_id != user_id:
        raise Exception("User can check only his habits.")
    
    check = await repo.create_check(habit_id, check_date)
    
    new_streak = await _calculate_streak(repo, habit_id)
    
    if new_streak != habit.current_streak:
        await repo.update(habit, current_streak=new_streak)

    await repo.commit()
    
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
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
    if habit.user_id != user_id:
        raise Exception("User can get only his check habits.")
    
    checks = await repo.get_checks(habit_id, limit)
    return [habit_check_model_to_schema(c) for c in checks]


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

    # Без коммита сессия закроется откатом, и удаление не доедет до базы
    await repo.commit()


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