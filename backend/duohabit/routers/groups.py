"""Group API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import get_token_claim
from duohabit.db import get_session
from duohabit.repositories.groups import GroupRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.groups import (
    GroupCheckinStatus,
    GroupCreate,
    GroupHabitCheckCreate,
    GroupHabitCheckRead,
    GroupHabitRead,
    GroupHabitUpdate,
    GroupInviteJoin,
    GroupMemberAdd,
    GroupMemberRead,
    GroupMemberWithUser,
    GroupRead,
    GroupUpdate,
    GroupWithHabit,
)
from duohabit.services.groups import (
    add_member,
    check_in,
    create_group,
    delete_group,
    get_checkin_status,
    get_group,
    get_my_checks,
    get_user_groups,
    join_group_by_code,
    leave_group,
    list_members,
    regenerate_invite_code,
    remove_member,
    update_group,
    update_group_habit,
)

groups_router = APIRouter(prefix="/groups", tags=["Groups"])


@groups_router.post("", response_model=GroupWithHabit)
async def create_group_endpoint(
    group_data: GroupCreate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabit:
    """Create a group together with its single shared habit."""
    return await create_group(
        repo=GroupRepository(session),
        user_id=token_claim.user_id,
        group_data=group_data,
    )


@groups_router.get("", response_model=list[GroupRead])
async def get_groups_endpoint(
    only_active: bool = Query(True, description="Filter by active status"),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[GroupRead]:
    """List groups the caller is an active member of."""
    return await get_user_groups(
        repo=GroupRepository(session),
        user_id=token_claim.user_id,
        only_active=only_active,
    )


@groups_router.get("/{group_id}", response_model=GroupWithHabit)
async def get_group_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabit:
    """Get group details, its habit, and member count."""
    return await get_group(
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
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


@groups_router.post("/join", response_model=GroupWithHabit)
async def join_group_endpoint(
    invite_join: GroupInviteJoin,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabit:
    """Join a group using its invite code."""
    return await join_group_by_code(
        repo=GroupRepository(session),
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
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
    )


# ========== GROUP HABIT ==========


@groups_router.patch("/{group_id}/habit", response_model=GroupHabitRead)
async def update_group_habit_endpoint(
    group_id: int,
    habit_data: GroupHabitUpdate,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupHabitRead:
    """Edit the group habit's title/description/allowed_misses (owner only)."""
    return await update_group_habit(
        repo=GroupRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
        habit_data=habit_data,
    )


# ========== CHECK-INS ==========


@groups_router.post("/{group_id}/check")
async def check_in_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> dict[str, Any]:
    """Check in on the group habit for the current period."""
    return await check_in(
        repo=GroupRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
        check_data=GroupHabitCheckCreate(),
    )


@groups_router.get("/{group_id}/checks/status", response_model=GroupCheckinStatus)
async def get_checkin_status_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupCheckinStatus:
    """See who has and hasn't checked in for the current period."""
    return await get_checkin_status(
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
    )


@groups_router.get("/{group_id}/checks/mine", response_model=list[GroupHabitCheckRead])
async def get_my_checks_endpoint(
    group_id: int,
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[GroupHabitCheckRead]:
    """Get the caller's own recent checks for the group habit."""
    return await get_my_checks(
        repo=GroupRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
        limit=limit,
    )
