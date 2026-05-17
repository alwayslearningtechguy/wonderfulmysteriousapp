# Test Plan

## 1. Introduction
This Test Plan outlines the testing strategy for the *Wonderful and Mysterious API*, a FastAPI-based application that provides several endpoints including weather information, insights, fortunes, data submission, and user favorites. The purpose of this plan is to ensure that all API functionality is validated through unit tests, integration tests, security tests, and negative tests.

The API is fully self-contained and does **not** rely on external services. All data is generated internally or stored in an in-memory structure.  
Rate limiting is implemented at the middleware layer to prevent excessive request volume.

---

## 2. Scope
This Test Plan covers:

- Functional testing of all API endpoints  
- Unit testing of internal logic  
- Integration testing of HTTP request/response behavior  
- Security testing (sanitization, error hygiene, rate limiting)  
- Negative testing for invalid inputs  
- Basic load/burst behavior  

Out of scope:

- Full penetration testing  
- External API failure simulation (no external APIs exist)  
- Distributed load testing  
- Authentication/authorization testing  
- TLS/HTTPS configuration testing  

---

## 3. Features to Be Tested

### 3.1 `/api/weather` (GET)
- Returns mock weather data  
- Accepts optional `city` parameter  
- Handles unusual or unexpected city input  
- Behaves correctly under rate limiting  

### 3.2 `/api/insight` (GET)
- Returns a random insight message  
- Accepts optional `topic` parameter  
- Behaves correctly under rate limiting  

### 3.3 `/api/fortune` (GET)
- Returns a random fortune  
- Ensures response contains required fields  
- Behaves correctly under rate limiting  

### 3.4 `/api/submit` (POST)
- Accepts structured payload (`user`, `data`)  
- Validates payload structure  
- Handles sanitization edge cases  
- Behaves correctly under rate limiting  

### 3.5 `/api/favorites` (POST)
- Accepts a favorite item ID  
- Updates in-memory favorites list  
- Returns updated list  
- Behaves correctly under rate limiting  

### 3.6 `/api/favorites` (GET)
- Returns current favorites list  
- Handles empty and populated states  
- Behaves correctly under rate limiting  

---

## 4. Suspension & Resumption Criteria
* **Suspend:** If the Docker container fails to stay in a "Running" state or if `404 Not Found` occurs on all endpoints.  
* **Resume:** Once the `main.py` routing or `Dockerfile` configuration is corrected and the container restarts successfully.

---

## 5. Test Approach

### 5.1 Unit Testing
Unit tests directly call the endpoint functions without HTTP routing.  
They validate:

- Default parameter behavior  
- Custom parameter behavior  
- Response structure  
- Randomized output fields  
- In-memory database behavior  
- Payload validation  

Unit tests ensure internal logic is correct and isolated from FastAPI routing.

---

### 5.2 Integration Testing
Integration tests validate:

- HTTP status codes  
- JSON response structure  
- Query parameter handling  
- POST body validation  
- Stateful behavior (`favorites`)  
- Serialization of Pydantic models  
- Rate limiting enforcement  

Each endpoint has its own integration test file for clarity and maintainability.

Note: Some usability tests are automated and consequently tested here too. They address the following:

- Verify that the landing page is reachable and returns valid HTML.
- Ensure that all available API endpoints are clearly listed.
- Validate that all endpoint links are present and correctly formatted.

Other usability tests are conducted by human interaction review.

---

### 5.3 Security Testing

#### 5.3.1 Input Sanitization
Tests ensure:

- Script-like input does not crash the API  
- No stack traces are leaked  
- No unsafe reflection of user input  

#### 5.3.2 Rate Limiting
Rate limiting is implemented globally via middleware.  
Tests validate:

- Requests within the allowed window return `200`  
- Requests exceeding the limit return `429 Too Many Requests`  
- Rate limiting applies consistently across endpoints  
- Rate limiting resets after the configured time window  

#### 5.3.3 Error Message Hygiene
Tests ensure:

- No internal error messages are exposed  
- No environment variables leak  
- No stack traces appear in responses  

---

### 5.4 Negative Testing
Negative tests validate how the API handles invalid or malformed input.

Examples include:

- Invalid city names  
- Empty or malformed JSON payloads  
- Missing required fields  
- Invalid types  
- Extremely long strings  
- Unexpected query parameters  

These tests ensure the API fails gracefully and predictably.

---

### 5.5 Load & Stress Testing (Scaled Down)
Because the API uses no external services, load testing focuses on:

- Burst request behavior  
- Stateful behavior under repeated access  
- Ensuring the API does not crash under rapid calls  
- Rate limiting behavior under load  

Full performance benchmarking is intentionally out of scope.

---

## 6. Test Environment
Tests run using:

- Python 3.11  
- FastAPI TestClient  
- Pytest  
- In-memory database (`db` dict)  
- In-memory rate limiter  

The CI pipeline:

- Installs dependencies  
- Sets `PYTHONPATH`  
- Runs all unit, integration, and security tests  
- Fails the build if any test fails  

---

## 7. Test Deliverables
- Unit test files for each endpoint  
- Integration test files for each endpoint  
- Security test files (sanitization, rate limiting)  
- Negative test cases  
- CI test results  

---

## 8. Risks and Mitigations

### Risk: Randomized output may cause inconsistent tests  
**Mitigation:** Tests validate structure, not specific random values.

### Risk: In-memory database may retain state across tests  
**Mitigation:** Tests explicitly reset `db["favorites"]` before use.

### Risk: Rate limiting may block unrelated tests  
**Mitigation:** Tests reset the rate limiter between runs or use isolated clients.

---

## 9. Approval
This Test Plan reflects the current API design, test suite, and project scope.  
It should be updated as new endpoints or security features are added.
