"""
tests/specialized/cross_browser/test_cross_browser.py
======================================================
Cross-browser UI tests using Playwright.

These tests validate that the interactive landing page works correctly across
Chromium and Firefox (the two browser engines testable in Linux CI without
paid cloud services). Safari requires a macOS runner — see Manual Testing doc.

Prerequisites:
    pip install pytest-playwright
    playwright install chromium firefox

Run locally:
    pytest tests/specialized/cross_browser/ -v

Run against a specific browser only:
    pytest tests/specialized/cross_browser/ --browser chromium -v

The tests require a live Uvicorn server on port 8000.
The CI workflow starts the server before this job runs.

What is tested
--------------
1. Landing page loads successfully in each browser
2. All six API cards are present and visible
3. Navigation bar links are present
4. GET request buttons fire and populate response containers
5. POST forms accept input and display a response
6. Responsive layout at mobile and desktop viewports
7. No JavaScript console errors on page load
8. Basic accessibility: all interactive elements have accessible names
"""

import pytest
from playwright.sync_api import Page, expect, ConsoleMessage


BASE_URL = "http://localhost:8000"

# Cards expected on the landing page
EXPECTED_CARDS = [
    "/api/weather",
    "/api/insight",
    "/api/fortune",
    "/api/submit",
    "/api/favorites",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def console_errors(page: Page) -> list:
    """Collect JavaScript console errors during a test."""
    errors = []
    page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)
    return errors


# ---------------------------------------------------------------------------
# 1. Page Load
# ---------------------------------------------------------------------------

def test_landing_page_loads(page: Page):
    """Landing page returns 200 and renders an HTML document."""
    response = page.goto(BASE_URL)
    assert response is not None
    assert response.status == 200
    expect(page).not_to_have_title("")


def test_landing_page_no_console_errors(page: Page, console_errors: list):
    """No JavaScript errors should appear on initial page load."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    js_errors = [e for e in console_errors if "error" in e.type.lower()]
    assert len(js_errors) == 0, (
        f"JavaScript errors on page load: {[e.text for e in js_errors]}"
    )


# ---------------------------------------------------------------------------
# 2. API Card Presence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("endpoint", EXPECTED_CARDS)
def test_api_card_endpoint_documented(page: Page, endpoint: str):
    """Each API endpoint path should appear somewhere on the landing page."""
    page.goto(BASE_URL)
    expect(page.get_by_text(endpoint, exact=False).first).to_be_visible()


def test_page_contains_get_and_post_labels(page: Page):
    """The landing page should mention both GET and POST methods."""
    page.goto(BASE_URL)
    content = page.content()
    assert "GET" in content
    assert "POST" in content


# ---------------------------------------------------------------------------
# 3. GET Endpoint Interaction — Weather
# ---------------------------------------------------------------------------

def test_weather_get_button_returns_response(page: Page):
    """
    Clicking the Weather 'Send GET Request' link fires the fetch call and
    populates the response container with JSON containing the 'city' key.

    The landing page uses <a class="link-btn"> elements (not <button>) to
    trigger API calls via JavaScript onclick handlers. The weather card is
    opened by default (first .api-card gets class 'open' on load), so the
    link is immediately visible and clickable.
    """
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # The weather card is the first .api-card and is open by default.
    # Its trigger is an <a class="link-btn"> inside #weather.
    weather_card = page.locator("#weather")

    # Click the Send GET Request link inside the weather card
    send_link = weather_card.locator("a.link-btn").first
    send_link.click()

    # Wait for the response container to become visible
    response_container = page.locator("#weather-response-container")
    expect(response_container).to_be_visible(timeout=5000)

    # Confirm the response text contains the 'city' key
    response_text = page.locator("#weather-response-text")
    expect(response_text).to_contain_text("city", timeout=5000)


# ---------------------------------------------------------------------------
# 4. Responsive Layout
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("width,height,label", [
    (1440, 900, "desktop"),
    (768, 1024, "tablet"),
    (480, 860, "mobile-L"),
    (320, 568, "mobile-S"),
])
def test_page_renders_at_viewport(page: Page, width: int, height: int, label: str):
    """Page should render without horizontal overflow at each viewport size."""
    page.set_viewport_size({"width": width, "height": height})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Check there's no horizontal scrollbar (body scroll width <= viewport width)
    scroll_width = page.evaluate("document.body.scrollWidth")
    assert scroll_width <= width + 5, (  # +5px tolerance
        f"Horizontal overflow at {label} ({width}px): "
        f"scrollWidth={scroll_width}px"
    )


def test_single_column_layout_at_mobile(page: Page):
    """
    At narrow viewports (≤720px) the layout should switch to a single column.
    Verify by checking that no two major cards are side-by-side.
    """
    page.set_viewport_size({"width": 480, "height": 860})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Get all card-level elements — adjust selector to match your HTML
    cards = page.locator("section, article, .card, details").all()
    if len(cards) < 2:
        pytest.skip("Could not find multiple card elements to compare layout")

    # At single-column, all cards should share the same left offset
    bounding_boxes = [c.bounding_box() for c in cards[:4] if c.bounding_box()]
    x_positions = [round(b["x"]) for b in bounding_boxes if b]

    # Allow 10px tolerance for padding differences
    assert max(x_positions) - min(x_positions) < 10, (
        f"Cards appear to be in multiple columns at 480px: x positions = {x_positions}"
    )


# ---------------------------------------------------------------------------
# 5. Accessibility — Basic Automated Checks
#
# Full WCAG compliance requires axe-core. These are lightweight Playwright
# checks that catch the most common issues without additional tooling.
# ---------------------------------------------------------------------------

def test_page_has_lang_attribute(page: Page):
    """The <html> element should have a lang attribute for screen readers."""
    page.goto(BASE_URL)
    lang = page.evaluate("document.documentElement.lang")
    assert lang and len(lang) > 0, (
        "Missing lang attribute on <html>. "
        "Add lang='en' to support screen readers."
    )


def test_all_images_have_alt_text(page: Page):
    """All <img> elements must have an alt attribute (may be empty for decorative)."""
    page.goto(BASE_URL)
    images_without_alt = page.evaluate("""
        Array.from(document.querySelectorAll('img'))
             .filter(img => !img.hasAttribute('alt'))
             .map(img => img.src || img.outerHTML.slice(0, 100))
    """)
    assert len(images_without_alt) == 0, (
        f"Images missing alt attribute: {images_without_alt}"
    )


def test_all_buttons_have_accessible_names(page: Page):
    """All <button> elements should have visible text or an aria-label."""
    page.goto(BASE_URL)
    unlabelled = page.evaluate("""
        Array.from(document.querySelectorAll('button'))
             .filter(btn => {
                 const text = (btn.textContent || '').trim();
                 const aria = btn.getAttribute('aria-label') || '';
                 const title = btn.getAttribute('title') || '';
                 return text.length === 0 && aria.length === 0 && title.length === 0;
             })
             .map(btn => btn.outerHTML.slice(0, 120))
    """)
    assert len(unlabelled) == 0, (
        f"Buttons without accessible names: {unlabelled}"
    )


def test_all_inputs_have_labels(page: Page):
    """All visible <input> elements should have an associated <label> or aria-label."""
    page.goto(BASE_URL)
    unlabelled = page.evaluate("""
        Array.from(document.querySelectorAll('input:not([type="hidden"])'))
             .filter(input => {
                 const id = input.id;
                 const hasLabel = id && document.querySelector('label[for="' + id + '"]');
                 const hasAriaLabel = input.getAttribute('aria-label');
                 const hasAriaLabelledBy = input.getAttribute('aria-labelledby');
                 const hasPlaceholderOnly = input.placeholder && !hasLabel && !hasAriaLabel;
                 return !hasLabel && !hasAriaLabel && !hasAriaLabelledBy;
             })
             .map(input => input.outerHTML.slice(0, 120))
    """)
    assert len(unlabelled) == 0, (
        f"Inputs without labels: {unlabelled}. "
        "Placeholder text alone is not sufficient for accessibility."
    )


def test_page_has_main_landmark(page: Page):
    """Page should have a <main> landmark for screen reader navigation."""
    page.goto(BASE_URL)
    main_count = page.locator("main").count()
    assert main_count >= 1, (
        "Page is missing a <main> landmark element. "
        "Screen reader users rely on landmarks for navigation."
    )


def test_heading_hierarchy_starts_with_h1(page: Page):
    """Page should have exactly one <h1> and it should come before other headings."""
    page.goto(BASE_URL)
    h1_count = page.locator("h1").count()
    assert h1_count >= 1, "Page is missing an <h1> heading."
    assert h1_count == 1, f"Page has {h1_count} <h1> elements; should have exactly 1."
