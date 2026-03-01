"""Users repository."""

from typing import Any

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from duohabbit.models.users import PersonProfile as PersonProfileModel
from duohabbit.models.users import User, UserType
from duohabbit.schemas.common import PaginationParams
from duohabbit.schemas.users import UserNew
from duohabbit.utils.pagination import apply_pagination


class UnitOfWorkUserDB(SQLAlchemyUserDatabase[User, int]):
    """User database adapter that doesn't commit the transaction."""

    async def create(self, create_dict: dict[str, Any]) -> User:
        """Create a new user and return it."""
        create_dict.pop("user_profile")
        create_dict["user_type"] = UserType(create_dict["user_type"])
        user = self.user_table(**create_dict)
        self.session.add(user)
        try:
            await self.session.flush()
            await self.session.refresh(user, ["id"])
            return user
        except IntegrityError:
            raise Exception("Email already in use")


class UsersRepository:
    """Users repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def get_users(
        self, pagination: PaginationParams | None = None
    ) -> list[User]:
        """Get all users."""
        stmt = select(User).options(
            selectinload(User.person_profile)
        )

        stmt = stmt.order_by(User.id_)

        if pagination is not None:
            stmt = apply_pagination(stmt, pagination)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user(self, user_id: int) -> User | None:
        """Get a single user by ID (or None)"""
        stmt = (
            select(User)
            .where(User.id_ == user_id)
            .options(
                selectinload(User.person_profile)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_profile(self, user_in: UserNew, user: User) -> User:
        """Create associated profile for user"""

        profile = PersonProfileModel(
            user_id=user.id,
            first_name=user_in.user_profile.first_name,  # type: ignore[union-attr]
            last_name=user_in.user_profile.last_name,  # type: ignore[union-attr]
        )
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(user, ["person_profile"])
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Fetch user by e-mail or None."""
        stmt = (
            select(User)
            .where(User.email_ == email)
            .options(
                selectinload(User.person_profile),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
