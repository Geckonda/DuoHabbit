"""Group models: a thin social container (name, invite code, roster) for shared habits.

Group and GroupMember hold membership only. Streak/grace state lives entirely on
HabitMember (see models/habits.py) -- a group can share any number of habits, and joining/
leaving a group is orchestrated by services/groups.py to keep each habit's HabitMember rows
in sync with the roster.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from duohabit.models.habits import Habit


class GroupRole(str, Enum):
    """Role of a member within a group."""

    OWNER = "owner"
    MEMBER = "member"


class JoinMethod(str, Enum):
    """How a member ended up in a group."""

    INVITE_CODE = "invite_code"
    ADDED_BY_OWNER = "added_by_owner"


class MemberStatus(str, Enum):
    """Whether a membership row is waiting on someone's response or is real membership."""

    PENDING = "pending"
    ACCEPTED = "accepted"


class Group(TimestampMixin, Base):
    """A cooperative group of up to 5 users sharing any number of habits."""

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
    habits: Mapped[list["Habit"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
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
    # Кто должен согласиться, зависит от join_method: ADDED_BY_OWNER -> сам user_id,
    # INVITE_CODE -> владелец группы. Пока pending, is_active=False - невидимо
    # во всех существующих выборках без единой правки на их стороне
    status: Mapped[str] = mapped_column(
        String(20), default=MemberStatus.ACCEPTED.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped["Group"] = relationship(back_populates="members")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)
