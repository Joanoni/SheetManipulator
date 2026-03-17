# T-010 Report — Schema Column Display Name Edit UI

> **Status:** ✅ Complete
> **Builder Run:** 2026-03-17T01:34:00Z

---

## Actions Performed

### 1. `src/frontend/src/api/schema.ts` — Extended
- Added `ColumnDisplayNameUpdate` interface: `{ display_name: string }`.
- Added `updateColumnDisplayName(tableName, columnId, body)` function calling `PUT /api/schemas/{table_name}/columns/{column_id}`.

### 2. `src/frontend/src/components/SchemaPanel/SchemaPanel.tsx` — **New file**
- Props: `tableName: string`, `columns: ColumnDefinition[]`, `onSchemaUpdated: () => void`.
- Renders a compact table with columns: **Display Name** (editable), **System Name** (read-only), **Type** (badge), **Required** (✓/—), **PK** (✓/—), **Actions**.
- Inline edit state: `editingId: number | null`, `editValue: string`, `error: string | null`.
- **Edit** button switches the display name cell to an `<input>` with auto-focus.
- Client-side validation: empty `display_name` shows inline error `"Display name cannot be empty."` — no network call made.
- `useMutation` from TanStack Query v5 calls `updateColumnDisplayName()`; on success calls `onSchemaUpdated()` and clears edit state.
- **Loading spinner** (animated SVG) shown on Save button while `mutation.isPending`.
- Server errors surfaced inline below the input field.
- `column_system_name` rendered as read-only monospace text — never editable.
- Keyboard shortcuts: `Enter` to save, `Escape` to cancel.
- Data type badges color-coded: String=gray, Integer=blue, Float=indigo, Boolean=yellow, Date=green.

### 3. `src/frontend/src/pages/ManagePage.tsx` — Updated
- Imported `useQueryClient` and `SchemaPanel`.
- Added `schemaOpen: boolean` state (default `false`); resets to `false` when a different table is selected.
- Added collapsible **"⚙ Schema — {tableName}"** section above `DataTable` with expand/collapse toggle.
- `handleSchemaUpdated()` calls `queryClient.invalidateQueries({ queryKey: ['schema', selectedTable] })` — causes `DataTable` headers to re-fetch updated `display_name` values.

### 4. TypeScript Validation
- Ran `npx tsc --noEmit` — **exit code 0, zero type errors**.

---

## Acceptance Criteria Verification

| # | Criterion | Status |
| :--- | :--- | :--- |
| AC-1 | Schema panel visible on ManagePage when table selected, showing all column metadata | ✅ |
| AC-2 | Each column row has inline Edit button switching display_name cell to `<input>` | ✅ |
| AC-3 | Saving calls `PUT /api/schemas/{table_name}/columns/{column_id}` with `{ display_name }` | ✅ |
| AC-4 | On success, invalidates `['schema', tableName]` query — DataTable headers update | ✅ |
| AC-5 | `column_system_name` and `data_type` displayed as read-only | ✅ |
| AC-6 | Empty `display_name` rejected client-side with inline error message | ✅ |
| AC-7 | Loading spinner shown on Save button while request is in-flight | ✅ |

---

## Manual Validation Checklist

1. [ ] Start the stack: `docker compose -f src/docker-compose.yml up --build`.
2. [ ] Navigate to `http://localhost:5173` → Ingestion page.
3. [ ] Upload a `.xlsx` file, map schema, and complete ingestion.
4. [ ] Navigate to **Manage** page — confirm the ingested table button appears.
5. [ ] Click the table button — confirm the **"⚙ Schema — {tableName}"** collapsible section appears above the DataTable.
6. [ ] Click **▼ Expand** — confirm the schema table renders with all columns showing Display Name, System Name, Type, Required, PK columns.
7. [ ] Confirm `column_system_name` and `data_type` cells have no Edit button and are read-only.
8. [ ] Click **Edit** on any column — confirm the Display Name cell switches to an `<input>` pre-filled with the current value.
9. [ ] Clear the input and click **Save** — confirm inline error `"Display name cannot be empty."` appears and no network request is made.
10. [ ] Type a new display name and click **Save** — confirm the spinner appears on the button during the request.
11. [ ] After save completes, confirm the schema table re-renders with the updated display name.
12. [ ] Confirm the DataTable column header for that column also updates (query invalidation working).
13. [ ] Press **Escape** while editing — confirm edit mode is cancelled without saving.
14. [ ] Press **Enter** while editing — confirm save is triggered.
15. [ ] Switch to a different table — confirm the Schema panel collapses (resets to closed state).
