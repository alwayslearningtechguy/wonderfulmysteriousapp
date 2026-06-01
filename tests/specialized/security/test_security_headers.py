"""
tests/specialized/security/test_security_headers.py
=====================================================
Automated security tests covering HTTP response headers, input size limits,
CORS behaviour, and common vulnerability indicators.

These tests run against the FastAPI TestClient (no live server required)
and are safe to include in the standard CI pipeline alongside unit and
integration tests.

Why these tests?
----------------
The existing sanitization test confirms the API tolerates script-like input.
These tests address the next layer: what does the *server* communicate to the
browser about how to handle responses? Missing security headers are one of the
most common findings in web application security scans (OWASP ZAP, Mozilla
Observatory) and are trivially fixable once identified.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.test_utils import reset_state

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset():
    reset_state()

@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Security Headers
#
# These tests DOCUMENT the current state of headers and will initially FAIL
# if the headers are not yet present. That is intentional — they act as a
# checklist that drives implementation.
#
# To make them pass, add a middleware to app/main.py that injects the headers.
# A reference implementation is provided in app/security_headers_middleware.py.
# ---------------------------------------------------------------------------

SECURITY_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
]

@pytest.mark.parametrize("header", SECURITY_HEADERS)
def test_security_header_present(client, header):
    """Each GET endpoint should return the required security header."""
    r = client.get("/api/weather")
    assert header in r.headers, (
        f"Missing security header: '{header}'. "
        f"Add it via middleware in app/main.py."
    )

def test_x_content_type_options_value(client):
    """X-Content-Type-Options must be 'nosniff'."""
    r = client.get("/api/weather")
    assert r.headers.get("x-content-type-options", "").lower() == "nosniff"

def test_x_frame_options_value(client):
    """X-Frame-Options must be DENY or SAMEORIGIN to prevent clickjacking."""
    r = client.get("/api/weather")
    value = r.headers.get("x-frame-options", "").upper()
    assert value in ("DENY", "SAMEORIGIN"), (
        f"X-Frame-Options should be DENY or SAMEORIGIN, got: '{value}'"
    )

def test_referrer_policy_value(client):
    """Referrer-Policy should restrict referrer information."""
    r = client.get("/api/weather")
    value = r.headers.get("referrer-policy", "").lower()
    acceptable = {
        "no-referrer",
        "no-referrer-when-downgrade",
        "strict-origin",
        "strict-origin-when-cross-origin",
    }
    assert value in acceptable, (
        f"Referrer-Policy value '{value}' is not in the acceptable set: {acceptable}"
    )

def test_security_headers_present_on_post_endpoints(client):
    """Security headers must also be present on POST responses."""
    r = client.post("/api/submit", json={"user": "test", "data": {"x": 1}})
    assert "x-content-type-options" in r.headers
    assert "x-frame-options" in r.headers


# ---------------------------------------------------------------------------
# 2. Input Size Limits
#
# The /api/submit endpoint accepts a free-form dict with no size constraint.
# These tests document expected behaviour for oversized payloads.
# ---------------------------------------------------------------------------

def test_submit_large_user_field_does_not_crash(client):
    """A very long 'user' string should not cause a 500 error."""
    payload = {"user": "a" * 10_000, "data": {"x": 1}}
    r = client.post("/api/submit", json=payload)
    assert r.status_code in (201, 413, 422), (
        f"Expected 201, 413, or 422 for oversized user field, got {r.status_code}"
    )
    assert r.status_code != 500

def test_submit_large_data_field_does_not_crash(client):
    """A deeply nested or large 'data' dict should not cause a 500 error."""
    large_data = {f"key_{i}": "x" * 100 for i in range(500)}
    payload = {"user": "tester", "data": large_data}
    r = client.post("/api/submit", json=payload)
    assert r.status_code in (201, 413, 422)
    assert r.status_code != 500

def test_weather_very_long_city_name_does_not_crash(client):
    """A very long city name query param should not cause a 500 error."""
    long_city = "A" * 5_000
    r = client.get(f"/api/weather?city={long_city}")
    assert r.status_code == 200
    assert r.status_code != 500

def test_insight_very_long_topic_does_not_crash(client):
    """A very long topic query param should fall back gracefully."""
    long_topic = "z" * 5_000
    r = client.get(f"/api/insight?topic={long_topic}")
    assert r.status_code == 200
    data = r.json()
    assert data["topic"] == "general"


# ---------------------------------------------------------------------------
# 3. Unexpected HTTP Methods
#
# Endpoints should reject methods they don't support with 405, not 500.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,path", [
    ("POST", "/api/weather"),
    ("POST", "/api/fortune"),
    ("POST", "/api/insight"),
    ("DELETE", "/api/favorites"),
    ("PUT", "/api/favorites"),
    ("DELETE", "/api/submit"),
])
def test_unsupported_method_returns_405(client, method, path):
    """Unsupported HTTP methods should return 405, not 500."""
    r = client.request(method, path)
    assert r.status_code == 405, (
        f"{method} {path} returned {r.status_code}, expected 405"
    )


# ---------------------------------------------------------------------------
# 4. Error Response Hygiene
#
# Error responses must not leak internal details, stack traces, or
# environment information.
# ---------------------------------------------------------------------------

SENSITIVE_PATTERNS = [
    "traceback",
    "file \"",
    "line ",
    "exception",
    "internal server error",
    "/home/",
    "/app/",
    "environ",
]

def test_422_response_does_not_leak_internals(client):
    """A 422 validation error should not contain stack traces or paths."""
    r = client.post("/api/submit", json={"bad": "payload"})
    assert r.status_code == 422
    body = r.text.lower()
    for pattern in SENSITIVE_PATTERNS:
        assert pattern not in body, (
            f"Error response leaks sensitive pattern: '{pattern}'"
        )

def test_405_response_does_not_leak_internals(client):
    """A 405 response should not contain internal details."""
    r = client.post("/api/weather")
    body = r.text.lower()
    for pattern in ["traceback", "file \""]:
        assert pattern not in body


# ---------------------------------------------------------------------------
# 5. Content-Type Enforcement
#
# POST endpoints should reject non-JSON content types gracefully.
# ---------------------------------------------------------------------------

def test_submit_with_wrong_content_type_does_not_crash(client):
    """Sending form data instead of JSON should return 422, not 500."""
    r = client.post(
        "/api/submit",
        data={"user": "alice", "data": "{}"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code in (415, 422)
    assert r.status_code != 500

def test_favorites_with_wrong_content_type_does_not_crash(client):
    """Sending plain text to a JSON endpoint should return 422, not 500."""
    r = client.post(
        "/api/favorites",
        content=b"not json at all",
        headers={"Content-Type": "text/plain"},
    )
    assert r.status_code in (415, 422)
    assert r.status_code != 500
