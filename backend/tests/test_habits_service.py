"""Service-level tests for the unified habit engine: personal habits and the per-member
streak/grace reconciliation algorithm shared by personal and group habits alike."""

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.errors import ConflictError, ForbiddenError
from duohabit.models.habits import HabitType as ModelHabitType
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.habits import HabitCreate, HabitType, HabitUpdate
from duohabit.services.habits import (
    _reconcile_member,
    check_in,
    create_habit,
    get_habit,
    update_habit,
)
from duohabit.utils.periods import compute_period_key, local_today
from tests.conftest import make_user

TZ = "UTC"


async def _make_personal_habit(
    habit_repo: HabitRepository,
    users_repo: UsersRepository,
    user_id: int,
    habit_type: HabitType = HabitType.DAILY,
    allowed_misses: int = 0,
):
    return await create_habit(
        habit_repo,
        users_repo,
        user_id,
        HabitCreate(title="Бег", habit_type=habit_type, allowed_misses=allowed_misses),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_personal_habit_has_single_member_and_zero_streak(
    db_session: AsyncSession,
) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")

    habit = await _make_personal_habit(habit_repo, users_repo, user.id)

    assert habit.group_id is None
    assert habit.member_count == 1
    assert habit.current_streak == 0
    assert habit.my_current_streak == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_increments_own_streak_and_is_reflected_as_min(
    db_session: AsyncSession,
) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(habit_repo, users_repo, user.id)

    result = await check_in(habit_repo, users_repo, habit.id, user.id)

    assert result["checked"] is True
    assert result["my_current_streak"] == 1
    assert (
        result["current_streak"] == 1
    )  # MIN over a single member == that member's streak


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_twice_same_period_conflicts(db_session: AsyncSession) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(habit_repo, users_repo, user.id)

    await check_in(habit_repo, users_repo, habit.id, user.id)
    with pytest.raises(ConflictError):
        await check_in(habit_repo, users_repo, habit.id, user.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_forbidden_for_non_participant(db_session: AsyncSession) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    outsider = await make_user(db_session, "outsider", "outsider@test.com")
    habit = await _make_personal_habit(habit_repo, users_repo, owner.id)

    with pytest.raises(ForbiddenError):
        await check_in(habit_repo, users_repo, habit.id, outsider.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_habit_reflects_reconciliation(db_session: AsyncSession) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(
        habit_repo, users_repo, user.id, allowed_misses=0
    )

    member = await habit_repo.get_member(habit.id, user.id)
    yesterday = local_today(TZ) - timedelta(days=1)
    await habit_repo.update_member(
        member,
        current_streak=5,
        last_resolved_period_key=compute_period_key(
            yesterday - timedelta(days=1), ModelHabitType.DAILY
        ),
    )
    await habit_repo.commit()
    # Nobody checked in yesterday -> a real miss, no grace available.

    read = await get_habit(habit_repo, users_repo, habit.id, user.id)

    assert read.current_streak == 0
    assert read.my_current_streak == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_update_habit_allowed_misses_adjusts_member_grace(
    db_session: AsyncSession,
) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(
        habit_repo, users_repo, user.id, allowed_misses=1
    )

    updated = await update_habit(
        habit_repo, habit.id, user.id, HabitUpdate(allowed_misses=3)
    )

    member = await habit_repo.get_member(habit.id, user.id)
    assert updated.allowed_misses == 3
    assert (
        member.misses_remaining == 3
    )  # 1 -> 3, delta of +2 applied on top of the existing 1


# ========== STREAK / GRACE RECONCILIATION (per-member) ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_hard_resets_streak_after_unforgiven_miss(
    db_session: AsyncSession,
) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(
        habit_repo, users_repo, user.id, allowed_misses=0
    )
    member = await habit_repo.get_member(habit.id, user.id)

    yesterday = local_today(TZ) - timedelta(days=1)
    member = await habit_repo.update_member(
        member,
        current_streak=5,
        last_resolved_period_key=compute_period_key(
            yesterday - timedelta(days=1), ModelHabitType.DAILY
        ),
    )

    reconciled = await _reconcile_member(habit_repo, member, ModelHabitType.DAILY, TZ)

    assert reconciled.current_streak == 0
    assert reconciled.last_resolved_period_key == compute_period_key(
        yesterday, ModelHabitType.DAILY
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_consumes_grace_instead_of_resetting(
    db_session: AsyncSession,
) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(
        habit_repo, users_repo, user.id, allowed_misses=1
    )
    member = await habit_repo.get_member(habit.id, user.id)

    yesterday = local_today(TZ) - timedelta(days=1)
    member = await habit_repo.update_member(
        member,
        current_streak=3,
        misses_remaining=1,
        last_resolved_period_key=compute_period_key(
            yesterday - timedelta(days=1), ModelHabitType.DAILY
        ),
    )

    reconciled = await _reconcile_member(habit_repo, member, ModelHabitType.DAILY, TZ)

    assert reconciled.current_streak == 3  # preserved
    assert reconciled.misses_remaining == 0  # grace spent


@pytest.mark.asyncio(loop_scope="session")
async def test_reconcile_exhausts_grace_across_multiple_missed_days(
    db_session: AsyncSession,
) -> None:
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(
        habit_repo, users_repo, user.id, allowed_misses=2
    )
    member = await habit_repo.get_member(habit.id, user.id)

    four_days_ago = local_today(TZ) - timedelta(days=4)
    member = await habit_repo.update_member(
        member,
        current_streak=10,
        misses_remaining=2,
        last_resolved_period_key=compute_period_key(
            four_days_ago, ModelHabitType.DAILY
        ),
    )

    reconciled = await _reconcile_member(habit_repo, member, ModelHabitType.DAILY, TZ)

    assert reconciled.misses_remaining == 0
    assert reconciled.current_streak == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_weekly_habit_streak_survives_daily_gaps_within_the_week(
    db_session: AsyncSession,
) -> None:
    """Regression test for the old naive engine, which ignored habit_type entirely and
    required a check on every single calendar day even for WEEKLY habits."""
    habit_repo = HabitRepository(db_session)
    users_repo = UsersRepository(db_session)
    user = await make_user(db_session, "owner", "owner@test.com")
    habit = await _make_personal_habit(
        habit_repo, users_repo, user.id, habit_type=HabitType.WEEKLY
    )

    result = await check_in(habit_repo, users_repo, habit.id, user.id)

    assert result["my_current_streak"] == 1
    # Reading again the same week (no new check-in) must not reset the streak just because
    # "today" isn't the day of the original check-in.
    read = await get_habit(habit_repo, users_repo, habit.id, user.id)
    assert read.my_current_streak == 1
