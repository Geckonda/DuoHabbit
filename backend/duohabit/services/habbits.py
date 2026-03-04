"""Habit business logic."""

from duohabit.repositories.habits import HabitRepository
from duohabit.schemas.habits import HabitCreate, HabitUpdate, HabitRead


async def create_habit(
    repo: HabitRepository,
    user_id: int,
    habit_data: HabitCreate
) -> HabitRead:
    """Create a new habit."""
    habit = await repo.create(
        user_id=user_id,
        title=habit_data.title,
        description=habit_data.description
    )
    return HabitRead.model_validate(habit)


async def get_user_habits(
    repo: HabitRepository,
    user_id: int
) -> list[HabitRead]:
    """Get all habits for a user."""
    habits = await repo.get_by_user(user_id)
    return [HabitRead.model_validate(h) for h in habits]


async def get_habit(
    repo: HabitRepository,
    habit_id: int,
    user_id: int
) -> HabitRead:
    """Get a specific habit."""
    habit = await repo.get_by_id(habit_id, user_id)
    if not habit:
        raise Exception("Habit not found")
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