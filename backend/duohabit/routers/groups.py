"""Group API routes: group/membership CRUD plus group-scoped habit listing and creation.
Per-habit read/check-in/checks live under /habits (routers/habits.py) -- a group habit is just
a Habit with group_id set, so it's served by the same endpoints as a personal one.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import get_token_claim
from duohabit.chat_hub import hub
from duohabit.db import get_session
from duohabit.repositories.groups import GroupRepository
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.push import PushRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.groups import (
    GroupCreate,
    GroupInviteJoin,
    GroupInviteRead,
    GroupJoinRequestRead,
    GroupMemberAdd,
    GroupMemberRead,
    GroupMemberWithUser,
    GroupRead,
    GroupUpdate,
    GroupWithHabits,
)
from duohabit.schemas.habits import HabitCreate, HabitRead
from duohabit.services.groups import (
    accept_invite,
    add_habit_to_group,
    add_member,
    approve_request,
    create_group,
    decline_invite,
    delete_group,
    get_group,
    get_group_habits,
    get_user_groups,
    join_group_by_code,
    leave_group,
    list_members,
    list_my_invites,
    list_my_join_requests,
    regenerate_invite_code,
    reject_request,
    remove_member,
    update_group,
)
from duohabit.services.notifications import NotificationPayload, notify

groups_router = APIRouter(prefix="/groups", tags=["Groups"])


async def _notify_if_offline(
    session: AsyncSession, user_ids: list[int], payload: NotificationPayload
) -> None:
    """Push only to recipients without a live socket - online ones will just see it in-app."""
    offline = [user_id for user_id in user_ids if not hub.is_online(user_id)]
    if offline:
        await notify(PushRepository(session), offline, payload)


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


@groups_router.get("/invites", response_model=list[GroupInviteRead])
async def get_my_invites_endpoint(
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[GroupInviteRead]:
    """List owner-sent invites the caller hasn't responded to yet."""
    return await list_my_invites(repo=GroupRepository(session), user_id=token_claim.user_id)


@groups_router.get("/requests", response_model=list[GroupJoinRequestRead])
async def get_my_join_requests_endpoint(
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> list[GroupJoinRequestRead]:
    """List pending join-by-code requests waiting on groups the caller owns."""
    return await list_my_join_requests(
        repo=GroupRepository(session), user_id=token_claim.user_id
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


@groups_router.post("/join", response_model=GroupMemberRead)
async def join_group_endpoint(
    invite_join: GroupInviteJoin,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupMemberRead:
    """Request to join a group by invite code. Owner has to approve before it's real membership."""
    repo = GroupRepository(session)
    member = await join_group_by_code(
        repo=repo, user_id=token_claim.user_id, invite_join=invite_join
    )

    group = await repo.get_group_by_id(member.group_id)
    requester = await UsersRepository(session).get_user(token_claim.user_id)
    if group is not None and requester is not None:
        await _notify_if_offline(
            session,
            [group.owner_id],
            NotificationPayload(
                title="Заявка на вступление",
                body=f"{requester.username} хочет вступить в «{group.name}»",
                url="/groups/invites",
                tag=f"group-request-{member.group_id}-{token_claim.user_id}",
            ),
        )

    return member


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
    """Invite a user to a group directly by id (owner only). Invitee has to accept."""
    repo = GroupRepository(session)
    member = await add_member(
        repo=repo,
        group_id=group_id,
        owner_user_id=token_claim.user_id,
        member_data=member_data,
    )

    group = await repo.get_group_by_id(group_id)
    inviter = await UsersRepository(session).get_user(token_claim.user_id)
    if group is not None and inviter is not None:
        await _notify_if_offline(
            session,
            [member_data.user_id],
            NotificationPayload(
                title="Приглашение в группу",
                body=f"{inviter.username} приглашает тебя в «{group.name}»",
                url="/groups/invites",
                tag=f"group-invite-{group_id}",
            ),
        )

    return member


@groups_router.post("/{group_id}/invites/accept", response_model=GroupWithHabits)
async def accept_invite_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupWithHabits:
    """Accept an owner-sent invite - grants membership and enrolls in current habits."""
    repo = GroupRepository(session)
    result = await accept_invite(
        repo=repo,
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        group_id=group_id,
        user_id=token_claim.user_id,
    )

    invitee = await UsersRepository(session).get_user(token_claim.user_id)
    if invitee is not None:
        await _notify_if_offline(
            session,
            [result.owner_id],
            NotificationPayload(
                title="Приглашение принято",
                body=f"{invitee.username} присоединился к «{result.name}»",
                url=f"/groups/{group_id}",
                tag=f"group-accepted-{group_id}",
            ),
        )

    return result


@groups_router.post("/{group_id}/invites/decline", status_code=204)
async def decline_invite_endpoint(
    group_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Decline an owner-sent invite."""
    await decline_invite(
        repo=GroupRepository(session), group_id=group_id, user_id=token_claim.user_id
    )


@groups_router.post("/{group_id}/requests/{user_id}/approve", response_model=GroupMemberRead)
async def approve_request_endpoint(
    group_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> GroupMemberRead:
    """Approve a join-by-code request (owner only) - grants membership."""
    repo = GroupRepository(session)
    result = await approve_request(
        repo=repo,
        habit_repo=HabitRepository(session),
        users_repo=UsersRepository(session),
        group_id=group_id,
        owner_user_id=token_claim.user_id,
        requester_id=user_id,
    )

    group = await repo.get_group_by_id(group_id)
    if group is not None:
        await _notify_if_offline(
            session,
            [user_id],
            NotificationPayload(
                title="Заявка одобрена",
                body=f"Тебя приняли в «{group.name}»",
                url=f"/groups/{group_id}",
                tag=f"group-approved-{group_id}",
            ),
        )

    return result


@groups_router.post("/{group_id}/requests/{user_id}/reject", status_code=204)
async def reject_request_endpoint(
    group_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Reject a join-by-code request (owner only)."""
    await reject_request(
        repo=GroupRepository(session),
        group_id=group_id,
        owner_user_id=token_claim.user_id,
        requester_id=user_id,
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
