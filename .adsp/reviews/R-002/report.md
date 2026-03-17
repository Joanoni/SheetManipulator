# R-002 — Implementation Report: Vite Dev Cache Staleness in Docker

## Metadata

| Field | Value |
| :--- | :--- |
| **Review ID** | R-002 |
| **Implemented** | 2026-03-17T03:15:00Z |
| **Severity** | 🔴 Critical (resolved) |
| **Affected Files** | `src/frontend/Dockerfile`, `src/frontend/.dockerignore` (new) |

---

## Root Cause (Summary)

`src/frontend/Dockerfile` executed `COPY . .` after `RUN npm ci`, which baked the developer's local `node_modules/.vite/` pre-bundle cache into the Docker image layer. If that cache predated the T-008 addition of `ColumnDefinition` to `schema.ts`, Vite served the stale cached module to the browser, causing:

```
Uncaught SyntaxError: The requested module '/src/api/schema.ts' does not provide an export named 'ColumnDefinition'
```

---

## Changes Applied

### Fix A — `src/frontend/.dockerignore` (new file)

Prevents `node_modules/`, `.vite/`, and `dist/` from being copied into the Docker build context:

```
node_modules/
.vite/
dist/
```

**Effect:** The stale `.vite/` cache directory is never included in the image layer. `node_modules/` exclusion also provides defense-in-depth (prevents local `node_modules/` from overwriting the `npm ci`-installed one).

### Fix B — `src/frontend/Dockerfile` CMD updated

**Before:**
```dockerfile
CMD ["npm", "run", "dev", "--", "--host"]
```

**After:**
```dockerfile
CMD ["npm", "run", "dev", "--", "--host", "--force"]
```

**Effect:** `--force` instructs Vite to ignore and regenerate the dependency pre-bundle cache on every container startup. This is a safety net — even if a stale cache somehow enters the image in the future, it will be discarded at startup.

---

## Fix C — Future Improvement (Not Implemented)

Switch to a multi-stage production build (`npm run build` + `serve`) to eliminate the Vite dev server from Docker entirely. This removes the cache problem at its root and produces a smaller, faster container. Recommended for production readiness.

---

## Manual Validation Checklist

- [ ] Run `docker compose -f src/docker-compose.yml up --build` on a machine with a local `.vite/` cache present.
- [ ] Confirm the frontend container starts without `SyntaxError` in the browser console.
- [ ] Confirm `ColumnDefinition` is resolved correctly in `AddRowModal.tsx`, `DataTable.tsx`, and `SchemaPanel.tsx`.
- [ ] Confirm the Manage page loads and renders the table selector.
- [ ] Confirm the Upload Wizard completes a full ingestion cycle.
- [ ] Confirm the History page loads and displays upload records.
- [ ] Inspect the Docker build log — confirm `node_modules/` and `.vite/` are excluded from the build context (`.dockerignore` active).
- [ ] Confirm Vite logs `--force` flag acknowledgment on container startup (cache regeneration message).
