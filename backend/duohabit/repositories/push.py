"""Push subscription repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.models.push import PushSubscription


class PushRepository:
    """Repository for Web Push subscriptions."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        """Get a subscription by its push-service endpoint."""
        stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self, user_id: int, endpoint: str, p256dh: str, auth: str
    ) -> PushSubscription:
        """
        Create or refresh a subscription by endpoint.

        Same endpoint re-subscribed under a different user (shared device,
        different account) simply reassigns it - the old owner never sees
        it again anyway once its keys are overwritten.
        """
        subscription = await self.get_by_endpoint(endpoint)
        if subscription is None:
            subscription = PushSubscription(
                user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth
            )
            self._session.add(subscription)
        else:
            subscription.user_id = user_id
            subscription.p256dh = p256dh
            subscription.auth = auth

        await self._session.flush()
        await self._session.refresh(subscription)
        return subscription

    async def delete_by_endpoint(self, user_id: int, endpoint: str) -> None:
        """Remove a subscription, scoped to its owner."""
        subscription = await self.get_by_endpoint(endpoint)
        if subscription is not None and subscription.user_id == user_id:
            await self.delete(subscription)

    async def delete(self, subscription: PushSubscription) -> None:
        """Remove a subscription."""
        await self._session.delete(subscription)
        await self._session.flush()

    async def get_by_users(self, user_ids: list[int]) -> list[PushSubscription]:
        """Get every subscription belonging to any of the given users."""
        if not user_ids:
            return []

        stmt = select(PushSubscription).where(PushSubscription.user_id.in_(user_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
