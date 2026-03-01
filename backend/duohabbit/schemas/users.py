"""Users schemas."""

from typing import Annotated, Literal, Union

from fastapi_users.schemas import BaseUserCreate
from pydantic import BaseModel, Field


class PersonProfile(BaseModel):
    """Person profile model."""

    user_type: Literal["person"] = "person"
    first_name: str
    last_name: str


class UserBase(BaseModel):
    """Common public fields for a user."""

    user_type: Literal["person", "company"]
    user_profile: Annotated[
        Union[PersonProfile], Field(discriminator="user_type")
    ]


class UserSensitiveCreateMixin(BaseModel):
    """Sensitive fields required to create a user."""

    email: str
    is_platform_admin: bool


class UserSensitiveOutMixin(BaseModel):
    """Sensitive fields in output.

    Kept optional so we can avoid leaking sensitive data to other users /
    unauthenticated clients.
    """

    email: str | None = None
    is_platform_admin: bool | None = None


class UserOut(UserBase, UserSensitiveOutMixin):
    """User output model.

    email and is_platform_admin are intentionally optional so we can avoid leaking
    sensitive data to other users / unauthenticated clients.
    """

    user_id: int


class UserCreateBase(UserBase, UserSensitiveCreateMixin):
    """Fields required to create a user."""


class UserNew(UserCreateBase):
    """User new model."""

    password: str


class InternalUserNew(BaseUserCreate, UserNew):
    """Internal user new model (for use in fastapi_users)."""
