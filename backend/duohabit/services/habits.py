"""Habit business logic: one engine for personal habits and group habits alike.

A habit's displayed streak is MIN(current_streak) over its active HabitMember rows. Each member
reconciles independently, in their own timezone -- there's no shared "period" to synchronize
across members, which is what lets a group habit work fairly across timezones. A personal habit
is simply a habit with exactly one member, so no code here special-cases it.
"""

from typing import Any, Literal, overload

from duohabit.errors import ConflictError, ForbiddenError, NotFoundError
from duohabit.models.habits import Habit, HabitCheck, HabitMember
from duohabit.models.habits import HabitType as ModelHabitType
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.habits import (
    HabitCheckinStatus,
    HabitCheckRead,
    HabitCreate,
    HabitRead,
    HabitType,
    HabitUpdate,
    HabitWithChecks,
)
from duohabit.utils.periods import (
    compute_period_key,
    current_period_key,
    local_today,
    period_end_local,
    previous_period_key,
)

DEFAULT_TZ = "UTC"


# ========== MODEL -> SCHEMA CONVERSION ==========


def habit_check_model_to_schema(check: HabitCheck) -> HabitCheckRead:
    """Convert a HabitCheck ORM model into a read schema."""
    return HabitCheckRead(
        id=check.id,
        habit_id=check.habit_id,
        user_id=check.user_id,
        check_date=check.check_date,
        period_key=check.period_key,
    )


def habit_model_to_schema(
    habit: Habit,
    min_streak: int,
    member_count: int,
    my_member: HabitMember | None,
    checks: list[HabitCheck] | None = None,
) -> HabitRead | HabitWithChecks:
    """Convert a Habit ORM model into a read schema.

    current_streak is MIN(current_streak) over active members -- the honest, team-wide number.
    my_current_streak/my_misses_remaining are the caller's own, for when they diverge (group).
    """
    fields: dict[str, Any] = dict(
        id=habit.id,
        group_id=habit.group_id,
        creator_id=habit.creator_id,
        title=habit.title,
        description=habit.description,
        is_active=habit.is_active,
        is_private=habit.is_private,
        habit_type=HabitType(habit.habit_type),
        allowed_misses=habit.allowed_misses,
        current_streak=min_streak,
        member_count=member_count,
        my_current_streak=my_member.current_streak if my_member else 0,
        my_misses_remaining=my_member.misses_remaining if my_member else 0,
        created_at=habit.created_at,
        updated_at=habit.updated_at,
    )
    if checks is not None:
        return HabitWithChecks(
            **fields, recent_checks=[habit_check_model_to_schema(c) for c in checks]
        )
    return HabitRead(**fields)


# ========== AUTHORIZATION HELPERS ==========


async def _get_habit_or_404(repo: HabitRepository, habit_id: int) -> Habit:
    habit = await repo.get_by_id(habit_id)
    if not habit:
        raise NotFoundError("Habit not found")
    return habit


async def _require_participant(
    repo: HabitRepository, habit_id: int, user_id: int
) -> HabitMember:
    await _get_habit_or_404(repo, habit_id)
    member = await repo.get_member(habit_id, user_id)
    if not member or not member.is_active:
        raise ForbiddenError("Not a participant in this habit")
    return member


# ========== STREAK / GRACE RECONCILIATION ==========


async def _reconcile_member(
    repo: HabitRepository, member: HabitMember, habit_type: ModelHabitType, tz: str
) -> HabitMember:
    """Close out every period that fully elapsed (in this member's own timezone) since last
    resolution. Eager, request-triggered (no scheduler): for each period strictly between
    last_resolved_period_key and the current one, a miss consumes grace if any is left,
    otherwise hard-resets current_streak.
    """
    current = current_period_key(habit_type, tz)

    period = member.last_resolved_period_key
    if period is None:
        # Defensive default; in practice always set when the member row is created.
        return await repo.update_member(member, last_resolved_period_key=current)
    if period == current:
        return member

    streak = member.current_streak
    misses_remaining = member.misses_remaining
    resolved_any = False

    while True:
        candidate = compute_period_key(
            period_end_local(period, habit_type, tz).date(), habit_type
        )
        if candidate == current:
            break

        done = await repo.get_check(member.habit_id, member.user_id, candidate)
        if done:
            pass  # success; in practice already handled eagerly at check-in time
        elif misses_remaining > 0:
            misses_remaining -= 1
        else:
            streak = 0

        period = candidate
        resolved_any = True

    if resolved_any:
        member = await repo.update_member(
            member,
            current_streak=streak,
            misses_remaining=misses_remaining,
            last_resolved_period_key=period,
        )
    return member


async def reconcile_all_members(
    repo: HabitRepository, users_repo: UsersRepository, habit: Habit
) -> list[HabitMember]:
    """Reconcile every active member of a habit, each in their own timezone."""
    members = await repo.get_active_members(habit.id)
    if not members:
        return []
    tz_map = await users_repo.get_timezones([m.user_id for m in members])
    habit_type = ModelHabitType(habit.habit_type)
    return [
        await _reconcile_member(repo, m, habit_type, tz_map.get(m.user_id, DEFAULT_TZ))
        for m in members
    ]


# ========== HABITS ==========


async def create_habit(
    repo: HabitRepository,
    users_repo: UsersRepository,
    user_id: int,
    habit_data: HabitCreate,
) -> HabitRead:
    """Create a new personal habit (group habits are created via services/groups.py)."""
    user = await users_repo.get_user(user_id)
    tz = user.timezone if user else DEFAULT_TZ
    habit_type = ModelHabitType(habit_data.habit_type.value)

    habit = await repo.create(
        creator_id=user_id,
        title=habit_data.title,
        description=habit_data.description,
        habit_type=habit_data.habit_type.value,
        allowed_misses=habit_data.allowed_misses,
        group_id=None,
    )
    member = await repo.add_member(
        habit.id,
        user_id,
        misses_remaining=habit_data.allowed_misses,
        last_resolved_period_key=previous_period_key(habit_type, tz),
    )
    await repo.commit()
    return habit_model_to_schema(habit, min_streak=0, member_count=1, my_member=member)


async def get_user_habits(
    repo: HabitRepository,
    users_repo: UsersRepository,
    user_id: int,
    only_active: bool = True,
) -> list[HabitRead]:
    """List the caller's personal habits (group habits are listed via /groups/{id}/habits)."""
    habits = await repo.get_personal_habits(user_id, only_active=only_active)
    result = []
    for habit in habits:
        await reconcile_all_members(repo, users_repo, habit)
        member = await repo.get_member(habit.id, user_id)
        min_streak = await repo.get_min_active_streak(habit.id)
        result.append(
            habit_model_to_schema(
                habit, min_streak=min_streak, member_count=1, my_member=member
            )
        )
    if result:
        await repo.commit()
    return result


@overload
async def get_habit(
    repo: HabitRepository,
    users_repo: UsersRepository,
    habit_id: int,
    user_id: int,
    with_checks: Literal[False] = False,
) -> HabitRead: ...


@overload
async def get_habit(
    repo: HabitRepository,
    users_repo: UsersRepository,
    habit_id: int,
    user_id: int,
    with_checks: Literal[True],
) -> HabitWithChecks: ...


async def get_habit(
    repo: HabitRepository,
    users_repo: UsersRepository,
    habit_id: int,
    user_id: int,
    with_checks: bool = False,
) -> HabitRead | HabitWithChecks:
    """Get a habit (personal or group). Reconciles all members first for an accurate streak."""
    habit = await _get_habit_or_404(repo, habit_id)
    await _require_participant(repo, habit_id, user_id)

    await reconcile_all_members(repo, users_repo, habit)
    await repo.commit()

    member = await repo.get_member(habit_id, user_id)
    min_streak = await repo.get_min_active_streak(habit_id)
    member_count = len(await repo.get_active_members(habit_id))

    checks = None
    if with_checks:
        checks = await repo.get_checks_for_user(habit_id, user_id, limit=30)

    return habit_model_to_schema(
        habit,
        min_streak=min_streak,
        member_count=member_count,
        my_member=member,
        checks=checks,
    )


async def update_habit(
    repo: HabitRepository, habit_id: int, user_id: int, habit_data: HabitUpdate
) -> HabitRead:
    """Update a habit's settings (creator only). Changing allowed_misses adjusts every active
    member's grace budget by the delta, same as their current allocation plus/minus the change.
    """
    habit = await _get_habit_or_404(repo, habit_id)
    if habit.creator_id != user_id:
        raise ForbiddenError("Only the habit's creator can edit it")

    update_data = habit_data.model_dump(exclude_unset=True)
    if update_data.get("allowed_misses") is not None:
        delta = update_data["allowed_misses"] - habit.allowed_misses
        for member in await repo.get_active_members(habit_id):
            await repo.update_member(
                member, misses_remaining=max(0, member.misses_remaining + delta)
            )

    updated = await repo.update(habit, **update_data)
    await repo.commit()

    my_member = await repo.get_member(habit_id, user_id)
    min_streak = await repo.get_min_active_streak(habit_id)
    member_count = len(await repo.get_active_members(habit_id))
    return habit_model_to_schema(
        updated, min_streak=min_streak, member_count=member_count, my_member=my_member
    )


async def delete_habit(repo: HabitRepository, habit_id: int, user_id: int) -> None:
    """Delete a habit permanently (creator only)."""
    habit = await _get_habit_or_404(repo, habit_id)
    if habit.creator_id != user_id:
        raise ForbiddenError("Only the habit's creator can delete it")
    await repo.delete(habit)
    await repo.commit()


async def archive_habit(
    repo: HabitRepository, habit_id: int, user_id: int
) -> HabitRead:
    """Archive a habit (creator only)."""
    habit = await _get_habit_or_404(repo, habit_id)
    if habit.creator_id != user_id:
        raise ForbiddenError("Only the habit's creator can archive it")
    archived = await repo.archive(habit)
    await repo.commit()
    my_member = await repo.get_member(habit_id, user_id)
    min_streak = await repo.get_min_active_streak(habit_id)
    member_count = len(await repo.get_active_members(habit_id))
    return habit_model_to_schema(
        archived, min_streak=min_streak, member_count=member_count, my_member=my_member
    )


async def restore_habit(
    repo: HabitRepository, habit_id: int, user_id: int
) -> HabitRead:
    """Restore an archived habit (creator only)."""
    habit = await _get_habit_or_404(repo, habit_id)
    if habit.creator_id != user_id:
        raise ForbiddenError("Only the habit's creator can restore it")
    restored = await repo.restore(habit)
    await repo.commit()
    my_member = await repo.get_member(habit_id, user_id)
    min_streak = await repo.get_min_active_streak(habit_id)
    member_count = len(await repo.get_active_members(habit_id))
    return habit_model_to_schema(
        restored, min_streak=min_streak, member_count=member_count, my_member=my_member
    )


# ========== CHECK-INS ==========


async def check_in(
    repo: HabitRepository, users_repo: UsersRepository, habit_id: int, user_id: int
) -> dict[str, Any]:
    """Check in on a habit for the caller's own current period. Always "today" in the caller's
    own timezone -- no backfill, no client-supplied date (trust the clock, not the client).
    """
    habit = await _get_habit_or_404(repo, habit_id)
    member = await _require_participant(repo, habit_id, user_id)

    user = await users_repo.get_user(user_id)
    tz = user.timezone if user else DEFAULT_TZ
    habit_type = ModelHabitType(habit.habit_type)

    member = await _reconcile_member(repo, member, habit_type, tz)
    period = current_period_key(habit_type, tz)

    if await repo.get_check(habit_id, user_id, period):
        raise ConflictError("Already checked in for this period")

    await repo.create_check(habit_id, user_id, local_today(tz), period)
    member = await repo.update_member(
        member,
        current_streak=member.current_streak + 1,
        last_resolved_period_key=period,
    )
    await repo.commit()

    min_streak = await repo.get_min_active_streak(habit_id)
    return {
        "checked": True,
        "period_key": period,
        "my_current_streak": member.current_streak,
        "current_streak": min_streak,
        "message": f"Стрик: {member.current_streak}! \U0001f525",
    }


async def get_checkin_status(
    repo: HabitRepository, users_repo: UsersRepository, habit_id: int, user_id: int
) -> HabitCheckinStatus:
    """Who has and hasn't checked in for their own current period."""
    habit = await _get_habit_or_404(repo, habit_id)
    await _require_participant(repo, habit_id, user_id)

    habit_type = ModelHabitType(habit.habit_type)
    members = await repo.get_active_members(habit_id)
    tz_map = await users_repo.get_timezones([m.user_id for m in members])

    checked_in_ids: list[int] = []
    missing_ids: list[int] = []
    for member in members:
        tz = tz_map.get(member.user_id, DEFAULT_TZ)
        period = current_period_key(habit_type, tz)
        if await repo.get_check(habit_id, member.user_id, period):
            checked_in_ids.append(member.user_id)
        else:
            missing_ids.append(member.user_id)

    return HabitCheckinStatus(
        total_active_members=len(members),
        checked_in_user_ids=checked_in_ids,
        missing_user_ids=missing_ids,
        all_done=len(members) > 0 and not missing_ids,
    )


async def get_my_checks(
    repo: HabitRepository, habit_id: int, user_id: int, limit: int = 30
) -> list[HabitCheckRead]:
    """Get the caller's recent checks for a habit."""
    await _require_participant(repo, habit_id, user_id)
    checks = await repo.get_checks_for_user(habit_id, user_id, limit=limit)
    return [habit_check_model_to_schema(c) for c in checks]
