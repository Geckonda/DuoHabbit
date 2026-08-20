"""Tests for the user business logic."""

from typing import cast

import pytest

from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.users import UserCreate
from duohabit.services.users import (
    UserManager,
    create_user,
    get_user,
    get_users,
    user_model_to_schema,
)
from tests.fakes import FakeUsersRepository, as_users_repo, make_user

OWNER = 1
STRANGER = 2
ADMIN = 3


def claim(user_id: int, is_admin: bool = False) -> AccessTokenClaim:
    """Build a token claim for the given user."""
    return AccessTokenClaim(user_id=user_id, account_is_platform_admin=is_admin)


class ExplodingUserManager:  # pylint: disable=too-few-public-methods
    """A manager that must never be reached: creation is rejected before it."""

    async def create(self, *args: object, **kwargs: object) -> object:
        """Fail loudly if the permission check let the call through."""
        raise AssertionError("Manager must not be called when rights are missing")


# ========== VISIBILITY ==========


def test_owner_sees_own_private_fields() -> None:
    """A user always sees their own email."""
    user = user_model_to_schema(
        make_user(OWNER, "alice", email="alice@duohabit.com"), claim(OWNER)
    )

    assert user.email == "alice@duohabit.com"
    assert user.username == "alice"


def test_stranger_does_not_see_email() -> None:
    """Another user's email stays hidden."""
    user = user_model_to_schema(
        make_user(OWNER, "alice", email="alice@duohabit.com"), claim(STRANGER)
    )

    assert user.email is None
    assert user.username == "alice"


def test_admin_sees_email_of_anyone() -> None:
    """A platform admin sees private fields of any profile."""
    user = user_model_to_schema(
        make_user(OWNER, "alice", email="alice@duohabit.com"),
        claim(ADMIN, is_admin=True),
    )

    assert user.email == "alice@duohabit.com"


def test_anonymous_viewer_does_not_see_email() -> None:
    """Without a token private fields are hidden as well."""
    user = user_model_to_schema(make_user(OWNER, "alice", email="alice@duohabit.com"))

    assert user.email is None


# ========== QUERIES ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_get_users_hides_foreign_emails() -> None:
    """Listing users exposes nobody's email except the viewer's own."""
    repo = FakeUsersRepository([make_user(OWNER, "alice"), make_user(STRANGER, "bob")])

    listed = await get_users(as_users_repo(repo), claim(OWNER))

    by_id = {user.id: user for user in listed}
    assert by_id[OWNER].email is not None
    assert by_id[STRANGER].email is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_by_id() -> None:
    """A profile can be fetched by id."""
    repo = FakeUsersRepository([make_user(OWNER, "alice")])

    user = await get_user(as_users_repo(repo), OWNER, claim(OWNER))

    assert user.username == "alice"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_missing_user_is_rejected() -> None:
    """An unknown id is an error, not an empty profile."""
    repo = FakeUsersRepository()

    with pytest.raises(Exception, match="User not found"):
        await get_user(as_users_repo(repo), 404, claim(OWNER))


# ========== REGISTRATION RIGHTS ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_admin_creation_requires_admin_rights() -> None:
    """A plain visitor cannot register themselves as a platform admin."""
    repo = FakeUsersRepository()
    manager = cast(UserManager, ExplodingUserManager())

    with pytest.raises(Exception, match="Platform admins must be created"):
        await create_user(
            as_users_repo(repo),
            UserCreate(
                email="eve@duohabit.com",
                password="password",
                username="eve",
                is_platform_admin=True,
            ),
            claim_admin=False,
            manager=manager,
        )

    assert repo.commits == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_admin_creation_is_rejected_for_anonymous_caller() -> None:
    """No token at all is not enough to mint an admin either."""
    repo = FakeUsersRepository()
    manager = cast(UserManager, ExplodingUserManager())

    with pytest.raises(Exception, match="Platform admins must be created"):
        await create_user(
            as_users_repo(repo),
            UserCreate(
                email="eve@duohabit.com",
                password="password",
                username="eve",
                is_platform_admin=True,
            ),
            claim_admin=None,
            manager=manager,
        )
