"""Group API routes: group/membership CRUD plus group-scoped habit listing and creation.
Per-habit read/check-in/checks live under /habits (routers/habits.py) -- a group habit is just
a Habit with group_id set, so it's served by the same endpoints as a personal one.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import get_token_claim
from duohabit.db import get_session
from duohabit.repositories.groups import GroupRepository
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.groups import (
    GroupCreate,
    GroupInviteJoin,
    GroupMemberAdd,
    GroupMemberRead,
    GroupMemberWithUser,
    GroupRead,
    GroupUpdate,
    GroupWithHabits,
)
from duohabit.schemas.habits import HabitCreate, HabitRead
from duohabit.services.groups import (
    add_habit_to_group,
    add_member,
    create_group,
    delete_group,
    get_group,
    get_group_habits,
    get_user_groups,
    join_group_by_code,
    leave_group,
    list_members,
    regenerate_invite_code,
    remove_member,
    update_group,
)

groups_router = APIRouter(prefix="/groups", tags=["Groups"])


@groups_router.post("", response_model=GroupWithHabits)
async def create_group_endpoint(
    group_data: GroupCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabits:
    """Create a group. Add habits to it afterwards via POST /groups/{group_id}/habits."""
    return await create_group(
        repo=GroupRepository(session),
        user_id=token_claim.user_id,
        group_data=group_data,
    )


@groups_router.get("", response_model=list[GroupWithHabits])
async def get_groups_endpoint(
    only_active: bool = Query(True, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[GroupWithHabits]:
    """List groups the caller is an active member of, each enriched with its habits."""
    return await get_user_groups(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        user_id=token_claim.user_id,
        only_active=only_active,
    )


@groups_router.get("/{group_id}", response_model=GroupWithHabits)
async def get_group_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabits:
    """Get group details, its habits, and member count."""
    return await get_group(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
    )


@groups_router.patch("/{group_id}", response_model=GroupRead)
async def update_group_endpoint(
    group_id: int,
    group_data: GroupUpdate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupRead:
    """Rename a group (owner only)."""
    return await update_group(
        repo=GroupRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
        group_data=group_data,
    )


@groups_router.delete("/{group_id}", status_code=204)
async def delete_group_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Disband a group (owner only)."""
    await delete_group(
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
    )


# ========== INVITES / MEMBERSHIP ==========


@groups_router.post("/{group_id}/invite/regenerate", response_model=GroupRead)
async def regenerate_invite_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupRead:
    """Rotate the group's invite code (owner only)."""
    return await regenerate_invite_code(
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
    )


@groups_router.post("/join", response_model=GroupWithHabits)
async def join_group_endpoint(
    invite_join: GroupInviteJoin,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabits:
    """Join a group using its invite code. Enrolls in every current habit of the group."""
    return await join_group_by_code(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        user_id=token_claim.user_id,
        invite_join=invite_join,
    )


@groups_router.get("/{group_id}/members", response_model=list[GroupMemberWithUser])
async def get_members_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[GroupMemberWithUser]:
    """List active members of a group (with usernames)."""
    return await list_members(
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
    )


@groups_router.post("/{group_id}/members", response_model=GroupMemberRead)
async def add_member_endpoint(
    group_id: int,
    member_data: GroupMemberAdd,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupMemberRead:
    """Directly add a member to a group (owner only)."""
    return await add_member(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        group_id=group_id,
        owner_user_id=token_claim.user_id,
        member_data=member_data,
    )


@groups_router.delete("/{group_id}/members/{target_user_id}", status_code=204)
async def remove_member_endpoint(
    group_id: int,
    target_user_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Remove a member from a group (owner only)."""
    await remove_member(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        group_id=group_id,
        owner_user_id=token_claim.user_id,
        target_user_id=target_user_id,
    )


@groups_router.post("/{group_id}/leave", status_code=204)
async def leave_group_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Leave a group (owner must delete the group instead)."""
    await leave_group(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
    )


# ========== GROUP HABITS ==========


@groups_router.get("/{group_id}/habits", response_model=list[HabitRead])
async def get_group_habits_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[HabitRead]:
    """List a group's habits."""
    return await get_group_habits(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
    )


@groups_router.post("/{group_id}/habits", response_model=HabitRead)
async def add_habit_to_group_endpoint(
    group_id: int,
    habit_data: HabitCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> HabitRead:
    """Add a new shared habit to a group (owner only); every current member joins it."""
    return await add_habit_to_group(
        repo=GroupRepository(session),
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        group_id=group_id,
        owner_user_id=token_claim.user_id,
        habit_data=habit_data,
    )
