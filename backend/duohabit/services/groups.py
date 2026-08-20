"""Group business logic: membership, invites, and the shared streak/grace algorithm."""

from datetime import datetime, timezone
from typing import Any

from duohabit.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from duohabit.models.groups import Group, GroupHabit, GroupMember
from duohabit.models.habits import HabitType
from duohabit.repositories.groups import GroupRepository
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
    GroupRole,
    GroupUpdate,
    GroupWithHabit,
    JoinMethod,
)
from duohabit.schemas.habits import HabitType as SchemaHabitType
from duohabit.utils.invite_codes import generate_invite_code
from duohabit.utils.periods import (
    compute_period_key,
    current_period_key,
    period_end_utc,
    previous_period_key,
    utc_today,
)

MAX_MEMBERS = 10


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


def group_with_habit_model_to_schema(
    group: Group, habit: GroupHabit | None, member_count: int
) -> GroupWithHabit:
    """Convert a Group ORM model into a read schema enriched with its habit and member count."""
    return GroupWithHabit(
        id=group.id,
        owner_id=group.owner_id,
        name=group.name,
        invite_code=group.invite_code,
        is_active=group.is_active,
        created_at=group.created_at,
        updated_at=group.updated_at,
        habit=group_habit_model_to_schema(habit) if habit else None,
        member_count=member_count,
    )


def group_member_model_to_schema(member: GroupMember) -> GroupMemberRead:
    """Convert a GroupMember ORM model into a plain read schema."""
    return GroupMemberRead(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        role=GroupRole(member.role),
        join_method=JoinMethod(member.join_method),
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
        is_active=member.is_active,
        created_at=member.created_at,
        username=username,
    )


def group_habit_model_to_schema(group_habit: GroupHabit) -> GroupHabitRead:
    """Convert a GroupHabit ORM model into a read schema."""
    return GroupHabitRead(
        id=group_habit.id,
        group_id=group_habit.group_id,
        title=group_habit.title,
        description=group_habit.description,
        habit_type=SchemaHabitType(group_habit.habit_type),
        allowed_misses=group_habit.allowed_misses,
        current_streak=group_habit.current_streak,
        misses_remaining=group_habit.misses_remaining,
        is_active=group_habit.is_active,
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


# ========== STREAK / GRACE RECONCILIATION ==========


async def _reconcile_group_habit(
    repo: GroupRepository, group_habit: GroupHabit
) -> GroupHabit:
    """Close out every period that fully elapsed since the last resolution.

    Eager, request-triggered (no scheduler in this codebase): for each period strictly
    between last_resolved_period_key and the current one, checks whether every member who
    was active as of that period's end had checked in; a miss consumes the grace pool
    (misses_remaining) if any is left, otherwise hard-resets current_streak.
    """
    habit_type = HabitType(group_habit.habit_type)
    current = current_period_key(habit_type)

    period = group_habit.last_resolved_period_key
    if period is None:
        # Defensive default; in practice always set at creation time.
        group_habit.last_resolved_period_key = current
        return group_habit
    if period == current:
        return group_habit

    resolved_any = False
    while True:
        candidate = compute_period_key(
            period_end_utc(period, habit_type).date(), habit_type
        )
        if candidate == current:
            break

        as_of = period_end_utc(candidate, habit_type)
        active_ids = await repo.get_active_member_ids_as_of(group_habit.group_id, as_of)
        done_count = await repo.count_checks_for_period(group_habit.id, candidate)

        if active_ids and done_count >= len(active_ids):
            pass  # success; in practice already handled eagerly at check-in time
        elif group_habit.misses_remaining > 0:
            group_habit.misses_remaining -= 1
        else:
            group_habit.current_streak = 0

        group_habit.last_resolved_period_key = candidate
        period = candidate
        resolved_any = True

    if resolved_any:
        group_habit = await repo.update_group_habit(
            group_habit,
            current_streak=group_habit.current_streak,
            misses_remaining=group_habit.misses_remaining,
            last_resolved_period_key=group_habit.last_resolved_period_key,
        )
    return group_habit


async def _get_reconciled_group_habit(
    repo: GroupRepository, group_id: int
) -> GroupHabit:
    group_habit = await repo.get_group_habit_by_group(group_id)
    if not group_habit:
        raise NotFoundError("Group habit not found")
    return await _reconcile_group_habit(repo, group_habit)


# ========== GROUPS ==========


async def create_group(
    repo: GroupRepository, user_id: int, group_data: GroupCreate
) -> GroupWithHabit:
    """Create a group together with its single shared habit; creator becomes owner."""
    if group_data.habit_type.value != HabitType.DAILY.value:
        raise ValidationAppError("Only daily group habits are supported for now")

    invite_code = await _generate_unique_invite_code(repo)
    group = await repo.create_group(
        owner_id=user_id, name=group_data.name, invite_code=invite_code
    )
    await repo.add_member(
        group.id, user_id, GroupRole.OWNER.value, JoinMethod.ADDED_BY_OWNER.value
    )

    # The current period is still in progress -- seed with the *previous* period key so
    # today can still be eagerly credited once every member checks in (see check_in).
    period_key = previous_period_key(HabitType(group_data.habit_type.value))
    group_habit = await repo.create_group_habit(
        group_id=group.id,
        title=group_data.habit_title,
        description=group_data.habit_description,
        habit_type=group_data.habit_type.value,
        allowed_misses=group_data.allowed_misses,
        initial_period_key=period_key,
    )

    await repo.commit()
    return group_with_habit_model_to_schema(group, group_habit, member_count=1)


async def get_user_groups(
    repo: GroupRepository, user_id: int, only_active: bool = True
) -> list[GroupRead]:
    """List groups the user is an active member of."""
    groups = await repo.get_groups_for_user(user_id, only_active=only_active)
    return [group_model_to_schema(g) for g in groups]


async def get_group(
    repo: GroupRepository, group_id: int, user_id: int
) -> GroupWithHabit:
    """Get group details, habit, and member count. Reconciles any elapsed periods first."""
    await _require_member(repo, group_id, user_id)
    group = await _get_group_or_404(repo, group_id)

    group_habit = await repo.get_group_habit_by_group(group_id)
    if group_habit:
        group_habit = await _reconcile_group_habit(repo, group_habit)
        await repo.commit()

    member_count = await repo.count_active_members(group_id)
    return group_with_habit_model_to_schema(
        group, group_habit, member_count=member_count
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
    """Disband a group (owner only). Cascades to members, habit, and checks."""
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


async def join_group_by_code(
    repo: GroupRepository, user_id: int, invite_join: GroupInviteJoin
) -> GroupWithHabit:
    """Join a group using its invite code."""
    group = await repo.get_group_by_invite_code(invite_join.invite_code)
    if not group or not group.is_active:
        raise NotFoundError("Invalid invite code")

    existing_member = await repo.get_member(group.id, user_id)
    if existing_member and existing_member.is_active:
        raise ConflictError("Already a member of this group")

    active_count = await repo.count_active_members(group.id)
    if active_count >= MAX_MEMBERS:
        raise ValidationAppError(f"Group is full (max {MAX_MEMBERS} members)")

    if existing_member:
        await repo.reactivate_member(existing_member, JoinMethod.INVITE_CODE.value)
    else:
        await repo.add_member(
            group.id, user_id, GroupRole.MEMBER.value, JoinMethod.INVITE_CODE.value
        )

    await repo.commit()

    group_habit = await repo.get_group_habit_by_group(group.id)
    member_count = await repo.count_active_members(group.id)
    return group_with_habit_model_to_schema(
        group, group_habit, member_count=member_count
    )


async def add_member(
    repo: GroupRepository,
    group_id: int,
    owner_user_id: int,
    member_data: GroupMemberAdd,
) -> GroupMemberRead:
    """Directly add a member to a group (owner only)."""
    await _require_owner(repo, group_id, owner_user_id)

    active_count = await repo.count_active_members(group_id)
    if active_count >= MAX_MEMBERS:
        raise ValidationAppError(f"Group is full (max {MAX_MEMBERS} members)")

    existing_member = await repo.get_member(group_id, member_data.user_id)
    if existing_member and existing_member.is_active:
        raise ConflictError("User is already a member of this group")

    if existing_member:
        member = await repo.reactivate_member(
            existing_member, JoinMethod.ADDED_BY_OWNER.value
        )
    else:
        member = await repo.add_member(
            group_id,
            member_data.user_id,
            GroupRole.MEMBER.value,
            JoinMethod.ADDED_BY_OWNER.value,
        )

    await repo.commit()
    return group_member_model_to_schema(member)


async def remove_member(
    repo: GroupRepository, group_id: int, owner_user_id: int, target_user_id: int
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

    await repo.remove_member(member, removed_at=datetime.now(timezone.utc))
    await repo.commit()


async def leave_group(repo: GroupRepository, group_id: int, user_id: int) -> None:
    """Leave a group (owner must delete the group instead)."""
    member = await _require_member(repo, group_id, user_id)
    group = await _get_group_or_404(repo, group_id)
    if group.owner_id == user_id:
        raise ValidationAppError("Owner cannot leave the group; delete it instead")

    await repo.remove_member(member, removed_at=datetime.now(timezone.utc))
    await repo.commit()


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


# ========== GROUP HABIT ==========


async def update_group_habit(
    repo: GroupRepository, group_id: int, user_id: int, habit_data: GroupHabitUpdate
) -> GroupHabitRead:
    """Edit the group habit's title/description/allowed_misses (owner only)."""
    await _require_owner(repo, group_id, user_id)
    group_habit = await _get_reconciled_group_habit(repo, group_id)

    update_data = habit_data.model_dump(exclude_unset=True)
    if update_data.get("allowed_misses") is not None:
        delta = update_data["allowed_misses"] - group_habit.allowed_misses
        update_data["misses_remaining"] = max(0, group_habit.misses_remaining + delta)

    updated = await repo.update_group_habit(group_habit, **update_data)
    await repo.commit()
    return group_habit_model_to_schema(updated)


# ========== CHECK-INS ==========


async def check_in(
    repo: GroupRepository,
    group_id: int,
    user_id: int,
    check_data: GroupHabitCheckCreate,
) -> dict[str, Any]:
    """Check in on the group habit for the current period."""
    await _require_member(repo, group_id, user_id)
    group_habit = await _get_reconciled_group_habit(repo, group_id)

    habit_type = HabitType(group_habit.habit_type)
    period = current_period_key(habit_type)
    check_date = check_data.check_date or utc_today()
    if compute_period_key(check_date, habit_type) != period:
        raise ValidationAppError("Check-in must be for the current period")

    existing = await repo.get_check(group_habit.id, user_id, period)
    if existing:
        raise ConflictError("Already checked in for this period")

    await repo.create_group_habit_check(group_habit.id, user_id, check_date, period)

    active_count = await repo.count_active_members(group_id)
    done_count = await repo.count_checks_for_period(group_habit.id, period)

    streak_incremented = False
    if done_count >= active_count and group_habit.last_resolved_period_key != period:
        group_habit = await repo.update_group_habit(
            group_habit,
            current_streak=group_habit.current_streak + 1,
            last_resolved_period_key=period,
        )
        streak_incremented = True

    await repo.commit()

    all_done = done_count >= active_count
    message = (
        f"Стрик: {group_habit.current_streak} дней подряд! 🔥"
        if streak_incremented
        else "Отмечено, ждём остальных участников."
    )
    return {
        "checked": True,
        "period_key": period,
        "current_streak": group_habit.current_streak,
        "all_members_done": all_done,
        "message": message,
    }


async def get_checkin_status(
    repo: GroupRepository, group_id: int, user_id: int
) -> GroupCheckinStatus:
    """Who has and hasn't checked in for the current period."""
    await _require_member(repo, group_id, user_id)
    group_habit = await _get_reconciled_group_habit(repo, group_id)
    await repo.commit()

    habit_type = HabitType(group_habit.habit_type)
    period = current_period_key(habit_type)

    checks = await repo.get_checks_for_period(group_habit.id, period)
    checked_in_ids = [c.user_id for c in checks]

    active_ids = await repo.get_active_member_ids_as_of(
        group_id, datetime.now(timezone.utc)
    )
    missing_ids = [uid for uid in active_ids if uid not in checked_in_ids]

    return GroupCheckinStatus(
        period_key=period,
        total_active_members=len(active_ids),
        checked_in_user_ids=checked_in_ids,
        missing_user_ids=missing_ids,
        all_done=len(active_ids) > 0 and len(missing_ids) == 0,
    )


async def get_my_checks(
    repo: GroupRepository, group_id: int, user_id: int, limit: int = 30
) -> list[GroupHabitCheckRead]:
    """Get the caller's recent checks for the group habit."""
    await _require_member(repo, group_id, user_id)
    group_habit = await repo.get_group_habit_by_group(group_id)
    if not group_habit:
        raise NotFoundError("Group habit not found")
    checks = await repo.get_checks_for_user(group_habit.id, user_id, limit=limit)
    return [GroupHabitCheckRead.model_validate(c) for c in checks]
