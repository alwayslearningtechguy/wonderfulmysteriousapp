"""
test_e2e_extended.py
====================
Extended E2E tests addressing the known limitations identified in the E2E Test
Report. These complement the existing test_e2e_health.py and
test_e2e_core_flow.py files without modifying them.

Limitations addressed:
  1. POST /api/favorites not tested E2E → test_favorites_post_and_read_back
  2. GET /api/favorites not in health check → test_all_endpoints_are_healthy
  3. Landing page (/) not tested E2E → test_all_endpoints_are_healthy
  4. No field-level schema assertions in health tests → dedicated schema tests
  5. Rate limit not tested against the live server → test_rate_limit_returns_429

Place this file at: tests/e2e/test_e2e_extended.py
"""

import pytest


# ---------------------------------------------------------------------------
# 1. Expanded Health Check — all six endpoints including GET /api/favorites
#    and the landing page, with field-level schema assertions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", [
    "/api/weather",
    "/api/insight",
    "/api/fortune",
    "/api/favorites",
])
def test_all_get_endpoints_return_200_and_json(client, path):
    """All GET endpoints return 200 with a non-empty JSON dict."""
    r = client.get(path)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert len(data) > 0, f"{path} returned an empty dict"


def test_landing_page_returns_200_html(client):
    """GET / returns 200 with HTML content containing all six endpoint paths."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    for endpoint in ["/api/weather", "/api/insight", "/api/fortune",
                     "/api/submit", "/api/favorites"]:
        assert endpoint in body, f"Landing page missing endpoint: {endpoint}"


# ---------------------------------------------------------------------------
# 2. Field-level schema assertions for each read endpoint
# ---------------------------------------------------------------------------

def test_weather_response_schema(client):
    """GET /api/weather returns all required fields with correct types."""
    r = client.get("/api/weather")
    assert r.status_code == 200
    data = r.json()
    assert data["city"] == "Seattle"
    assert data["region"] == "Washington, US"
    assert isinstance(data["temp_c"], int)
    assert isinstance(data["temp_f"], int)
    assert isinstance(data["condition"], str)
    assert isinstance(data["humidity_pct"], int)
    assert isinstance(data["wind_mph"], int)
    assert isinstance(data["visibility_miles"], int)
    assert isinstance(data["uv_index"], int)


def test_insight_response_schema(client):
    """GET /api/insight returns all required fields with correct types."""
    r = client.get("/api/insight")
    assert r.status_code == 200
    data = r.json()
    assert "insight" in data
    assert "topic" in data
    assert "id" in data
    assert "available_topics" in data
    assert isinstance(data["insight"], str)
    assert len(data["insight"]) > 0
    assert data["topic"] == "general"
    assert isinstance(data["id"], int)
    assert isinstance(data["available_topics"], list)
    assert set(data["available_topics"]) == {
        "general", "technology", "productivity", "leadership", "creativity"
    }


def test_fortune_response_schema(client):
    """GET /api/fortune returns all required fields with correct types."""
    r = client.get("/api/fortune")
    assert r.status_code == 200
    data = r.json()
    assert "fortune" in data
    assert "lucky_number" in data
    assert "lucky_color" in data
    assert "advice" in data
    assert "id" in data
    assert isinstance(data["fortune"], str)
    assert len(data["fortune"]) > 0
    assert isinstance(data["lucky_number"], int)
    assert isinstance(data["lucky_color"], str)
    assert isinstance(data["advice"], str)
    assert isinstance(data["id"], int)


def test_favorites_get_response_schema(client):
    """GET /api/favorites always returns a dict with a 'favorites' list."""
    r = client.get("/api/favorites")
    assert r.status_code == 200
    data = r.json()
    assert "favorites" in data
    assert isinstance(data["favorites"], list)


# ---------------------------------------------------------------------------
# 3. POST /api/favorites → GET /api/favorites read-back
# ---------------------------------------------------------------------------

def test_favorites_post_returns_201_and_saved_message(client):
    """POST /api/favorites with a valid integer id returns 201 and 'Saved'."""
    r = client.post("/api/favorites", json={"id": 7001})
    assert r.status_code == 201
    data = r.json()
    assert data["message"] == "Saved"
    assert "current_favorites" in data
    assert isinstance(data["current_favorites"], list)


def test_favorites_post_id_appears_in_get(client):
    """An id POSTed to /api/favorites appears in the GET /api/favorites list."""
    unique_id = 7002
    r = client.post("/api/favorites", json={"id": unique_id})
    assert r.status_code == 201
    # Read back and confirm membership (not equality — list may have prior items)
    r = client.get("/api/favorites")
    assert r.status_code == 200
    assert unique_id in r.json()["favorites"]


def test_favorites_multiple_posts_all_appear_in_get(client):
    """Multiple POSTed ids all appear in GET /api/favorites."""
    ids = [7003, 7004, 7005]
    for fav_id in ids:
        r = client.post("/api/favorites", json={"id": fav_id})
        assert r.status_code == 201
    r = client.get("/api/favorites")
    assert r.status_code == 200
    favorites = r.json()["favorites"]
    for fav_id in ids:
        assert fav_id in favorites


def test_favorites_post_missing_id_returns_422(client):
    """POST /api/favorites with no id field returns 422 Unprocessable Entity."""
    r = client.post("/api/favorites", json={"not_id": "oops"})
    assert r.status_code == 422


def test_favorites_post_non_integer_id_returns_422(client):
    """POST /api/favorites with a string id returns 422 — id must be integer."""
    r = client.post("/api/favorites", json={"id": "not-a-number"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# 4. POST /api/submit field-level assertions
# ---------------------------------------------------------------------------

def test_submit_valid_payload_returns_201_with_echo(client):
    """POST /api/submit returns 201 with status='Created' and echoed payload."""
    r = client.post("/api/submit", json={"user": "e2e-tester", "data": {"score": 42}})
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "Created"
    assert data["received"]["user"] == "e2e-tester"
    assert data["received"]["data"] == {"score": 42}


def test_submit_missing_user_returns_422(client):
    """POST /api/submit without 'user' field returns 422."""
    r = client.post("/api/submit", json={"data": {"score": 1}})
    assert r.status_code == 422


def test_submit_missing_data_returns_422(client):
    """POST /api/submit without 'data' field returns 422."""
    r = client.post("/api/submit", json={"user": "alice"})
    assert r.status_code == 422


def test_submit_does_not_affect_favorites(client):
    """
    POST /api/submit does not write to favorites.
    The favorites list is unchanged after a submit call.
    """
    before = set(client.get("/api/favorites").json()["favorites"])
    client.post("/api/submit", json={"user": "test", "data": {"x": 1}})
    after = set(client.get("/api/favorites").json()["favorites"])
    assert before == after


# ---------------------------------------------------------------------------
# 5. Rate limiting against the live server
#
# Strategy: use the RateLimiter class directly with a fresh instance to avoid
# consuming the global server limit (which would break subsequent tests).
# The global middleware behavior is validated via the unit test suite.
# A separate rate_limit_integration test using the actual live endpoint is
# included but isolated via a unique IP simulation note.
# ---------------------------------------------------------------------------

def test_rate_limiter_unit_allows_100_then_blocks(client):
    """
    Validates rate limit threshold using a fresh RateLimiter instance (not the
    global one), so this test does not consume the live server's request budget.
    """
    from app.rate_limiter import RateLimiter
    rl = RateLimiter(max_requests=100, window_seconds=10)
    test_ip = "10.99.99.1"
    for i in range(100):
        assert rl.is_allowed(test_ip) is True, f"Request {i+1} should be allowed"
    assert rl.is_allowed(test_ip) is False, "101st request should be blocked"


def test_rate_limiter_is_per_ip(client):
    """Rate limiting is per IP — exhausting one IP does not affect another."""
    from app.rate_limiter import RateLimiter
    rl = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        rl.is_allowed("10.99.99.2")
    assert rl.is_allowed("10.99.99.2") is False
    assert rl.is_allowed("10.99.99.3") is True


def test_live_server_rate_limit_returns_429(client):
    """
    Sends 101 requests to the live server and confirms the 101st returns 429.

    WARNING: This test consumes 101 requests from the global rate limiter on the
    live server. It must be the last test to run in the E2E session, or subsequent
    tests may receive unexpected 429 responses. The rate limit window is 10 seconds,
    after which normal service resumes.

    If this test causes flakiness, move it to a separate pytest mark and run it
    in isolation: pytest tests/e2e -m ratelimit
    """
    for i in range(100):
        r = client.get("/api/fortune")
        assert r.status_code == 200, (
            f"Request {i+1} should be 200 but got {r.status_code}. "
            "Check if another test already consumed part of the rate limit budget."
        )
    r = client.get("/api/fortune")
    assert r.status_code == 429
    assert r.json()["detail"] == "Too Many Requests"
