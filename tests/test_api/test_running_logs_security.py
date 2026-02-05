from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from infrastructure.orm_models import User
from domain.auth import auth_service
from api.main import app


@pytest.fixture
async def secondary_user(setup_db):
    """Creates a second user in the database with all required fields."""
    from tests.conftest import TestingSessionLocal
    async with TestingSessionLocal() as session:
        hashed = auth_service.hash_password("password456")
        user = User(
            email="attacker@example.com",
            hashed_password=hashed,
            age=25,
            goal="fat_loss",
            equipment="none",
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

@pytest.fixture
async def secondary_client(secondary_user) -> AsyncGenerator[AsyncClient, None]:
    """Provides a fresh client authenticated as the secondary user."""
    # We use the 'app' we imported at the top here
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_response = auth_service.get_auth_tokens(user_id=secondary_user.id)
        token = token_response.access_token
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac


@pytest.mark.asyncio
async def test_user_cannot_delete_others_log(authenticated_client, secondary_client):
    """
    Test that User A cannot delete a log belonging to User B.
    """
    # 1. User A creates a log
    payload = {"running_date": "2023-10-27", "distance_km": 5.0, "duration_min": 25.0}
    res = await authenticated_client.post("/v1/running_logs/", json=payload)
    log_id = res.json()["id"]

    # 2. User B (secondary_client) tries to delete User A's log
    attack_res = await secondary_client.delete(f"/v1/running_logs/{log_id}")

    # 3. Assert failure (Should be 404 because the service filters by user_id)
    assert attack_res.status_code == 404

@pytest.mark.asyncio
async def test_user_cannot_update_others_log(authenticated_client, secondary_client):
    """
    Test that User A cannot update a log belonging to User B.
    """
    # 1. User A creates a log
    payload = {"running_date": "2023-10-27", "distance_km": 5.0, "duration_min": 25.0}
    res = await authenticated_client.post("/v1/running_logs/", json=payload)
    log_id = res.json()["id"]

    # 2. User B tries to update User A's distance
    update_payload = {"distance_km": 100.0}
    attack_res = await secondary_client.patch(f"/v1/running_logs/{log_id}", json=update_payload)

    assert attack_res.status_code == 404