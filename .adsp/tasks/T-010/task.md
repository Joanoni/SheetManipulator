# T-010 — Schema Column Display Name Edit UI

> **Layer:** Frontend
> **Complexity:** Medium
> **Depends on:** T-004, T-008
> **Status:** Pending

---

## 🎯 Objective

The backend exposes `PUT /api/schemas/{table_name}/columns/{column_id}` to update a column's `display_name`.
No frontend surface exists to invoke this endpoint. Users cannot rename columns after ingestion.

Implement an inline edit UI in `ManagePage.tsx` that allows users to rename column display names directly from the Manage page.

---

## 📋 Acceptance Criteria

| # | Criterion |
| :--- | :--- |
| AC-1 | A "Schema" panel is visible on `ManagePage` when a table is selected, showing all columns with their `display_name`, `column_system_name`, `data_type`, `is_mandatory`, `is_primary_key` |
| AC-2 | Each column row has an inline "Edit" button that switches the `display_name` cell to an `<input>` |
| AC-3 | Saving calls `PUT /api/schemas/{table_name}/columns/{column_id}` with `{ display_name: newValue }` |
| AC-4 | On success, the column list re-fetches and the `DataTable` header updates (invalidate `['schema', tableName]` query) |
| AC-5 | `column_system_name` and `data_type` are displayed as read-only — they cannot be edited |
| AC-6 | Empty `display_name` is rejected client-side with an inline error message |
| AC-7 | A loading spinner is shown on the Save button while the request is in-flight |

---

## 🔧 Implementation Notes

### New API function — `src/frontend/src/api/schema.ts`

Add:
```typescript
export interface ColumnDisplayNameUpdate {
  display_name: string
}

export function updateColumnDisplayName(
  tableName: string,
  columnId: number,
  body: ColumnDisplayNameUpdate
) {
  return client.put<ColumnDefinition>(
    `/api/schemas/${tableName}/columns/${columnId}`,
    body
  )
}
```

### New Component — `src/frontend/src/components/SchemaPanel/SchemaPanel.tsx`

```
Props:
  tableName: string
  columns: ColumnDefinition[]
  onSchemaUpdated: () => void   // triggers query invalidation in parent
```

Renders a compact table:
| Display Name (editable) | System Name (read-only) | Type | Required | PK |
| :--- | :--- | :--- | :--- | :--- |

Inline edit state: `editingId: number | null`, `editValue: string`.

### `ManagePage.tsx` update

- Add a collapsible "⚙ Schema" section above the `DataTable`.
- Pass `onSchemaUpdated` callback that calls `queryClient.invalidateQueries(['schema', selectedTable])`.

---

## 📁 Files to Create / Modify

| File | Change |
| :--- | :--- |
| `src/frontend/src/api/schema.ts` | Add `updateColumnDisplayName()` + `ColumnDisplayNameUpdate` interface |
| `src/frontend/src/components/SchemaPanel/SchemaPanel.tsx` | **New file** — inline column rename UI |
| `src/frontend/src/pages/ManagePage.tsx` | Import and render `SchemaPanel` above `DataTable` |

---

## ⚠️ Constraints

- `column_system_name` is **immutable** — never render it as an editable field.
- The `PUT` endpoint returns `HTTP 400` if `display_name` is empty — handle this error and display it inline.
- Do not introduce any new npm dependencies.
