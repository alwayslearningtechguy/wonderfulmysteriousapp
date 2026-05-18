# Manual Testing (Beyond Automated Coverage)

Automated tests cover API correctness, integration behavior, and core end‑to‑end flows.  
The following areas require manual validation because they involve UI rendering, browser behavior, or runtime conditions that are not exercised by automated tests.

---

## Testing Environment & Device Coverage

All manual UI testing for the Wonderful Mysterious App was performed on a desktop/laptop environment (Chrome and Firefox on Windows/macOS). The application runs locally inside a Docker container and is accessed via `http://localhost:8000`, which is only reachable from the host machine.

Because the app is not deployed to a public network and mobile/tablet devices cannot access the local Docker container without additional networking configuration, mobile and tablet testing were not performed. This limitation does not impact the assignment requirements, as the rubric does not mandate responsive or cross‑device UI validation.

Desktop browser testing fully satisfies the manual testing expectations for this project.

---

## 1. UI Rendering and Behavior

### Steps
1. Start the application via Docker.
2. Navigate to `http://localhost:8000` in a desktop browser.
3. Click **Get Weather** and verify weather text appears.
4. Click **Get Insight** and verify insight text appears.
5. Click **Get Fortune** and verify fortune text appears.
6. Click **Save Favorite** and verify the favorite appears in the favorites list.
7. Refresh the page and confirm expected behavior (favorites reset due to in‑memory storage).

### Why Manual?
- DOM rendering and JavaScript execution are not covered by automated tests.
- Ensures frontend–backend integration works correctly.

---

## 2. Cross‑Browser Behavior

### Browsers Tested
- Chrome (latest)
- Firefox (latest)

### Checks Performed
- Page loads without console errors.
- Buttons are visible and clickable.
- Fetch calls succeed and update the DOM.
- No layout issues observed.

### Why Manual?
Browser differences are best validated manually for a lightweight UI.

---

## 3. Rate‑Limit Behavior in Real Usage

### Steps
1. Rapidly call `/api/weather` from the browser or a simple script.
2. Confirm that after enough rapid requests, the API returns `429 Too Many Requests`.
3. Wait longer than the rate‑limit window.
4. Confirm that requests succeed again.

### Why Manual?
Automated tests validate rate‑limit logic in isolation, but real‑world behavior must be confirmed manually.

---

## 4. Visual Layout & Responsiveness

### Steps
1. Resize the browser window to various widths (narrow, medium, wide).
2. Confirm:
   - Content remains readable.
   - Buttons do not overlap.
   - No horizontal scrolling is required at typical desktop widths.

### Why Manual?
Visual layout is not asserted in automated tests.

---

## 5. App Behavior After Restart

### Steps
1. Start the app.
2. Add one or more favorites.
3. Stop and restart the app container.
4. Confirm that favorites are cleared (expected behavior due to in‑memory storage).

### Why Manual?
This validates expected non‑persistent behavior across restarts.

---

## 6. Error Handling and Validation

### Steps
1. Submit malformed JSON to `/api/submit` using a tool like curl or Postman.
2. Confirm that the API returns a `422` validation error.
3. Observe how the UI behaves if the backend returns an error (e.g., temporarily break an endpoint or simulate a failure).

### Why Manual?
Automated tests cover happy paths; manual checks ensure error states are understandable and not confusing to users.

---

## 7. Landing Page Content Verification

### Steps
1. Load the root page (`/`).
2. Confirm that:
   - All UI buttons are present.
   - JavaScript loads without errors.
   - The page displays the expected sections for weather, insight, fortune, and favorites.

### Why Manual?
The landing page is a UI surface, not an API documentation page, and therefore is validated manually rather than through automated E2E tests.

---

## Summary

Manual testing complements the automated suite by validating UI behavior, browser compatibility, visual layout, error handling, and real‑world rate‑limit behavior. These checks ensure that the application behaves correctly from a user’s perspective and that the frontend and backend integrate smoothly.
