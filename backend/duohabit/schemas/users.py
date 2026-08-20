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


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a user (registration)."""
    
    username: str
    is_platform_admin: bool = False


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating a user."""
    
    username: str | None = None
    is_platform_admin: bool | None = None