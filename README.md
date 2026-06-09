# The Wonderful & Mysterious API 3.1

A self-contained FastAPI application that exposes several fun and useful
endpoints — weather data, insights, fortunes, data submission, and user
favorites — all backed by in-memory storage with no external service
dependencies. Built as a learning project for software testing strategy,
CI/CD pipeline design, and testability principles.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Data validation | Pydantic |
| Container | Docker (multi-stage build) |
| Orchestration | Docker Compose |
| Test runner | pytest + pytest-asyncio |
| E2E HTTP client | httpx |
| Browser automation | Playwright |
| Accessibility scanning | axe-core (axe-playwright-python) |
| Load testing | Locust |
| Dependency scanning | pip-audit |
| Static analysis | Bandit |
| Security scanning | OWASP ZAP |
| CI/CD | GitHub Actions |

---

## Quick Start

### Run with Docker Compose (recommended)

```bash
git clone https://github.com/AlwaysLearningTechGuy/WonderfulMysteriousApp.git
cd WonderfulMysteriousApp
docker compose up --build
```

Open `http://localhost:8000` in your browser.

### Run with Docker directly

```bash
# Build the image (runs unit + integration tests during build)
docker build -t wonderfulmysteriousapp .

# Run the container
docker run -p 8000:8000 wonderfulmysteriousapp
```

### Run locally (without Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

---

## API Endpoints

| Method | Endpoint | Input | Description |
|---|---|---|---|
| GET | `/` | None | Interactive landing page with live API test forms |
| GET | `/health` | None | Health check — returns `{"status": "ok"}` |
| GET | `/api/weather` | `city` (string, optional) | Returns mock weather data. Defaults to Seattle |
| GET | `/api/insight` | `topic` (string, optional) | Returns a random insight. Defaults to `general` |
| GET | `/api/fortune` | None | Returns a random fortune |
| POST | `/api/submit` | `{ "user": string, "data": {} }` | Accepts and echoes a structured payload |
| GET | `/api/favorites` | None | Returns the current favorites list |
| POST | `/api/favorites` | `{ "id": integer }` | Adds an integer ID to the favorites list |

> **Note:** The favorites endpoint stores integer IDs only — passing anything
> other than a whole number will return a `422 Unprocessable Entity` error.
> These IDs are intended to correspond to the `id` values returned by the
> `/api/insight` and `/api/fortune` endpoints.
>
> **Note:** `POST /api/submit` validates the request body and returns
> `201 Created` with the submitted payload echoed back. It does **not**
> persist data or interact with the favorites list. Input is **not**
> sanitized — submitted values including special characters are returned as-is.
>
> **Note:** Rate limiting is enforced globally via middleware at **100 requests
> per window** per client IP. Exceeding the limit returns `429 Too Many
> Requests`. The limit resets automatically after the window expires.
>
> **Note:** `/health` is an operational endpoint used by the Docker Compose
> healthcheck and any uptime monitor or load balancer. It is also used in
> manual testing to verify container health status.

---

## Project Structure

```
WonderfulMysteriousApp/
├── .github/
│   └── workflows/
│       └── ci.yml                        # CI/CD pipeline (5 jobs)
├── .zap/
│   └── rules.tsv                         # OWASP ZAP scan rule config
├── app/
│   ├── main.py                           # FastAPI application
│   ├── rate_limiter.py                   # RateLimiter class
│   ├── security_headers_middleware.py    # HTTP security headers
│   ├── test_utils.py                     # State reset for tests
│   └── static/
│       └── index.html                    # Interactive landing page
├── tests/
│   ├── conftest.py                       # Unit + integration fixtures (autouse reset)
│   ├── unit/                             # Async handler unit tests
│   ├── integration/                      # TestClient integration tests
│   ├── e2e/
│   │   ├── conftest.py                   # E2E server + client fixtures
│   │   ├── test_e2e_core_flow.py
│   │   ├── test_e2e_health.py
│   │   └── test_e2e_extended.py
│   └── specialized/
│       ├── security/                     # Security header + input tests
│       ├── performance/                  # Locust load tests
│       ├── cross_browser/               # Playwright cross-browser tests
│       └── accessibility/               # axe-core WCAG 2.1 AA tests
├── docker-compose.yml                    # Docker Compose config with healthcheck
├── Dockerfile                            # Multi-stage build (test + runtime)
├── requirements.txt                      # Runtime dependencies
├── requirements-dev.txt                  # Test and dev dependencies
├── CI_Reflection.md                      # CI troubleshooting and lessons learned
├── Common_Production_Issues.md           # Common production risks for this product type
├── E2E_Test_Report.md                    # E2E-specific test results
├── Manual_Testing.md                     # Manual test procedures with reasoning
├── Test_Configuration_Matrix.md          # Device, browser, and OS test matrix
├── Test_Plan.md                          # Test scope, objectives, and coverage
├── Test_Strategy.md                      # Testing philosophy and approach
├── Updated_Test_Report.md               # Full automated test results (all layers)
└── README.md
```

---

## Running Tests

### Install test dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
playwright install chromium firefox
```

### Unit and integration tests

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/unit tests/integration -v
```

### E2E tests (starts a live server automatically via fixture)

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/e2e -v
```

### Specialized — Security (no live server needed)

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/specialized/security/ -v
```

### Specialized — Performance (requires running server on port 8000)

```bash
locust -f tests/specialized/performance/locustfile.py \
  --host http://localhost:8000 \
  --users 10 --spawn-rate 2 --run-time 30s --headless
```

### Specialized — Cross-browser (requires running server on port 8000)

```bash
pytest tests/specialized/cross_browser/ --browser chromium -v
pytest tests/specialized/cross_browser/ --browser firefox -v
```

### Specialized — Accessibility (requires running server on port 8000)

```bash
pytest tests/specialized/accessibility/ --browser chromium -v
```

---

## Test Coverage Summary

| Layer | Tests | What It Covers |
|---|---|---|
| Unit | 15 | Route handlers in isolation |
| Integration | 20 | Full stack via TestClient |
| E2E | 25 | Live Uvicorn subprocess |
| Security | 18+ | Headers, input limits, method validation, ZAP |
| Performance | 1 job | p95 < 200ms under 10 concurrent users |
| Cross-browser | 20 per browser | Chromium and Firefox |
| Accessibility | 5 per browser | WCAG 2.1 AA via axe-core |
| **Total automated** | **~125** | |

Manual testing covers Safari, screen readers, keyboard navigation, colour
contrast of dynamic content, rate limit window reset, OWASP ZAP full active
scan, sustained load, and Docker restart behavior. See `Manual_Testing.md`.

---

## CI/CD Pipeline

The GitHub Actions pipeline runs on every push and pull request with five jobs:

```
build-and-test          Unit + integration tests + Docker build
    │
    ├── e2e-tests                     Live server E2E tests
    ├── security-tests                pip-audit + Bandit + security pytest + ZAP
    ├── performance-tests             Locust (p95 < 200ms enforced)
    └── cross-browser-accessibility   Playwright matrix (Chromium + Firefox)
```

All specialized jobs run in parallel after `build-and-test`. A failure in any
job fails the overall pipeline. Security reports, performance results, and
Playwright failure traces are uploaded as CI artifacts.

---

## Documentation

| Document | Description |
|---|---|
| [Test_Plan.md](Test_Plan.md) | Test scope, objectives, layers, tools, entry/exit criteria |
| [Test_Strategy.md](Test_Strategy.md) | Testing philosophy, automation rationale, Pareto analysis |
| [Manual_Testing.md](Manual_Testing.md) | Manual test procedures with step-by-step instructions and reasoning |
| [Updated_Test_Report.md](Updated_Test_Report.md) | Full automated test results across all layers |
| [E2E_Test_Report.md](E2E_Test_Report.md) | E2E-specific results and validation notes |
| [CI_Reflection.md](CI_Reflection.md) | CI troubleshooting log and testability lessons learned |
| [Common_Production_Issues.md](Common_Production_Issues.md) | Common production risks for this type of product |
| [Test_Configuration_Matrix.md](Test_Configuration_Matrix.md) | Device, browser, OS, and environment test matrix |
