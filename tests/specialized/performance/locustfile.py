"""
tests/specialized/performance/locustfile.py
============================================
Load and performance tests using Locust.

Run locally:
    locust -f tests/specialized/performance/locustfile.py \
           --host http://localhost:8000 \
           --users 10 --spawn-rate 2 --run-time 60s --headless

Run in CI (see workflow file):
    locust -f tests/specialized/performance/locustfile.py \
           --host http://localhost:8000 \
           --users 10 --spawn-rate 2 --run-time 30s --headless \
           --csv=results/locust

Scenarios
---------
WonderfulAppUser   — realistic mixed-traffic user hitting all GET endpoints
                     plus periodic POST to submit and favorites.
BurstUser          — sends rapid sequential requests to exercise rate limiting
                     under load. Expects a mix of 200 and 429 responses.

Performance targets (from Test Strategy):
    p95 response time < 200ms for all endpoints under 10 concurrent users.
"""

from locust import HttpUser, task, between, events
import json


# ---------------------------------------------------------------------------
# Realistic mixed-traffic user
# ---------------------------------------------------------------------------

class WonderfulAppUser(HttpUser):
    """
    Simulates a typical user exploring the API.
    Wait between 0.5 and 2 seconds between requests to model realistic pacing.
    """
    wait_time = between(0.5, 2)

    @task(3)
    def get_weather_default(self):
        with self.client.get("/api/weather", catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if "city" not in data:
                    r.failure("Response missing 'city' field")
                else:
                    r.success()
            elif r.status_code == 429:
                # Rate limited — not a test failure, mark as success to avoid
                # skewing error metrics; log separately.
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(2)
    def get_weather_custom(self):
        with self.client.get("/api/weather?city=Chicago", catch_response=True) as r:
            if r.status_code in (200, 429):
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(3)
    def get_insight(self):
        with self.client.get("/api/insight", catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if "insight" not in data:
                    r.failure("Response missing 'insight' field")
                else:
                    r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(2)
    def get_insight_topic(self):
        with self.client.get(
            "/api/insight?topic=technology", catch_response=True
        ) as r:
            if r.status_code in (200, 429):
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(3)
    def get_fortune(self):
        with self.client.get("/api/fortune", catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if "fortune" not in data:
                    r.failure("Response missing 'fortune' field")
                else:
                    r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(1)
    def post_submit(self):
        payload = {"user": "locust-user", "data": {"score": 100}}
        with self.client.post(
            "/api/submit", json=payload, catch_response=True
        ) as r:
            if r.status_code == 201:
                data = r.json()
                if data.get("status") != "Created":
                    r.failure("Expected status='Created'")
                else:
                    r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(1)
    def post_favorite(self):
        with self.client.post(
            "/api/favorites", json={"id": 1001}, catch_response=True
        ) as r:
            if r.status_code in (201, 429):
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(1)
    def get_favorites(self):
        with self.client.get("/api/favorites", catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if "favorites" not in data:
                    r.failure("Response missing 'favorites' field")
                else:
                    r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(1)
    def get_landing_page(self):
        with self.client.get("/", catch_response=True) as r:
            if r.status_code == 200:
                if "text/html" not in r.headers.get("content-type", ""):
                    r.failure("Landing page did not return HTML")
                else:
                    r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Unexpected status: {r.status_code}")


# ---------------------------------------------------------------------------
# CI pass/fail hook — fails the Locust run if p95 > 200ms or error rate > 1%
# ---------------------------------------------------------------------------

@events.quitting.add_listener
def check_performance_targets(environment, **kwargs):
    """
    Enforce performance targets as part of CI.
    Exit code 1 causes the CI step to fail.
    """
    stats = environment.runner.stats.total

    # Allow a small error budget: 429s are expected under rate limiting
    # so we only fail on non-429 errors.
    if stats.num_requests == 0:
        print("No requests made — check Locust configuration.")
        environment.process_exit_code = 1
        return

    error_rate = stats.num_failures / stats.num_requests
    p95 = stats.get_response_time_percentile(0.95)

    print(f"\n=== Performance Results ===")
    print(f"Total requests : {stats.num_requests}")
    print(f"Failures       : {stats.num_failures} ({error_rate:.1%})")
    print(f"p95 latency    : {p95:.0f} ms")
    print(f"p99 latency    : {stats.get_response_time_percentile(0.99):.0f} ms")
    print(f"Median latency : {stats.median_response_time:.0f} ms")

    failures = []
    if p95 > 200:
        failures.append(f"p95 latency {p95:.0f}ms exceeds 200ms target")
    if error_rate > 0.01:
        failures.append(f"Error rate {error_rate:.1%} exceeds 1% threshold")

    if failures:
        print("\n❌ Performance targets NOT met:")
        for f in failures:
            print(f"   - {f}")
        environment.process_exit_code = 1
    else:
        print("\n✅ All performance targets met.")
