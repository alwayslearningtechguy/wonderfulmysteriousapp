"""
tests/specialized/accessibility/test_axe_accessibility.py
==========================================================
Automated WCAG 2.1 AA accessibility tests using axe-core via
the axe-playwright-python library.

Prerequisites:
    pip install pytest-playwright axe-playwright-python
    playwright install chromium

Run:
    pytest tests/specialized/accessibility/ -v

These tests require a live server on port 8000. Start it first:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

API note (axe-playwright-python 0.1.x):
    axe.run(page) returns a plain dict, not a typed object.
    Access results as results["violations"], not results.violations.
"""

import pytest
from playwright.sync_api import Page

try:
    from axe_playwright_python.sync_playwright import Axe
    AXE_AVAILABLE = True
except ImportError:
    AXE_AVAILABLE = False

BASE_URL = "http://localhost:8000"

pytestmark = pytest.mark.skipif(
    not AXE_AVAILABLE,
    reason="axe-playwright-python not installed. Run: pip install axe-playwright-python"
)


def format_violations(violations: list) -> str:
    """Format axe-core violations for readable test output."""
    lines = []
    for v in violations:
        impact = v.get("impact", "unknown").upper()
        lines.append(f"\n  [{impact}] {v['id']}: {v['description']}")
        lines.append(f"    Help: {v.get('helpUrl', 'N/A')}")
        for node in v.get("nodes", [])[:2]:
            lines.append(f"    Element: {node.get('html', '')[:120]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. Full-page axe scan — critical and serious violations fail the build
# ---------------------------------------------------------------------------

def test_landing_page_no_critical_accessibility_violations(page: Page):
    """
    Landing page must have zero critical or serious axe-core violations.
    Moderate and minor violations are reported but do not fail the test.
    """
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(page)
    violations = results["violations"]

    critical = [v for v in violations if v.get("impact") in ("critical", "serious")]
    moderate = [v for v in violations if v.get("impact") in ("moderate", "minor")]

    if moderate:
        print(f"\n⚠️  Moderate/minor violations (not failing):{format_violations(moderate)}")

    assert len(critical) == 0, (
        f"Found {len(critical)} critical/serious accessibility violation(s):"
        f"{format_violations(critical)}\n\n"
        f"Fix these before release. See https://dequeuniversity.com/rules/axe/"
    )


# ---------------------------------------------------------------------------
# 2. WCAG 2.1 AA tag-based scan
# ---------------------------------------------------------------------------

def test_landing_page_wcag_21_aa_compliance(page: Page):
    """
    Run axe with WCAG 2.1 AA tags explicitly to confirm compliance
    with the specific standard.
    """
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(
        page,
        options={"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21aa"]}}
    )
    violations = results["violations"]

    blocking = [v for v in violations if v.get("impact") in ("critical", "serious")]

    assert len(blocking) == 0, (
        f"WCAG 2.1 AA violations found:{format_violations(blocking)}"
    )


# ---------------------------------------------------------------------------
# 3. Colour contrast
# ---------------------------------------------------------------------------

def test_colour_contrast_sufficient(page: Page):
    """Text must meet WCAG 2.1 AA minimum contrast ratio (4.5:1 for normal text)."""
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(
        page,
        options={"runOnly": {"type": "rule", "values": ["color-contrast"]}}
    )
    violations = results["violations"]

    assert len(violations) == 0, (
        f"Colour contrast violations:{format_violations(violations)}\n"
        "Use a contrast checker: https://webaim.org/resources/contrastchecker/"
    )


# ---------------------------------------------------------------------------
# 4. Form labels
# ---------------------------------------------------------------------------

def test_form_elements_have_labels(page: Page):
    """All form inputs must have associated labels."""
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(
        page,
        options={"runOnly": {"type": "rule", "values": ["label"]}}
    )
    violations = results["violations"]

    assert len(violations) == 0, (
        f"Form label violations:{format_violations(violations)}"
    )


# ---------------------------------------------------------------------------
# 5. Keyboard / focus accessibility
#    focus-trap is not a valid axe rule ID — replaced with valid rules:
#    - scrollable-region-focusable: scrollable regions must be keyboard reachable
#    - tabindex: elements must not have tabindex > 0 (breaks natural focus order)
# ---------------------------------------------------------------------------

def test_keyboard_focus_accessible(page: Page):
    """
    Scrollable regions must be reachable by keyboard, and no element should
    have a tabindex greater than 0 (which disrupts natural focus order).
    """
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(
        page,
        options={
            "runOnly": {
                "type": "rule",
                "values": ["scrollable-region-focusable", "tabindex"]
            }
        }
    )
    violations = results["violations"]

    assert len(violations) == 0, (
        f"Keyboard focus violations:{format_violations(violations)}"
    )
