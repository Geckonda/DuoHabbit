"""Habit models: a single unified engine for both personal and group habits.

A personal habit is just a Habit with group_id=None and exactly one HabitMember (its creator).
A group habit has group_id set and one HabitMember per active GroupMember of that group. Each
HabitMember tracks its own streak/grace independently, in that member's own timezone -- the
habit's displayed streak is derived as MIN(current_streak) over its active members.
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from duohabit.models.groups import Group


class HabitType(str, Enum):
    """Habit frequency types."""

    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Habit(TimestampMixin, Base):
    """A trackable habit. Personal (group_id is None) or shared by a group."""

    __tablename__ = "habit"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("habit_group.id", ondelete="CASCADE")
    )
    creator_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)

    habit_type: Mapped[str] = mapped_column(
        String(20),
        default=HabitType.DAILY.value,
        nullable=False,
    )

    allowed_misses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    group: Mapped["Group | None"] = relationship(back_populates="habits")
    members: Mapped[list["HabitMember"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )
    checks: Mapped[list["HabitCheck"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )


class HabitMember(TimestampMixin, Base):
    """One participant's independent streak/grace state for a habit."""

    __tablename__ = "habit_member"

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habit.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    misses_remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_resolved_period_key: Mapped[str | None] = mapped_column(String(20))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    habit: Mapped["Habit"] = relationship(back_populates="members")

    __table_args__ = (UniqueConstraint("habit_id", "user_id", name="uq_habit_member"),)


class HabitCheck(TimestampMixin, Base):
    """Record of one member's completion of a habit for a specific period."""

    __tablename__ = "habit_check"

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habit.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)

    habit: Mapped["Habit"] = relationship(back_populates="checks")

    __table_args__ = (
        UniqueConstraint(
            "habit_id", "user_id", "period_key", name="uq_habit_check_period"
        ),
    )
