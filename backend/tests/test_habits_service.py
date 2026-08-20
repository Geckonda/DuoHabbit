"""Tests for the habit business logic."""

from datetime import date, timedelta

import pytest

from duohabit.schemas.habits import HabitCreate, HabitType, HabitUpdate, HabitWithChecks
from duohabit.services.habits import (
    archive_habit,
    check_habit,
    create_habit,
    delete_check,
    delete_habit,
    get_habit,
    get_habit_checks,
    get_user_habits,
    restore_habit,
    update_habit,
)
from tests.fakes import FakeHabitRepository, as_habit_repo

OWNER = 1
STRANGER = 2


async def seed_habit(
    repo: FakeHabitRepository, title: str = "Бегать", user_id: int = OWNER
) -> int:
    """Create a habit through the service, return its id."""
    habit = await create_habit(
        as_habit_repo(repo), user_id, HabitCreate(title=title, description=None)
    )
    return habit.id


# ========== CRUD ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_create_habit_persists() -> None:
    """A new habit belongs to its author and starts with a zero streak."""
    repo = FakeHabitRepository()

    habit = await create_habit(
        as_habit_repo(repo),
        OWNER,
        HabitCreate(title="Бегать", description="3 км", habit_type=HabitType.DAILY),
    )

    assert habit.title == "Бегать"
    assert habit.user_id == OWNER
    assert habit.current_streak == 0
    assert habit.is_active is True
    assert repo.commits == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_habits_hides_archived_by_default() -> None:
    """The default listing shows active habits only."""
    repo = FakeHabitRepository()
    first = await seed_habit(repo, "Бегать")
    second = await seed_habit(repo, "Читать")

    await archive_habit(as_habit_repo(repo), second, OWNER)

    active = await get_user_habits(as_habit_repo(repo), OWNER)
    everything = await get_user_habits(as_habit_repo(repo), OWNER, only_active=False)

    assert [h.id for h in active] == [first]
    assert {h.id for h in everything} == {first, second}


@pytest.mark.asyncio(loop_scope="session")
async def test_get_habit_of_another_user_is_not_found() -> None:
    """Habits are scoped to their owner."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)

    with pytest.raises(Exception, match="Habit not found"):
        await get_habit(as_habit_repo(repo), habit_id, STRANGER)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_habit_with_checks_returns_recent_checks() -> None:
    """The details view carries the habit's checks."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    repo.add_checks(habit_id, [0, 1, 2])

    habit = await get_habit(as_habit_repo(repo), habit_id, OWNER, with_checks=True)

    assert isinstance(habit, HabitWithChecks)
    assert len(habit.recent_checks) == 3
    # Свежие сверху
    assert habit.recent_checks[0].check_date == date.today()
    assert all(check.habit_id == habit_id for check in habit.recent_checks)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_habit_touches_only_given_fields() -> None:
    """A partial update leaves untouched fields alone."""
    repo = FakeHabitRepository()
    habit = await create_habit(
        as_habit_repo(repo),
        OWNER,
        HabitCreate(title="Бегать", description="3 км"),
    )
    commits_before = repo.commits

    updated = await update_habit(
        as_habit_repo(repo), habit.id, OWNER, HabitUpdate(title="Бегать больше")
    )

    assert updated.title == "Бегать больше"
    assert updated.description == "3 км"
    assert repo.commits == commits_before + 1


@pytest.mark.asyncio(loop_scope="session")
async def test_update_missing_habit_is_rejected() -> None:
    """Updating something that does not exist fails."""
    repo = FakeHabitRepository()

    with pytest.raises(Exception, match="Habit not found"):
        await update_habit(as_habit_repo(repo), 404, OWNER, HabitUpdate(title="x"))


@pytest.mark.asyncio(loop_scope="session")
async def test_archive_and_restore_flip_the_flag() -> None:
    """Archiving is a soft delete and is reversible."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)

    archived = await archive_habit(as_habit_repo(repo), habit_id, OWNER)
    assert archived.is_active is False

    restored = await restore_habit(as_habit_repo(repo), habit_id, OWNER)
    assert restored.is_active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_habit_removes_it() -> None:
    """A deleted habit is gone for good."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    commits_before = repo.commits

    await delete_habit(as_habit_repo(repo), habit_id, OWNER)

    assert not repo.habits
    assert repo.commits == commits_before + 1


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_habit_of_another_user_is_rejected() -> None:
    """A stranger cannot delete someone else's habit."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)

    with pytest.raises(Exception, match="Habit not found"):
        await delete_habit(as_habit_repo(repo), habit_id, STRANGER)

    assert habit_id in repo.habits


# ========== CHECKS AND STREAK ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_first_check_starts_the_streak() -> None:
    """Checking in today gives a streak of one."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    commits_before = repo.commits

    result = await check_habit(as_habit_repo(repo), habit_id, OWNER)

    assert result["checked"] is True
    assert result["current_streak"] == 1
    assert result["check_date"] == date.today().isoformat()
    assert repo.habits[habit_id].current_streak == 1
    assert repo.commits == commits_before + 1


@pytest.mark.asyncio(loop_scope="session")
async def test_streak_counts_consecutive_days() -> None:
    """Yesterday and the day before extend today's streak."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    repo.add_checks(habit_id, [1, 2])

    result = await check_habit(as_habit_repo(repo), habit_id, OWNER)

    assert result["current_streak"] == 3


@pytest.mark.asyncio(loop_scope="session")
async def test_streak_breaks_on_a_missed_day() -> None:
    """A gap resets the streak to the unbroken tail only."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    # Вчера пропущено, поэтому более старые отметки в стрик не идут
    repo.add_checks(habit_id, [2, 3])

    result = await check_habit(as_habit_repo(repo), habit_id, OWNER)

    assert result["current_streak"] == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_second_check_on_the_same_day_is_rejected() -> None:
    """One check per habit per day."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    await check_habit(as_habit_repo(repo), habit_id, OWNER)

    with pytest.raises(ValueError, match="already exists"):
        await check_habit(as_habit_repo(repo), habit_id, OWNER)

    assert len(repo.checks) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_archived_habit_cannot_be_checked() -> None:
    """An archived habit is out of the game."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    await archive_habit(as_habit_repo(repo), habit_id, OWNER)

    with pytest.raises(Exception, match="Cannot check archived habit"):
        await check_habit(as_habit_repo(repo), habit_id, OWNER)


@pytest.mark.asyncio(loop_scope="session")
async def test_check_of_another_user_habit_is_rejected() -> None:
    """A stranger cannot check someone else's habit."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)

    with pytest.raises(Exception, match="Habit not found"):
        await check_habit(as_habit_repo(repo), habit_id, STRANGER)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_habit_checks_returns_own_habit_id() -> None:
    """Every returned check must point at the habit it belongs to."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    repo.add_checks(habit_id, [0, 1])

    checks = await get_habit_checks(as_habit_repo(repo), habit_id, OWNER)

    assert len(checks) == 2
    assert {check.habit_id for check in checks} == {habit_id}
    assert len({check.id for check in checks}) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_get_habit_checks_of_another_user_is_rejected() -> None:
    """Checks are as private as the habit itself."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    repo.add_checks(habit_id, [0])

    with pytest.raises(Exception, match="Habit not found"):
        await get_habit_checks(as_habit_repo(repo), habit_id, STRANGER)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_check_recalculates_streak_and_persists() -> None:
    """Removing today's check drops the streak, and the change must be saved."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    repo.add_checks(habit_id, [1])
    await check_habit(as_habit_repo(repo), habit_id, OWNER)
    assert repo.habits[habit_id].current_streak == 2

    today_check = await repo.get_check_by_date(habit_id, date.today())
    assert today_check is not None
    commits_before = repo.commits

    await delete_check(as_habit_repo(repo), today_check.id, OWNER)

    # Стрик считается от сегодня, вчерашняя отметка сама по себе его не держит
    assert repo.habits[habit_id].current_streak == 0
    assert await repo.get_check_by_date(habit_id, date.today()) is None
    assert repo.commits == commits_before + 1


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_missing_check_is_rejected() -> None:
    """Deleting a non-existent check fails."""
    repo = FakeHabitRepository()

    with pytest.raises(Exception, match="Check not found"):
        await delete_check(as_habit_repo(repo), 404, OWNER)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_check_of_another_user_is_rejected() -> None:
    """A stranger cannot delete a check of someone else's habit."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)
    repo.add_checks(habit_id, [0])
    check = await repo.get_check_by_date(habit_id, date.today())
    assert check is not None

    with pytest.raises(Exception, match="Access denied"):
        await delete_check(as_habit_repo(repo), check.id, STRANGER)

    assert len(repo.checks) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_check_for_a_past_date_does_not_fake_a_streak() -> None:
    """A check dated in the past leaves today's streak at zero."""
    repo = FakeHabitRepository()
    habit_id = await seed_habit(repo)

    result = await check_habit(
        as_habit_repo(repo),
        habit_id,
        OWNER,
        check_date=date.today() - timedelta(days=1),
    )

    assert result["current_streak"] == 0
