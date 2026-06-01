# Common Production Issues — FastAPI Web Application

This document describes the most common categories of production issues for a
FastAPI-based web application with an interactive HTML frontend, in-memory
storage, and a Dockerised deployment. Issues are grouped by area and ranked
roughly by frequency in real-world deployments.

---

## 1. Performance & Scalability

### 1.1 Response Time Degradation Under Load
FastAPI is async-capable but a single Uvicorn worker process handles requests
sequentially within a thread. Under sustained concurrent load, response times
climb even when CPU is not saturated. Common causes:

- Single worker process (default `uvicorn` invocation starts one worker)
- Blocking synchronous code accidentally introduced into async route handlers
- In-memory state accessed without locks becoming a contention point

**Symptom:** p95 response time exceeds SLA (e.g. the 200 ms target in the Test
Strategy) under moderate concurrency.

### 1.2 Memory Leak from Unbounded In-Memory Storage
The `db["favorites"]` list grows indefinitely. In production with many users
this eventually consumes all available container memory and causes an OOM kill.

**Symptom:** Container restarts periodically with no application-level error.

### 1.3 Rate Limiter Memory Growth
The `RateLimiter` stores a record per unique IP. With a large and varied client
population (or spoofed IPs) the limiter's internal dict grows without bound.

**Symptom:** Gradual memory increase; harder to diagnose than favorites growth.

---

## 2. Security

### 2.1 No Authentication or Authorisation
All endpoints are publicly reachable with no credentials required. Any client
can read all favorites, submit arbitrary payloads, and exhaust rate limit budgets
shared across all users.

### 2.2 Rate Limiter Bypass via IP Spoofing / Proxies
The rate limiter keys on `request.client.host`. Behind a load balancer or
reverse proxy this is the proxy IP, not the real client IP, effectively making
the rate limiter per-proxy rather than per-user.

**Symptom:** Rate limit is hit immediately for all users when the first client
exhausts the proxy's budget.

### 2.3 No HTTPS / TLS
The Dockerfile exposes port 8000 with plain HTTP. Production traffic should
terminate TLS at a reverse proxy (nginx, Caddy, AWS ALB). Without it all data
is transmitted in cleartext.

### 2.4 Missing Security Headers
Responses contain no HTTP security headers:

- `Content-Security-Policy` — mitigates XSS
- `X-Content-Type-Options` — prevents MIME sniffing
- `X-Frame-Options` — prevents clickjacking
- `Strict-Transport-Security` — enforces HTTPS
- `Referrer-Policy`

**Symptom:** Security scanner (OWASP ZAP, Mozilla Observatory) flags all
responses.

### 2.5 No Input Size Limits
The `/api/submit` `data` field is a free-form dict with no size constraint.
A client can POST megabytes of JSON, consuming memory and CPU for each request.

---

## 3. Availability & Reliability

### 3.1 No Health Check Endpoint
The Dockerfile has no `HEALTHCHECK` instruction and there is no `/health`
endpoint. Orchestrators (Kubernetes, ECS, Docker Compose) cannot determine
whether the application is alive and ready to serve traffic.

**Symptom:** A container that has started but whose application has crashed
continues to receive traffic.

### 3.2 Single Point of Failure
One container, one process, no redundancy. Any crash or deployment takes the
entire service offline.

### 3.3 Unhandled Startup Errors
If `app/static/index.html` is missing, the landing page route raises
`FileNotFoundError` at request time rather than at startup, meaning the
container appears healthy while silently failing for all `/` requests.

### 3.4 No Graceful Shutdown Handling
Uvicorn handles `SIGTERM` but in-flight requests may be dropped during container
stop/restart cycles without explicit shutdown timeouts configured.

---

## 4. Observability

### 4.1 No Structured Logging
Uvicorn's default access log writes plaintext to stdout. There is no
application-level structured logging (JSON) with request IDs, user context,
or timing data. Log aggregators (Datadog, CloudWatch, ELK) cannot parse or
alert on unstructured logs effectively.

### 4.2 No Metrics or Tracing
There are no Prometheus metrics, no distributed tracing headers, and no
instrumentation. It is impossible to answer questions like "what is my p99
latency for `/api/fortune`?" or "how many 429s did we return in the last hour?"
without parsing raw logs.

### 4.3 No Alerting
No uptime monitoring, no error rate alerts, no latency alerts. The first
indication of a production incident is typically a user complaint.

---

## 5. Frontend / Browser

### 5.1 JavaScript Errors on Older Browsers
The landing page uses modern JavaScript (fetch API, template literals, CSS
custom properties). Browsers that do not support these features will silently
fail or display broken UI.

### 5.2 No Error Feedback for Failed API Calls
If the API returns a 429 or 422, the frontend JavaScript may not surface a
meaningful error message to the user, leaving them with a blank response
container and no explanation.

### 5.3 CORS Not Configured
FastAPI does not enable CORS by default. If the frontend is ever served from a
different origin than the API (e.g. a CDN), all API calls will be blocked by
the browser's same-origin policy.

### 5.4 No Content Security Policy
Without a CSP header, the browser will execute any inline scripts or load
resources from any origin, increasing XSS risk.

---

## 6. Deployment & Configuration

### 6.1 No Environment-Specific Configuration
There is no concept of `dev` / `staging` / `prod` configuration. Rate limit
thresholds, log levels, and other tunables are hardcoded.

### 6.2 Dependency Version Drift
`requirements.txt` pins versions at install time but does not use a lock file
(e.g. `pip-compile`). A fresh install months later may pull in a minor version
with a breaking change.

### 6.3 No Image Tagging or Versioning Strategy
The Docker image is built as `wonderfulapp` with no tag. Rolling back to a
previous version requires rebuilding from git history rather than pulling a
tagged image.

### 6.4 Secrets Management
There are currently no secrets, but any future addition of API keys, database
credentials, or JWT signing keys would need to be injected via environment
variables or a secrets manager — not hardcoded in source.

---

## Summary Table

| Area | Issue | Severity |
|---|---|---|
| Performance | Unbounded in-memory growth | High |
| Performance | Single worker under load | Medium |
| Security | No authentication | High |
| Security | Missing security headers | High |
| Security | Rate limiter IP spoofing | Medium |
| Security | No HTTPS | High |
| Availability | No health check | Medium |
| Availability | FileNotFoundError on missing static file | Medium |
| Observability | No structured logging | High |
| Observability | No metrics or tracing | Medium |
| Frontend | CORS not configured | Medium |
| Frontend | No CSP | Medium |
| Deployment | No image versioning | Low |
| Deployment | No environment config | Medium |
