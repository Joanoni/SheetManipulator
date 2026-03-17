# R-003 — Implementation Report

## Metadata

| Field | Value |
| :--- | :--- |
| **Review ID** | R-003 |
| **Implemented** | 2026-03-17T03:23:00Z |
| **Severity** | 🟡 Medium |
| **Fixes Applied** | Fix A (README `git pull` step) + Fix B (Production Build Dockerfile) |

---

## Root Cause (from review.md)

The user's local `src/frontend/src/api/schema.ts` was a pre-T-008 version that did not contain the `ColumnDefinition` export. The user had not run `git pull` since cloning. `docker compose up --build` copies the local working tree via `COPY . .` — baking the stale local file into the image. Vite served it to the browser, which threw `SyntaxError: The requested module '/src/api/schema.ts' does not provide an export named 'ColumnDefinition'`.

The R-002 fixes (`.dockerignore` + `--force`) addressed Vite cache staleness but did not address the scenario where the **source file itself** is stale in the user's local working tree.

---

## Changes Applied

### Fix A — README Quickstart `git pull` Step

**File:** `README.md`

Added a callout block immediately after the `docker compose up --build` command in the Quickstart section:

```markdown
> **Re-running after an update?** Run `git pull` first to ensure your local files are current before rebuilding:
> ```bash
> git pull
> docker compose -f src/docker-compose.yml up --build
> ```
```

This directly addresses the user's workflow gap — they were re-running the Quickstart without pulling the latest commits.

---

### Fix B — Multi-Stage Production Build Dockerfile

**File:** `src/frontend/Dockerfile`

**Before:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "--force"]
```

**After:**
```dockerfile
# Stage 1 — Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2 — Serve
FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
```

**Key design decisions:**
- `VITE_API_URL` is declared as a Docker `ARG` and set as `ENV` before `npm run build` — Vite bakes it into the bundle at build time (required for `import.meta.env.VITE_API_URL` to work in the browser).
- Default value `http://localhost:8000` matches the existing Docker Compose environment.
- Stage 2 uses `serve` (a lightweight static file server) to serve the compiled `dist/` — no Node.js dev server, no Vite, no cache.
- The final image contains only `dist/` and `serve` — no source files, no `node_modules/`, no dev tooling.

**File:** `src/docker-compose.yml`

Changed `frontend` service from `environment:` (runtime) to `build.args:` (build-time) for `VITE_API_URL`:

**Before:**
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

**After:**
```yaml
frontend:
  build:
    context: ./frontend
    args:
      - VITE_API_URL=http://localhost:8000
  ports:
    - "5173:5173"
  depends_on:
    - backend
```

This is critical: Vite reads `VITE_*` variables at **build time** via `import.meta.env`. Passing them as runtime `environment:` variables has no effect on the compiled bundle.

---

## Why This Eliminates the Error Class

| Scenario | Before R-003 | After R-003 |
| :--- | :--- | :--- |
| User clones before T-008, runs `docker compose up --build` | ❌ Stale `schema.ts` baked in; `ColumnDefinition` missing | ✅ README instructs `git pull` first |
| Stale Vite dev cache in `node_modules/.vite/` | ✅ Fixed by R-002 `.dockerignore` + `--force` | ✅ Eliminated — no dev server in production build |
| Any future source file staleness | ❌ Dev server serves whatever `COPY . .` baked in | ✅ `npm run build` fails fast if imports are broken |
| `VITE_API_URL` not available in browser | ❌ Runtime env var ignored by compiled bundle | ✅ Baked into bundle via `ARG` → `ENV` → `npm run build` |

---

## Manual Validation Checklist

- [ ] 1. Run `git pull` to get latest commits.
- [ ] 2. Run `docker compose -f src/docker-compose.yml up --build` — build should succeed with no errors.
- [ ] 3. Confirm Docker build log shows two stages: `builder` and the final `serve` stage.
- [ ] 4. Open http://localhost:5173 — React app loads without console errors.
- [ ] 5. Confirm no `SyntaxError: The requested module '/src/api/schema.ts' does not provide an export named 'ColumnDefinition'` in browser console.
- [ ] 6. Navigate to `/manage` — table selector renders; selecting a table loads `DataTable` with `AddRowModal` functional.
- [ ] 7. Navigate to `/` (Ingest) — `UploadWizard` renders; upload a `.xlsx` file through all 4 steps.
- [ ] 8. Navigate to `/history` — `HistoryPage` renders with upload rows.
- [ ] 9. Confirm `VITE_API_URL` is correctly baked: open browser DevTools → Network tab → verify API calls go to `http://localhost:8000`.
- [ ] 10. Run `docker compose down` and `docker compose up --build` again (no `--no-cache`) — confirm build uses layer cache for `npm ci` stage.
- [ ] 11. Verify README Quickstart section contains the `git pull` callout block.
- [ ] 12. Verify `src/frontend/Dockerfile` has two `FROM` stages (`builder` and final).
