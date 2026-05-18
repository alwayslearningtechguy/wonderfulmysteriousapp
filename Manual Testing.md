# Manual Testing Requirements

This document lists the manual tests that I should also run in addition to the automated unit and integration tests. These checks validate real runtime behavior that should help confirm everything is running right.

---

## 1. Deployment & Runtime Verification

### 1.1 Docker Build
- Build the image using `docker build`.
- Confirm the image builds without errors.

### 1.2 Container Startup
- Run the container.
- Verify the app starts cleanly with no stack traces.
- Confirm Uvicorn reports successful startup.

### 1.3 Endpoint Reachability
Manually visit or curl:
- `/api/weather`
- `/api/insight`
- `/api/fortune`
- `/api/submit`
- `/api/favorites` (GET + POST)

Each should return valid JSON and the correct status code.

---

## 2. Manual Rate Limiting Checks

### 2.1 Enforcement
- Send 100 quick requests to any endpoint → expect `200`.
- Send an 101st request → expect `429`.

### 2.2 Reset Behavior
- Hit the limit.
- Wait for the rate‑limit window to expire.
- Send another request → expect `200`.

---

## 3. Manual Input & Error Handling

### 3.1 Script Injection Attempt
POST a payload containing `<script>` tags to `/api/submit`.  
Expect:
- `201` response
- No script execution
- No internal error output

### 3.2 Malformed JSON
Send invalid JSON.  
Expect:
- `422 Unprocessable Entity`

### 3.3 Unexpected Parameters
Add extra query parameters to endpoints.  
Expect:
- API ignores unknown parameters
- Response remains valid

---

## 4. Stateful Behavior

### 4.1 Favorites During Runtime
- Add multiple favorites.
- Retrieve favorites list.
- Confirm values persist during the session.

### 4.2 Reset on Restart
- Add favorites.
- Restart the container.
- Confirm favorites list resets (in‑memory only).

---

## Summary
These manual tests complement the automated suite by validating deployment behavior, runtime stability, rate limiting in real conditions, and state behavior across container restarts.
