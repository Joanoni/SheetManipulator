# T-007 Implementation Report — Frontend: Upload Wizard + Schema Mapping UI

> **Builder Run:** 2026-03-16T23:23:00Z
> **Status:** ✅ Complete

---

## Actions Performed

### 1. Dependency Installation
- Ran `npm install react-router-dom` inside `src/frontend/` — added 4 packages (react-router, react-router-dom, @remix-run/router, turbo-stream).

### 2. API Layer
| File | Action | Notes |
| :--- | :--- | :--- |
| `src/frontend/src/api/client.ts` | Created | Axios instance with `VITE_API_URL` base URL |
| `src/frontend/src/api/ingestion.ts` | Created | `uploadFile`, `getWorksheets`, `processUpload`, `getUploadStatus` typed functions |
| `src/frontend/src/api/schema.ts` | Created | `createSchema`, `listSchemas`, `getSchema` + `ColumnCreate`, `SchemaCreate`, `ColumnDefinitionRead`, `SchemaRead` interfaces |

### 3. Components
| File | Action | Notes |
| :--- | :--- | :--- |
| `src/frontend/src/components/UploadWizard/StepIndicator.tsx` | Created | Horizontal step progress bar; completed steps show checkmark, active step shows blue ring, pending steps gray |
| `src/frontend/src/components/UploadWizard/UploadWizard.tsx` | Created | Full 4-step wizard with local state, drag-and-drop upload, worksheet radio selection, dynamic column schema builder, status polling |

### 4. Pages
| File | Action | Notes |
| :--- | :--- | :--- |
| `src/frontend/src/pages/IngestionPage.tsx` | Created | Thin wrapper rendering `<UploadWizard />` |
| `src/frontend/src/pages/ManagePage.tsx` | Created | Stub placeholder for T-008 |

### 5. Application Shell
- Replaced `src/frontend/src/App.tsx` — `BrowserRouter` + `Routes` with `/` → `IngestionPage` and `/manage` → `ManagePage`; top nav with `NavLink` active-state styling.

### 6. TypeScript Validation
- `npx tsc --noEmit` — exit code 0, zero type errors.

---

## Acceptance Criteria Verification

| # | Criterion | Status |
| :--- | :--- | :--- |
| AC-1 | Top nav with "Ingest" and "Manage" NavLinks | ✅ Implemented in `App.tsx` |
| AC-2 | Drag-and-drop / click file input, `.xlsx` only | ✅ `accept=".xlsx"` + drag handlers |
| AC-3 | `POST /api/upload` on file select; `upload_id` stored in state | ✅ `uploadFile()` → `state.uploadId` |
| AC-4 | Worksheet list fetched; radio button selection | ✅ `getWorksheets()` on upload success; radio buttons |
| AC-5 | Schema form: all required fields per column | ✅ `display_name`, `column_system_name`, `data_type`, `is_mandatory`, `is_primary_key`, `column_order` |
| AC-6 | `POST /api/schemas` on "Save Schema" | ✅ `createSchema()` called before `processUpload()` |
| AC-7 | `POST /api/uploads/{id}/process` triggered | ✅ `processUpload()` called after schema save |
| AC-8 | Status polled every 2s; stops on terminal state | ✅ `setInterval(2000)` cleared on `ingested`/`error` |
| AC-9 | Error state: message + download link | ✅ Red alert card with `<a download>` link |
| AC-10 | Success state: green card + "Go to Manage" button | ✅ `<Link to="/manage">` button |
| AC-11 | API errors show toast/inline message | ✅ Toast state + inline error display |

---

## Manual Validation Checklist

- [ ] Run `docker compose up` from `src/` — both services start without errors.
- [ ] Navigate to `http://localhost:5173` — SheetManipulator nav bar visible with "Ingest" and "Manage" links.
- [ ] "Ingest" link is active (blue) on `/`; "Manage" link is active on `/manage`.
- [ ] On `/manage`, stub text "Data management interface — coming in T-008." is displayed.
- [ ] On `/`, drag a non-`.xlsx` file onto the drop zone — toast error "Only .xlsx files are accepted." appears.
- [ ] Upload a valid `.xlsx` file — spinner shows during upload; wizard advances to Step 2.
- [ ] Step 2 shows worksheet names as radio buttons; selecting one and clicking "Next →" advances to Step 3.
- [ ] Step 3 shows table system name input and one default column row with all 5 fields.
- [ ] Entering an invalid table name (e.g. `123abc`) and clicking "Save Schema & Process" shows inline validation error.
- [ ] Adding columns via "+ Add Column" appends a new row; removing with "×" removes it (minimum 1 enforced).
- [ ] Saving a valid schema advances to Step 4 with spinning progress indicator.
- [ ] On successful ingestion, green success card appears with "Go to Manage →" button that navigates to `/manage`.
- [ ] On validation failure, red error card appears with "Download Error Report" link.
