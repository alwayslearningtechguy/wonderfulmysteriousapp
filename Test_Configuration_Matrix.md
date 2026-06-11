# Test Configuration Matrix — Wonderful Mysterious App

This document describes all configurations in which the application should be
tested before release. Configurations are grouped by layer: API, browser,
operating system, device, network, and deployment environment.

---

## 1. API / Backend Configurations

These apply to all automated unit, integration, E2E, performance, and security
tests.

| Dimension | Configurations |
|---|---|
| Python version | 3.11 (current), 3.12 (forward compatibility) |
| FastAPI version | Pinned in requirements.txt; test on minor upgrade |
| Uvicorn workers | 1 worker (current), 4 workers (production-like) |
| Startup directory | Repo root (current), `/app` inside container |
| Rate limit config | Default (100 req / 10s), low threshold (3 req / 60s) for test isolation |
| Concurrency | Sequential (current), 10 concurrent clients, 50 concurrent clients |

---

## 2. Browser Configurations (Frontend / UI)

The interactive landing page must be tested across the following browsers.
Automated cross-browser testing via Playwright covers the primary matrix;
manual testing covers the remainder.

### 2.1 Desktop Browsers — Automated (Playwright)

| Browser | Engine | OS | Priority |
|---|---|---|---|
| Chrome (latest) | Chromium | Linux (CI) | P0 |
| Firefox (latest) | Gecko | Linux (CI) | P0 |
| Chrome (latest) | Chromium | macOS | P1 |
| Firefox (latest) | Gecko | macOS | P1 |
| Chrome (latest) | Chromium | Windows | P1 |
| Edge (latest) | Chromium | Windows | P1 |

### 2.2 Desktop Browsers — Manual Only

| Browser | Reason Manual |
|---|---|
| Safari (latest, macOS) | Playwright Safari support requires macOS runner (paid); test manually |
| Safari (latest, iOS) | Requires physical device or paid cloud service |

### 2.3 Mobile Browsers — Manual Only

| Browser | Device / OS | Priority |
|---|---|---|
| Chrome Mobile | Android (latest) | P2 |
| Safari Mobile | iOS (latest) | P2 |
| Samsung Internet | Android | P3 |

**Note:** Mobile testing is excluded from the current automated suite because
the app runs on `localhost` inside Docker and is not reachable from physical
devices without additional networking configuration. See Manual Testing document
for steps.

---

## 3. Viewport / Responsive Breakpoints

Test at the following viewport widths. Automated via Playwright; visual
verification manual.

| Breakpoint | Width | Represents |
|---|---|---|
| Mobile S | 320px | Small phones |
| Mobile L | 480px | Large phones |
| Tablet | 768px | iPad portrait |
| Desktop S | 1024px | Small laptops |
| Desktop L | 1440px | Standard monitors |
| Wide | 1920px | Large displays |

The app CSS switches to a single-column grid at ≤720px. The 768px and 480px
breakpoints specifically target this transition.

---

## 4. Operating System Configurations

| OS | Version | Role |
|---|---|---|
| Ubuntu (latest) | 24.04 LTS | CI runner (GitHub Actions) |
| macOS | Sonoma (14) | Local development, manual browser testing |
| Windows | 11 | Manual browser testing (Edge, Chrome) |

The application itself runs inside Docker so OS-level differences are largely
abstracted, but the CI runner OS affects Python installation, path handling,
and subprocess behavior in E2E tests.

---

## 5. Docker / Container Configurations

| Configuration | Test Type |
|---|---|
| Fresh build from scratch (no cache) | Automated (CI Docker build step) |
| Runtime image only (Stage 2) | Automated (E2E tests run against container) |
| Test stage (Stage 1) | Automated (Docker build runs unit + integration) |
| Container restart (favorites reset) | Manual |
| Container with non-root user | Manual (security hardening check) |
| Multi-worker Uvicorn (`--workers 4`) | Manual / performance testing |

---

## 6. Network Configurations

| Configuration | Relevance |
|---|---|
| Localhost (127.0.0.1) | Current automated and manual testing |
| Docker bridge network | E2E subprocess tests |
| Behind a reverse proxy (nginx) | Manual — tests real `X-Forwarded-For` header handling for rate limiter |
| Slow network (throttled) | Manual — tests frontend loading behavior |
| No network (offline) | Manual — confirms app does not depend on external resources |

---

## 7. Accessibility Configurations

| Configuration | Tool |
|---|---|
| axe-core automated scan | Automated via Playwright + axe-playwright |
| Keyboard-only navigation | Manual |
| Screen reader (NVDA + Chrome, Windows) | Manual |
| Screen reader (VoiceOver + Safari, macOS) | Manual |
| High contrast mode (Windows) | Manual |
| 200% browser zoom | Manual |
| Color blindness simulation | Manual (browser DevTools) |

---

## 8. Performance / Load Configurations

| Scenario | Tool | Type |
|---|---|---|
| Baseline single user | pytest + httpx | Automated |
| 10 concurrent users, 60s | Locust | Automated |
| 50 concurrent users, 60s | Locust | Automated |
| Rate limit boundary (100 req burst) | Locust | Automated |
| Sustained load to OOM | Locust (long run) | Manual / monitored |

---

## 9. Security Scan Configurations

| Tool | Target | Type |
|---|---|---|
| pip-audit | requirements.txt | Automated (CI) |
| Bandit | Python source | Automated (CI) |
| OWASP ZAP (baseline scan) | Running app | Automated (CI, passive) |
| OWASP ZAP (full scan) | Running app | Manual |
| Mozilla Observatory | HTTP headers | Manual |

---

## 10. What Is Out of Scope

| Configuration | Reason |
|---|---|
| Internet Explorer | End-of-life; no longer supported |
| Mobile device physical testing | App not network-accessible from devices in current setup |
| Multi-region / CDN | Not deployed to a CDN |
| TLS / HTTPS termination | Not configured; out of scope for current release |
| Distributed load (multi-node) | Single container deployment |
| Penetration testing | Explicitly out of scope per Test Plan |
