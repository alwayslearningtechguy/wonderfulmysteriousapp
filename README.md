# WonderfulMysteriousApp

A self-contained FastAPI application that exposes several fun and useful endpoints — weather data, insights, fortunes, data submission, and user favorites — all backed by in-memory storage with no substantial external service dependencies.

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
│   └── ...
│
├── tests/
│   ├── conftest.py              # Unit + integration fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
│       ├── conftest.py          # E2E server + client fixtures
│       ├── test_e2e_core_flow.py
│       └── test_e2e_health.py
│
├── GoldenPaths.md               # Golden path analysis
├── E2E_Test_Report.md           # E2E test execution summary
├── Manual_Testing.md            # General manual testing
├── E2E_Manual_Testing.md        # Manual UI testing beyond automation
└── README.md
```

## API Endpoints

| Method | Endpoint | Input | Description |
|--------|----------|-------|-------------|
| GET | `/api/weather` | `city` (string, optional) | Returns mock weather data. Defaults to Seattle |
| GET | `/api/insight` | `topic` (string, optional) | Returns a random insight. Defaults to "general" |
| GET | `/api/fortune` | None | Returns a random fortune |
| POST | `/api/submit` | `{ "user": string, "data": {} }` | Accepts a structured payload |
| GET | `/api/favorites` | None | Returns the current favorites list |
| POST | `/api/favorites` | `{ "id": integer }` | Adds an integer ID to the favorites list |

> **Note:** The favorites endpoint stores integer IDs only — passing anything other than a whole number will return a `422 Unprocessable Entity` error. These IDs are intended to correspond to the `id` values returned by the `/api/insight` and `/api/fortune` endpoints.

> Rate limiting is enforced globally via middleware. Exceeding the limit returns `429 Too Many Requests`. In the latest build, a graphical front end is provided so that users can use this web app without requiring the use of swagger.

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
# Build the image
docker build -t wonderfulmysteriousapp .

# Run the container
docker run -p 8000:8000 wonderfulmysteriousapp
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v
```

The test suite includes unit tests, integration tests (via FastAPI's `TestClient`), security tests (input sanitization, rate limiting), usability, and negative tests for invalid inputs.

## CI

The GitHub Actions pipeline automatically runs the full test suite on every push. A failing test fails the build. This functionality has also been integrated with the dockerfile.

## Documentation

Additional testing documentation is available in the repository:

- [`Test Plan.md`](./Test%20Plan.md) — Full testing strategy and scope
- [`Test Strategy.md`](./Test%20Strategy.md) — High-level testing approach
- [`Manual_Testing.md`](./Manual_Testing.md) — Manual test cases
- ['E2E_Manual_Testing.md'](./E2E_Manual_Testing.md) - E2E manual testing
- [`Updated Test Report.md`](./Updated%20Test%20Report.md) — Latest test results
- ['E2E Test Report.md](./E2E%20Test%20Report.md) - Latest test report of the automated E2E tests
- ['Golden Paths.md'](./GoldenPaths.md) - Golden Paths Scenarios

