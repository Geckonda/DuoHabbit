"""Users schemas."""

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserOut(schemas.BaseUser[int]):
    """Schema for reading user data (response)."""
    
    username: str
    is_platform_admin: bool = False


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a user (registration)."""
    
    username: str
    is_platform_admin: bool = False


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating a user."""
    
    username: str | None = None
    is_platform_admin: bool | None = None