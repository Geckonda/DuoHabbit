"""Push subscription API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.auth import get_token_claim
from duohabit.config import settings
from duohabit.db import get_session
from duohabit.repositories.push import PushRepository
from duohabit.schemas.auth import AccessTokenClaim
from duohabit.schemas.push import (
    PushSubscribeRequest,
    PushUnsubscribeRequest,
    VapidPublicKeyResponse,
)
from duohabit.services.push import subscribe, unsubscribe

push_router = APIRouter(prefix="/push", tags=["Push"])


@push_router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
async def vapid_public_key_endpoint() -> VapidPublicKeyResponse:
    """Expose the server's public VAPID key - not a secret, needed to subscribe."""
    return VapidPublicKeyResponse(public_key=settings.vapid_public_key)


@push_router.post("/subscribe", status_code=204)
async def subscribe_endpoint(
    subscription_data: PushSubscribeRequest,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Register the caller's browser for Web Push notifications."""
    await subscribe(
        repo=PushRepository(session),
        user_id=token_claim.user_id,
        data=subscription_data,
    )


@push_router.post("/unsubscribe", status_code=204)
async def unsubscribe_endpoint(
    unsubscribe_data: PushUnsubscribeRequest,
    session: AsyncSession = Depends(get_session),
    token_claim: AccessTokenClaim = Depends(get_token_claim),
) -> None:
    """Remove the caller's subscription."""
    await unsubscribe(
        repo=PushRepository(session),
        user_id=token_claim.user_id,
        endpoint=unsubscribe_data.endpoint,
    )
