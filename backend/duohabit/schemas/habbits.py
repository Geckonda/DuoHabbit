"""Habit schemas."""

from pydantic import BaseModel


class HabitBase(BaseModel):
    """Base habit schema."""
    
    title: str
    description: str | None = None
    is_active: bool = True


class HabitCreate(HabitBase):
    """Schema for creating a habit."""
    pass


class HabitUpdate(BaseModel):
    """Schema for updating a habit."""
    
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None


class HabitRead(HabitBase):
    """Schema for reading a habit."""
    
    id: int
    user_id: int
    
    class Config:
        from_attributes = True