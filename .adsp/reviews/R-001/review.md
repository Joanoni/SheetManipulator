# Review R-001 — Frontend Import Error: `react-router-dom` Not Found

**Date:** 2026-03-17T02:16:00Z
**Severity:** 🔴 Critical
**Source:** `.adsp/inbox/review_features/error.txt`
**Reported Error:**
```
[plugin:vite:import-analysis] Failed to resolve import "react-router-dom" from "src/App.tsx". Does the file exist?
```

---

## 🔍 Root Cause Analysis

### Symptom
User ran `docker compose -f src/docker-compose.yml up --build` per the README Quickstart. Docker build succeeded. Opening the frontend at `http://localhost:5173` produced a Vite import resolution failure for `react-router-dom`.

### Investigation

| File | Finding |
| :--- | :--- |
| `src/frontend/package.json` | `react-router-dom: ^7.13.1` is correctly listed under `dependencies`. |
| `src/frontend/package-lock.json` | Contains 3 references to `react-router-dom` — lockfile is in sync. |
| `src/frontend/Dockerfile` | Runs `npm ci` before `COPY . .` — installs packages into container `/app/node_modules` at build time. |
| `src/docker-compose.yml` | Mounts `./frontend:/app` (bind mount) AND declares `/app/node_modules` as an anonymous volume. |

### Root Cause: Docker Volume Shadowing

The `docker-compose.yml` frontend service declares two volume entries:

```yaml
volumes:
  - ./frontend:/app          # bind mount — overwrites /app at runtime
  - /app/node_modules        # anonymous volume — intended to protect node_modules
```

The intent of the anonymous volume `/app/node_modules` is to preserve the `node_modules/` directory installed during the Docker image build, preventing the host bind mount from shadowing it. However, **this pattern only works reliably when the anonymous volume has been previously populated** (i.e., on a subsequent `docker compose up` after the first run).

On a **fresh `docker compose up --build`** (as instructed in the README Quickstart):

1. The image is built — `npm ci` installs all packages including `react-router-dom` into `/app/node_modules` inside the image layer.
2. At container startup, Docker applies the bind mount `./frontend:/app`, which **replaces the entire `/app` directory** with the host filesystem contents.
3. The anonymous volume `/app/node_modules` is created **empty** (no prior data) and mounted on top of the bind mount.
4. The result: `/app/node_modules` is an **empty anonymous volume** — the host's `node_modules/` (which may not exist or may be incomplete) is never used, and the image-built `node_modules/` is discarded.
5. Vite starts and cannot resolve `react-router-dom` because `node_modules/` is empty.

### Why It Appeared to Work Previously
The TypeScript check (`npx tsc --noEmit`) was run on the **host** machine where `node_modules/` was populated by the host `npm install`. The Docker container environment was never validated.

---

## 📋 Affected Files

| File | Issue |
| :--- | :--- |
| [`src/docker-compose.yml`](../../src/docker-compose.yml) | Bind mount `./frontend:/app` shadows the container's `node_modules/` on fresh builds. |
| [`src/frontend/Dockerfile`](../../src/frontend/Dockerfile) | Build-time `npm ci` output is discarded at runtime due to volume ordering. |

---

## 🛠️ Recommended Fix

**Option A — Remove the bind mount (Recommended for Docker Quickstart)**

Remove the `./frontend:/app` bind mount from `docker-compose.yml`. The container will use the image-built copy of the frontend. Hot-reload will not be available in Docker mode, but the Quickstart will work correctly.

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

**Option B — Use a named volume for `node_modules` with explicit population**

Keep the bind mount for hot-reload but ensure `node_modules` is populated before the bind mount takes effect by using a startup entrypoint that runs `npm install` inside the container:

```yaml
volumes:
  - ./frontend:/app
  - frontend_node_modules:/app/node_modules
```

This requires a named volume declaration and an entrypoint script — more complex and not suitable for a simple Quickstart.

**Recommended action:** Apply Option A. The README already documents a separate "Development (Local)" workflow for hot-reload. The Docker Quickstart should be a zero-friction path.

---

## 🎯 Action Required

**Route to:** ADSP-Builder
**Task scope:** Modify [`src/docker-compose.yml`](../../src/docker-compose.yml) — remove `./frontend:/app` bind mount and `/app/node_modules` anonymous volume from the `frontend` service. Verify the backend bind mount (`./backend:/app`) does not have the same issue (Python does not use `node_modules` so it is unaffected).

---

## 📎 Origin File

`.adsp/reviews/R-001/origin/error.txt`
