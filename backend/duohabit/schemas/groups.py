"""Group schemas."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel

from duohabit.schemas.habits import HabitType


class GroupRole(str, Enum):
    """Role of a member within a group (должен совпадать с моделью)."""

    OWNER = "owner"
    MEMBER = "member"


class JoinMethod(str, Enum):
    """How a member ended up in a group (должен совпадать с моделью)."""

    INVITE_CODE = "invite_code"
    ADDED_BY_OWNER = "added_by_owner"


# ========== GROUP ==========


class GroupBase(BaseModel):
    """Base group schema."""

    name: str


class GroupCreate(GroupBase):
    """Schema for creating a group together with its single shared habit."""

    habit_title: str
    habit_description: str | None = None
    habit_type: HabitType = HabitType.DAILY
    allowed_misses: int = 0


class GroupUpdate(BaseModel):
    """Schema for renaming a group."""

    name: str | None = None


class GroupRead(GroupBase):
    """Schema for reading a group."""

    id: int
    owner_id: int
    invite_code: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ========== GROUP HABIT ==========


class GroupHabitBase(BaseModel):
    """Base group-habit schema."""

    title: str
    description: str | None = None
    habit_type: HabitType = HabitType.DAILY
    allowed_misses: int = 0


class GroupHabitUpdate(BaseModel):
    """Schema for updating a group habit (habit_type is intentionally not editable)."""

    title: str | None = None
    description: str | None = None
    allowed_misses: int | None = None


class GroupHabitRead(GroupHabitBase):
    """Schema for reading a group habit."""

    id: int
    group_id: int
    current_streak: int = 0
    misses_remaining: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True


class GroupWithHabit(GroupRead):
    """Group enriched with its habit and member count."""

    habit: GroupHabitRead | None = None
    member_count: int = 0


# ========== MEMBERS ==========


class GroupMemberBase(BaseModel):
    """Base group-member schema."""

    user_id: int
    role: GroupRole
    join_method: JoinMethod


class GroupMemberRead(GroupMemberBase):
    """Schema for reading a group member."""

    id: int
    group_id: int
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class GroupMemberWithUser(GroupMemberRead):
    """Group member enriched with the user's username."""

    username: str


class GroupMemberAdd(BaseModel):
    """Schema for the owner directly adding a member."""

    user_id: int


class GroupInviteJoin(BaseModel):
    """Schema for joining a group by invite code."""

    invite_code: str


# ========== CHECKS ==========


class GroupHabitCheckCreate(BaseModel):
    """Schema for checking in on the group habit (always the current period)."""

    check_date: date | None = None


class GroupHabitCheckRead(BaseModel):
    """Schema for reading a group habit check."""

    id: int
    group_habit_id: int
    user_id: int
    check_date: date
    period_key: str

    class Config:
        from_attributes = True


class GroupCheckinStatus(BaseModel):
    """Who has and hasn't checked in for the current period."""

    period_key: str
    total_active_members: int
    checked_in_user_ids: list[int]
    missing_user_ids: list[int]
    all_done: bool
