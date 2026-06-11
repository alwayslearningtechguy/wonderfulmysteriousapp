# CI Troubleshooting & Maintenance Reflection

## Designing Testable Software — Lessons from the Wonderful Mysterious App

This document reflects on the practical challenges encountered while building,
running, and maintaining the CI pipeline for this project. It covers decisions
made to make the software testable, problems encountered during CI setup, and
lessons learned about the relationship between software design and test quality.

---

## 1. Designing for Testability

### State Reset as a First-Class Concern

The single most important testability decision in this project was the
introduction of `test_utils.py` and the `reset_state()` function, called via
an `autouse=True` fixture before every unit and integration test.

Without this, tests that write to `db["favorites"]` or exhaust the rate limiter
would leave state that contaminates subsequent tests. The failure mode is subtle:
tests pass in isolation but fail intermittently depending on execution order —
one of the hardest categories of test failure to diagnose.

The lesson: shared mutable state (even simple in-memory dicts) must be
explicitly reset between tests. Don't rely on test ordering or assume state
is clean.

### Separating the Rate Limiter into its own Module

The `RateLimiter` class lives in `app/rate_limiter.py` rather than inline in
`app/main.py`. This made it directly importable in unit tests:

```python
from app.rate_limiter import RateLimiter
rl = RateLimiter(max_requests=3, window_seconds=60)
assert rl.is_allowed("1.1.1.1")
```

If the rate limiter were embedded in middleware with no seam, the only way to
test it would be to send 100 real HTTP requests and observe the 429 — slow,
expensive, and unable to test the per-IP logic in isolation.

The lesson: middleware logic with non-trivial behavior should be extracted into
testable classes. The middleware itself becomes a thin wrapper.

### E2E State Isolation — the Port 8001 Pattern

The rate limit E2E test needs to send 101 requests and observe a 429. If it
shares a server with other E2E tests, it consumes the rate limit budget for
all of them — any test running after it would get 429s unexpectedly.

The solution was to start a second Uvicorn instance on port 8001 exclusively
for the rate limit test. This gives it a fresh budget of 100 without affecting
the shared server on port 8000.

The lesson: when a test has destructive or resource-consuming side effects that
can't be reset between tests, isolate it at the infrastructure level rather than
trying to coordinate test ordering.

### Async Route Handlers and pytest-asyncio

FastAPI route handlers are async functions. Testing them directly (not via
HTTP) requires `pytest-asyncio` and the `@pytest.mark.asyncio` decorator.
The project uses `asyncio_mode = STRICT` which requires every async test to
be explicitly marked — this is more verbose but prevents accidental synchronous
execution of async tests, which would silently pass without actually running
the async code.

The lesson: async code requires explicit test infrastructure. `STRICT` mode
is the right default — it surfaces problems rather than hiding them.

### The Dockerfile as a Local Test Enforcement Mechanism

The multi-stage Dockerfile ensures unit and integration tests run whenever
anyone builds the image — whether via GitHub Actions, a local `docker build`,
or after cloning the repo and running Docker Compose. Stage 1 installs both
runtime and test dependencies and runs `pytest tests/unit tests/integration`
before Stage 2 produces the runtime image. A failing test breaks the build
regardless of how or where it is triggered. This means CI is not the only
gate — the Docker build itself is a test enforcement mechanism available to
anyone with the source code.

---

## 2. CI Pipeline Problems Encountered and Fixed

### Problem: Bandit Flag Conflict

**Error:** `bandit: error: argument --severity-level: not allowed with argument -l/--level`

**Cause:** The initial CI workflow used both `-l` (old short flag) and
`--severity-level` (new long flag) in the same Bandit invocation. Newer
versions of Bandit treat these as conflicting arguments.

**Fix:** Replaced `--severity-level high` with `-lll` (three l's = high
severity only) and `-iii` (three i's = high confidence only), which are
the correct short-flag equivalents.

**Lesson:** Pin tool versions in `requirements-dev.txt`. Flag interfaces
change across minor versions. When a tool fails in CI but works locally,
check whether the versions match.

---

### Problem: Playwright Button Selector Timeout

**Error:** `TimeoutError: Locator.click: Timeout 30000ms exceeded — waiting for locator("section, div, details").filter(has_text="/api/weather").first.get_by_role("button").first`

**Cause:** The cross-browser test used a generic selector (`get_by_role("button")`)
to find the weather card's send button. The landing page uses `<a class="link-btn">`
elements with JavaScript `onclick` handlers — not `<button>` elements. Playwright's
role-based selector correctly found nothing.

**Fix:** Updated the selector to target the actual HTML structure:
```python
weather_card = page.locator("#weather")
send_link = weather_card.locator("a.link-btn").first
```

**Lesson:** Browser automation tests written without access to the actual HTML
will produce selectors that don't match. Always inspect the real DOM before
writing Playwright selectors. Generic role-based selectors are fragile when
the HTML uses non-semantic elements for interactive components.

---

### Problem: axe-playwright-python API Mismatch

**Error (round 1):** `AttributeError: 'AxeResults' object has no attribute 'violations'`
**Error (round 2):** `TypeError: 'AxeResults' object is not subscriptable`

**Cause:** The `axe-playwright-python` library returns an `AxeResults` object
that supports neither attribute access (`.violations`) nor dict-style access
(`["violations"]`). The actual violations list is accessed via
`results.response["violations"]`.

**Fix:** Introduced a `get_violations(results)` helper:
```python
def get_violations(results) -> list:
    return results.response["violations"]
```

**Lesson:** Third-party library APIs are not always documented accurately or
match what their README suggests. When a library returns an opaque object,
inspect its source code (`inspect.getsource()`) to find the actual data
structure before writing tests against it.

---

### Problem: OWASP ZAP Artifact and Permission Errors

**Error 1:** `Resource not accessible by integration` when ZAP tried to create
a GitHub Issue and upload an artifact.

**Cause:** The default `GITHUB_TOKEN` in GitHub Actions does not have
`issues: write` or `actions: write` permissions. The ZAP action attempts
both operations to report results.

**Fix:** Added explicit permissions to the `security-tests` job:
```yaml
permissions:
  contents: read
  issues: write
  actions: write
```

**Error 2:** Artifact upload annotation failure despite a valid artifact name.

**Cause:** Even with a valid name (`zap-report`), the ZAP action's internal
artifact creation can fail at the GitHub Actions API level when permissions
are partially resolved.

**Fix:** Disabled the ZAP action's own artifact management entirely by setting
`artifact_name: ""` and relying on the separate `upload-artifact` step for
report storage. This cleanly separates scanning from reporting.

**Lesson:** GitHub Actions jobs run with a minimal token by default. Any action
that writes to the repository requires explicit permission grants. When a
third-party action manages its own artifact upload, conflicts with the workflow's
upload step can cause confusing errors. Prefer letting one step own artifact
management.

---

### Problem: Input Labels Accessibility Failure

**Error:** `AssertionError: Inputs without labels: ['<input type="text" id="weather-city"...']`

**Cause:** The landing page had `<label>` elements visually associated with
inputs but without `for` attributes linking them programmatically. Adding
`for` attributes didn't fix the test because the label check queries the DOM
via JavaScript and inputs inside collapsed cards weren't resolving the
association correctly.

**Fix:** Added `aria-label` attributes directly to each input element:
```html
<input type="text" id="weather-city" aria-label="City" placeholder="Seattle">
```

**Lesson:** Visual appearance and programmatic accessibility are not the same
thing. A label that looks connected to an input in the browser is meaningless
to a screen reader without the `for`/`id` association or an `aria-label`.
Accessibility tests catch real issues — treat failures as findings, not
as obstacles.

---

### Problem: Color Contrast Violation

**Error:** `[SERIOUS] color-contrast: Ensures the contrast between foreground
and background colors meets WCAG 2 AA contrast ratio thresholds — Element:
<p class="api-section-title">`

**Cause:** The `--muted` CSS variable (`#4a5560`) used for section titles and
table headers did not meet the WCAG AA 4.5:1 minimum contrast ratio against
the dark surface background (`#13171a`).

**Fix:** Updated `--muted` in the CSS `:root` from `#4a5560` to `#7a8f9e`,
which passes the contrast check while maintaining the intended subdued aesthetic.

**Lesson:** Dark-theme designs frequently fail contrast checks for secondary
text colors. Automated accessibility testing in CI catches these before users
with visual impairments encounter them.

---

### Problem: Docker Healthcheck — curl Not Available in Slim Image

**Error:** Container healthcheck silently fails because `curl` is not installed
in `python:3.11-slim`.

**Cause:** The initial `docker-compose.yml` used a curl-based healthcheck:
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```
`python:3.11-slim` strips out non-essential tools including `curl` to minimize
image size. The healthcheck command exits with "not found" and the container
is marked unhealthy even though the app is running correctly.

**Fix:** Replaced the curl command with Python's built-in `urllib.request`,
which is guaranteed to be available in any Python runtime image:
```yaml
test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
```

**Lesson:** Never assume shell tools are available in minimal Docker base
images. `python:3.11-slim`, `node:alpine`, and similar slim/alpine images
omit curl, wget, bash, and many other utilities by default. Use the runtime
language's standard library for operational commands wherever possible — it
has no additional dependencies and will always be present.

---

## 3. What Made the Software Testable

Looking back, the design decisions that most enabled effective testing were:

**Hardcoded data pools instead of external APIs.** Because `WEATHER_DATA`,
`INSIGHTS`, and `FORTUNES` are static dicts in `main.py`, there is no network
dependency, no mocking required, and no flakiness from external service
availability. Tests run identically in CI and locally.

**Explicit state with a reset mechanism.** `db = {"favorites": []}` is simple,
visible, and resettable. A database or cache would require teardown fixtures,
container lifecycle management, or test database isolation strategies.

**Thin middleware.** The rate limiter middleware is a single `if` statement
that delegates to `RateLimiter.is_allowed()`. The interesting logic is in the
class, which is unit-testable. The middleware itself is integration-testable.

**Consistent response shapes.** Every endpoint returns a well-defined JSON
structure with documented field names and types. This made schema assertion
tests straightforward to write and maintain.

---

## 4. What Would Be Harder to Test in a More Complex System

This project's simplicity is also its limitation as a learning vehicle. In a
production system, the following would add significant testing complexity:

- **External API dependencies** (real weather data) would require mocking,
  VCR cassettes, or contract testing
- **A real database** would require test isolation via transactions, test
  databases, or containerized instances
- **Authentication** would require test users, token management, and
  authorization matrix testing
- **Asynchronous background jobs** would require event-driven test patterns
  and timing-sensitive assertions
- **Multiple services** would require service virtualization or a full
  integration environment

The Wonderful Mysterious App intentionally avoids all of these, making it
an effective environment for learning the fundamentals of test strategy,
CI pipeline construction, and testability design without the noise of
infrastructure complexity.
