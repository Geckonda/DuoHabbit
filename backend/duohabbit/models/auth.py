"""Auth models."""

from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTable
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from duohabbit.db import Base

# pylint: disable=too-few-public-methods
# Models exist for a different reason.


class AccessToken(SQLAlchemyBaseAccessTokenTable[int], Base):
    """
    Access token model to store a fastapi-users access token.
    Can be extended for session management.
    """

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
