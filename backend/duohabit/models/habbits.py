"""Habit models."""

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin


class Habit(TimestampMixin, Base):
    """User habit model."""
    
    __tablename__ = "habit"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    habit_type: Mapped[str] = mapped_column(String(50), default="daily")  # daily, weekly, etc.