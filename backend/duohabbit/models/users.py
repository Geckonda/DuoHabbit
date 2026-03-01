"""User models for people and companies."""

# pylint: disable=too-few-public-methods
# Models exist for a different reason.

from enum import Enum
from typing import TYPE_CHECKING, ClassVar, Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column, relationship

from duohabbit.db import Base
from duohabbit.models.mixins import TimestampMixin


class UserType(Enum):
    """User types."""

    PERSON = "person"
    COMPANY = "company"


class User(TimestampMixin, SQLAlchemyBaseUserTable[int], Base):
    """Common user model.

    Note: id and email use TYPE_CHECKING pattern to satisfy fastapi-users'
    UserProtocol (which expects plain types) while keeping Mapped[] at runtime
    for SQLAlchemy. This mirrors what SQLAlchemyBaseUserTable does internally.

    Use id_ and email_ (with underscore) in queries to get proper column types.
    """

    __tablename__ = "user"

    if TYPE_CHECKING:
        id: int
        email: str
    else:
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Column aliases for queries - mypy sees proper SQLAlchemy column types
    id_: ClassVar[InstrumentedAttribute[int]]
    email_: ClassVar[InstrumentedAttribute[str]]

    # password_hash: Mapped[str] = mapped_column(String(255))
    is_platform_admin: Mapped[bool] = mapped_column(Boolean)
    # Discriminates if company_profile or person_profile is set
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType, name="user_type"), nullable=False
    )
    person_profile: Mapped[Optional["PersonProfile"]] = relationship(
        "PersonProfile", back_populates="user"
    )

# Bind column aliases at runtime (single location for type: ignore)
User.id_ = User.id  # type: ignore[assignment]
User.email_ = User.email  # type: ignore[assignment]


class PersonProfile(Base):
    """Person profile model."""

    __tablename__ = "person_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    user: Mapped[User] = relationship(back_populates="person_profile")

    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
