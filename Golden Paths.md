# Golden Paths Analysis — Wonderful Mysterious App

This document identifies the most valuable end-to-end scenarios in the Wonderful
Mysterious App. These represent the core user journeys that must always work, and
are the primary basis for the automated E2E test suite.

---

## What Makes a Golden Path?

A Golden Path is a scenario where:

- It is the primary reason a user interacts with the app
- A failure in it would be immediately visible and impactful
- It exercises multiple layers of the system (HTTP request → middleware → route handler → response)
- It gates or enables other features (e.g. rate limiting affects every endpoint)

---

## 1. Core API Health (Smoke Test Golden Path)

**Priority: Critical**

### Steps

1. `GET /api/weather` — expect 200 with a JSON dict containing `city`, `temp_f`, `condition`, and other weather fields
2. `GET /api/insight` — expect 200 with a JSON dict containing `insight`, `topic`, and `available_topics`
3. `GET /api/fortune` — expect 200 with a JSON dict containing `fortune`, `lucky_number`, `lucky_color`, and `advice`

### Why It Matters

If any of these three read-only endpoints fail, the app feels entirely broken.
They are the most frequently called endpoints and the first thing any consumer
would test. All three are covered by `test_e2e_health.py` via a parametrized
health check.

---

## 2. Daily Mystery Experience (Primary Golden Path)

**Priority: Critical**

### Steps

1. User requests weather via `GET /api/weather` (optionally with a `?city=` param)
2. User requests an insight via `GET /api/insight` (optionally with a `?topic=` param)
3. User requests a fortune via `GET /api/fortune`
4. User submits the combined result via `POST /api/submit` with a `user` string and a `data` object
5. User saves the `id` from the fortune or insight response as a favorite via `POST /api/favorites` with `{"id": <integer>}`
6. User views the updated favorites list via `GET /api/favorites`

### Why It Matters

This path exercises all six API endpoints in a realistic sequence. It validates
the in-memory favorites store, Pydantic request validation on both POST endpoints,
and the full request-response cycle end-to-end. It is covered by
`test_e2e_core_flow.py`.

**Important notes:**
- `POST /api/submit` echoes the payload back and returns `201 Created` — it does **not** persist data or write to favorites
- `POST /api/favorites` accepts only an integer `id` — it does not accept composite objects
- Favorites are stored in-memory and reset on container restart

---

## 3. Data Submission Path

**Priority: High**

### Steps

1. `POST /api/submit` with a valid JSON body: `{"user": "string", "data": {}}`
2. Verify the response is `201 Created` with `"status": "Created"` and `"received"` echoing the payload
3. `POST /api/submit` with a missing `user` or `data` field — expect `422 Unprocessable Entity`

### Why It Matters

Submit is the only POST endpoint with strict Pydantic schema validation on the
request body. It protects against schema drift and ensures the API correctly
rejects malformed input. Note: the API does **not** sanitize input — script tags
and special characters are accepted and echoed back unchanged.

---

## 4. Favorites Add and Retrieve

**Priority: High**

### Steps

1. `GET /api/favorites` — confirm the list is returned (may be empty or populated depending on session state)
2. `POST /api/favorites` with `{"id": <integer>}` — expect `201 Created` with `"message": "Saved"`
3. `GET /api/favorites` again — confirm the posted `id` appears in the list
4. `POST /api/favorites` with a non-integer `id` — expect `422 Unprocessable Entity`

### Why It Matters

Favorites is the only stateful flow in the application. It is the only endpoint
that persists data across multiple requests within a session. Testing the
POST → GET read-back cycle confirms the in-memory store is working correctly.

---

## 5. Rate Limiting Enforcement

**Priority: High**

### Steps

1. Send 100 requests to any endpoint from the same IP — all should return `200`. This must be done in a small window of time (10 seconds - Good luck clicking)
2. Send the 101st request — expect `429 Too Many Requests` with `{"detail": "Too Many Requests"}`
3. Wait for the rate limit window to expire — confirm requests return `200` again

### Why It Matters

Rate limiting is global middleware that gates every single endpoint. If it breaks
in either direction — too permissive (never blocks) or too aggressive (blocks
legitimate traffic) — the entire API is affected. 

---

## 6. UI Fetch Flow (Manual Golden Path)

**Priority: Medium — requires manual testing**

### Steps

1. Load `/` in a browser — confirm the landing page renders with all six API cards
2. Expand the Weather card, enter a city, click "Send GET Request" — verify the response renders in the page
3. Expand the Insight card, enter a topic, click "Send GET Request" — verify the response renders
4. Expand the Fortune card, click "Send GET Request" — verify the response renders
5. Expand the Submit card, fill in user and score, click "Send POST Request" — verify `201 Created` renders
6. Expand the Favorites (POST) card, enter an ID, click "Send POST Request" — verify `201 Created` renders
7. Click the "Open /api/favorites" link — verify the saved ID appears in the list

### Why It Matters

The landing page (`index.html`) provides an interactive frontend for the API.
Browser JavaScript execution and DOM rendering are not covered by automated tests
and must be validated manually.

---

## Summary Matrix

| Golden Path | Priority | Automated? | Test File |
|---|---|---|---|
| Core API Health | Critical | Yes | `test_e2e_health.py` |
| Daily Mystery Experience | Critical | Partial | `test_e2e_core_flow.py` |
| Data Submission | High | Via integration tests | `test_submit_integration.py` |
| Favorites Add and Retrieve | High | Via integration tests | `test_favorites_integration.py` |
| Rate Limiting Enforcement | High | Via unit tests | `test_rate_limiter_unit.py` |
| UI Fetch Flow | Medium | No — manual only | `E2E_Manual_Testing.md` |
