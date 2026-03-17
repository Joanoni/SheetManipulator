# T-011 — Upload History Page

> **Layer:** Frontend + Backend
> **Complexity:** Low
> **Depends on:** T-001, T-002, T-003
> **Status:** Pending

---

## 🎯 Objective

Blueprint Goal G-03 requires preserving original files and maintaining a full audit trail.
Currently there is no way to view past uploads, their statuses, or re-download error reports.

Implement:
1. A `GET /api/uploads` backend endpoint that lists all `upload_registry` records.
2. A new `HistoryPage.tsx` frontend page that displays the upload history table.
3. A nav link in `App.tsx` to reach the history page.

---

## 📋 Acceptance Criteria

| # | Criterion |
| :--- | :--- |
| AC-1 | `GET /api/uploads` returns a list of `UploadRegistryRead` objects ordered by `timestamp DESC` |
| AC-2 | `HistoryPage.tsx` renders a table with columns: Filename, Upload ID (truncated), Timestamp, Status badge, Error Report link |
| AC-3 | Status badges are color-coded: `pending`=gray, `validating`=yellow, `error`=red, `ingested`=green |
| AC-4 | If `error_report_path` is set, an "⬇ Error Report" link is shown pointing to `/files/uploads/...` (from T-009) |
| AC-5 | The page auto-refreshes every 5 seconds if any row has `status = 'validating'` or `status = 'pending'` |
| AC-6 | A "History" `NavLink` is added to the top nav in `App.tsx` at route `/history` |
| AC-7 | Empty state: "No uploads yet." message when the list is empty |

---

## 🔧 Implementation Notes

### Backend — `src/backend/app/routers/upload.py`

Add a new route **before** the existing routes:

```python
@router.get("/uploads", response_model=list[UploadRegistryRead])
async def list_uploads(
    db: AsyncSession = Depends(get_db),
) -> list[UploadRegistryRead]:
    result = await db.execute(
        select(UploadRegistry).order_by(UploadRegistry.timestamp.desc())
    )
    return result.scalars().all()
```

### Frontend — `src/frontend/src/api/ingestion.ts`

Add:
```typescript
export function listUploads() {
  return client.get<UploadStatus[]>('/api/uploads')
}
```

Where `UploadStatus` interface already exists (or add it):
```typescript
export interface UploadStatus {
  upload_id: string
  original_filename: string
  timestamp: string
  status: 'pending' | 'validating' | 'error' | 'ingested'
  error_report_path: string | null
}
```

### New Page — `src/frontend/src/pages/HistoryPage.tsx`

- Uses `useQuery` with `refetchInterval: (data) => data?.some(r => r.status === 'validating' || r.status === 'pending') ? 5000 : false`
- Status badge component (inline, no separate file needed): `<span className={badgeClass[status]}>{status}</span>`

### `App.tsx` update

Add route and NavLink:
```tsx
<NavLink to="/history">History</NavLink>
// ...
<Route path="/history" element={<HistoryPage />} />
```

---

## 📁 Files to Create / Modify

| File | Change |
| :--- | :--- |
| `src/backend/app/routers/upload.py` | Add `GET /api/uploads` list endpoint |
| `src/frontend/src/api/ingestion.ts` | Add `listUploads()` + `UploadStatus` interface |
| `src/frontend/src/pages/HistoryPage.tsx` | **New file** — upload history table |
| `src/frontend/src/App.tsx` | Add `/history` route + NavLink |

---

## ⚠️ Constraints

- The new `GET /api/uploads` route must be added **before** `GET /api/uploads/{upload_id}/worksheets` in the router file to avoid path conflicts with FastAPI's route matching.
- Do not paginate — the upload list is expected to be small (< 1,000 records for single-tenant use).
- Do not introduce any new npm dependencies.
