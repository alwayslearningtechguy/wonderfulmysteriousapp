# Specialized Manual Testing — Wonderful Mysterious App

This document covers manual testing that complements the automated specialized
test suite. These checks are required because they involve real browsers, screen
readers, physical devices, time-dependent behaviour, or conditions that are
impractical to automate reliably in CI.

---

## 1. Safari Cross-Browser Testing (macOS Required)

**Why manual:** Safari (WebKit) is not available on Linux GitHub Actions runners
without paid cloud services. Playwright's Safari support requires macOS.

### 1.1 Desktop Safari (macOS)

**Prerequisites:** macOS with Safari 16+

**Steps:**
1. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Open `http://localhost:8000` in Safari
3. Open DevTools (Develop menu → Show Web Inspector)
4. Check the Console tab — confirm no JavaScript errors on load
5. Expand each API card and click its button — confirm responses render
6. Check the Network tab — confirm all fetch calls return 200
7. Resize the window to <720px — confirm single-column layout activates
8. Check that buttons are clearly visible and clickable at all sizes

**Pass criteria:** No JS errors, all cards interactive, layout responsive

### 1.2 iOS Safari (iPhone)

**Prerequisites:** iPhone or iPad with iOS 16+, on the same network as the
host machine running the app.

**Note:** The app binds to `0.0.0.0` so it is reachable from devices on the
same network via the host machine's local IP (e.g. `http://192.168.1.x:8000`).

**Steps:**
1. Find your machine's local IP: `ipconfig getifaddr en0` (macOS)
2. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. On iPhone, navigate to `http://<your-ip>:8000`
4. Verify the page loads and is readable without horizontal scrolling
5. Tap each card to expand it — confirm touch targets are large enough
6. Submit a request from each card — confirm responses display

**Pass criteria:** Page loads, no horizontal scroll, all cards usable by touch

---

## 2. Screen Reader Testing

**Why manual:** Automated tools like axe-core detect structural issues (missing
labels, invalid ARIA) but cannot verify what is actually *announced* by a
screen reader or whether the announcement is meaningful.

### 2.1 NVDA + Chrome (Windows)

**Prerequisites:** NVDA (free, https://www.nvaccess.org), Chrome on Windows

**Steps:**
1. Start NVDA. Open Chrome. Navigate to `http://localhost:8000`
2. Press H to navigate by headings — confirm the page structure is logical
3. Press F to navigate by form fields — confirm each input is announced with its label
4. Press B to navigate by buttons — confirm each button has a meaningful name
5. Tab through the page — confirm focus order is logical (top to bottom, left to right)
6. Activate the Weather card's Send button with Enter or Space
7. Confirm NVDA announces the response when it appears (live region or focus move)

**Pass criteria:** All headings, labels, and buttons announced meaningfully;
response content reachable by keyboard after submission.

### 2.2 VoiceOver + Safari (macOS)

**Prerequisites:** macOS (VoiceOver is built-in — Cmd+F5 to activate)

**Steps:**
1. Activate VoiceOver (Cmd+F5). Open Safari. Navigate to `http://localhost:8000`
2. Use VO+Right to read through the page — confirm all content is read
3. Use VO+U to open the Rotor — check Headings, Links, and Form Controls
4. Tab to each button — confirm VoiceOver announces a meaningful name
5. Submit a GET request — confirm the response is reachable and readable

**Pass criteria:** Same as NVDA test above.

---

## 3. Keyboard-Only Navigation

**Why manual:** Playwright can detect focus traps but cannot verify the full
keyboard navigation experience end-to-end.

**Steps:**
1. Open `http://localhost:8000` in Chrome or Firefox
2. Do not touch the mouse for the entire test
3. Press Tab to move forward through all interactive elements
4. Press Shift+Tab to move backward — confirm focus moves in reverse
5. Confirm focus is always visible (highlighted outline) on every element
6. Press Enter or Space on each button — confirm it fires
7. Confirm there are no focus traps (places where Tab does not move forward)
8. Press Escape after opening any expanded card — confirm it closes if applicable

**Pass criteria:** All interactive elements reachable and operable by keyboard;
focus always visible; no traps.

---

## 4. Colour Contrast and Visual Accessibility

**Why manual:** axe-core checks contrast for static content. Dynamic content
(response containers populated by JavaScript) is checked after rendering.

**Steps:**
1. Open `http://localhost:8000` in Chrome DevTools
2. Open the Rendering panel (More tools → Rendering)
3. Enable "Emulate vision deficiencies: Deuteranopia" (red-green colour blindness)
4. Verify all text, buttons, and UI elements are still distinguishable
5. Repeat for "Achromatopsia" (no colour vision)
6. Fire a request and verify the response text in the response container is readable
7. Enable "Force dark mode" in Rendering — verify the page does not become unreadable

**Steps for contrast check:**
1. Install the axe DevTools browser extension (free tier)
2. Navigate to `http://localhost:8000`
3. Open axe DevTools and run a full scan
4. Inspect any contrast violations in the response containers (dynamically added content)

**Pass criteria:** All text readable under colour blindness simulation; no
contrast failures in dynamic content.

---

## 5. Rate Limit Window Reset (Real Wall-Clock)

**Why manual:** The automated tests confirm that the 101st request returns 429.
They do not wait for the 10-second window to expire and confirm recovery.

**Steps:**
1. Start the app fresh: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Send 100 requests rapidly:
   ```bash
   for i in $(seq 1 100); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/weather; done
   ```
3. Confirm all return 200
4. Send one more: `curl -s http://localhost:8000/api/weather`
5. Confirm it returns 429 with `{"detail": "Too Many Requests"}`
6. Wait 10 seconds
7. Send another: `curl -s http://localhost:8000/api/weather`
8. Confirm it returns 200

**Pass criteria:** 429 after 100 requests; 200 again after window expires.

---

## 6. OWASP ZAP Full Active Scan

**Why manual:** The CI pipeline runs ZAP in passive (baseline) mode which does
not send attack payloads. A full active scan should be run manually before major
releases.

**Prerequisites:** Docker, ZAP installed or use Docker image

**Steps:**
1. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Run ZAP full scan:
   ```bash
   docker run --network host \
     -v $(pwd):/zap/wrk/:rw \
     ghcr.io/zaproxy/zaproxy:stable \
     zap-full-scan.py \
     -t http://localhost:8000 \
     -r zap-full-report.html
   ```
3. Review `zap-full-report.html` for High and Medium alerts
4. Investigate and remediate any High severity findings before release

**Pass criteria:** No High severity findings; Medium findings documented and
accepted or remediated.

---

## 7. Performance Under Sustained Load

**Why manual/monitored:** The CI Locust run uses 10 users for 30 seconds —
enough to enforce the p95 target but not enough to detect memory leaks or
degradation over time.

**Steps:**
1. Start the app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. In a separate terminal, monitor memory:
   ```bash
   watch -n 2 'ps aux | grep uvicorn | grep -v grep'
   ```
3. Run a longer Locust test:
   ```bash
   locust -f tests/specialized/performance/locustfile.py \
     --host http://localhost:8000 \
     --users 50 --spawn-rate 5 --run-time 300s --headless \
     --html=results/sustained_load_report.html
   ```
4. Monitor memory usage throughout — look for consistent growth
5. After the test, check the HTML report for latency trends over time

**Pass criteria:** Memory usage stable (not consistently growing); p95 < 200ms
maintained throughout the test run; no 500 errors.

---

## 8. Docker Container Restart Behaviour

**Why manual:** Requires Docker stop/start which is not practical in the
automated E2E test suite against a subprocess-managed server.

**Steps:**
1. Build and start the container:
   ```bash
   docker build -t wonderfulapp .
   docker run -d -p 8000:8000 --name wma wonderfulapp
   ```
2. Add favorites:
   ```bash
   curl -X POST http://localhost:8000/api/favorites -H "Content-Type: application/json" -d '{"id": 9999}'
   curl http://localhost:8000/api/favorites
   ```
3. Confirm 9999 is in the list
4. Restart the container:
   ```bash
   docker stop wma && docker rm wma
   docker run -d -p 8000:8000 --name wma wonderfulapp
   ```
5. Check favorites again:
   ```bash
   curl http://localhost:8000/api/favorites
   ```
6. Confirm the list is empty

**Pass criteria:** Favorites list is empty after container restart (documented
in-memory behaviour).

---

## 9. Health Check Endpoint (Operational Verification)

**Steps:**
1. Start the app
2. `curl -f http://localhost:8000/health`
3. Confirm response: `{"status": "ok"}` with HTTP 200
4. Build and run Docker image: `docker run -d -p 8000:8000 wonderfulapp`
5. Check Docker health status after 30 seconds:
   ```bash
   docker inspect --format='{{.State.Health.Status}}' <container_id>
   ```
6. Confirm status is `healthy`

**Pass criteria:** `/health` returns 200; Docker reports container as healthy.

---

## Summary

| Area | Tool | Automated | Manual |
|---|---|---|---|
| Security headers | pytest + TestClient | ✅ | — |
| Dependency vulnerabilities | pip-audit | ✅ | — |
| Static analysis | Bandit | ✅ | — |
| OWASP ZAP passive scan | ZAP baseline action | ✅ | — |
| OWASP ZAP full active scan | ZAP | — | ✅ Section 6 |
| Performance p95 < 200ms | Locust (10 users, 30s) | ✅ | — |
| Sustained load / memory leak | Locust (50 users, 5min) | — | ✅ Section 7 |
| Cross-browser — Chromium | Playwright | ✅ | — |
| Cross-browser — Firefox | Playwright | ✅ | — |
| Cross-browser — Safari desktop | Playwright (macOS) | — | ✅ Section 1.1 |
| Cross-browser — Safari iOS | Manual | — | ✅ Section 1.2 |
| Accessibility — axe-core | axe-playwright | ✅ | — |
| Accessibility — screen reader | NVDA / VoiceOver | — | ✅ Section 2 |
| Accessibility — keyboard nav | Manual | — | ✅ Section 3 |
| Accessibility — colour contrast (dynamic) | Manual + axe ext | — | ✅ Section 4 |
| Rate limit window reset | Manual | — | ✅ Section 5 |
| Docker restart / state reset | Manual | — | ✅ Section 8 |
| Health check operational | Manual | — | ✅ Section 9 |
