# T-009 — Static File Serving for Error Reports — Implementation Report

> **Status:** ✅ Complete
> **Builder Run:** 2026-03-17T01:31:00Z

---

## Summary

Mounted `/data/uploads` as a FastAPI `StaticFiles` directory at `/files/uploads`, enabling the frontend to download error reports via HTTP. Updated `generate_error_report()` to return a relative URL path instead of an absolute filesystem path, and fixed the `UploadWizard` download href to use the new `/files/` prefix.

---

## Files Modified

| File | Change |
| :--- | :--- |
| `src/backend/app/main.py` | Added `import os`, `from fastapi.staticfiles import StaticFiles`, `_UPLOADS_DIR` constant, `os.makedirs(_UPLOADS_DIR, exist_ok=True)`, and `app.mount("/files/uploads", StaticFiles(...), name="uploads")` after all API routers |
| `src/backend/app/services/export.py` | Changed `generate_error_report()` return value from absolute path (`/data/uploads/{id}/error_report_{id}.xlsx`) to relative URL path (`uploads/{id}/error_report_{id}.xlsx`) |
| `src/frontend/src/components/UploadWizard/UploadWizard.tsx` | Fixed error report download `href` from `.../${state.errorReportPath}` to `.../files/${state.errorReportPath}` |

---

## Acceptance Criteria Verification

| # | Criterion | Status |
| :--- | :--- | :--- |
| AC-1 | `GET /files/uploads/{upload_id}/error_report_{upload_id}.xlsx` returns the file | ✅ StaticFiles mount serves files from `/data/uploads` at `/files/uploads` |
| AC-2 | `main.py` mounts `StaticFiles(directory="/data/uploads", html=False)` at `/files/uploads` | ✅ Implemented with `html=False` default |
| AC-3 | `UploadWizard.tsx` error report download href uses `/files/` prefix | ✅ href now: `${VITE_API_URL}/files/${state.errorReportPath}` |
| AC-4 | `/data/uploads` is created before mounting if it doesn't exist | ✅ `os.makedirs(_UPLOADS_DIR, exist_ok=True)` at module level |
| AC-5 | CORS policy is not broken by the static mount | ✅ `CORSMiddleware` is registered before the static mount; CORS applies to all routes |

---

## URL Construction Flow

```
Backend stores:   upload_registry.error_report_path = "uploads/{id}/error_report_{id}.xlsx"
Frontend builds:  ${VITE_API_URL}/files/uploads/{id}/error_report_{id}.xlsx
FastAPI serves:   GET /files/uploads/{id}/error_report_{id}.xlsx → /data/uploads/{id}/error_report_{id}.xlsx
```

---

## Manual Validation Checklist

1. Start the stack: `docker compose up --build`
2. Upload a `.xlsx` file with intentional type errors (e.g., text in an Integer column).
3. Complete the wizard through Step 3 (define schema with an Integer column).
4. Observe Step 4 polling — status should transition to `error`.
5. Confirm the **Download Error Report** button appears.
6. Click the button — browser should download `error_report_{upload_id}.xlsx`.
7. Open the downloaded file — verify it contains columns: `original_line_index`, `column`, `original_value`, `error_reason`.
8. Verify the download URL in the browser network tab matches: `http://localhost:8000/files/uploads/{upload_id}/error_report_{upload_id}.xlsx`.
9. Directly `GET http://localhost:8000/files/uploads/{upload_id}/error_report_{upload_id}.xlsx` in a browser — should return the file with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
10. Verify `GET http://localhost:8000/health` still returns `{"status": "ok"}` (CORS not broken).
11. Verify `GET http://localhost:8000/api/schemas` still returns correctly (API routes not shadowed by static mount).
12. Attempt `GET http://localhost:8000/files/uploads/nonexistent.xlsx` — should return HTTP 404.
