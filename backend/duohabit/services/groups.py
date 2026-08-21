"""Group business logic: membership, invites, and keeping each habit's per-member streak rows
(HabitMember, see services/habits.py) in sync with the group roster.
"""

from datetime import datetime, timezone

from duohabit.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from duohabit.models.groups import Group, GroupMember
from duohabit.models.habits import Habit
from duohabit.models.habits import HabitType as ModelHabitType
from duohabit.repositories.groups import GroupRepository
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.groups import (
    GroupCreate,
    GroupInviteJoin,
    GroupInviteRead,
    GroupJoinRequestRead,
    GroupMemberAdd,
    GroupMemberRead,
    GroupMemberWithUser,
    GroupRead,
    GroupRole,
    GroupUpdate,
    GroupWithHabits,
    JoinMethod,
    MemberStatus,
)
from duohabit.schemas.habits import HabitCreate, HabitRead
from duohabit.services.habits import reconcile_all_members, habit_model_to_schema
from duohabit.utils.invite_codes import generate_invite_code
from duohabit.utils.periods import previous_period_key

MAX_MEMBERS = 5
DEFAULT_TZ = "UTC"


# ========== MODEL -> SCHEMA CONVERSION ==========


def group_model_to_schema(group: Group) -> GroupRead:
    """Convert a Group ORM model into a plain read schema."""
    return GroupRead(
        id=group.id,
        owner_id=group.owner_id,
        name=group.name,
        invite_code=group.invite_code,
        is_active=group.is_active,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


def group_member_model_to_schema(member: GroupMember) -> GroupMemberRead:
    """Convert a GroupMember ORM model into a plain read schema."""
    return GroupMemberRead(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        role=GroupRole(member.role),
        join_method=JoinMethod(member.join_method),
        status=MemberStatus(member.status),
        is_active=member.is_active,
        created_at=member.created_at,
    )


def group_member_with_user_model_to_schema(
    member: GroupMember, username: str
) -> GroupMemberWithUser:
    """Convert a GroupMember ORM model into a read schema enriched with the user's username."""
    return GroupMemberWithUser(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        role=GroupRole(member.role),
        join_method=JoinMethod(member.join_method),
        status=MemberStatus(member.status),
        is_active=member.is_active,
        created_at=member.created_at,
        username=username,
    )


# ========== AUTHORIZATION HELPERS ==========


async def _get_group_or_404(repo: GroupRepository, group_id: int) -> Group:
    group = await repo.get_group_by_id(group_id)
    if not group:
        raise NotFoundError("Group not found")
    return group


async def _require_member(
    repo: GroupRepository, group_id: int, user_id: int
) -> GroupMember:
    await _get_group_or_404(repo, group_id)
    member = await repo.get_member(group_id, user_id)
    if not member or not member.is_active:
        raise ForbiddenError("Not a member of this group")
    return member


async def _require_owner(repo: GroupRepository, group_id: int, user_id: int) -> Group:
    group = await _get_group_or_404(repo, group_id)
    if group.owner_id != user_id:
        raise ForbiddenError("Only the group owner can do this")
    return group


async def _generate_unique_invite_code(repo: GroupRepository) -> str:
    for _ in range(5):
        code = generate_invite_code()
        existing = await repo.get_group_by_invite_code(code)
        if not existing:
            return code
    raise ValidationAppError("Could not generate a unique invite code, try again")


# ========== HABIT-MEMBERSHIP SYNC ==========


async def _add_or_reset_member_habit(
    habit_repo: HabitRepository, habit: Habit, user_id: int, tz: str
) -> None:
    """Give a member a fresh per-habit streak row (first join, or rejoin -- resets to 0)."""
    habit_type = ModelHabitType(habit.habit_type)
    seed_period = previous_period_key(habit_type, tz)
    existing = await habit_repo.get_member(habit.id, user_id)
    if existing:
        await habit_repo.update_member(
            existing,
            current_streak=0,
            misses_remaining=habit.allowed_misses,
            last_resolved_period_key=seed_period,
            is_active=True,
            removed_at=None,
        )
    else:
        await habit_repo.add_member(
            habit.id,
            user_id,
            misses_remaining=habit.allowed_misses,
            last_resolved_period_key=seed_period,
        )


async def _sync_join(
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    user_id: int,
) -> None:
    """On join/rejoin: give the member a streak row for every active habit of the group."""
    habits = await habit_repo.get_by_group(group_id, only_active=True)
    if not habits:
        return
    user = await users_repo.get_user(user_id)
    tz = user.timezone if user else DEFAULT_TZ
    for habit in habits:
        await _add_or_reset_member_habit(habit_repo, habit, user_id, tz)


async def _sync_leave(
    habit_repo: HabitRepository, group_id: int, user_id: int, removed_at: datetime
) -> None:
    """On leave/kick: freeze the member's streak row on every habit of the group."""
    habits = await habit_repo.get_by_group(group_id, only_active=True)
    for habit in habits:
        member = await habit_repo.get_member(habit.id, user_id)
        if member and member.is_active:
            await habit_repo.deactivate_member(member, removed_at=removed_at)


# ========== GROUPS ==========


async def create_group(
    repo: GroupRepository, user_id: int, group_data: GroupCreate
) -> GroupWithHabits:
    """Create a group; creator becomes owner. Habits are added afterwards via add_habit_to_group."""
    invite_code = await _generate_unique_invite_code(repo)
    group = await repo.create_group(
        owner_id=user_id, name=group_data.name, invite_code=invite_code
    )
    await repo.add_member(
        group.id, user_id, GroupRole.OWNER.value, JoinMethod.ADDED_BY_OWNER.value
    )
    await repo.commit()
    return GroupWithHabits(
        **group_model_to_schema(group).model_dump(), habits=[], member_count=1
    )


async def _build_group_habit_reads(
    habit_repo: HabitRepository, users_repo: UsersRepository, group_id: int, user_id: int
) -> list[HabitRead]:
    """Reconcile and MIN-aggregate every habit of a group, for the calling member's view."""
    habits = await habit_repo.get_by_group(group_id, only_active=True)
    habit_reads: list[HabitRead] = []
    for habit in habits:
        await reconcile_all_members(habit_repo, users_repo, habit)
        my_member = await habit_repo.get_member(habit.id, user_id)
        min_streak = await habit_repo.get_min_active_streak(habit.id)
        member_count = len(await habit_repo.get_active_members(habit.id))
        habit_reads.append(
            habit_model_to_schema(
                habit,
                min_streak=min_streak,
                member_count=member_count,
                my_member=my_member,
            )
        )
    if habits:
        await habit_repo.commit()
    return habit_reads


async def get_user_groups(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    user_id: int,
    only_active: bool = True,
) -> list[GroupWithHabits]:
    """List groups the user is an active member of, each enriched with its habits."""
    groups = await repo.get_groups_for_user(user_id, only_active=only_active)
    result = []
    for group in groups:
        habit_reads = await _build_group_habit_reads(habit_repo, users_repo, group.id, user_id)
        member_count = await repo.count_active_members(group.id)
        result.append(
            GroupWithHabits(
                **group_model_to_schema(group).model_dump(),
                habits=habit_reads,
                member_count=member_count,
            )
        )
    return result


async def get_group(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    user_id: int,
) -> GroupWithHabits:
    """Get group details, its habits (each reconciled), and member count."""
    await _require_member(repo, group_id, user_id)
    group = await _get_group_or_404(repo, group_id)

    habit_reads = await _build_group_habit_reads(habit_repo, users_repo, group_id, user_id)
    member_count = await repo.count_active_members(group_id)
    return GroupWithHabits(
        **group_model_to_schema(group).model_dump(),
        habits=habit_reads,
        member_count=member_count,
    )


async def update_group(
    repo: GroupRepository, group_id: int, user_id: int, group_data: GroupUpdate
) -> GroupRead:
    """Rename a group (owner only)."""
    group = await _require_owner(repo, group_id, user_id)
    update_data = group_data.model_dump(exclude_unset=True)
    updated = await repo.update_group(group, **update_data)
    await repo.commit()
    return group_model_to_schema(updated)


async def delete_group(repo: GroupRepository, group_id: int, user_id: int) -> None:
    """Disband a group (owner only). Cascades to members and habits."""
    group = await _require_owner(repo, group_id, user_id)
    await repo.delete_group(group)
    await repo.commit()


async def regenerate_invite_code(
    repo: GroupRepository, group_id: int, user_id: int
) -> GroupRead:
    """Rotate the group's invite code (owner only)."""
    group = await _require_owner(repo, group_id, user_id)
    new_code = await _generate_unique_invite_code(repo)
    updated = await repo.regenerate_invite_code(group, new_code)
    await repo.commit()
    return group_model_to_schema(updated)


# ========== MEMBERSHIP ==========


def _require_not_already_pending_or_member(existing_member: GroupMember | None) -> None:
    """Shared guard for both invite/request creation paths."""
    if existing_member is None:
        return
    if existing_member.is_active:
        raise ConflictError("Already a member of this group")
    if existing_member.status == MemberStatus.PENDING.value:
        raise ConflictError("Membership is already pending")


async def _create_or_reset_pending(
    repo: GroupRepository,
    group_id: int,
    user_id: int,
    role: str,
    join_method: str,
    existing_member: GroupMember | None,
) -> GroupMember:
    """Shared by join_group_by_code/add_member: start (or restart) a pending row."""
    if existing_member:
        return await repo.reset_to_pending(existing_member, join_method)
    try:
        return await repo.create_pending_member(group_id, user_id, role, join_method)
    except ValueError as exc:
        # Two concurrent requests for the same pair can both pass the pre-check
        # above and race on the unique constraint - the loser gets a proper
        # ConflictError instead of an opaque 400 from the repo's plain ValueError
        raise ConflictError("Membership is already pending") from exc


async def join_group_by_code(
    repo: GroupRepository,
    user_id: int,
    invite_join: GroupInviteJoin,
) -> GroupMemberRead:
    """
    Request to join a group using its invite code.

    Does not grant membership - the owner has to approve first (see approve_request).
    """
    group = await repo.get_group_by_invite_code(invite_join.invite_code)
    if not group or not group.is_active:
        raise NotFoundError("Invalid invite code")

    existing_member = await repo.get_member(group.id, user_id)
    _require_not_already_pending_or_member(existing_member)

    active_count = await repo.count_active_members(group.id)
    if active_count >= MAX_MEMBERS:
        raise ValidationAppError(f"Group is full (max {MAX_MEMBERS} members)")

    member = await _create_or_reset_pending(
        repo, group.id, user_id, GroupRole.MEMBER.value, JoinMethod.INVITE_CODE.value,
        existing_member,
    )
    await repo.commit()
    return group_member_model_to_schema(member)


async def add_member(
    repo: GroupRepository,
    group_id: int,
    owner_user_id: int,
    member_data: GroupMemberAdd,
) -> GroupMemberRead:
    """
    Invite a user to a group directly by id (owner only).

    Does not grant membership - the invitee has to accept first (see accept_invite).
    """
    await _require_owner(repo, group_id, owner_user_id)

    active_count = await repo.count_active_members(group_id)
    if active_count >= MAX_MEMBERS:
        raise ValidationAppError(f"Group is full (max {MAX_MEMBERS} members)")

    existing_member = await repo.get_member(group_id, member_data.user_id)
    _require_not_already_pending_or_member(existing_member)

    member = await _create_or_reset_pending(
        repo, group_id, member_data.user_id, GroupRole.MEMBER.value,
        JoinMethod.ADDED_BY_OWNER.value, existing_member,
    )
    await repo.commit()
    return group_member_model_to_schema(member)


async def _get_pending_member_or_404(
    repo: GroupRepository, group_id: int, user_id: int, join_method: JoinMethod
) -> GroupMember:
    member = await repo.get_member(group_id, user_id)
    if (
        member is None
        or member.status != MemberStatus.PENDING.value
        or member.join_method != join_method.value
    ):
        raise NotFoundError("No pending membership found")
    return member


async def _grant_membership(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    user_id: int,
    join_method: JoinMethod,
) -> GroupMember:
    """
    Shared pending->accepted transition for both accept_invite and approve_request:
    capacity recheck (the group may have filled up while this was waiting), flip
    to active, enroll in current habits.
    """
    member = await _get_pending_member_or_404(repo, group_id, user_id, join_method)

    active_count = await repo.count_active_members(group_id)
    if active_count >= MAX_MEMBERS:
        raise ValidationAppError(f"Group is full (max {MAX_MEMBERS} members)")

    await repo.accept_member(member)
    await _sync_join(habit_repo, users_repo, group_id, user_id)
    await repo.commit()
    await habit_repo.commit()
    return member


async def _revoke_pending(
    repo: GroupRepository, group_id: int, user_id: int, join_method: JoinMethod
) -> None:
    """Shared by decline_invite/reject_request: drop the pending row, nothing to unwind."""
    member = await _get_pending_member_or_404(repo, group_id, user_id, join_method)
    await repo.delete_member(member)
    await repo.commit()


async def accept_invite(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    user_id: int,
) -> GroupWithHabits:
    """Accept an owner-sent invite - grants membership and enrolls in current habits."""
    await _grant_membership(
        repo, habit_repo, users_repo, group_id, user_id, JoinMethod.ADDED_BY_OWNER
    )
    return await get_group(repo, habit_repo, users_repo, group_id, user_id)


async def decline_invite(repo: GroupRepository, group_id: int, user_id: int) -> None:
    """Decline an owner-sent invite."""
    await _revoke_pending(repo, group_id, user_id, JoinMethod.ADDED_BY_OWNER)


async def approve_request(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    owner_user_id: int,
    requester_id: int,
) -> GroupMemberRead:
    """Approve a join-by-code request (owner only) - grants membership."""
    await _require_owner(repo, group_id, owner_user_id)
    member = await _grant_membership(
        repo, habit_repo, users_repo, group_id, requester_id, JoinMethod.INVITE_CODE
    )
    return group_member_model_to_schema(member)


async def reject_request(
    repo: GroupRepository, group_id: int, owner_user_id: int, requester_id: int
) -> None:
    """Reject a join-by-code request (owner only)."""
    await _require_owner(repo, group_id, owner_user_id)
    await _revoke_pending(repo, group_id, requester_id, JoinMethod.INVITE_CODE)


async def list_my_invites(repo: GroupRepository, user_id: int) -> list[GroupInviteRead]:
    """List owner-sent invites the user hasn't responded to yet."""
    rows = await repo.get_pending_invites_for_user(user_id)
    return [
        GroupInviteRead(
            id=member.id,
            group_id=group.id,
            group_name=group.name,
            created_at=member.created_at,
        )
        for member, group in rows
    ]


async def list_my_join_requests(
    repo: GroupRepository, user_id: int
) -> list[GroupJoinRequestRead]:
    """List pending join-by-code requests waiting on groups the user owns."""
    rows = await repo.get_pending_requests_for_owner(user_id)
    return [
        GroupJoinRequestRead(
            id=member.id,
            group_id=group.id,
            group_name=group.name,
            user_id=member.user_id,
            username=username,
            created_at=member.created_at,
        )
        for member, group, username in rows
    ]


async def remove_member(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    group_id: int,
    owner_user_id: int,
    target_user_id: int,
) -> None:
    """Remove a member from a group (owner only; owner cannot remove themself)."""
    await _require_owner(repo, group_id, owner_user_id)
    if target_user_id == owner_user_id:
        raise ValidationAppError(
            "Owner cannot remove themself; delete the group instead"
        )

    member = await repo.get_member(group_id, target_user_id)
    if not member or not member.is_active:
        raise NotFoundError("Member not found")

    removed_at = datetime.now(timezone.utc)
    await repo.remove_member(member, removed_at=removed_at)
    await _sync_leave(habit_repo, group_id, target_user_id, removed_at)
    await repo.commit()
    await habit_repo.commit()


async def leave_group(
    repo: GroupRepository, habit_repo: HabitRepository, group_id: int, user_id: int
) -> None:
    """Leave a group (owner must delete the group instead)."""
    member = await _require_member(repo, group_id, user_id)
    group = await _get_group_or_404(repo, group_id)
    if group.owner_id == user_id:
        raise ValidationAppError("Owner cannot leave the group; delete it instead")

    removed_at = datetime.now(timezone.utc)
    await repo.remove_member(member, removed_at=removed_at)
    await _sync_leave(habit_repo, group_id, user_id, removed_at)
    await repo.commit()
    await habit_repo.commit()


async def list_members(
    repo: GroupRepository, group_id: int, user_id: int
) -> list[GroupMemberWithUser]:
    """List active members of a group, enriched with their usernames."""
    await _require_member(repo, group_id, user_id)
    rows = await repo.get_members_with_usernames(group_id)
    return [
        group_member_with_user_model_to_schema(member, username=username)
        for member, username in rows
    ]


# ========== GROUP HABITS ==========


async def add_habit_to_group(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    owner_user_id: int,
    habit_data: HabitCreate,
) -> HabitRead:
    """Add a new shared habit to a group (owner only); every current active member joins it."""
    await _require_owner(repo, group_id, owner_user_id)

    habit = await habit_repo.create(
        creator_id=owner_user_id,
        title=habit_data.title,
        description=habit_data.description,
        habit_type=habit_data.habit_type.value,
        allowed_misses=habit_data.allowed_misses,
        group_id=group_id,
    )
    members = await repo.get_members(group_id, only_active=True)
    for group_member in members:
        user = await users_repo.get_user(group_member.user_id)
        tz = user.timezone if user else DEFAULT_TZ
        await _add_or_reset_member_habit(habit_repo, habit, group_member.user_id, tz)
    await habit_repo.commit()

    my_member = await habit_repo.get_member(habit.id, owner_user_id)
    return habit_model_to_schema(
        habit, min_streak=0, member_count=len(members), my_member=my_member
    )


async def get_group_habits(
    repo: GroupRepository,
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    group_id: int,
    user_id: int,
) -> list[HabitRead]:
    """List a group's habits, each reconciled and MIN-aggregated across active members."""
    await _require_member(repo, group_id, user_id)
    return await _build_group_habit_reads(habit_repo, users_repo, group_id, user_id)
