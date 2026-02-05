# API Testing Manifest: Running Logs

## Overview
This suite ensures the integrity of the Running Log lifecycle, ML-driven pace recommendations, and strict multi-tenant security boundaries. Tests are executed using `pytest` and `httpx` with an isolated in-memory SQLite database.

---

## Functional Tests

### 1. test_create_running_log_authenticated
* **Goal:** Verify authorized log creation.
* **Achievement:** Confirmed $Pace = Duration / Distance$ calculation and `201 Created` response.

### 2. test_get_running_logs
* **Goal:** Verify data retrieval.
* **Achievement:** Confirmed user-specific log listing and schema validation.

### 3. test_create_running_log_unauthenticated
* **Goal:** Verify baseline security.
* **Achievement:** Confirmed that requests without a JWT are blocked with `401 Unauthorized`.

### 4. test_get_recommend_pace_basic
* **Goal:** Verify ML Integration.
* **Achievement:** Confirmed the `/recommend_pace` endpoint returns valid numerical predictions from the ML service.

### 5. test_get_recommend_pace_invalid_distance
* **Goal:** Verify input sanitization.
* **Achievement:** Confirmed that distances $\le 0$ result in a `400 Bad Request`.

### 6. test_recommend_pace_updates_with_data
* **Goal:** Verify dynamic model behavior.
* **Achievement:** Confirmed that a user's latest running performance successfully influences future pace recommendations.

### 7. test_update_running_log
* **Goal:** Verify PATCH functionality.
* **Achievement:** Confirmed partial updates trigger automatic pace recalculation.

### 8. test_delete_running_log
* **Goal:** Verify resource cleanup.
* **Achievement:** Confirmed `204 No Content` and verified record removal from the database.

---

## Security & Authorization (IDOR) Tests

### 9. test_user_cannot_delete_others_log
* **Goal:** Prevent unauthorized data deletion.
* **Achievement:** Verified that User B cannot delete User A's logs. The API returns `404 Not Found`, preventing resource enumeration.

### 10. test_user_cannot_update_others_log
* **Goal:** Prevent unauthorized data modification.
* **Achievement:** Verified that User B cannot edit User A's data. Cross-user requests are rejected with `404 Not Found`.

---

## Infrastructure
* **Isolation:** Used `ASGITransport` to generate unique, isolated `AsyncClient` instances per user to prevent session/header bleeding.
* **Database:** Temporary `sqlite+aiosqlite` instance, cleared and migrated via `setup_db` fixture for every test.
* **State Management:** `expire_on_commit=False` allows Pydantic models to access ORM attributes safely after database commits.

TODO Modify workout tests to Not use Mocks and use Integration. 