"""
Usability tests for the landing page (GET /).

These tests validate two usability requirements:
  A) The landing page is reachable by navigating to the root URL ("/")
     so users do not hit a 404 when visiting the app directly.
  B) The landing page contains documentation and direct links for every
     API endpoint so users can understand and navigate the API without
     consulting GitHub.
"""

# Endpoints that must be documented and linked on the landing page
EXPECTED_ENDPOINTS = [
    "/api/weather",
    "/api/insight",
    "/api/fortune",
    "/api/submit",
    "/api/favorites",
]


def test_landing_page_is_reachable(client):
    """A) Navigating to '/' returns a successful response, not a 404."""
    res = client.get("/")
    assert res.status_code == 200, (
        "Landing page must return 200. "
        "Previously '/' returned 404 because no root route was defined."
    )


def test_landing_page_returns_html(client):
    """A) The root URL serves HTML content, confirming a real page is rendered."""
    res = client.get("/")
    assert res.status_code == 200
    content_type = res.headers.get("content-type", "")
    assert "text/html" in content_type, (
        f"Expected HTML content-type, got: {content_type}"
    )


def test_landing_page_contains_all_endpoint_paths(client):
    """B) Every API endpoint path is mentioned in the landing page HTML
    so users can identify and navigate to each one without referencing GitHub."""
    res = client.get("/")
    assert res.status_code == 200
    body = res.text
    for endpoint in EXPECTED_ENDPOINTS:
        assert endpoint in body, (
            f"Landing page must document endpoint '{endpoint}'. "
            f"It was not found in the page body."
        )


def test_landing_page_contains_endpoint_links(client):
    """B) Every API endpoint is represented as a navigable href link
    so users can click through directly from the landing page."""
    res = client.get("/")
    assert res.status_code == 200
    body = res.text
    for endpoint in EXPECTED_ENDPOINTS:
        assert f'href="{endpoint}"' in body or f"href='{endpoint}'" in body, (
            f"Landing page must contain a clickable link (href) to '{endpoint}'. "
            f"No href found for this endpoint."
        )


def test_landing_page_documents_http_methods(client):
    """B) The landing page indicates HTTP methods (GET/POST) for each endpoint
    so users know how to call them without reading external documentation."""
    res = client.get("/")
    assert res.status_code == 200
    body = res.text
    assert "GET" in body, "Landing page must mention GET method."
    assert "POST" in body, "Landing page must mention POST method."


def test_landing_page_documents_parameters(client):
    """B) The landing page mentions query parameters so users know
    how to customise requests without consulting GitHub."""
    res = client.get("/")
    assert res.status_code == 200
    body = res.text
    # city param for /api/weather
    assert "city" in body, "Landing page must document the 'city' parameter for /api/weather."
    # topic param for /api/insight
    assert "topic" in body, "Landing page must document the 'topic' parameter for /api/insight."
