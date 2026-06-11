# CI Troubleshooting & Maintenance Reflection

## Designing Testable Software — Lessons from the Wonderful Mysterious App

This document reflects on the practical challenges encountered while building,
running, and maintaining the CI pipeline for this project. It covers decisions
made to make the software testable, problems encountered during CI setup, and
lessons learned about the relationship between software design and test quality.

I do want to acknowledge that I found myself fighting scope creep over the lifecycle of
this project. I would want to adjust some design in the HTML or API feature or make an 
adjustment to the middleware, only to realize that post change, it breaks some of the
automated (and sometimes manual) tests. Then I would return back to the tests and adjust 
them based on my current design. Keeping the CI pipeline, with its expanding types of tests,
and integration with GitHub in sync was a lesson I learned the importance of along the way.

---

## 1. Designing for Testability

### State Reset Concern

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

### E2E State Isolation via Port 8001

The rate limit E2E test needs to send 101 requests and observe a 429. If it
shares a server with other E2E tests, it consumes the rate limit budget for
all of them — any test running after it would get 429s unexpectedly.

The solution was to start a second Uvicorn instance on port 8001 exclusively
for the rate limit test. This gives it a fresh budget of 100 without affecting
the shared server on port 8000.

The lesson: when a test has resource-consuming side effects that
can't be reset between tests, isolate it at the infrastructure level rather than
trying to coordinate test ordering.

### Async Route Handlers and pytest-asyncio

FastAPI route handlers are async functions. Testing them directly (not via
HTTP) requires `pytest-asyncio` and the `@pytest.mark.asyncio` decorator.
The project uses `asyncio_mode = STRICT` which requires every async test to
be explicitly marked — this is more verbose but prevents accidental synchronous
execution of async tests, which would silently pass without actually running
the async code. I had to look into how this worked in particular as it was completely new to me.

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

### Problem: Tool Syntax Integrations

**Error:** `bandit: error: argument --severity-level: not allowed with argument -l/--level`

**Cause:** The initial CI workflow used both `-l` (old short flag) and
`--severity-level` (new long flag) in the same Bandit invocation. This was bad syntax.

**Fix:** Replaced `--severity-level high` with `-lll` (three l's = high
severity only) and `-iii` (three i's = high confidence only), which are
the correct short-flag equivalents.

**Lesson:** When incorporating tools in one's project, it is best to evaluate the syntax and review integration functionality prior to pushing a commit.

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

**Lesson:** Browser automation tests written without understanding the correct actual HTML
will produce selectors that don't match. AI can hallucinate and seem to think it reads the HTML, but very evidently does not parse it or understand it fully. This gives me confidence that a human in a loop will still be a vital element in development and engineering as we move into the future.

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
upload step can cause confusing errors. When incorporating tools into a solution or in my case expanding the way a tool is used, it is best to look at the documentation and have trial and error practice in a dev environment versus a pseudo production environment. :)

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
It is somewhat challenging to meaningfully incorporate some of these tests, 
with little knowledge of how they are confiugred to identify and guage accessiblitity. 

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

**Lesson:** After reviewing my frontend and thinking the contrast was sufficient, I added the contrast test into my CI 
and had it fail. This was a good lesson to (re)learn the value of partnering with objective tests to remove subjectivity.

---

### Problem: Docker Healthcheck — curl Not Available in Slim Image

**Error:** Container healthcheck silently fails because `curl` is not installed
in `python:3.11-slim`.

**Cause:** In one of my `docker-compose.yml` versions, I used a curl-based healthcheck:
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```
Apparently based on the CI logs, `python:3.11-slim` strips out non-essential tools including `curl` to minimize
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
availability. Tests run identically in CI and locally. This is something that works 
for a mock project with this particular scope, but I recognize would not exist 
generally in a production business app.

**Explicit state with a reset mechanism.** `db = {"favorites": []}` is simple,
visible, and resettable. The simple structure made easy testing. A robust database, beyond requiring building up the
infrastructure, would require more complext management and testing strategies. 

**Consistent response shapes.** Every endpoint returns a well-defined JSON
structure with documented field names and types. This made schema assertion
tests straightforward to write and maintain.

---



