"""Service-level tests for groups: membership, invites, and keeping each habit's per-member
HabitMember rows in sync with the roster (join/leave/add-habit)."""

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from duohabit.repositories.groups import GroupRepository
from duohabit.repositories.habits import HabitRepository
from duohabit.repositories.users import UsersRepository
from duohabit.schemas.groups import GroupCreate, GroupInviteJoin, GroupMemberAdd
from duohabit.schemas.habits import HabitCreate, HabitType
from duohabit.services.groups import (
    MAX_MEMBERS,
    add_habit_to_group,
    add_member,
    create_group,
    get_group,
    join_group_by_code,
    leave_group,
    remove_member,
)
from duohabit.services.habits import check_in
from tests.conftest import make_user


def _repos(
    session: AsyncSession,
) -> tuple[GroupRepository, HabitRepository, UsersRepository]:
    return GroupRepository(session), HabitRepository(session), UsersRepository(session)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_group_creates_owner_membership_with_no_habits(
    db_session: AsyncSession,
) -> None:
    group_repo, _, _ = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")

    result = await create_group(
        group_repo, owner.id, GroupCreate(name="Утренняя пробежка")
    )

    assert result.owner_id == owner.id
    assert result.member_count == 1
    assert result.habits == []


@pytest.mark.asyncio(loop_scope="session")
async def test_add_habit_to_group_enrolls_all_current_members(
    db_session: AsyncSession,
) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    member2 = await make_user(db_session, "member2", "member2@test.com")

    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=member2.id),
    )

    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )

    assert habit.member_count == 2
    owner_member = await habit_repo.get_member(habit.id, owner.id)
    member2_member = await habit_repo.get_member(habit.id, member2.id)
    assert owner_member is not None and owner_member.is_active
    assert member2_member is not None and member2_member.is_active


@pytest.mark.asyncio(loop_scope="session")
async def test_add_habit_to_group_forbidden_for_non_owner(
    db_session: AsyncSession,
) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    member2 = await make_user(db_session, "member2", "member2@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=member2.id),
    )

    with pytest.raises(ForbiddenError):
        await add_habit_to_group(
            group_repo,
            habit_repo,
            users_repo,
            group.id,
            member2.id,
            HabitCreate(title="Бег"),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_group_streak_is_min_across_members(db_session: AsyncSession) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    member2 = await make_user(db_session, "member2", "member2@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=member2.id),
    )
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )

    # Only the owner checks in today -> team streak stays at the laggard's level (0).
    result = await check_in(habit_repo, users_repo, habit.id, owner.id)
    assert result["my_current_streak"] == 1
    assert result["current_streak"] == 0  # member2 hasn't checked in yet

    result2 = await check_in(habit_repo, users_repo, habit.id, member2.id)
    assert result2["current_streak"] == 1  # now both are at 1 -> MIN is 1


@pytest.mark.asyncio(loop_scope="session")
async def test_new_member_resets_displayed_group_streak(
    db_session: AsyncSession,
) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )
    await check_in(habit_repo, users_repo, habit.id, owner.id)

    newcomer = await make_user(db_session, "newcomer", "newcomer@test.com")
    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=newcomer.id),
    )

    group_with_habits = await get_group(
        group_repo, habit_repo, users_repo, group.id, owner.id
    )
    assert (
        group_with_habits.habits[0].current_streak == 0
    )  # newcomer starts fresh -> MIN is 0
    assert (
        group_with_habits.habits[0].my_current_streak == 1
    )  # owner's own streak is untouched


@pytest.mark.asyncio(loop_scope="session")
async def test_leave_group_freezes_streak_and_excludes_from_min(
    db_session: AsyncSession,
) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    member2 = await make_user(db_session, "member2", "member2@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=member2.id),
    )
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )
    await check_in(habit_repo, users_repo, habit.id, owner.id)
    # member2 never checks in and then leaves -- shouldn't drag the team streak to 0 forever.

    await remove_member(group_repo, habit_repo, group.id, owner.id, member2.id)

    group_with_habits = await get_group(
        group_repo, habit_repo, users_repo, group.id, owner.id
    )
    assert group_with_habits.habits[0].current_streak == 1  # only the owner counts now
    assert group_with_habits.habits[0].member_count == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_rejoin_starts_streak_at_zero(db_session: AsyncSession) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    member2 = await make_user(db_session, "member2", "member2@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=member2.id),
    )
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )
    await check_in(habit_repo, users_repo, habit.id, member2.id)
    await remove_member(group_repo, habit_repo, group.id, owner.id, member2.id)

    await add_member(
        group_repo,
        habit_repo,
        users_repo,
        group.id,
        owner.id,
        GroupMemberAdd(user_id=member2.id),
    )
    member = await habit_repo.get_member(habit.id, member2.id)
    assert member.current_streak == 0
    assert member.is_active


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_by_code_enrolls_in_existing_habits(
    db_session: AsyncSession,
) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    joiner = await make_user(db_session, "joiner", "joiner@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )

    result = await join_group_by_code(
        group_repo,
        habit_repo,
        users_repo,
        joiner.id,
        GroupInviteJoin(invite_code=group.invite_code),
    )

    assert result.member_count == 2
    joiner_member = await habit_repo.get_member(habit.id, joiner.id)
    assert joiner_member is not None and joiner_member.is_active


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_by_code_invalid_code(db_session: AsyncSession) -> None:
    group_repo, _, _ = _repos(db_session)
    joiner = await make_user(db_session, "joiner", "joiner@test.com")

    with pytest.raises(NotFoundError):
        await join_group_by_code(
            group_repo,
            HabitRepository(db_session),
            UsersRepository(db_session),
            joiner.id,
            GroupInviteJoin(invite_code="does-not-exist"),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_by_code_rejects_when_full(db_session: AsyncSession) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))

    for i in range(MAX_MEMBERS - 1):
        member = await make_user(db_session, f"member{i}", f"member{i}@test.com")
        await join_group_by_code(
            group_repo,
            habit_repo,
            users_repo,
            member.id,
            GroupInviteJoin(invite_code=group.invite_code),
        )

    overflow = await make_user(db_session, "overflow", "overflow@test.com")
    with pytest.raises(ValidationAppError):
        await join_group_by_code(
            group_repo,
            habit_repo,
            users_repo,
            overflow.id,
            GroupInviteJoin(invite_code=group.invite_code),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_owner_cannot_leave_group(db_session: AsyncSession) -> None:
    group_repo, habit_repo, _ = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))

    with pytest.raises(ValidationAppError):
        await leave_group(group_repo, habit_repo, group.id, owner.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_owner_cannot_remove_self(db_session: AsyncSession) -> None:
    group_repo, habit_repo, _ = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))

    with pytest.raises(ValidationAppError):
        await remove_member(group_repo, habit_repo, group.id, owner.id, owner.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_group_not_found(db_session: AsyncSession) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")

    with pytest.raises(NotFoundError):
        await get_group(group_repo, habit_repo, users_repo, 999_999, owner.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_forbidden_for_non_member(db_session: AsyncSession) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    outsider = await make_user(db_session, "outsider", "outsider@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )

    with pytest.raises(ForbiddenError):
        await check_in(habit_repo, users_repo, habit.id, outsider.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_conflict_when_already_checked_in(
    db_session: AsyncSession,
) -> None:
    group_repo, habit_repo, users_repo = _repos(db_session)
    owner = await make_user(db_session, "owner", "owner@test.com")
    group = await create_group(group_repo, owner.id, GroupCreate(name="Group"))
    habit = await add_habit_to_group(
        group_repo, habit_repo, users_repo, group.id, owner.id, HabitCreate(title="Бег")
    )

    await check_in(habit_repo, users_repo, habit.id, owner.id)
    with pytest.raises(ConflictError):
        await check_in(habit_repo, users_repo, habit.id, owner.id)
