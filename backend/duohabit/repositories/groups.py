"""Group repository: group and membership CRUD only. Habit state lives in repositories/habits.py."""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from duohabit.models.groups import Group, GroupMember
from duohabit.models.users import User
from duohabit.schemas.common import PaginationParams
from duohabit.utils.pagination import apply_pagination


class GroupRepository:
    """Repository for group and membership operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    # ========== GROUP METHODS ==========

    async def create_group(self, owner_id: int, name: str, invite_code: str) -> Group:
        """Create a new group."""
        group = Group(
            owner_id=owner_id, name=name, invite_code=invite_code, is_active=True
        )
        self._session.add(group)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError("Invite code collision") from exc
        await self._session.refresh(group)
        return group

    async def get_group_by_id(
        self, group_id: int, load_members: bool = False, load_habits: bool = False
    ) -> Group | None:
        """Get a group by id, optionally eager-loading members and/or its habits."""
        stmt = select(Group).where(Group.id == group_id)
        if load_members:
            stmt = stmt.options(selectinload(Group.members))
        if load_habits:
            stmt = stmt.options(selectinload(Group.habits))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_group_by_invite_code(self, invite_code: str) -> Group | None:
        """Get a group by its invite code."""
        stmt = select(Group).where(Group.invite_code == invite_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_groups_for_user(
        self, user_id: int, only_active: bool = True
    ) -> list[Group]:
        """Get all groups a user is an active member of."""
        stmt = (
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .where(GroupMember.user_id == user_id, GroupMember.is_active == True)
        )
        if only_active:
            stmt = stmt.where(Group.is_active == True)
        stmt = stmt.order_by(Group.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_group(self, group: Group, **kwargs: Any) -> Group:
        """Update group fields."""
        kwargs.pop("owner_id", None)
        kwargs.pop("invite_code", None)
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        await self._session.flush()
        await self._session.refresh(group)
        return group

    async def regenerate_invite_code(self, group: Group, new_code: str) -> Group:
        """Overwrite the group's invite code."""
        group.invite_code = new_code
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError("Invite code collision") from exc
        await self._session.refresh(group)
        return group

    async def delete_group(self, group: Group) -> None:
        """Delete a group (cascades to members and habits)."""
        await self._session.delete(group)
        await self._session.flush()

    # ========== MEMBER METHODS ==========

    async def add_member(
        self, group_id: int, user_id: int, role: str, join_method: str
    ) -> GroupMember:
        """Add a user as an active member of a group."""
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role,
            join_method=join_method,
            is_active=True,
        )
        self._session.add(member)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError("User is already a member of this group") from exc
        await self._session.refresh(member)
        return member

    async def get_member(self, group_id: int, user_id: int) -> GroupMember | None:
        """Get a (possibly inactive) membership row for a user in a group."""
        stmt = select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_members(
        self,
        group_id: int,
        only_active: bool = True,
        pagination: PaginationParams | None = None,
    ) -> list[GroupMember]:
        """List members of a group."""
        stmt = select(GroupMember).where(GroupMember.group_id == group_id)
        if only_active:
            stmt = stmt.where(GroupMember.is_active == True)
        stmt = stmt.order_by(GroupMember.id)
        if pagination is not None:
            stmt = apply_pagination(stmt, pagination)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_active_members(self, group_id: int) -> int:
        """Count currently-active members of a group."""
        stmt = (
            select(func.count())
            .select_from(GroupMember)
            .where(GroupMember.group_id == group_id, GroupMember.is_active == True)
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def remove_member(
        self, member: GroupMember, removed_at: datetime
    ) -> GroupMember:
        """Soft-remove a member (leave or kick)."""
        member.is_active = False
        member.removed_at = removed_at
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def reactivate_member(
        self, member: GroupMember, join_method: str
    ) -> GroupMember:
        """Reactivate a previously-removed membership (rejoin)."""
        member.is_active = True
        member.removed_at = None
        member.join_method = join_method
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def get_members_with_usernames(
        self, group_id: int, only_active: bool = True
    ) -> list[tuple[GroupMember, str]]:
        """List members of a group together with their username, for display."""
        stmt = (
            select(GroupMember, User.username)
            .join(User, User.id == GroupMember.user_id)
            .where(GroupMember.group_id == group_id)
        )
        if only_active:
            stmt = stmt.where(GroupMember.is_active == True)
        stmt = stmt.order_by(GroupMember.id)
        result = await self._session.execute(stmt)
        return list(result.tuples().all())
