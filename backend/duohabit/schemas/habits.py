"""Habit schemas."""

from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional


class HabitType(str, Enum):
    """Habit frequency types (должен совпадать с моделью)."""
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class HabitBase(BaseModel):
    """Base habit schema."""
    
    title: str
    description: str | None = None
    is_active: bool = True
    habit_type: HabitType = HabitType.DAILY  # 👈 добавил тип с дефолтом


class HabitCreate(HabitBase):
    """Schema for creating a habit."""
    # title, description, habit_type приходят с фронта
    pass


class HabitUpdate(BaseModel):
    """Schema for updating a habit."""
    
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None
    habit_type: HabitType | None = None  # 👈 можно менять тип


class HabitRead(HabitBase):
    """Schema for reading a habit."""
    
    id: int
    user_id: int
    current_streak: int = 0  # 👈 текущий стрик
    created_at: date | None = None  # 👈 из TimestampMixin
    updated_at: date | None = None  # 👈 из TimestampMixin
    
    class Config:
        from_attributes = True


class HabitCheckBase(BaseModel):
    """Base habit check schema."""
    
    habit_id: int
    check_date: date


class HabitCheckCreate(BaseModel):
    """Schema for creating a habit check."""
    
    habit_id: int
    check_date: date | None = None  # если не указан - сегодня


class HabitCheckRead(HabitCheckBase):
    """Schema for reading a habit check."""
    
    id: int
    created_at: date | None = None
    
    class Config:
        from_attributes = True


class HabitWithChecks(HabitRead):
    """Habit with its last checks."""
    
    recent_checks: list[HabitCheckRead] = []  # последние 30 дней
    total_checks: int = 0
    last_check_date: date | None = None


class HabitStats(BaseModel):
    """Habit statistics."""
    
    habit_id: int
    title: str
    total_checks: int
    current_streak: int
    last_check: date | None
    first_check: date | None
    habit_type: HabitType
    completion_rate: float | None = None  # процент выполнения за последние 30 дней