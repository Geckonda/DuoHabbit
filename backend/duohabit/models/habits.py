"""Habit models."""

from datetime import date
from enum import Enum
from sqlalchemy import Date, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin


class HabitType(str, Enum):
    """Habit frequency types."""
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Habit(TimestampMixin, Base):
    """User habit model."""
    
    __tablename__ = "habit"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 👇 ПРОСТО STRING (в базе будет 'daily', 'weekly' и т.д.)
    habit_type: Mapped[str] = mapped_column(
        String(20), 
        default=HabitType.DAILY.value,
        nullable=False
    )

    current_streak: Mapped[int] = mapped_column(Integer, default=0)

    checks: Mapped[list["HabitCheck"]] = relationship(
        back_populates="habit", 
        cascade="all, delete-orphan"
    )


class HabitCheck(TimestampMixin, Base):
    """Record of habit completion for a specific day."""
    
    __tablename__ = "habit_check"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habit.id", ondelete="CASCADE"))
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    habit: Mapped["Habit"] = relationship(back_populates="checks")
    
    __table_args__ = (UniqueConstraint('habit_id', 'check_date', name='uq_habit_check'),)