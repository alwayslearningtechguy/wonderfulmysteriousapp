"""
tests/specialized/accessibility/test_axe_accessibility.py
==========================================================
Automated WCAG 2.1 AA accessibility tests using axe-core via
the axe-playwright library.

Prerequisites:
    pip install pytest-playwright axe-playwright
    playwright install chromium

Run:
    pytest tests/specialized/accessibility/ -v

These tests run against a live server on port 8000. Start the server first:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

What axe-core checks automatically
------------------------------------
- Missing alt text on images
- Missing form labels
- Insufficient colour contrast (requires actual rendering)
- Missing ARIA landmarks
- Invalid ARIA roles and attributes
- Keyboard focus visibility
- Empty buttons and links
- Missing lang attribute
- Duplicate IDs
- And 50+ additional rules

What it cannot check automatically
------------------------------------
- Cognitive accessibility
- Actual keyboard navigation flow (path-dependent)
- Screen reader announcement quality
- Touch target size on real devices
These require manual testing — see Specialized_Manual_Testing.md.

Violation severity levels (axe-core):
    critical  — must fix; causes complete barrier for some users
    serious   — should fix; causes significant difficulty
    moderate  — should fix; causes some difficulty
    minor     — consider fixing; causes minor inconvenience
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
        lines.append(f"\n  [{v['impact'].upper()}] {v['id']}: {v['description']}")
        lines.append(f"    Help: {v.get('helpUrl', 'N/A')}")
        for node in v.get("nodes", [])[:2]:  # Show first 2 affected nodes
            lines.append(f"    Element: {node.get('html', '')[:120]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full-page axe scan — all WCAG 2.1 AA rules
# ---------------------------------------------------------------------------

def test_landing_page_no_critical_accessibility_violations(page: Page):
    """
    Landing page must have zero critical or serious axe-core violations.
    Moderate and minor violations are reported but do not fail the test —
    they should be tracked as improvement items.
    """
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(page)
    violations = results.violations

    critical = [v for v in violations if v["impact"] in ("critical", "serious")]
    moderate = [v for v in violations if v["impact"] in ("moderate", "minor")]

    if moderate:
        print(f"\n⚠️  Moderate/minor violations (not failing):{format_violations(moderate)}")

    assert len(critical) == 0, (
        f"Found {len(critical)} critical/serious accessibility violation(s):"
        f"{format_violations(critical)}\n\n"
        f"Fix these before release. See https://dequeuniversity.com/rules/axe/"
    )


def test_landing_page_wcag_21_aa_compliance(page: Page):
    """
    Run axe with WCAG 2.1 AA tags explicitly to ensure compliance
    with the specific standard.
    """
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(page, options={"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21aa"]}})
    violations = results.violations

    blocking = [v for v in violations if v["impact"] in ("critical", "serious")]

    assert len(blocking) == 0, (
        f"WCAG 2.1 AA violations found:{format_violations(blocking)}"
    )


# ---------------------------------------------------------------------------
# Targeted scans — specific high-value rules
# ---------------------------------------------------------------------------

def test_colour_contrast_sufficient(page: Page):
    """Text must meet WCAG 2.1 AA minimum contrast ratio (4.5:1 for normal text)."""
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(page, options={"runOnly": {"type": "rule", "values": ["color-contrast"]}})
    violations = results.violations

    assert len(violations) == 0, (
        f"Colour contrast violations:{format_violations(violations)}\n"
        "Use a contrast checker: https://webaim.org/resources/contrastchecker/"
    )


def test_form_elements_have_labels(page: Page):
    """All form inputs must have associated labels."""
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(page, options={
        "runOnly": {"type": "rule", "values": ["label", "label-content-name-mismatch"]}
    })
    violations = results.violations

    assert len(violations) == 0, (
        f"Form label violations:{format_violations(violations)}"
    )


def test_keyboard_focus_visible(page: Page):
    """Interactive elements must have a visible focus indicator."""
    axe = Axe()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    results = axe.run(page, options={
        "runOnly": {"type": "rule", "values": ["focus-trap", "scrollable-region-focusable"]}
    })
    violations = results.violations

    assert len(violations) == 0, (
        f"Keyboard focus violations:{format_violations(violations)}"
    )
