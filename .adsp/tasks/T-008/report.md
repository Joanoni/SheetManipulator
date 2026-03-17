# T-008 Implementation Report — Frontend: Dynamic DataTable CRUD + Audit Drawer

> **Status:** ✅ Complete
> **Builder Run:** 2026-03-17T00:00:00Z

---

## Actions Performed

### 1. Fixed `src/frontend/src/api/schema.ts`
- Added `ColumnDefinition` interface (used by T-008 DataTable components).
- Corrected `listSchemas()` return type to `{ tables: string[] }` — matches actual `GET /api/schemas` backend response.
- Corrected `getSchema()` return type to `ColumnDefinition[]` — matches actual `GET /api/schemas/{table_name}` backend response (flat array, not wrapped object).
- Added explicit return type to `createSchema()`.

### 2. Created `src/frontend/src/api/data.ts`
- `PaginatedRows` and `AuditEntry` TypeScript interfaces.
- `listRows(tableName, page, pageSize, includeDeleted)` — `GET /api/tables/{table_name}/rows`.
- `insertRow(tableName, data)` — `POST /api/tables/{table_name}/rows`.
- `updateRow(tableName, rowId, data)` — `PUT /api/tables/{table_name}/rows/{row_id}`.
- `deleteRow(tableName, rowId)` — `DELETE /api/tables/{table_name}/rows/{row_id}`.
- `exportTable(tableName)` — `GET /api/tables/{table_name}/export` with `responseType: 'blob'`.
- `getAuditLog(tableName, rowId?, limit)` — `GET /api/tables/{table_name}/audit`.

### 3. Updated `src/frontend/src/main.tsx`
- Added `QueryClient` instantiation and `QueryClientProvider` wrapper around `<App />`.

### 4. Created `src/frontend/src/components/DataTable/CellEditor.tsx`
- Type-aware cell input component.
- `Boolean` → `<input type="checkbox">`.
- `Integer` → `<input type="number" step="1">`.
- `Float` → `<input type="number" step="any">`.
- `Date` → `<input type="date">`.
- `String` (default) → `<input type="text">`.

### 5. Created `src/frontend/src/components/DataTable/AddRowModal.tsx`
- Modal overlay with form for inserting a new row.
- Initializes form state from `columns` prop (Boolean defaults to `false`, others to `''`).
- Renders one `CellEditor` per column; mandatory columns marked with `*`.
- Calls `insertRow()` on submit → `onSuccess()` → `onClose()`.
- Displays inline error message on failure.

### 6. Created `src/frontend/src/components/AuditDrawer/AuditDrawer.tsx`
- Fixed right-side panel (`fixed inset-y-0 right-0 w-96`).
- Fetches `getAuditLog(tableName, rowId)` via TanStack Query.
- Renders scrollable list of audit entries with `column_name`, `old_value → new_value`, operation badge (color-coded: green=INSERT, blue=UPDATE, red=DELETE), and formatted timestamp.
- Backdrop overlay dims main content; clicking backdrop closes drawer.

### 7. Created `src/frontend/src/components/DataTable/DataTable.tsx`
- Fetches rows via `useQuery` keyed on `[tableName, page]` with `placeholderData` for smooth pagination.
- Toolbar: "Add Row" button + "Export .xlsx" button + row count.
- Dynamic column headers from `columns[].display_name`.
- Read-only rows with Edit / History / Delete action buttons.
- Inline edit mode: row switches to `CellEditor` cells; Save / Cancel buttons.
- Save: builds payload from user columns only (excludes `_row_id`, `is_deleted`, `_upload_id`), calls `updateRow()`, invalidates query cache.
- Delete: `window.confirm()` guard → `deleteRow()` → cache invalidation.
- Export: `exportTable()` → `URL.createObjectURL()` → programmatic `<a download>` click → `revokeObjectURL()`.
- History: sets `auditRowId` → renders `AuditDrawer`.
- Pagination: Previous / Next buttons + "Page X of Y" indicator; disabled at boundaries.

### 8. Replaced `src/frontend/src/pages/ManagePage.tsx`
- Fetches `listSchemas()` → renders table selector buttons (active state highlighted in blue).
- Fetches `getSchema(selectedTable)` when a table is selected.
- Renders `DataTable` when both `selectedTable` and `columns` are available.
- Empty state messages for no tables and no selection.

### 9. TypeScript Validation
- Ran `npx tsc --noEmit` — **exit code 0, zero type errors**.

---

## Deviation Notes

> None. All acceptance criteria implemented as specified. The `listSchemas` and `getSchema` return types in the pre-existing `schema.ts` were mismatched with the actual backend API; corrected as part of this task.

---

## Manual Validation Checklist

| # | Step | Expected Result |
| :--- | :--- | :--- |
| 1 | Start `docker compose up` from `src/` | Both `backend` (port 8000) and `frontend` (port 5173) start without errors |
| 2 | Ingest a `.xlsx` file via the Ingestion page | Upload completes with status `ingested` |
| 3 | Navigate to `/manage` | Page loads; table selector shows the ingested table name |
| 4 | Click the table button | `DataTable` renders with correct `display_name` column headers |
| 5 | Verify row data | Rows display correct values from the ingested file |
| 6 | Click "Edit" on a row | Row switches to inline edit mode; cells become type-appropriate inputs |
| 7 | Modify a cell value and click "Save" | Row updates in place; no full page reload |
| 8 | Click "Cancel" during edit | Row reverts to read-only mode with original values |
| 9 | Click "Delete" on a row | Confirmation dialog appears; on confirm, row disappears from table |
| 10 | Click "+ Add Row" | Modal opens with all schema columns; mandatory columns marked with `*` |
| 11 | Fill form and click "Save Row" | New row appears in table |
| 12 | Click "↓ Export .xlsx" | Browser downloads `{table_name}.xlsx` file |
| 13 | Open downloaded file | Contains correct column headers (`display_name`) and non-deleted rows |
| 14 | Click "History" on a row | Audit drawer slides in from right with audit entries for that row |
| 15 | Verify audit entries | Shows `column_name`, `old_value → new_value`, operation badge, timestamp |
| 16 | Click backdrop or × to close drawer | Drawer closes; main content is interactive again |
| 17 | Navigate to page 2 (if > 50 rows) | "Next →" button fetches next page; "← Previous" returns to page 1 |
| 18 | Verify Boolean column | Displays ✓/✗ in read mode; checkbox in edit mode |
| 19 | Verify Date column | Displays date string in read mode; date picker in edit mode |
| 20 | Verify Integer/Float column | Displays number in read mode; number input in edit mode |
