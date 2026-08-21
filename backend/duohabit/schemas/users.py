"""Users schemas."""

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserOut(schemas.BaseUser[int]):
    """Schema for reading user data (response)."""

    # Приватные поля скрываются от чужих глаз в user_model_to_schema и вырезаются
    # из ответа через response_model_exclude_none, поэтому они допускают None:
    # у BaseUser email обязателен, и без переопределения сборка схемы падала бы
    email: EmailStr | None = None  # type: ignore[assignment]
    username: str
    is_platform_admin: bool | None = False
    timezone: str | None = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a user (registration).

    timezone should be the client's detected IANA name (e.g. Intl.DateTimeFormat().
    resolvedOptions().timeZone on the frontend); defaults server-side to UTC if omitted.
    """

    username: str
    is_platform_admin: bool = False
    timezone: str = "UTC"


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating a user."""

    username: str | None = None
    is_platform_admin: bool | None = None
    timezone: str | None = None


class UserSelfUpdate(BaseModel):
    """Schema for a user editing their own profile (PATCH /users/me).

    Deliberately narrow: no is_platform_admin, email, or password here, so a self-service
    edit can never smuggle a privilege escalation through the shared UserUpdate/manager.update
    path -- the router builds a UserUpdate from only these two fields before calling the
    fastapi-users manager.
    """

    username: str | None = None
    timezone: str | None = None
