# WonderfulMysteriousApp

A self-contained FastAPI application that exposes several fun and useful endpoints — weather data, insights, fortunes, data submission, and user favorites — all backed by in-memory storage with no external service dependencies.

## Tech Stack

- **Python 3.11**
- **FastAPI** — web framework
- **Uvicorn** — ASGI server
- **Pydantic** — data validation
- **Pytest + pytest-asyncio + httpx** — testing
- **Docker** — containerization

## Project Structure

```
WonderfulMysteriousApp/
│
├── app/
│   ├── main.py
│   ├── rate_limiter.py
│   ├── test_utils.py
│   └── static/
│       └── index.html
│
├── tests/
│   ├── conftest.py              # Unit + integration fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
│       ├── conftest.py          # E2E server + client fixtures
│       ├── test_e2e_core_flow.py
│       ├── test_e2e_health.py
│       └── test_e2e_extended.py
│
├── GoldenPaths.md               # Golden path analysis
├── E2E_Test_Report.md           # E2E test execution summary
├── E2E_Manual_Testing.md        # Manual UI testing beyond automation
└── README.md
```

## API Endpoints

| Method | Endpoint | Input | Description |
| --- | --- | --- | --- |
| GET | `/api/weather` | `city` (string, optional) | Returns mock weather data. Defaults to Seattle |
| GET | `/api/insight` | `topic` (string, optional) | Returns a random insight. Defaults to `general` |
| GET | `/api/fortune` | None | Returns a random fortune |
| POST | `/api/submit` | `{ "user": string, "data": {} }` | Accepts and echoes a structured payload |
| GET | `/api/favorites` | None | Returns the current favorites list |
| POST | `/api/favorites` | `{ "id": integer }` | Adds an integer ID to the favorites list |

> **Note:** The favorites endpoint stores integer IDs only — passing anything other than a whole number will return a `422 Unprocessable Entity` error. These IDs are intended to correspond to the `id` values returned by the `/api/insight` and `/api/fortune` endpoints.
>
> **Note:** `POST /api/submit` validates the request body and returns `201 Created` with the submitted payload echoed back. It does **not** persist data or interact with the favorites list. Input is **not** sanitized — submitted values including special characters are returned as-is.
>
> **Note:** Rate limiting is enforced globally via middleware at **100 requests per window** per client IP. Exceeding the limit returns `429 Too Many Requests`. A graphical frontend is provided at `/` so the API can be used without Swagger.

## Getting Started

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Run with Docker

```bash
# Build the image (runs unit + integration tests during build)
docker build -t wonderfulmysteriousapp .

# Run the container
docker run -p 8000:8000 wonderfulmysteriousapp
```

## Running Tests

```bash
# Run unit and integration tests
pytest tests/unit tests/integration -v

# Run E2E tests (starts a live server automatically)
pytest tests/e2e -v

# Run all tests
pytest tests/ -v
```

The test suite includes unit tests, integration tests (via FastAPI's `TestClient`), and end-to-end tests that run against a live Uvicorn server. Tests cover API correctness, Pydantic validation, rate limiting logic, usability, and negative cases for invalid inputs.

## CI

The GitHub Actions pipeline (`.github/workflows/python_tests.yml`) runs in two sequential jobs on every push:

1. **`build-and-test`** — runs unit and integration tests, then builds the Docker image
2. **`e2e-tests`** — runs after `build-and-test` passes; starts a live server and runs the full E2E suite

A failing test in either job fails the build.

## Documentation

Additional testing documentation is available in the repository:

- [`Test Plan.md`](Test%20Plan.md) — Full testing strategy and scope
- [`Test Strategy.md`](Test%20Strategy.md) — High-level testing approach
- [`GoldenPaths.md`](GoldenPaths.md) — Most valuable end-to-end scenarios
- [`E2E_Manual_Testing.md`](E2E_Manual_Testing.md) — Manual UI testing beyond automation
- [`E2E_Test_Report.md`](E2E_Test_Report.md) — E2E test validation report
- [`Updated Test Report.md`](Updated%20Test%20Report.md) — Latest overall test results
