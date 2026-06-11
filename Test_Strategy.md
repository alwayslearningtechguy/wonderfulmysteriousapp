# Test Strategy — Wonderful Mysterious App v3.1

## 1. Purpose

This document describes the overall testing strategy for the *Wonderful and
Mysterious API*: the principles behind test design decisions, the rationale for
what is automated versus manual, and the quality targets the test suite enforces.

---

## 2. Testing Layers

The test suite is organized into five layers, each serving a distinct purpose.

### Layer 1 — Unit Tests

**Purpose:** Verify individual route handler functions in isolation.

**Approach:** Import async handlers directly from `app.main` and call them
with `pytest-asyncio`. No HTTP stack, no middleware, no rate limiter. State
is reset before every test via an `autouse` fixture.

**Design principle:** If a unit test fails, the cause is always inside the
function under test — never in middleware, routing, or infrastructure.

### Layer 2 — Integration Tests

**Purpose:** Verify the full FastAPI stack including middleware, routing,
validation, and state management.

**Approach:** `FastAPI.TestClient` sends real HTTP requests through the full
application stack. State is reset before every test via an `autouse` fixture
that calls `reset_state()`.

**Design principle:** Integration tests confirm that the pieces assemble
correctly. They do not replace unit tests — they complement them.

### Layer 3 — E2E Tests

**Purpose:** Verify the application behaves correctly as a running process,
including subprocess startup, real network I/O, and process-level behavior.

**Approach:** A session-scoped fixture starts Uvicorn as a subprocess on port
8000. Tests use `httpx.Client` to send real HTTP requests. A second isolated
subprocess on port 8001 is used for rate limit testing to prevent budget
contamination of the shared server.

**Design principle:** E2E tests confirm that the application works as deployed,
not just as code. They are the last line of automated defense before release.

### Layer 4 — Specialized Tests

**Purpose:** Cover quality dimensions not addressed by functional tests:
security, performance, cross-browser compatibility, and accessibility.

**Approach and rationale:**

| Area | Tool | Why automated |
|---|---|---|
| Security headers | pytest + TestClient | Deterministic, no server needed, fast |
| Input limits and method validation | pytest + TestClient | Deterministic, regression-safe |
| Dependency vulnerabilities | pip-audit | New CVEs published continuously; must run on every push |
| Static analysis | Bandit | Catches common Python security antipatterns at source level |
| OWASP ZAP passive scan | ZAP baseline action | Catches HTTP-level issues a unit test cannot see |
| Performance | Locust | Enforces the p95 < 200ms SLA; prevents silent regressions |
| Cross-browser | Playwright | Catches rendering and JS execution differences across engines |
| Accessibility | axe-core | Catches structural WCAG violations at scale; complements manual screen reader testing |

### Layer 5 — Manual Tests

**Purpose:** Cover quality dimensions that cannot be meaningfully automated.

| Area | Why manual |
|---|---|
| Safari (desktop and iOS) | macOS runner not available in CI |
| Screen reader behavior | Automated tools detect structural issues; only humans can evaluate announcement quality |
| Keyboard navigation flow | Path-dependent; requires human judgment |
| Color contrast of dynamic content | axe-core scans static DOM; JS-populated response containers need human verification |
| Rate limit window reset | Requires real wall-clock wait; impractical in CI |
| OWASP ZAP full active scan | Sends attack payloads; not safe to run on every push |
| Sustained load / memory leak detection | Requires monitored long run with human observation |
| Docker container restart behavior | Requires Docker stop/start cycle |

---

## 3. Quality Targets

| Metric | Target | How enforced |
|---|---|---|
| Functional correctness | 100% of defined behaviors tested | Unit + integration + E2E |
| p95 response time | < 200ms under 10 concurrent users | Locust CI job |
| Error rate under load | < 1% | Locust CI job |
| Dependency vulnerabilities | Zero known CVEs | pip-audit CI job |
| Security headers | Present on all responses | Security test suite |
| WCAG 2.1 AA | Zero critical/serious violations | axe-core CI job |
| Cross-browser | Passes on Chromium and Firefox | Playwright CI matrix |

**Note on code coverage:** Coverage measurement via `pytest-cov` is not
currently configured. This is a known open item. The existing test suite
exercises all primary code paths, but branch coverage for `WEATHER_DATA`
lookup (10 named cities plus fallback) and random selection paths is not
formally measured.

---

## 4. State Management

A critical design decision in this test suite is how state is managed between
tests.

**Unit and integration tests:** An `autouse=True` fixture in `conftest.py`
calls `reset_state()` before every test. This resets `db["favorites"]` and
the rate limiter's request counters. Tests are completely isolated from each
other regardless of execution order.

**E2E tests:** The E2E conftest does not call `reset_state()` — it cannot,
because it communicates with a subprocess over HTTP rather than importing the
app directly. E2E tests that write to favorites may leave state that affects
subsequent E2E tests reading favorites. This is a known and accepted limitation
documented in the E2E test report. CI run evidence confirms this does not
cause failures in practice due to test ordering.

**Rate limit isolation in E2E:** The `test_live_server_rate_limit_returns_429`
test starts a second Uvicorn instance on port 8001. This gives the test a
fresh rate limit budget of 100 and prevents it from consuming requests on the
shared server. All other E2E tests use port 8000 exclusively.

---

## 5. CI/CD Integration

The CI pipeline runs five jobs, structured so that specialized tests only run
after the core build and test job succeeds.

```
build-and-test (unit + integration + Docker build)
    │
    ├── e2e-tests
    ├── security-tests (pip-audit + Bandit + security pytest + ZAP)
    ├── performance-tests (Locust)
    └── cross-browser-accessibility-tests (Playwright matrix: chromium, firefox)
```

All specialized jobs run in parallel after `build-and-test`. A failure in any
job fails the overall pipeline. Security reports, performance CSVs, and
Playwright traces on failure are uploaded as artifacts with 30-day retention.

The pipeline triggers on every push and every pull request. A scheduled weekly
run (`cron: '0 9 * * 1'`) is recommended to catch newly published CVEs on
dormant branches without requiring a code push.

---

## 6. Pareto Analysis — Highest Value Tests

Applying the Pareto principle to this specific product, the 20% of tests that
deliver 80% of the value are:

1. **Security header tests** — lowest effort to fix, highest scanner visibility,
   directly addresses the most common automated finding against HTTP APIs.

2. **pip-audit dependency scan** — catches CVEs like CVE-2026-48710 (BadHost /
   Starlette) automatically the moment they are published, without requiring a
   code change to trigger detection.

3. **Performance baseline (Locust)** — the only mechanism that enforces the p95
   < 200ms SLA stated in this document; without it the target is aspirational only.

4. **axe-core accessibility scan** — identified a genuine WCAG AA color contrast
   violation (`--muted: #4a5560`) during this cycle that would not have been caught
   by any other automated test.

---

## 7. Automation Philosophy

Approximately 70% of testing in this project is automated. The remaining 30%
is intentionally manual — not because automation is impractical, but because
some quality signals require human judgment to interpret correctly.

Automated tests are appropriate when: the pass/fail criterion is deterministic,
the test is stable across runs, and the cost of a false positive or false
negative is low.

Manual tests are appropriate when: the evaluation requires human perception
(screen reader quality, visual layout judgment), the test is inherently
time-dependent (rate limit window reset), or the test involves destructive
actions not safe to run in CI (ZAP full active scan, Docker restart).

Tests that are technically automatable but would be unreliable or slow
(e.g. sleeping 11 seconds for a rate limit window) are deliberately kept
manual. A flaky or slow automated test is worse than a well-documented
manual procedure.
