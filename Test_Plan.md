# Test Plan — Wonderful Mysterious App v3.1

## 1. Overview

This document defines the testing approach, scope, objectives, and coverage
requirements for the *Wonderful and Mysterious API*. It covers all testing
layers: unit, integration, end-to-end, and specialized testing added in the
current release cycle.

---

## 2. Objectives

- Verify all API endpoints return correct HTTP status codes, JSON structures,
  and field types
- Confirm rate limiting enforces the 100-request-per-window global limit
- Confirm the landing page is reachable, documents all endpoints, and meets
  usability and accessibility requirements
- Confirm the application tolerates malformed and hostile input without crashing
  or leaking internal details
- Confirm standard HTTP security headers are present on all responses
- Confirm no known vulnerabilities exist in declared dependencies
- Confirm the application meets WCAG 2.1 AA accessibility standards
- Confirm the landing page functions correctly across Chromium and Firefox
- Confirm p95 response time remains below 200ms under 10 concurrent users

---

## 3. Scope

### 3.1 In Scope

| Area | Coverage |
|---|---|
| All API endpoints (GET and POST) | Unit, integration, E2E |
| Rate limiter (global, per-IP) | Unit, integration, E2E |
| Landing page (HTML, links, methods, parameters) | Integration, E2E, cross-browser |
| Input validation (422 on missing fields) | Integration, E2E |
| Input tolerance (hostile/oversized input) | Security tests |
| HTTP security headers | Security tests |
| Dependency vulnerabilities | pip-audit (CI) |
| Static code analysis | Bandit (CI) |
| OWASP ZAP passive scan | CI (baseline) |
| WCAG 2.1 AA accessibility | axe-core, Playwright |
| Cross-browser UI (Chromium, Firefox) | Playwright |
| Responsive layout (320px – 1440px) | Playwright |
| Performance (p95 < 200ms, 10 users) | Locust (CI) |

### 3.2 Out of Scope

| Area | Reason |
|---|---|
| Safari browser | macOS runner required; tested manually |
| Mobile / tablet devices | App not network-accessible from physical devices |
| OWASP ZAP full active scan | Requires manual execution; see manual testing doc |
| Penetration testing | Not in scope for this release |
| Persistent storage | App uses in-memory storage by design |
| Authentication / authorisation | Not implemented |
| TLS / HTTPS | Not configured for this release |
| Internet Explorer | End-of-life |

---

## 4. Test Layers

### 4.1 Unit Tests (`tests/unit/`)

Test individual async route handlers in isolation by importing them directly
from `app.main`. State is reset before every test via the `autouse` fixture
in `conftest.py`.

**Coverage:**
- `get_weather` — default and custom city
- `get_insight` — default topic, known topic, unknown topic fallback, available topics
- `get_fortune` — structure, field types, id range, content from pool
- `post_submit` — payload structure and echo
- `add_favorite` / `get_favorites` — state mutation and read
- `RateLimiter` — allows within limit, blocks after limit

### 4.2 Integration Tests (`tests/integration/`)

Test all endpoints via `FastAPI.TestClient`. State is reset before every test
via the `autouse` fixture.

**Coverage:**
- All endpoints: correct status codes and JSON structure
- Fortune, insight: field types, non-empty strings, fallback behavior
- Weather: default and custom city
- Submit: payload echo, missing field 422
- Favorites: add and read state
- Rate limiting: 100 allowed, 101st blocked
- Security: API tolerates and echoes script-like input without crashing
- Usability: landing page reachable, returns HTML, documents all endpoints
  with links, HTTP methods, and query parameters

### 4.3 E2E Tests (`tests/e2e/`)

Test the full stack against a live Uvicorn subprocess on port 8000. A second
isolated subprocess on port 8001 is used exclusively for the rate limit E2E
test to prevent budget contamination.

**Coverage:**
- Full user flow (weather → insight → fortune → submit → favorites)
- Health check on all GET endpoints
- Schema validation on all endpoint responses
- Favorites POST/GET read-back, input validation (422)
- Submit field assertions, missing field 422, isolation from favorites
- Rate limit: 100 allowed, 101st blocked, per-IP isolation
- Landing page: 200, HTML content-type, all endpoints linked

### 4.4 Specialized Tests (`tests/specialized/`)

#### Security (`tests/specialized/security/`)

Tests run via `TestClient` — no live server required.

| Area | Tests |
|---|---|
| HTTP security headers | X-Content-Type-Options, X-Frame-Options, Referrer-Policy present and correct on GET and POST responses |
| Input size limits | Oversized user field, oversized data dict, long city name, long topic — all return non-500 |
| Unsupported HTTP methods | POST on GET-only routes, DELETE/PUT on favorites — return 405 |
| Error response hygiene | 422 and 405 responses contain no stack traces, file paths, or internal details |
| Content-type enforcement | Form data and plain text to JSON endpoints return 422, not 500 |

Additional security checks run in CI outside pytest:

| Tool | Target | Failure condition |
|---|---|---|
| pip-audit | `requirements.txt` | Any known CVE in declared dependencies |
| Bandit | `app/` source | High severity, high confidence findings |
| OWASP ZAP baseline | Running app on port 8000 | Any FAIL-level alert per `.zap/rules.tsv` |

#### Performance (`tests/specialized/performance/`)

Locust load test. Pass/fail enforced via the `quitting` event hook.

| Parameter | Value |
|---|---|
| Tool | Locust |
| Concurrent users | 10 |
| Spawn rate | 2 users/second |
| Duration | 30 seconds |
| p95 target | < 200ms |
| Error rate target | < 1% |

#### Cross-Browser (`tests/specialized/cross_browser/`)

Playwright tests run against a live server. CI matrix: Chromium and Firefox.
Safari is manual only.

| Area | Tests |
|---|---|
| Page load | 200 response, no JS console errors |
| Card presence | All 5 endpoint paths visible |
| Interaction | Weather GET button fires and populates response container |
| Responsive layout | No horizontal overflow at 320, 480, 768, 1440px |
| Accessibility (basic) | lang attribute, image alt text, button names, input labels, main landmark, h1 hierarchy |

#### Accessibility (`tests/specialized/accessibility/`)

axe-core scans via `axe-playwright-python`. Run against Chromium and Firefox.

| Test | Standard |
|---|---|
| No critical/serious violations | axe-core all rules |
| WCAG 2.1 AA compliance | wcag2a, wcag2aa, wcag21aa tags |
| Color contrast | WCAG AA 4.5:1 minimum |
| Form labels | All inputs have programmatic labels |
| Keyboard focus | No keyboard traps, no tabindex > 0 |

---

## 5. Test Data

All test data is hardcoded or generated within tests. No external data sources,
databases, or network calls are used. The application itself uses hardcoded data
pools (`WEATHER_DATA`, `INSIGHTS`, `FORTUNES`) — no mocking of external APIs
is required.

---

## 6. Entry and Exit Criteria

### Entry Criteria
- All source changes committed to the branch under test
- `requirements.txt` and `requirements-dev.txt` up to date
- Docker image builds successfully (Stage 1 test run must pass)

### Exit Criteria
- All automated tests pass (0 failures)
- No pip-audit CVEs in declared dependencies
- No Bandit high-severity findings
- OWASP ZAP baseline scan produces no FAIL-level alerts
- p95 latency confirmed below 200ms
- All manual testing procedures in `Manual_Testing.md` and
  `Specialized_Manual_Testing.md` completed and signed off

---

## 7. Known Gaps and Accepted Limitations

| Gap | Acceptance rationale |
|---|---|
| Duplicate favorites behavior untested | In-memory append-only behavior is simple and observable; low risk |
| Rate limit window reset not automated | Requires wall-clock wait; impractical in CI; covered manually |
| Code coverage not measured | No `pytest-cov` configured; known open item for next cycle |
| Safari not automated | macOS runner not available; covered manually |
| Screen reader testing manual | Cannot be meaningfully automated; covered manually |
| Sustained load / memory leak manual | Requires monitored long run; covered manually |

---

## 8. Tools and Dependencies

| Tool | Version | Purpose |
|---|---|---|
| pytest | 8.3.5 | Test runner |
| pytest-asyncio | 0.25.3 | Async test support |
| httpx | 0.28.1 | HTTP client for E2E tests |
| anyio | 4.13.0 | Async I/O |
| locust | 2.32.2 | Load testing |
| pytest-playwright | 0.5.2 | Browser automation |
| axe-playwright-python | 0.1.3 | Accessibility scanning |
| pip-audit | 2.7.3 | Dependency vulnerability scanning |
| bandit | 1.7.10 | Static security analysis |
