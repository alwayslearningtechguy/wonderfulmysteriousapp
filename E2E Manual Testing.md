# Manual Testing (Beyond Automated Coverage)

Automated tests cover API correctness, integration behavior, and core end-to-end
flows via a live Uvicorn server. The following areas require manual validation
because they involve UI rendering, real browser behavior, Docker runtime
conditions, or time-dependent states that are not practical to automate.

---

## Testing Environment & Device Coverage

All manual UI testing for the Wonderful Mysterious App was performed on a
desktop/laptop environment (Chrome and Firefox on Windows/macOS). The application
runs locally inside a Docker container and is accessed via `http://localhost:8000`,
which is only reachable from the host machine.

Because the app is not deployed to a public network, mobile and tablet devices
cannot access the local Docker container without additional networking
configuration. Mobile and tablet testing were therefore not performed.

---

## 1. UI Rendering and Behavior

### Steps

1. Start the application via Docker.
2. Navigate to `http://localhost:8000` in a desktop browser.
3. Expand the **Weather** card, enter a city (e.g. "Chicago"), and click **Send GET Request**. Verify that the weather JSON renders in the response container below the button.
4. Expand the **Insight** card, enter a topic (e.g. "technology"), and click **Send GET Request**. Verify that the insight JSON renders.
5. Expand the **Fortune** card and click **Send GET Request**. Verify that the fortune JSON renders.
6. Expand the **Submit** card, enter a username and score, and click **Send POST Request**. Verify that `201 Created` and the echoed payload appear in the response container.
7. Expand the **Favorites (POST)** card, enter an integer ID, and click **Send POST Request**. Verify that `201 Created` and `"message": "Saved"` appear.
8. Click the **Open /api/favorites** link in the Favorites (GET) card. Verify the saved ID appears in the list.
9. Refresh the page and confirm the page reloads correctly. Note: favorites persist in-memory for the life of the container — they do not reset on page refresh, only on container restart.

### Why Manual?

DOM rendering and JavaScript execution are not covered by automated tests.
Ensures that all six interactive test forms work correctly and that
frontend-to-backend integration produces visible results in the UI.

---

## 2. Cross-Browser Behavior

### Browsers Tested

- Chrome (latest)
- Firefox (latest)

### Checks Performed

- Page loads without console errors.
- All six API cards are visible and expandable.
- Buttons trigger fetch calls that update the response containers.
- No layout issues observed.

### Why Manual?

Browser differences in JavaScript execution and CSS rendering are best validated
manually for a lightweight frontend like this.

---

## 3. Rate-Limit Behavior in Real Usage

### Steps

1. Rapidly call `/api/weather` 100 times using a script or curl loop.
2. Confirm that all 100 requests return `200 OK`.
3. Send a 101st request and confirm it returns `429 Too Many Requests` with body `{"detail": "Too Many Requests"}`.
4. Wait longer than the rate-limit window (10 seconds).
5. Confirm that the next request returns `200 OK` again.

### Why Manual?

Automated unit tests validate rate-limit logic in isolation using a custom
`RateLimiter` instance. Real-world window expiry behavior requires actual
wall-clock waiting and is not practical to automate reliably in CI.

---

## 4. Visual Layout and Responsiveness

### Steps

1. Resize the browser window to various widths (narrow, medium, wide).
2. Confirm:
   - Content remains readable at all widths.
   - Buttons do not overlap or become inaccessible.
   - No horizontal scrolling is required at typical desktop widths.
   - At narrow widths (≤720px) the layout switches to a single-column grid.

### Why Manual?

Visual layout and responsive breakpoints are not asserted in automated tests.

---

## 5. App Behavior After Container Restart

### Steps

1. Start the app via Docker.
2. Use the Favorites (POST) card (or curl) to add one or more favorites.
3. Confirm via `GET /api/favorites` that the items are present.
4. Stop and restart the container (`docker stop` then `docker run`).
5. Confirm that `GET /api/favorites` returns an empty list.

### Why Manual?

This validates the documented non-persistent behavior of in-memory storage across
container restarts — something automated E2E tests cannot verify since they run
against a single server session.

---

## 6. Error Handling and Edge Cases

### Steps

1. Submit malformed JSON to `/api/submit` using curl or Postman (e.g. `'{bad json'`). Confirm `422 Unprocessable Entity` is returned.
2. Submit a valid payload containing `<script>` tags to `/api/submit`. Confirm the tags are echoed back unchanged in the `"received"` field — the API does **not** sanitize input.
3. Call `/api/weather` with a very long city name string. Confirm no 500 error occurs and the name is returned title-cased.
4. Call `/api/insight` with an unknown topic (e.g. `?topic=finance`). Confirm the response falls back to `"topic": "general"` with a `200` status.

### Why Manual?

Automated tests cover the primary validation paths. Manual checks ensure that
edge cases and error states are understandable and do not cause unexpected server
errors.

---

## 7. Landing Page Content Verification

### Steps

1. Load the root page (`/`).
2. Confirm that all six API cards are present: Weather, Insight, Fortune, Submit, Favorites (POST), and Favorites (GET).
3. Confirm that the sticky navigation bar links scroll to the correct card sections.
4. Confirm that JavaScript loads without errors (check browser console).
5. Confirm that the page header, response containers, and footer render correctly.

### Why Manual?

The landing page is an interactive API documentation page with embedded live test
forms. Its JavaScript-driven behavior — card toggling, fetch calls, and DOM
updates — cannot be validated by the automated HTTP-level E2E tests.

---

## Summary

Manual testing complements the automated suite by validating UI behavior, browser
compatibility, visual layout, error handling, and real-world rate-limit behavior.
These checks ensure that the application behaves correctly from a user's
perspective and that the frontend and backend integrate smoothly in a live browser
environment.
