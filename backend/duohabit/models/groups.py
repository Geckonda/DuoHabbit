"""Group models: cooperative group habits shared by 2-10 members."""

from datetime import date, datetime
from enum import Enum

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
from duohabit.models.habits import HabitType
from duohabit.models.mixins import TimestampMixin


class GroupRole(str, Enum):
    """Role of a member within a group."""

    OWNER = "owner"
    MEMBER = "member"


class JoinMethod(str, Enum):
    """How a member ended up in a group."""

    INVITE_CODE = "invite_code"
    ADDED_BY_OWNER = "added_by_owner"


class Group(TimestampMixin, Base):
    """A cooperative group of 2-10 users sharing one GroupHabit."""

    __tablename__ = "habit_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    invite_code: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    members: Mapped[list["GroupMember"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    habit: Mapped["GroupHabit | None"] = relationship(
        back_populates="group", uselist=False, cascade="all, delete-orphan"
    )


class GroupMember(TimestampMixin, Base):
    """Membership of a user in a group."""

    __tablename__ = "group_member"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("habit_group.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(
        String(20), default=GroupRole.MEMBER.value, nullable=False
    )
    join_method: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped["Group"] = relationship(back_populates="members")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)


class GroupHabit(TimestampMixin, Base):
    """The single shared habit a group tracks together."""

    __tablename__ = "group_habit"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("habit_group.id", ondelete="CASCADE"), unique=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    habit_type: Mapped[str] = mapped_column(
        String(20), default=HabitType.DAILY.value, nullable=False
    )

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    allowed_misses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    misses_remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_resolved_period_key: Mapped[str | None] = mapped_column(String(20))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    group: Mapped["Group"] = relationship(back_populates="habit")
    checks: Mapped[list["GroupHabitCheck"]] = relationship(
        back_populates="group_habit", cascade="all, delete-orphan"
    )


class GroupHabitCheck(TimestampMixin, Base):
    """A single member's check-in for one period of the group habit."""

    __tablename__ = "group_habit_check"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_habit_id: Mapped[int] = mapped_column(
        ForeignKey("group_habit.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)

    group_habit: Mapped["GroupHabit"] = relationship(back_populates="checks")

    __table_args__ = (
        UniqueConstraint(
            "group_habit_id",
            "user_id",
            "period_key",
            name="uq_group_habit_check_period",
        ),
    )
