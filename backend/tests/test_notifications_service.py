"""Tests for the push subscription management and notification center."""

from types import SimpleNamespace

import pytest
from pywebpush import WebPushException

from duohabit.config import settings
from duohabit.schemas.push import PushKeys, PushSubscribeRequest
from duohabit.services.notifications import NotificationPayload, notify
from duohabit.services.push import subscribe, unsubscribe
from tests.fakes import FakePushRepository, as_push_repo

ALICE = 1
BOB = 2


def subscribe_request(endpoint: str) -> PushSubscribeRequest:
    """A subscription payload as the browser would send it."""
    return PushSubscribeRequest(endpoint=endpoint, keys=PushKeys(p256dh="p256dh", auth="auth"))


# ========== SUBSCRIBE / UNSUBSCRIBE ==========


@pytest.mark.asyncio(loop_scope="session")
async def test_subscribe_persists_and_is_idempotent_per_endpoint() -> None:
    """Re-subscribing the same endpoint refreshes it instead of duplicating it."""
    repo = FakePushRepository()

    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/a"))
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/a"))

    assert len(repo.subscriptions) == 1
    assert repo.commits == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_unsubscribe_removes_the_subscription() -> None:
    """Unsubscribing drops the endpoint from the store."""
    repo = FakePushRepository()
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/a"))

    await unsubscribe(as_push_repo(repo), ALICE, "https://push.example/a")

    assert repo.subscriptions == {}


# ========== NOTIFY ==========


@pytest.fixture(autouse=True)
def vapid_keys(monkeypatch: pytest.MonkeyPatch):
    """notify() no-ops without VAPID keys configured - give it some for these tests."""
    monkeypatch.setattr(settings, "vapid_private_key", "test-private-key")
    monkeypatch.setattr(settings, "vapid_public_key", "test-public-key")


@pytest.mark.asyncio(loop_scope="session")
async def test_notify_sends_to_every_subscription_of_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every live subscription of the target users gets pushed to."""
    repo = FakePushRepository()
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/a1"))
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/a2"))
    await subscribe(as_push_repo(repo), BOB, subscribe_request("https://push.example/b"))

    calls = []
    monkeypatch.setattr(
        "duohabit.services.notifications.webpush",
        lambda **kwargs: calls.append(kwargs["subscription_info"]["endpoint"]),
    )

    await notify(as_push_repo(repo), [ALICE], NotificationPayload(title="Bob", body="hi"))

    assert sorted(calls) == ["https://push.example/a1", "https://push.example/a2"]


@pytest.mark.asyncio(loop_scope="session")
async def test_notify_noop_without_vapid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """No VAPID key configured means push is off - notify() must not call webpush at all."""
    monkeypatch.setattr(settings, "vapid_private_key", "")
    repo = FakePushRepository()
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/a"))

    calls = []
    monkeypatch.setattr("duohabit.services.notifications.webpush", lambda **_: calls.append(1))

    await notify(as_push_repo(repo), [ALICE], NotificationPayload(title="Bob", body="hi"))

    assert calls == []


@pytest.mark.asyncio(loop_scope="session")
async def test_notify_drops_dead_subscription_on_410(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 410 Gone from the push service means the subscription is dead - delete it."""
    repo = FakePushRepository()
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/dead"))
    await subscribe(as_push_repo(repo), ALICE, subscribe_request("https://push.example/alive"))

    def fake_webpush(**kwargs):
        if kwargs["subscription_info"]["endpoint"].endswith("dead"):
            raise WebPushException("gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr("duohabit.services.notifications.webpush", fake_webpush)

    await notify(as_push_repo(repo), [ALICE], NotificationPayload(title="Bob", body="hi"))

    assert list(repo.subscriptions) == ["https://push.example/alive"]
    assert repo.commits == 3  # 2 subscribe() + 1 cleanup commit inside notify()
