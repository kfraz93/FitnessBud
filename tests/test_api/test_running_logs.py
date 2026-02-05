import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_running_log_authenticated(authenticated_client: AsyncClient):
    """
    Test that an authenticated user can successfully log a run.
    """
    payload = {
        "running_date": "2023-10-27",
        "distance_km": 5.0,
        "duration_min": 25.0,
        "avg_heart_rate": 150,
        "run_type": "Easy"
    }

    response = await authenticated_client.post("/v1/running_logs/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["distance_km"] == 5.0
    assert "id" in data
    # Check that pace was calculated (25 / 5 = 5.0)
    assert data["pace_min_per_km"] == 5.0


@pytest.mark.asyncio
async def test_get_running_logs(authenticated_client: AsyncClient):
    """
    Test that we can retrieve the list of logs for the user.
    """
    response = await authenticated_client.get("/v1/running_logs/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_running_log_unauthenticated(client: AsyncClient):
    """
    Test that a request without a token is rejected.
    """
    payload = {"distance_km": 5.0, "duration_min": 25.0}
    response = await client.post("/v1/running_logs/", json=payload)

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_get_recommend_pace_basic(authenticated_client: AsyncClient):
    """
    Test that the ML recommendation endpoint returns a valid float prediction.
    """
    params = {"distance_km": 10.0}
    response = await authenticated_client.get("/v1/running_logs/recommend_pace",
                                              params=params)

    assert response.status_code == 200
    # The response should be a float (like 7.04)
    data = response.json()
    assert isinstance(data, (int, float))
    assert data > 0


@pytest.mark.asyncio
async def test_get_recommend_pace_invalid_distance(authenticated_client: AsyncClient):
    """
    Test that the API rejects invalid distances (like 0 or negative).
    """
    params = {"distance_km": -5.0}
    response = await authenticated_client.get("/v1/running_logs/recommend_pace",
                                              params=params)

    assert response.status_code == 400
    assert response.json()["detail"] == "Distance must be greater than zero."


@pytest.mark.asyncio
async def test_recommend_pace_updates_with_data(authenticated_client: AsyncClient):
    """
    Advanced: Verify that adding slow runs changes the prediction.
    """
    # 1. Get initial prediction
    res1 = await authenticated_client.get("/v1/running_logs/recommend_pace",
                                          params={"distance_km": 5})
    initial_pace = res1.json()

    # 2. Log a very SLOW run (10 min/km)
    slow_run = {
        "running_date": "2023-10-28",
        "distance_km": 5.0,
        "duration_min": 50.0,  # 50 / 5 = 10 min/km
        "avg_heart_rate": 130,
        "run_type": "Easy"
    }
    await authenticated_client.post("/v1/running_logs/", json=slow_run)

    # 3. Get new prediction
    res2 = await authenticated_client.get("/v1/running_logs/recommend_pace",
                                          params={"distance_km": 5})
    updated_pace = res2.json()

    # The ML model should have 'learned' and adjusted the pace
    # Note: Depending on your model weight, this might be a small change
    assert updated_pace != initial_pace


@pytest.mark.asyncio
async def test_update_running_log(authenticated_client: AsyncClient):
    """
    Test updating an existing log (PATCH).
    """
    # 1. Create a log first
    payload = {
        "running_date": "2023-10-27",
        "distance_km": 5.0,
        "duration_min": 25.0
    }
    create_res = await authenticated_client.post("/v1/running_logs/", json=payload)
    log_id = create_res.json()["id"]

    # 2. Update the distance
    update_payload = {"distance_km": 6.0}
    response = await authenticated_client.patch(f"/v1/running_logs/{log_id}",
                                                json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["distance_km"] == 6.0
    # The pace should automatically re-calculate (25 / 6 = 4.17)
    assert data["pace_min_per_km"] == pytest.approx(4.17, rel=1e-2)


@pytest.mark.asyncio
async def test_delete_running_log(authenticated_client: AsyncClient):
    """
    Test deleting a log.
    """
    # 1. Create a log
    payload = {"running_date": "2023-10-27", "distance_km": 5.0, "duration_min": 25.0}
    create_res = await authenticated_client.post("/v1/running_logs/", json=payload)
    log_id = create_res.json()["id"]

    # 2. Delete it
    delete_res = await authenticated_client.delete(f"/v1/running_logs/{log_id}")
    assert delete_res.status_code == 204

    # 3. Verify it's gone
    get_res = await authenticated_client.get(f"/v1/running_logs/{log_id}")
    assert get_res.status_code == 404
