"""
test_e2e_extended.py
====================
Extended E2E tests addressing the known limitations identified in the E2E Test
Report. These complement the existing test_e2e_health.py and
test_e2e_core_flow.py without modifying them.

Place this file at: tests/e2e/test_e2e_extended.py

Limitations addressed:
  1. POST /api/favorites not tested E2E
  2. GET /api/favorites and GET / absent from health check
  3. No field-level schema assertions in health tests
  4. POST /api/submit not tested E2E with field assertions
  5. Rate limit not tested against the live server

Rate limit design note
----------------------
The live-server rate limit test (test_live_server_rate_limit_returns_429) uses
its own session-scoped server fixture (isolated_app_server) that starts a second
Uvicorn instance on port 8001. This gives the test a fresh rate limit budget
of 100 and prevents it from consuming requests from the shared server on 8000
that all other tests use. The shared session therefore never reaches 100 requests
and no other test is affected.
"""

import subprocess
import time
import socket
import pytest
import httpx


# ---------------------------------------------------------------------------
# Isolated server fixture for rate limit test only
# Starts a second Uvicorn on port 8001 with a clean rate limit budget.
# ---------------------------------------------------------------------------

def _wait_for_port(host, port, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Server did not start on {host}:{port} within {timeout}s")


@pytest.fixture(scope="session")
def isolated_app_server():
    """Start a second Uvicorn instance on port 8001 for the rate limit test."""
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_for_port("127.0.0.1", 8001)
    yield
    proc.terminate()
    proc.wait()


@pytest.fixture
def isolated_client(isolated_app_server):
    """httpx.Client pointing at the isolated server on port 8001."""
    with httpx.Client(base_url="http://127.0.0.1:8001") as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Expanded Health Check — adds GET /api/favorites and GET /
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
    """GET / returns 200 HTML containing all five API endpoint paths."""
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
    """GET /api/favorites returns a dict with a 'favorites' list."""
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
    """An id POSTed to /api/favorites appears in GET /api/favorites."""
    unique_id = 7002
    r = client.post("/api/favorites", json={"id": unique_id})
    assert r.status_code == 201
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
    """POST /api/favorites with no id field returns 422."""
    r = client.post("/api/favorites", json={"not_id": "oops"})
    assert r.status_code == 422


def test_favorites_post_non_integer_id_returns_422(client):
    """POST /api/favorites with a string id returns 422."""
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
    """POST /api/submit has no effect on the favorites list."""
    before = set(client.get("/api/favorites").json()["favorites"])
    client.post("/api/submit", json={"user": "test", "data": {"x": 1}})
    after = set(client.get("/api/favorites").json()["favorites"])
    assert before == after


# ---------------------------------------------------------------------------
# 5. Rate limiting — isolated server on port 8001
#
# Uses isolated_client (port 8001) so this test starts with a clean budget
# of 100 and cannot affect any other test using the shared server on port 8000.
# ---------------------------------------------------------------------------

def test_rate_limiter_unit_allows_100_then_blocks():
    """
    Validates the RateLimiter class directly with a fresh instance.
    Does not touch any live server.
    """
    from app.rate_limiter import RateLimiter
    rl = RateLimiter(max_requests=100, window_seconds=10)
    test_ip = "10.99.99.1"
    for i in range(100):
        assert rl.is_allowed(test_ip) is True, f"Request {i+1} should be allowed"
    assert rl.is_allowed(test_ip) is False, "101st request should be blocked"


def test_rate_limiter_is_per_ip():
    """Rate limiting is per IP — exhausting one does not block another."""
    from app.rate_limiter import RateLimiter
    rl = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        rl.is_allowed("10.99.99.2")
    assert rl.is_allowed("10.99.99.2") is False
    assert rl.is_allowed("10.99.99.3") is True


def test_live_server_rate_limit_returns_429(isolated_client):
    """
    Sends 101 requests to the isolated server (port 8001) and confirms the
    101st returns 429 Too Many Requests.

    Uses isolated_client (port 8001) — a fresh Uvicorn process with a clean
    rate limit budget. This ensures the test is self-contained and cannot
    affect any other test that uses the shared server on port 8000.
    """
    for i in range(100):
        r = isolated_client.get("/api/fortune")
        assert r.status_code == 200, (
            f"Request {i+1} should be 200 but got {r.status_code}."
        )
    r = isolated_client.get("/api/fortune")
    assert r.status_code == 429
    assert r.json()["detail"] == "Too Many Requests"
