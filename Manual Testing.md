# Manual Testing Guide — Wonderful Mysterious App v3.1

This document covers all manual testing required for the *Wonderful and
Mysterious API*. It consolidates the original `Manual_Testing.md` and the
specialized manual testing procedures added during the current release cycle.

Automated tests cover API correctness, integration behavior, core E2E flows,
security headers, dependency vulnerabilities, performance baselines,
cross-browser layout, and WCAG 2.1 AA structural accessibility. The tests
below address what automation cannot: UI rendering, real browser behavior,
screen reader quality, Docker runtime conditions, and time-dependent states.

---

## Testing Environment

All manual UI testing for desktop browsers was performed on Chrome and Firefox
on Windows/macOS. The application runs inside a Docker container and is
accessed via `http://localhost:8000`.

Because the app is not deployed to a public network, mobile and tablet devices
cannot access the local Docker container without additional networking
configuration (see Section 2.2 for steps). Mobile and tablet testing in a
standard local setup were therefore not performed.

---

## 1. UI Rendering and Core Behavior

### Steps

1. Start the app via Docker.
2. Navigate to `http://localhost:8000` in a desktop browser.
3. Expand the **Weather** card, enter a city (e.g. "Chicago"), and click
   **Send GET Request**. Verify weather JSON renders in the response container.
4. Expand the **Insight** card, enter a topic (e.g. "technology"), and click
   **Send GET Request**. Verify insight JSON renders.
5. Expand the **Fortune** card and click **Send GET Request**. Verify fortune
   JSON renders.
6. Expand the **Submit** card, enter a username and score, and click
   **Send POST Request**. Verify `201 Created` and echoed payload appear.
7. Expand the **Favorites (POST)** card, enter an integer ID, and click
   **Send POST Request**. Verify `201 Created` and `"message": "Saved"` appear.
8. Click the **Open /api/favorites** link in the Favorites (GET) card.
   Verify the saved ID appears in the list.
9. Refresh the page and confirm it reloads correctly. Note: favorites persist
   in-memory for the life of the container — they do not reset on page refresh,
   only on container restart.

### Why Manual

DOM rendering and JavaScript execution are not covered by automated tests.
Ensures all six interactive forms work correctly and that frontend-to-backend
integration produces visible results in the UI.

---

## 2. Cross-Browser Testing

### 2.1 Desktop Browsers (Chrome and Firefox)

**Automated:** Chromium and Firefox are covered by the Playwright cross-browser
test suite in CI. Manual verification below confirms visual fidelity beyond
what automated tests assert.

**Browsers to test manually:** Chrome (latest), Firefox (latest), and
Safari (see Section 2.2).

**Checks:**
- Page loads without console errors
- All six API cards are visible and expandable
- Buttons trigger fetch calls that update the response containers
- No layout issues at standard desktop widths

### 2.2 Safari — Desktop (macOS Required)

**Prerequisites:** macOS with Safari 16+

**Steps:**
1. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Open `http://localhost:8000` in Safari
3. Open DevTools (Develop menu → Show Web Inspector). Check Console for errors.
4. Expand each API card and click its button. Confirm responses render.
5. Resize the window to below 720px. Confirm single-column layout activates.

**Pass criteria:** No JS errors, all cards interactive, layout responsive.

### 2.3 Safari — iOS (iPhone/iPad)

**Prerequisites:** iPhone or iPad on the same network as the host machine.

**Steps:**
1. Find your machine's local IP: `ipconfig getifaddr en0` (macOS)
2. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. On iPhone, navigate to `http://<your-ip>:8000`
4. Verify the page loads without horizontal scrolling
5. Tap each card to expand it. Confirm touch targets are large enough.
6. Submit a request from each card. Confirm responses display.

**Pass criteria:** Page loads, no horizontal scroll, all cards usable by touch.

---

## 3. Screen Reader Testing

Automated axe-core scans detect structural issues (missing labels, invalid ARIA).
Manual screen reader testing verifies what is actually *announced* and whether
announcements are meaningful.

### 3.1 NVDA + Chrome (Windows)

**Prerequisites:** NVDA (free, https://www.nvaccess.org), Chrome on Windows

**Steps:**
1. Start NVDA. Open Chrome. Navigate to `http://localhost:8000`
2. Press H to navigate by headings. Confirm the structure is logical.
3. Press F to navigate by form fields. Confirm each input is announced with
   its label.
4. Press B to navigate by buttons. Confirm each button has a meaningful name.
5. Tab through the page. Confirm focus order is logical (top to bottom).
6. Activate the Weather card's Send button with Enter or Space.
7. Confirm NVDA announces the response when it appears.

**Pass criteria:** All headings, labels, and buttons announced meaningfully;
response content reachable by keyboard after submission.

### 3.2 VoiceOver + Safari (macOS)

**Prerequisites:** macOS (VoiceOver built-in — Cmd+F5 to activate)

**Steps:**
1. Activate VoiceOver (Cmd+F5). Open Safari. Navigate to `http://localhost:8000`
2. Use VO+Right to read through the page. Confirm all content is read.
3. Use VO+U to open the Rotor. Check Headings, Links, and Form Controls.
4. Tab to each button. Confirm VoiceOver announces a meaningful name.
5. Submit a GET request. Confirm the response is reachable and readable.

**Pass criteria:** Same as NVDA test above.

---

## 4. Keyboard-Only Navigation

**Steps:**
1. Open `http://localhost:8000` in Chrome or Firefox. Do not touch the mouse.
2. Press Tab to move forward through all interactive elements.
3. Press Shift+Tab to move backward. Confirm focus moves in reverse.
4. Confirm focus is always visible (highlighted outline) on every element.
5. Press Enter or Space on each button. Confirm it fires.
6. Confirm there are no focus traps.

**Pass criteria:** All interactive elements reachable and operable by keyboard;
focus always visible; no traps.

---

## 5. Visual Layout and Responsive Breakpoints

**Steps:**
1. Open `http://localhost:8000` in Chrome DevTools.
2. Resize to each breakpoint: 320px, 480px, 768px, 1024px, 1440px.
3. Confirm:
   - Content is readable at all widths
   - Buttons do not overlap or become inaccessible
   - No horizontal scrolling at typical desktop widths
   - At ≤720px the layout switches to a single-column grid
4. Enable "Emulate vision deficiencies: Deuteranopia" in the Rendering panel.
   Verify all text, buttons, and UI elements are still distinguishable.
5. Repeat for "Achromatopsia".
6. Enable "Force dark mode". Verify the page does not become unreadable.

**Why manual:** Visual layout, responsive breakpoints, and colour blindness
rendering are not fully asserted in automated tests.

---

## 6. Rate Limit Window Reset

**Why manual:** Automated tests confirm the 101st request returns 429. They
do not wait for the window to expire and confirm recovery.

**Steps:**
1. Start the app fresh.
2. Send 100 rapid requests:
   ```bash
   for i in $(seq 1 100); do
     curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/weather
   done
   ```
3. Confirm all return 200.
4. Send one more: `curl -s http://localhost:8000/api/weather`
5. Confirm it returns 429 with `{"detail": "Too Many Requests"}`.
6. Wait 10 seconds.
7. Send another: `curl -s http://localhost:8000/api/weather`
8. Confirm it returns 200.

**Pass criteria:** 429 after 100 requests; 200 again after window expires.

---

## 7. Error Handling and Edge Cases

**Steps:**
1. Submit malformed JSON to `/api/submit`:
   ```bash
   curl -X POST http://localhost:8000/api/submit \
     -H "Content-Type: application/json" \
     -d '{bad json'
   ```
   Confirm `422 Unprocessable Entity`.

2. Submit a valid payload with `<script>` tags:
   ```bash
   curl -X POST http://localhost:8000/api/submit \
     -H "Content-Type: application/json" \
     -d '{"user": "<script>alert(1)</script>", "data": {"x": 1}}'
   ```
   Confirm the tags are **echoed back unchanged** in the `"received"` field.
   The API does **not** sanitize input — this is intentional behavior.

3. Call `/api/weather` with a very long city name. Confirm no 500 error and
   the name is returned title-cased.

4. Call `/api/insight` with an unknown topic (e.g. `?topic=finance`). Confirm
   the response falls back to `"topic": "general"` with a 200 status.

---

## 8. OWASP ZAP Full Active Scan

**Why manual:** CI runs ZAP in passive (baseline) mode only. A full active
scan sends attack payloads and should be run manually before major releases.

**Steps:**
1. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Run the full scan:
   ```bash
   docker run --network host \
     -v $(pwd):/zap/wrk/:rw \
     ghcr.io/zaproxy/zaproxy:stable \
     zap-full-scan.py \
     -t http://localhost:8000 \
     -r zap-full-report.html
   ```
3. Review `zap-full-report.html` for High and Medium alerts.
4. Investigate and remediate any High severity findings before release.

**Pass criteria:** No High severity findings.

---

## 9. Performance Under Sustained Load

**Why manual:** The CI Locust run uses 10 users for 30 seconds. Longer runs
are needed to detect memory leaks or degradation over time.

**Steps:**
1. Start the app. In a separate terminal, monitor memory:
   ```bash
   watch -n 2 'ps aux | grep uvicorn | grep -v grep'
   ```
2. Run a sustained Locust test:
   ```bash
   locust -f tests/specialized/performance/locustfile.py \
     --host http://localhost:8000 \
     --users 50 --spawn-rate 5 --run-time 300s --headless \
     --html=results/sustained_load_report.html
   ```
3. Monitor memory throughout. Look for consistent growth.
4. After the test, check the HTML report for latency trends over time.

**Pass criteria:** Memory usage stable; p95 < 200ms maintained throughout;
no 500 errors.

---

## 10. Docker Container Restart Behavior

**Steps:**
1. Build and start the container:
   ```bash
   docker build -t wonderfulapp .
   docker run -d -p 8000:8000 --name wma wonderfulapp
   ```
2. Add a favorite:
   ```bash
   curl -X POST http://localhost:8000/api/favorites \
     -H "Content-Type: application/json" -d '{"id": 9999}'
   curl http://localhost:8000/api/favorites
   ```
3. Confirm 9999 is in the list.
4. Restart the container:
   ```bash
   docker stop wma && docker rm wma
   docker run -d -p 8000:8000 --name wma wonderfulapp
   ```
5. Check favorites: `curl http://localhost:8000/api/favorites`
6. Confirm the list is empty.

**Pass criteria:** Favorites list is empty after container restart.

---

## 11. Health Check Endpoint

**Why manual:** Confirms the `/health` endpoint works correctly and that
Docker reports the container as healthy using the Python-based healthcheck.
`python:3.11-slim` does not include `curl`, so the healthcheck uses Python's
built-in `urllib.request` instead — no additional dependencies required.

### Steps

1. Verify the endpoint directly:
```bash
   curl -f http://localhost:8000/health
```
   Confirm response: `{"status": "ok"}` with HTTP 200.

2. Start via Docker Compose:
```bash
   docker compose up --build -d
```

3. Wait 30 seconds, then check status:
```bash
   docker inspect --format='{{.State.Health.Status}}' wonderful_mysterious_app
```
   Confirm status is `healthy`.

4. Verify the healthcheck command works inside the container:
```bash
   docker exec wonderful_mysterious_app \
     python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```
   Confirm it exits without error.

**Pass criteria:** `/health` returns 200; Docker reports container as `healthy`;
Python urllib healthcheck exits cleanly.

---

## Summary

| Area | Automated | Manual |
|---|---|---|
| UI rendering and interaction | — | ✅ Section 1 |
| Cross-browser — Chromium | ✅ Playwright CI | — |
| Cross-browser — Firefox | ✅ Playwright CI | — |
| Cross-browser — Safari desktop | — | ✅ Section 2.2 |
| Cross-browser — Safari iOS | — | ✅ Section 2.3 |
| Screen reader (NVDA, VoiceOver) | — | ✅ Section 3 |
| Keyboard navigation | — | ✅ Section 4 |
| Responsive layout / colour blindness | Partial (Playwright viewport) | ✅ Section 5 |
| Rate limit window reset | — | ✅ Section 6 |
| Error handling edge cases | Partial (security tests) | ✅ Section 7 |
| OWASP ZAP full active scan | — | ✅ Section 8 |
| Sustained load / memory leak | — | ✅ Section 9 |
| Docker restart / state reset | — | ✅ Section 10 |
| Health check endpoint | — | ✅ Section 11 |
| Security headers | ✅ Security test suite | — |
| Dependency vulnerabilities | ✅ pip-audit CI | — |
| Static analysis | ✅ Bandit CI | — |
| OWASP ZAP passive scan | ✅ ZAP baseline CI | — |
| Performance p95 < 200ms | ✅ Locust CI | — |
| Accessibility WCAG 2.1 AA | ✅ axe-core CI | — |
