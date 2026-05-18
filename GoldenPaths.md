# Golden Paths Analysis

This document identifies the most valuable end‑to‑end scenarios in the Wonderful Mysterious App. These represent the core user journeys that must always work.

---

## 1. Daily Mystery Experience (Primary Golden Path)

### Steps
1. User requests weather.
2. User requests an insight.
3. User requests a fortune.
4. User saves the combined result as a favorite.
5. User views the favorites list.

### Why It Matters
- Exercises all core API endpoints.
- Validates the in‑memory favorites store.
- Represents the main user value.

---

## 2. Data Submission Golden Path

### Steps
1. POST valid JSON to `/api/submit`.
2. GET `/api/favorites`.

### Why It Matters
- Ensures structured data is accepted and stored.
- Protects against schema drift.

---

## 3. Core API Health

### Steps
- GET `/api/weather`
- GET `/api/insight`
- GET `/api/fortune`

### Why It Matters
If any of these fail, the app feels broken.

---

## 4. UI Fetch Flow (Manual)

### Steps
1. Load `/`
2. Click each button
3. Verify UI updates

### Why It Matters
Frontend behavior is not covered by automated tests.
