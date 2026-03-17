# T-011 Report — Upload History Page

> **Status:** ✅ Complete
> **Builder Run:** 2026-03-17T01:38:00Z

---

## Actions Performed

| File | Change |
| :--- | :--- |
| `src/backend/app/routers/upload.py` | Added `GET /api/uploads` list endpoint before path-param routes |
| `src/frontend/src/api/ingestion.ts` | Added `UploadStatus` interface + `listUploads()` function; tightened `getUploadStatus` return type to `UploadStatus` |
| `src/frontend/src/pages/HistoryPage.tsx` | **New file** — upload history table with auto-refresh |
| `src/frontend/src/App.tsx` | Added `HistoryPage` import, `/history` route, and "History" `NavLink` |

---

## Implementation Details

### Backend — `GET /api/uploads`
- Inserted **before** `GET /api/uploads/{upload_id}/worksheets` to avoid FastAPI path-matching conflict.
- Returns `list[UploadRegistryRead]` ordered by `timestamp DESC`.
- No pagination (single-tenant, < 1,000 records expected).

### Frontend — `UploadStatus` interface
- Defined in `ingestion.ts` with fields: `upload_id`, `original_filename`, `timestamp`, `status` (union literal), `error_report_path`.
- `getUploadStatus` return type tightened from `{ status: string; error_report_path: string | null }` to `UploadStatus`.

### Frontend — `HistoryPage.tsx`
- `useQuery` with `queryKey: ['uploads']` and `queryFn` calling `listUploads().then(r => r.data)`.
- `refetchInterval` callback: returns `5000` if any row has `status === 'validating' || status === 'pending'`, otherwise `false` (AC-5).
- Color-coded `StatusBadge` component (inline): gray=pending, yellow=validating, red=error, green=ingested (AC-3).
- Upload ID column truncated to `{first8}…{last4}` with full ID in `title` tooltip (AC-2).
- Error report column: `⬇ Error Report` anchor with `href="${VITE_API_URL}/files/${error_report_path}"` and `download` attribute (AC-4).
- Empty state: "No uploads yet." centered message (AC-7).
- Loading and error states handled with appropriate messages.

### Frontend — `App.tsx`
- Extracted `navClass` helper to eliminate repeated inline function (DRY).
- Added `<NavLink to="/history">History</NavLink>` in nav (AC-6).
- Added `<Route path="/history" element={<HistoryPage />} />` in routes (AC-6).

---

## TypeScript Validation

```
npx tsc --noEmit → exit code 0, zero type errors
```

---

## Manual Validation Checklist

| # | Step | Expected Result |
| :--- | :--- | :--- |
| 1 | `docker compose up --build` in `src/` | Both services start without errors |
| 2 | Navigate to `http://localhost:5173` | Top nav shows: Ingest · Manage · **History** |
| 3 | Click "History" in nav | URL changes to `/history` |
| 4 | No uploads yet | "No uploads yet." message displayed |
| 5 | Upload a valid `.xlsx` via Ingest page | Upload record appears in History with `status=pending` then `ingested` |
| 6 | Upload an invalid `.xlsx` | History row shows `status=error` (red badge) with "⬇ Error Report" link |
| 7 | Click "⬇ Error Report" | Browser downloads the error report `.xlsx` file |
| 8 | While upload is `validating` | Page auto-refreshes every 5 seconds |
| 9 | After upload reaches terminal state | Auto-refresh stops (no more polling) |
| 10 | `GET http://localhost:8000/api/uploads` | Returns JSON array ordered by `timestamp DESC` |
| 11 | Filename column | Shows original `.xlsx` filename |
| 12 | Upload ID column | Shows truncated ID (e.g. `abc12345…ef01`) with full ID on hover |
| 13 | Timestamp column | Shows human-readable local date/time |
| 14 | Status badges | pending=gray, validating=yellow, error=red, ingested=green |
| 15 | Multiple uploads | All rows shown, newest first |
