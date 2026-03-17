# R-001 Implementation Report — Frontend Import Error Fix

**Date:** 2026-03-17T02:28:00Z
**Review Source:** `.adsp/reviews/R-001/review.md`
**Severity:** 🔴 Critical → ✅ Resolved

---

## Summary

Applied **Option A** from the Reviewer's recommendation: removed the `./frontend:/app` bind mount and the `/app/node_modules` anonymous volume from the `frontend` service in `src/docker-compose.yml`.

---

## Changes Made

| File | Change |
| :--- | :--- |
| `src/docker-compose.yml` | Removed `volumes:` block from `frontend` service (2 lines deleted: `./frontend:/app` bind mount and `/app/node_modules` anonymous volume). |

---

## Before / After

**Before:**
```yaml
frontend:
  build: ./frontend
  ports:
    - "5173:5173"
  volumes:
    - ./frontend:/app
    - /app/node_modules
  environment:
    - VITE_API_URL=http://localhost:8000
  depends_on:
    - backend
```

**After:**
```yaml
frontend:
  build: ./frontend
  ports:
    - "5173:5173"
  environment:
    - VITE_API_URL=http://localhost:8000
  depends_on:
    - backend
```

---

## Root Cause (from R-001 review)

On a fresh `docker compose up --build`, Docker applied the bind mount `./frontend:/app` at container startup, replacing the entire `/app` directory (including the `node_modules/` installed by `npm ci` during the image build). The anonymous volume `/app/node_modules` was created empty on first run, so Vite could not resolve `react-router-dom`.

---

## Impact of Fix

- `docker compose -f src/docker-compose.yml up --build` now correctly serves the frontend using the image-built `node_modules/`.
- Hot-reload is **not** available in Docker mode (by design — the README documents a separate local dev workflow for that).
- The backend service retains its `./backend:/app` bind mount (Python does not use `node_modules`; `uvicorn --reload` works correctly with a bind mount).

---

## Manual Validation Checklist

- [ ] Run `docker compose -f src/docker-compose.yml up --build` on a machine with no local `node_modules/` in `src/frontend/`.
- [ ] Confirm frontend container starts without Vite import errors.
- [ ] Open `http://localhost:5173` — confirm the React app loads.
- [ ] Navigate to `/ingest`, `/manage`, `/history` — confirm all routes resolve.
- [ ] Confirm `http://localhost:8000/health` returns `{"status": "ok"}`.
- [ ] Confirm `http://localhost:8000/docs` loads the Swagger UI.
- [ ] Run `docker compose down` and `docker compose up --build` again (second run) — confirm still works.
