# Review R-001 — Frontend Import Error: `react-router-dom` Not Found

**Review ID:** R-001
**Date:** 2026-03-17T02:08:00Z
**Origin File:** `.adsp/reviews/R-001/origin/error.txt`
**Reported By:** User (via `.adsp/inbox/review_features/error.txt`)

---

## 📋 Issue Summary

After running the Quickstart (Docker) commands from `README.md`, the frontend fails to load with the following Vite import-analysis error:

```
[plugin:vite:import-analysis] Failed to resolve import "react-router-dom" from "src/App.tsx". Does the file exist?
```

---

## 🔍 Root Cause Analysis

### What Happened

According to the Builder annotation for **T-007** (Run: `2026-03-16T23:23:00Z`), `react-router-dom` was installed by running `npm install react-router-dom` inside the `src/frontend/` directory on the **host machine**. This correctly added the package to `src/frontend/package.json` and `src/frontend/package-lock.json`.

However, the **Docker build** for the frontend service uses a `Dockerfile` that runs `npm ci` (or `npm install`) based on the `package.json` at build time. The critical issue is:

> **`react-router-dom` was installed locally on the host but the `src/frontend/node_modules/` directory is either excluded from the Docker build context (via `.dockerignore` or `.gitignore`) or the Docker image's `npm install` step is not picking up the updated `package-lock.json` correctly.**

More specifically, the most likely cause is one of the following:

| # | Scenario | Likelihood |
| :--- | :--- | :--- |
| 1 | `src/frontend/node_modules/` is bind-mounted or volume-shadowed in `docker-compose.yml`, overwriting the container's installed modules with the host's (possibly stale) `node_modules/` | **High** |
| 2 | The `src/frontend/Dockerfile` does not copy `package-lock.json` before running `npm install`, causing a fresh install that misses `react-router-dom` if `package.json` was not updated | **Medium** |
| 3 | `react-router-dom` was installed locally but `package.json` was not saved with `--save` flag, so it is absent from the dependency list used during Docker build | **Low** (Builder used standard `npm install react-router-dom` which auto-saves) |

### Supporting Evidence from Status Log

- T-007 Builder annotation explicitly states: *"Installed `react-router-dom` (4 packages) in `src/frontend/`"* — confirming the install was performed on the host.
- T-007 also confirms `npx tsc --noEmit` passed with zero type errors on the host, meaning the package was resolvable locally.
- The error only manifests when running via Docker, pointing to a container-build isolation issue rather than a code defect.

---

## 🛠️ Recommended Fix

The ADSP-Builder should investigate and resolve the following:

1. **Verify `src/frontend/Dockerfile`** — Ensure it copies `package.json` AND `package-lock.json` before running `npm ci` (preferred over `npm install` for reproducible builds).
2. **Verify `src/docker-compose.yml`** — Ensure no volume mount is shadowing `/app/node_modules` inside the frontend container with the host's `node_modules/`.
3. **Verify `src/frontend/package.json`** — Confirm `react-router-dom` appears under `dependencies`.
4. **Rebuild with `--no-cache`** — After any fix, run `docker compose -f src/docker-compose.yml build --no-cache` to ensure a clean layer rebuild.

---

## 📊 Impact Assessment

| Dimension | Assessment |
| :--- | :--- |
| **Severity** | 🔴 Critical — Frontend is completely non-functional via Docker |
| **Scope** | Frontend only; backend is unaffected |
| **User Impact** | Blocks all UI workflows (Upload, Manage, History) |
| **Root in Code** | No — the application code is correct; this is a build/packaging defect |
| **Tasks Affected** | T-007 (react-router-dom install), T-001 (Docker Compose scaffold) |

---

## ✅ Review Conclusion

This is a **build reproducibility defect** introduced during T-007. The `react-router-dom` package is correctly used in the source code but is not available inside the Docker container at runtime. The fix is confined to the `Dockerfile` and/or `docker-compose.yml` configuration — no application logic changes are required.

**Action Required:** Route to ADSP-Builder for a targeted fix to the frontend Docker build configuration.

*Reviewer Agent Run: 2026-03-17T02:08:00Z*
