"""Service-level tests for cooperative group habits, focused on the streak/grace algorithm."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from duohabit.models.habits import HabitType as ModelHabitType
from duohabit.repositories.groups import GroupRepository
from duohabit.schemas.groups import (
    GroupCreate,
    GroupHabitCheckCreate,
    GroupInviteJoin,
    GroupMemberAdd,
)
from duohabit.schemas.habits import HabitType
from duohabit.services.groups import (
    MAX_MEMBERS,
    _reconcile_group_habit,
    add_member,
    check_in,
    create_group,
    get_group,
    join_group_by_code,
    leave_group,
    remove_member,
)
from duohabit.utils.periods import compute_period_key, utc_today
from tests.conftest import make_user


async def _backdate_membership(
    repo: GroupRepository, session: AsyncSession, group_id: int, user_id: int, days: int
) -> None:
    """Push a member's created_at into the past, so period-boundary checks treat them
    as having been active all along (a freshly-inserted row always has created_at="now").
    """
    member = await repo.get_member(group_id, user_id)
    assert member is not None
    member.created_at = datetime.now(timezone.utc) - timedelta(days=days)
    session.add(member)
    await session.flush()


async def _make_group(repo: GroupRepository, owner_id: int, allowed_misses: int = 0):
    """Create a group with a daily habit for tests."""
    return await create_group(
        repo,
        owner_id,
        GroupCreate(
            name="Утренняя пробежка",
            habit_title="Бег",
            habit_description=None,
            habit_type=HabitType.DAILY,
            allowed_misses=allowed_misses,
        ),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_group_creates_owner_membership_and_habit(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")

    result = await _make_group(repo, owner.id, allowed_misses=1)

    assert result.owner_id == owner.id
    assert result.member_count == 1
    assert result.habit is not None
    assert result.habit.current_streak == 0
    assert result.habit.misses_remaining == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_create_group_rejects_non_daily_habit_type(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")

    with pytest.raises(ValidationAppError):
        await create_group(
            repo,
            owner.id,
            GroupCreate(
                name="Group",
                habit_title="Habit",
                habit_type=HabitType.WEEKLY,
                allowed_misses=0,
            ),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_increments_streak_once_all_members_done(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    member2 = await make_user(db_session, "member2", "member2@test.com")

    group = await _make_group(repo, owner.id)
    await add_member(repo, group.id, owner.id, GroupMemberAdd(user_id=member2.id))

    first = await check_in(repo, group.id, owner.id, GroupHabitCheckCreate())
    assert first["all_members_done"] is False

    second = await check_in(repo, group.id, member2.id, GroupHabitCheckCreate())
    assert second["all_members_done"] is True
    assert second["current_streak"] == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_conflict_when_already_checked_in(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id)

    await check_in(repo, group.id, owner.id, GroupHabitCheckCreate())
    with pytest.raises(ConflictError):
        await check_in(repo, group.id, owner.id, GroupHabitCheckCreate())


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_forbidden_for_non_member(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    outsider = await make_user(db_session, "outsider", "outsider@test.com")
    group = await _make_group(repo, owner.id)

    with pytest.raises(ForbiddenError):
        await check_in(repo, group.id, outsider.id, GroupHabitCheckCreate())


@pytest.mark.asyncio(loop_scope="session")
async def test_get_group_not_found(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")

    with pytest.raises(NotFoundError):
        await get_group(repo, 999_999, owner.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_by_code_happy_path(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    joiner = await make_user(db_session, "joiner", "joiner@test.com")
    group = await _make_group(repo, owner.id)

    result = await join_group_by_code(
        repo, joiner.id, GroupInviteJoin(invite_code=group.invite_code)
    )
    assert result.member_count == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_by_code_invalid_code(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    joiner = await make_user(db_session, "joiner", "joiner@test.com")

    with pytest.raises(NotFoundError):
        await join_group_by_code(
            repo, joiner.id, GroupInviteJoin(invite_code="does-not-exist")
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_by_code_rejects_when_full(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id)

    for i in range(MAX_MEMBERS - 1):
        member = await make_user(db_session, f"member{i}", f"member{i}@test.com")
        await join_group_by_code(
            repo, member.id, GroupInviteJoin(invite_code=group.invite_code)
        )

    overflow = await make_user(db_session, "overflow", "overflow@test.com")
    with pytest.raises(ValidationAppError):
        await join_group_by_code(
            repo, overflow.id, GroupInviteJoin(invite_code=group.invite_code)
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_owner_cannot_leave_group(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id)

    with pytest.raises(ValidationAppError):
        await leave_group(repo, group.id, owner.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_owner_cannot_remove_self(db_session: AsyncSession) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id)

    with pytest.raises(ValidationAppError):
        await remove_member(repo, group.id, owner.id, owner.id)


# ========== STREAK / GRACE RECONCILIATION ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_hard_resets_streak_after_unforgiven_miss(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id, allowed_misses=0)
    await _backdate_membership(repo, db_session, group.id, owner.id, days=10)
    group_habit = await repo.get_group_habit_by_group(group.id)
    assert group_habit is not None

    yesterday = utc_today() - timedelta(days=1)
    await repo.update_group_habit(
        group_habit,
        current_streak=5,
        last_resolved_period_key=compute_period_key(
            yesterday - timedelta(days=1), ModelHabitType.DAILY
        ),
    )
    # Nobody checked in yesterday -> a real miss, no grace available.

    reconciled = await _reconcile_group_habit(repo, group_habit)

    assert reconciled.current_streak == 0
    # "Today" is still open and is never resolved -- only yesterday was.
    assert reconciled.last_resolved_period_key == compute_period_key(
        yesterday, ModelHabitType.DAILY
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_consumes_grace_instead_of_resetting(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id, allowed_misses=1)
    await _backdate_membership(repo, db_session, group.id, owner.id, days=10)
    group_habit = await repo.get_group_habit_by_group(group.id)
    assert group_habit is not None

    yesterday = utc_today() - timedelta(days=1)
    await repo.update_group_habit(
        group_habit,
        current_streak=3,
        misses_remaining=1,
        last_resolved_period_key=compute_period_key(
            yesterday - timedelta(days=1), ModelHabitType.DAILY
        ),
    )

    reconciled = await _reconcile_group_habit(repo, group_habit)

    assert reconciled.current_streak == 3  # preserved
    assert reconciled.misses_remaining == 0  # grace spent


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_exhausts_grace_across_multiple_missed_days(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id, allowed_misses=2)
    await _backdate_membership(repo, db_session, group.id, owner.id, days=10)
    group_habit = await repo.get_group_habit_by_group(group.id)
    assert group_habit is not None

    # Seed last_resolved_period_key four days back so exactly three periods (D-3, D-2, D-1)
    # are fully elapsed and unresolved once we reach "today": two are forgiven, the third resets.
    four_days_ago = utc_today() - timedelta(days=4)
    await repo.update_group_habit(
        group_habit,
        current_streak=10,
        misses_remaining=2,
        last_resolved_period_key=compute_period_key(
            four_days_ago, ModelHabitType.DAILY
        ),
    )

    reconciled = await _reconcile_group_habit(repo, group_habit)

    assert reconciled.misses_remaining == 0
    assert reconciled.current_streak == 0
    yesterday = utc_today() - timedelta(days=1)
    assert reconciled.last_resolved_period_key == compute_period_key(
        yesterday, ModelHabitType.DAILY
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_does_not_blame_a_member_who_joined_after_the_period(
    db_session: AsyncSession,
) -> None:
    repo = GroupRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await _make_group(repo, owner.id, allowed_misses=0)
    await _backdate_membership(repo, db_session, group.id, owner.id, days=10)
    group_habit = await repo.get_group_habit_by_group(group.id)
    assert group_habit is not None

    yesterday = utc_today() - timedelta(days=1)
    yesterday_key = compute_period_key(yesterday, ModelHabitType.DAILY)
    # Only the owner was around yesterday, and the owner checked in.
    await repo.create_group_habit_check(
        group_habit.id, owner.id, yesterday, yesterday_key
    )
    await repo.update_group_habit(
        group_habit,
        current_streak=3,
        last_resolved_period_key=compute_period_key(
            yesterday - timedelta(days=1), ModelHabitType.DAILY
        ),
    )

    # A second member joins today, *after* yesterday's period already closed.
    late_joiner = await make_user(db_session, "late", "late@test.com")
    await add_member(repo, group.id, owner.id, GroupMemberAdd(user_id=late_joiner.id))
    group_habit = await repo.get_group_habit_by_group(group.id)
    assert group_habit is not None

    reconciled = await _reconcile_group_habit(repo, group_habit)

    # Yesterday only had one active member (the owner), who checked in -> not a miss.
    assert reconciled.current_streak == 3
