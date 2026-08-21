"""Push subscription schemas."""

from pydantic import BaseModel, Field


class PushKeys(BaseModel):
    """Encryption keys from the browser's PushSubscription.toJSON()."""

    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    """Schema for registering a browser's Web Push subscription."""

    endpoint: str = Field(min_length=1)
    keys: PushKeys


class PushUnsubscribeRequest(BaseModel):
    """Schema for removing a subscription."""

    endpoint: str = Field(min_length=1)


class VapidPublicKeyResponse(BaseModel):
    """Schema exposing the server's public VAPID key to the frontend."""

    public_key: str
