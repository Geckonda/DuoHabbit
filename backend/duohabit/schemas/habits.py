"""Habit schemas: shared by personal habits (group_id=None) and group habits."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel


class HabitType(str, Enum):
    """Habit frequency types (should match the model)."""

    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class HabitBase(BaseModel):
    """Base habit schema."""

    title: str
    description: str | None = None
    is_private: bool = True
    habit_type: HabitType = HabitType.DAILY
    allowed_misses: int = 0


class HabitCreate(HabitBase):
    """Schema for creating a personal habit (group habits go through /groups/{id}/habits)."""


class HabitUpdate(BaseModel):
    """Schema for updating a habit."""

    title: str | None = None
    description: str | None = None
    is_active: bool | None = None
    is_private: bool | None = None
    allowed_misses: int | None = None


class HabitRead(BaseModel):
    """Schema for reading a habit.

    current_streak is the team-honest number: MIN(current_streak) over active members (for a
    personal habit this is just the one member's own streak). my_current_streak/
    my_misses_remaining are the caller's own numbers, useful when the two diverge in a group.
    """

    id: int
    group_id: int | None
    creator_id: int
    title: str
    description: str | None = None
    is_active: bool
    is_private: bool
    habit_type: HabitType
    allowed_misses: int
    current_streak: int = 0
    member_count: int = 1
    my_current_streak: int = 0
    my_misses_remaining: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class HabitCheckRead(BaseModel):
    """Schema for reading a habit check."""

    id: int
    habit_id: int
    user_id: int
    check_date: date
    period_key: str

    class Config:
        from_attributes = True


class HabitWithChecks(HabitRead):
    """Habit with the caller's recent checks."""

    recent_checks: list[HabitCheckRead] = []


class HabitCheckinStatus(BaseModel):
    """Who has and hasn't checked in for their own current period (meaningful mainly for groups).

    There is no single shared period_key here: each member's "current period" is evaluated in
    their own timezone, so two members can legitimately be in different calendar days at once.
    """

    total_active_members: int
    checked_in_user_ids: list[int]
    missing_user_ids: list[int]
    all_done: bool
