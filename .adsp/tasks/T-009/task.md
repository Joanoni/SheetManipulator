# T-009 — Static File Serving for Error Reports

> **Layer:** Backend
> **Complexity:** Low
> **Depends on:** T-003, T-006
> **Status:** Pending

---

## 🎯 Objective

The ingestion pipeline writes error reports to `/data/uploads/{upload_id}/error_report_{upload_id}.xlsx`.
The frontend wizard returns a download link constructed from `error_report_path` (a raw filesystem path).
Currently no route serves these files — the download button is broken.

Fix: mount `/data/uploads` as a `StaticFiles` directory in FastAPI so the frontend can download error reports via HTTP.

---

## 📋 Acceptance Criteria

| # | Criterion |
| :--- | :--- |
| AC-1 | `GET /files/uploads/{upload_id}/error_report_{upload_id}.xlsx` returns the file with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| AC-2 | `src/backend/app/main.py` mounts `StaticFiles(directory="/data/uploads", html=False)` at `/files/uploads` |
| AC-3 | `src/frontend/src/components/UploadWizard/UploadWizard.tsx` — the error report download `href` is updated to use the `/files/` prefix correctly |
| AC-4 | If `/data/uploads` does not exist at startup, it is created before mounting (use `os.makedirs`) |
| AC-5 | CORS policy in `main.py` is not broken by the static mount |

---

## 🔧 Implementation Notes

### Backend — `src/backend/app/main.py`

```python
import os
from fastapi.staticfiles import StaticFiles

# In lifespan or at module level, before app.mount():
os.makedirs("/data/uploads", exist_ok=True)

# After router registrations:
app.mount("/files/uploads", StaticFiles(directory="/data/uploads"), name="uploads")
```

### Frontend — `src/frontend/src/components/UploadWizard/UploadWizard.tsx`

The current href pattern:
```tsx
href={`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/${state.errorReportPath}`}
```

`error_report_path` from the backend is currently stored as a relative path like
`/data/uploads/{upload_id}/error_report_{upload_id}.xlsx`.

The frontend href must be rewritten to:
```tsx
// Extract just the upload_id sub-path from error_report_path
// Backend should return path as: uploads/{upload_id}/error_report_{upload_id}.xlsx
// OR frontend constructs it from uploadId directly:
href={`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/files/uploads/${state.uploadId}/error_report_${state.uploadId}.xlsx`}
```

**Also update `src/backend/app/services/export.py`** — `generate_error_report()` currently returns the full filesystem path. Change the return value to a **relative URL path** (`uploads/{upload_id}/error_report_{upload_id}.xlsx`) so `upload_registry.error_report_path` stores a URL-ready value.

---

## 📁 Files to Modify

| File | Change |
| :--- | :--- |
| `src/backend/app/main.py` | Add `os.makedirs` + `app.mount("/files/uploads", ...)` |
| `src/backend/app/services/export.py` | Return relative URL path instead of absolute filesystem path |
| `src/frontend/src/components/UploadWizard/UploadWizard.tsx` | Fix download href to use `/files/uploads/...` |

---

## ⚠️ Constraints

- Do **not** expose the entire `/data` volume — mount only `/data/uploads`.
- `StaticFiles` must be mounted **after** all API routers to avoid path conflicts.
- No new dependencies required (`fastapi.staticfiles` is bundled with FastAPI).
