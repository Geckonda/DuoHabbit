"""User models."""

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin


class User(TimestampMixin, SQLAlchemyBaseUserTable[int], Base):
    """Common user model."""

    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    sex: Mapped[int] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
