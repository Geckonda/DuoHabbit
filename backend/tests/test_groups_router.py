"""Router-level tests for /groups: happy paths plus the AppError -> HTTP conversion."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import as_user, make_user


@pytest.mark.asyncio(loop_scope="session")
async def test_create_group_endpoint_happy_path(
    app: FastAPI, client: AsyncClient, db_session: AsyncSession
) -> None:
    owner = await make_user(db_session, "owner", "owner@test.com")
    as_user(app, owner.id)

    response = await client.post(
        "/groups",
        json={
            "name": "Утренняя пробежка",
            "habit_title": "Бег",
            "allowed_misses": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["owner_id"] == owner.id
    assert body["member_count"] == 1
    assert body["habit"]["current_streak"] == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_create_group_endpoint_error_conversion(
    app: FastAPI, client: AsyncClient, db_session: AsyncSession
) -> None:
    owner = await make_user(db_session, "owner", "owner@test.com")
    as_user(app, owner.id)

    response = await client.post(
        "/groups",
        json={
            "name": "Group",
            "habit_title": "Habit",
            "habit_type": "weekly",
            "allowed_misses": 0,
        },
    )

    # ValidationAppError -> 400, not an unhandled 500.
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio(loop_scope="session")
async def test_get_group_endpoint_not_found_returns_404(
    app: FastAPI, client: AsyncClient, db_session: AsyncSession
) -> None:
    owner = await make_user(db_session, "owner", "owner@test.com")
    as_user(app, owner.id)

    response = await client.get("/groups/999999")

    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_check_in_endpoint_happy_path(
    app: FastAPI, client: AsyncClient, db_session: AsyncSession
) -> None:
    owner = await make_user(db_session, "owner", "owner@test.com")
    as_user(app, owner.id)

    create_resp = await client.post(
        "/groups",
        json={"name": "Solo group", "habit_title": "Читать", "allowed_misses": 0},
    )
    group_id = create_resp.json()["id"]

    check_resp = await client.post(f"/groups/{group_id}/check")

    assert check_resp.status_code == 200
    body = check_resp.json()
    assert body["checked"] is True
    assert body["all_members_done"] is True  # owner is the only active member
    assert body["current_streak"] == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_join_group_endpoint_happy_path(
    app: FastAPI, client: AsyncClient, db_session: AsyncSession
) -> None:
    owner = await make_user(db_session, "owner", "owner@test.com")
    joiner = await make_user(db_session, "joiner", "joiner@test.com")

    as_user(app, owner.id)
    create_resp = await client.post(
        "/groups", json={"name": "Group", "habit_title": "Habit", "allowed_misses": 0}
    )
    invite_code = create_resp.json()["invite_code"]

    as_user(app, joiner.id)
    join_resp = await client.post("/groups/join", json={"invite_code": invite_code})

    assert join_resp.status_code == 200
    assert join_resp.json()["member_count"] == 2
