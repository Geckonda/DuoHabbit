"""Group schemas: name, invite code, membership. Habit schemas live in schemas/habits.py."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from duohabit.schemas.habits import HabitRead


class GroupRole(str, Enum):
    """Role of a member within a group (должен совпадать с моделью)."""

    OWNER = "owner"
    MEMBER = "member"


class JoinMethod(str, Enum):
    """How a member ended up in a group (должен совпадать с моделью)."""

    INVITE_CODE = "invite_code"
    ADDED_BY_OWNER = "added_by_owner"


class MemberStatus(str, Enum):
    """Whether a membership row is waiting on a response (должен совпадать с моделью)."""

    PENDING = "pending"
    ACCEPTED = "accepted"


# ========== GROUP ==========


class GroupBase(BaseModel):
    """Base group schema."""

    name: str


class GroupCreate(GroupBase):
    """Schema for creating a group. Habits are added afterwards via /groups/{id}/habits."""


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


class GroupWithHabits(GroupRead):
    """Group enriched with its habits and member count."""

    habits: list[HabitRead] = []
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
    status: MemberStatus
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


# ========== PENDING (INVITES / REQUESTS) ==========


class GroupInviteRead(BaseModel):
    """An owner-sent invite the current user hasn't responded to yet."""

    id: int
    group_id: int
    group_name: str
    created_at: datetime | None = None


class GroupJoinRequestRead(BaseModel):
    """A pending join-by-code request on a group the current user owns."""

    id: int
    group_id: int
    group_name: str
    user_id: int
    username: str
    created_at: datetime | None = None
