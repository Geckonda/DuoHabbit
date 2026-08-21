"""Push subscription management."""

from duohabit.repositories.push import PushRepository
from duohabit.schemas.push import PushSubscribeRequest


async def subscribe(repo: PushRepository, user_id: int, data: PushSubscribeRequest) -> None:
    """Register (or refresh) a browser's Web Push subscription for a user."""
    await repo.upsert(
        user_id=user_id,
        endpoint=data.endpoint,
        p256dh=data.keys.p256dh,
        auth=data.keys.auth,
    )
    await repo.commit()


async def unsubscribe(repo: PushRepository, user_id: int, endpoint: str) -> None:
    """Remove a user's subscription by endpoint."""
    await repo.delete_by_endpoint(user_id, endpoint)
    await repo.commit()
