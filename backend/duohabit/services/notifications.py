"""
Notification center.

Single entry point (`notify`) for pushing a message to a set of users,
regardless of which feature triggered it. Chat is the first caller; habit
reminders or group invites can call the same function later without knowing
anything about Web Push.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Iterable

from pywebpush import WebPushException, webpush
from sqlalchemy.ext.asyncio import AsyncSession

from duohabit.chat_hub import hub
from duohabit.config import settings
from duohabit.logger import logger
from duohabit.models.push import PushSubscription
from duohabit.repositories.push import PushRepository

DEAD_SUBSCRIPTION_STATUSES = {404, 410}


@dataclass
class NotificationPayload:
    """What to show the user, channel-agnostic."""

    title: str
    body: str
    url: str = "/"
    tag: str | None = None


def _send(subscription: PushSubscription, payload: NotificationPayload) -> bool:
    """
    Send one Web Push message. Runs in a thread - pywebpush is sync (uses requests).

    Returns False when the subscription is dead (push service says 404/410)
    and should be deleted, True otherwise.
    """
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(
                {
                    "title": payload.title,
                    "body": payload.body,
                    "url": payload.url,
                    "tag": payload.tag,
                }
            ),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )
        return True
    except WebPushException as error:
        status = error.response.status_code if error.response is not None else None
        if status in DEAD_SUBSCRIPTION_STATUSES:
            return False
        logger.warning("Push delivery failed for subscription %s: %s", subscription.id, error)
        return True


async def notify(
    repo: PushRepository, user_ids: Iterable[int], payload: NotificationPayload
) -> None:
    """Fan a notification out to every push subscription of the given users."""
    if not settings.vapid_private_key:
        logger.debug("Push disabled (no VAPID key configured), skipping notify()")
        return

    subscriptions = await repo.get_by_users(list(set(user_ids)))
    if not subscriptions:
        return

    results = await asyncio.gather(
        *(asyncio.to_thread(_send, subscription, payload) for subscription in subscriptions)
    )

    dead = [sub for sub, alive in zip(subscriptions, results) if not alive]
    if dead:
        for subscription in dead:
            await repo.delete(subscription)
        await repo.commit()


async def notify_if_offline(
    session: AsyncSession, user_ids: list[int], payload: NotificationPayload
) -> None:
    """
    Push only to recipients without a live socket.

    Online ones already have (or will get) the news some other way - a WS
    event, an in-app toast - a push on top would just be a duplicate.
    """
    offline = [user_id for user_id in user_ids if not hub.is_online(user_id)]
    if offline:
        await notify(PushRepository(session), offline, payload)
