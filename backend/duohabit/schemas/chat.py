"""Chat schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from duohabit.schemas.users import UserOut


class MessageCreate(BaseModel):
    """Schema for sending a message."""

    text: str = Field(min_length=1, max_length=4000)


class MessageRead(BaseModel):
    """Schema for reading a message."""

    id: int
    conversation_id: int
    sender_id: int
    text: str
    created_at: datetime


class ConversationCreate(BaseModel):
    """Schema for opening a direct conversation with another user."""

    user_id: int


class ConversationRead(BaseModel):
    """Schema for reading a conversation from the current user's point of view."""

    id: int
    companion: UserOut
    last_message: MessageRead | None = None
    unread_count: int = 0
    status: str
    initiator_id: int


class MarkReadRequest(BaseModel):
    """Schema for marking a conversation as read up to a message."""

    message_id: int
