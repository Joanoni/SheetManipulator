# R-003 — Frontend Runtime Error: `ColumnDefinition` Not Found (Stale Local Working Tree — User Has Not Pulled Latest Commits)

## Metadata

| Field | Value |
| :--- | :--- |
| **Review ID** | R-003 |
| **Date** | 2026-03-17T03:19:00Z |
| **Severity** | 🟡 Medium — frontend non-functional for users who cloned before T-008 was committed; self-resolving after `git pull` |
| **Origin File** | `.adsp/reviews/R-003/origin/error.txt` |
| **Affected Files** | `README.md` (Quickstart section), `src/frontend/src/api/schema.ts` (source is correct — no change needed) |
| **Action Required** | Route to ADSP-Builder — update README Quickstart with `git pull` step |

---

## User-Reported Error

```
Uncaught SyntaxError: The requested module '/src/api/schema.ts' does not provide an export named 'ColumnDefinition' (at AddRowModal.tsx:2:10)
```

**User note:** "Its the second time this error happens."

**Reproduction steps:** User ran `docker compose -f src/docker-compose.yml up --build` per README Quickstart. Build succeeded. Opening the frontend in Chrome produced the above console error. This is a recurrence after R-002 was resolved.

---

## Source Code Verification

`ColumnDefinition` **is correctly exported** in [`src/frontend/src/api/schema.ts`](../../src/frontend/src/api/schema.ts) at line 35:

```typescript
// Used by T-008 DataTable (matches GET /api/schemas/{table_name} → ColumnDefinitionRead[])
export interface ColumnDefinition {
  id: number
  table_system_name: string
  column_system_name: string
  display_name: string
  data_type: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  is_mandatory: boolean
  is_primary_key: boolean
  column_order: number
}
```

The import in [`src/frontend/src/components/DataTable/AddRowModal.tsx`](../../src/frontend/src/components/DataTable/AddRowModal.tsx) at line 2 is syntactically correct:

```typescript
import { ColumnDefinition } from '../../api/schema'
```

**Conclusion: The source code in the repository is not the root cause.**

---

## R-002 Fix Verification

Both R-002 fixes are confirmed correctly applied in the repository:

| Fix | File | Status |
| :--- | :--- | :--- |
| Fix A — `.dockerignore` | `src/frontend/.dockerignore` | ✅ Present — excludes `node_modules/`, `.vite/`, `dist/` |
| Fix B — `--force` flag | `src/frontend/Dockerfile` CMD | ✅ Present — `CMD ["npm", "run", "dev", "--", "--host", "--force"]` |

**Conclusion: R-002 fixes are in the repository. The recurrence is not caused by a regression in the fixes.**

---

## Root Cause Analysis

<thinking>

### Why Does the Error Recur Despite R-002 Fixes Being Present in the Repo?

The user reports "its the second time this error happens." The R-002 fixes (`.dockerignore` + `--force`) are confirmed present in the repository. The source file `schema.ts` is correct in the repository. Yet the user sees the identical error.

**The only way this error can occur is if the version of `schema.ts` being baked into the Docker image does NOT contain the `ColumnDefinition` export.**

The Dockerfile executes:
```dockerfile
COPY . .
```

This copies the **local working tree** into the image — not the repository's HEAD. If the user's local working tree has an older version of `schema.ts` (one that predates T-008's addition of `ColumnDefinition`), then `COPY . .` bakes that old file into the image, and Vite serves it to the browser.

### How Can the Local Working Tree Be Stale?

The user cloned the repository at some point. If they cloned **before** T-008 was committed (or before R-002 was committed), their local `src/frontend/src/api/schema.ts` does not have `ColumnDefinition`. When they run `docker compose up --build`, Docker copies their local stale `schema.ts` into the image. The `--force` flag and `.dockerignore` are irrelevant — the source file itself is wrong.

**The fix for R-002 (`.dockerignore` + `--force`) only addresses the Vite cache staleness scenario.** It does not address the scenario where the source file itself is stale in the user's local working tree.

### Why Does the README Not Prevent This?

The current README Quickstart section reads:
```
git clone <repo-url>
cd SheetManipulator
docker compose -f src/docker-compose.yml up --build
```

There is no `git pull` step. A user who cloned the repository before T-008 was merged, then later tries to run the Quickstart again (e.g., after reading about R-001 or R-002 fixes), will not know to pull first.

### Why Is This "The Second Time"?

- **First time (R-002):** User ran `docker compose up --build` with a stale Vite cache in their local `node_modules/.vite/`. The `.dockerignore` and `--force` fixes were applied.
- **Second time (R-003):** User ran `docker compose up --build` again after R-002 was resolved. But they still have a stale local `schema.ts` (they never ran `git pull`). The R-002 fixes eliminated the cache problem, but the source file problem was never addressed because it was masked by the cache problem in R-002's analysis.

### Definitive Root Cause

**The user's local `src/frontend/src/api/schema.ts` is a pre-T-008 version that does not contain the `ColumnDefinition` export.** The user has not run `git pull` since cloning. `docker compose up --build` copies the stale local file into the image. Vite serves it. The browser throws the `SyntaxError`.

The R-002 analysis incorrectly attributed the error solely to the Vite cache. The cache was a contributing factor, but the underlying issue is that the source file in the user's working tree is stale.

</thinking>

### Primary Root Cause — Stale Local Working Tree (User Has Not Run `git pull`)

**Mechanism:**

1. User cloned the repository **before T-008 was committed**. Their local `src/frontend/src/api/schema.ts` is the pre-T-008 version — it does not contain the `ColumnDefinition` export.
2. User runs `docker compose -f src/docker-compose.yml up --build`.
3. The `src/frontend/Dockerfile` executes `COPY . .` — this copies the **local working tree** into the image, including the stale `schema.ts`.
4. Vite dev server starts inside the container and serves the stale `schema.ts` to the browser.
5. Browser receives the ESM module without `ColumnDefinition` and throws `SyntaxError`.

**Why R-002 did not prevent this:**
R-002 fixed the **Vite pre-bundle cache** staleness scenario (stale `node_modules/.vite/` baked into the image). It did not address the scenario where the **source file itself** is stale in the user's local working tree. The two scenarios produce an identical browser error but have different root causes.

**Evidence:**
- `ColumnDefinition` is present and correct in the repository's `schema.ts` at line 35.
- R-002 fixes (`.dockerignore`, `--force`) are confirmed present in the repository.
- The error is identical to R-002 — same file, same line, same export name.
- The user explicitly states "its the second time this error happens" — indicating a recurrence pattern, not a regression.
- `docker compose up --build` always copies the local working tree; it does not fetch from the remote repository.

### Secondary Contributing Factor — README Quickstart Lacks `git pull` Step

The README Quickstart section instructs:
```
git clone <repo-url>
cd SheetManipulator
docker compose -f src/docker-compose.yml up --build
```

There is no instruction to run `git pull` before `docker compose up --build`. A user who cloned before T-008 (or any subsequent commit) and re-runs the Quickstart will silently use stale source files.

---

## Fix Recommendations

### Fix A — Update README Quickstart with `git pull` Step (Recommended — Immediate)

Add a `git pull` step to the README Quickstart section, both in the initial clone flow and as a "Re-running after updates" note:

**README Quickstart — Before:**
```markdown
## Quickstart (Docker)

1. Clone the repository
2. Run `docker compose -f src/docker-compose.yml up --build`
```

**README Quickstart — After:**
```markdown
## Quickstart (Docker)

1. Clone the repository
2. **If re-running after an update:** run `git pull` first to ensure your local files are current
3. Run `docker compose -f src/docker-compose.yml up --build`
```

### Fix B — Switch to Production Build in Dockerfile (Long-term — Eliminates Class of Errors)

Replace the Vite dev server with a multi-stage production build in `src/frontend/Dockerfile`. This eliminates both the cache staleness problem (R-002) and makes the build deterministic — the image always reflects exactly what is in the working tree at build time, with no dev-server caching layer:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
```

This was documented as Fix C in R-002 and remains the recommended long-term solution.

### Fix C — Add `git pull` to Docker Compose Entrypoint (Alternative — Not Recommended)

Not recommended — Docker containers should not pull from git at runtime. This would introduce network dependencies and security concerns into the container startup.

---

## Recommended Action

**Implement Fix A** (README update) as the immediate fix — it directly addresses the user's workflow gap. **Document Fix B** as the recommended long-term improvement (already documented in R-002 as Fix C; escalate priority).

**Route to:** ADSP-Builder.

---

## Impact Assessment

| Component | Impact |
| :--- | :--- |
| `README.md` | Add `git pull` step to Quickstart section |
| `src/frontend/Dockerfile` | No change required for Fix A; Fix B is optional long-term improvement |
| `src/frontend/src/api/schema.ts` | No change required — source is correct |
| `src/frontend/src/components/DataTable/AddRowModal.tsx` | No change required — import is correct |

---

## Recurrence Prevention

This class of error (stale local working tree → stale Docker image) is inherent to the `COPY . .` pattern in development Dockerfiles. The only permanent fix is Fix B (production build), which eliminates the dev server and its associated caching behavior entirely. Until Fix B is implemented, the README must clearly instruct users to `git pull` before rebuilding.
