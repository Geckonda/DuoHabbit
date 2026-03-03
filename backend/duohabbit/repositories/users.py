"""Users repository."""

from typing import Any

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from duohabbit.models.users import User
from duohabbit.schemas.common import PaginationParams
from duohabbit.utils.pagination import apply_pagination


class UnitOfWorkUserDB(SQLAlchemyUserDatabase[User, int]):
    """User database adapter that doesn't commit the transaction."""

    async def create(self, create_dict: dict[str, Any]) -> User:
        """Create a new user and return it."""
        user = self.user_table(**create_dict)
        self.session.add(user)
        try:
            await self.session.flush()
            await self.session.refresh(user)
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
        stmt = select(User).order_by(User.id)

        if pagination is not None:
            stmt = apply_pagination(stmt, pagination)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user(self, user_id: int) -> User | None:
        """Get a single user by ID (or None)"""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Fetch user by e-mail or None."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()