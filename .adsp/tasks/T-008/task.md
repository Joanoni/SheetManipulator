# T-008 — Frontend: Dynamic DataTable CRUD + Audit Drawer

> **Layer:** Frontend
> **Dependencies:** T-005, T-006
> **Complexity:** High
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Replace the `ManagePage` stub (created in T-007) with a fully functional data management interface. The page renders a table selector, a dynamic `DataTable` component driven by `schema_definitions` metadata, inline row editing, soft-delete, export-to-xlsx, and an `AuditDrawer` side panel that shows the audit trail for a selected row. All column types, headers, and cell editors are derived from the API — no hardcoded field names.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `ManagePage` fetches `GET /api/schemas` and renders a dropdown/tab selector for each available table | Selector shows all ingested table names |
| AC-2 | Selecting a table fetches `GET /api/schemas/{table_name}` and renders column headers using `display_name` | Headers match schema `display_name` values |
| AC-3 | `DataTable` fetches `GET /api/tables/{table_name}/rows` with pagination (page, page_size) | Rows render with correct values |
| AC-4 | Pagination controls (Previous / Next / page indicator) are functional | Page changes fetch new data |
| AC-5 | Each row has an "Edit" button that switches the row to inline edit mode | Cells become inputs matching their `data_type` |
| AC-6 | Saving an edited row calls `PUT /api/tables/{table_name}/rows/{row_id}` | Row updates without full page reload |
| AC-7 | Each row has a "Delete" button that calls `DELETE /api/tables/{table_name}/rows/{row_id}` after confirmation | Row disappears from table (soft-deleted) |
| AC-8 | "Add Row" button opens a modal form with all schema columns; submitting calls `POST /api/tables/{table_name}/rows` | New row appears in table |
| AC-9 | "Export" button calls `GET /api/tables/{table_name}/export` and triggers browser file download | `.xlsx` file downloaded |
| AC-10 | Clicking a row's "History" button opens the `AuditDrawer` with audit entries for that `row_id` | Drawer shows `column_name`, `old_value`, `new_value`, `timestamp` |
| AC-11 | `AuditDrawer` fetches `GET /api/tables/{table_name}/audit?row_id={row_id}` | Entries ordered newest-first |
| AC-12 | Cell editors are type-appropriate: text for `String`, number for `Integer`/`Float`, date picker for `Date`, checkbox for `Boolean` | Input types match data types |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. Typed API Functions — `src/frontend/src/api/data.ts`

```ts
import { api } from './client'

export interface PaginatedRows {
  items: Record<string, unknown>[]
  total: number
  page: number
  page_size: number
}

export const listRows = (
  tableName: string,
  page = 1,
  pageSize = 50,
  includeDeleted = false
) =>
  api.get<PaginatedRows>(`/api/tables/${tableName}/rows`, {
    params: { page, page_size: pageSize, include_deleted: includeDeleted },
  })

export const insertRow = (tableName: string, data: Record<string, unknown>) =>
  api.post(`/api/tables/${tableName}/rows`, { data })

export const updateRow = (
  tableName: string,
  rowId: string,
  data: Record<string, unknown>
) => api.put(`/api/tables/${tableName}/rows/${rowId}`, { data })

export const deleteRow = (tableName: string, rowId: string) =>
  api.delete(`/api/tables/${tableName}/rows/${rowId}`)

export const exportTable = (tableName: string) =>
  api.get(`/api/tables/${tableName}/export`, { responseType: 'blob' })

export const getAuditLog = (tableName: string, rowId?: string, limit = 100) =>
  api.get(`/api/tables/${tableName}/audit`, {
    params: { row_id: rowId, limit },
  })
```

### 2. Typed API Functions — `src/frontend/src/api/schema.ts` (extend)

Add to the existing file from T-007:

```ts
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

export const listSchemas = () =>
  api.get<{ tables: string[] }>('/api/schemas')

export const getSchema = (tableName: string) =>
  api.get<ColumnDefinition[]>(`/api/schemas/${tableName}`)
```

### 3. Cell Editor Component — `src/frontend/src/components/DataTable/CellEditor.tsx`

Renders the correct input type based on `data_type`:

```tsx
interface Props {
  dataType: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  value: unknown
  onChange: (value: unknown) => void
}

export default function CellEditor({ dataType, value, onChange }: Props) {
  switch (dataType) {
    case 'Boolean':
      return <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />
    case 'Integer':
      return <input type="number" step="1" value={String(value ?? '')} onChange={e => onChange(parseInt(e.target.value))} className="w-full border rounded px-2 py-1" />
    case 'Float':
      return <input type="number" step="any" value={String(value ?? '')} onChange={e => onChange(parseFloat(e.target.value))} className="w-full border rounded px-2 py-1" />
    case 'Date':
      return <input type="date" value={String(value ?? '')} onChange={e => onChange(e.target.value)} className="w-full border rounded px-2 py-1" />
    default:
      return <input type="text" value={String(value ?? '')} onChange={e => onChange(e.target.value)} className="w-full border rounded px-2 py-1" />
  }
}
```

### 4. DataTable Component — `src/frontend/src/components/DataTable/DataTable.tsx`

```tsx
interface Props {
  tableName: string
  columns: ColumnDefinition[]
}
```

**State:**
```ts
const [rows, setRows] = useState<Record<string, unknown>[]>([])
const [total, setTotal] = useState(0)
const [page, setPage] = useState(1)
const [editingRowId, setEditingRowId] = useState<string | null>(null)
const [editBuffer, setEditBuffer] = useState<Record<string, unknown>>({})
const [auditRowId, setAuditRowId] = useState<string | null>(null)  // triggers AuditDrawer
const [showAddModal, setShowAddModal] = useState(false)
```

**Data fetching:** Use `useEffect` + `useQuery` (TanStack Query v5) keyed on `[tableName, page]`.

**Render structure:**
```
<div>
  <toolbar>  ← "Add Row" button + "Export" button
  <table>
    <thead>  ← display_name headers + "Actions" column
    <tbody>
      {rows.map(row =>
        editingRowId === row._row_id
          ? <EditableRow ... />   ← inline edit mode
          : <ReadOnlyRow ... />   ← normal display
      )}
    </tbody>
  </table>
  <PaginationBar total={total} page={page} pageSize={50} onPageChange={setPage} />
  {auditRowId && <AuditDrawer tableName={tableName} rowId={auditRowId} onClose={() => setAuditRowId(null)} />}
  {showAddModal && <AddRowModal columns={columns} tableName={tableName} onClose={() => setShowAddModal(false)} onSuccess={refetch} />}
</div>
```

**Edit flow:**
1. "Edit" button: `setEditingRowId(row._row_id)`, `setEditBuffer({...row})`.
2. User edits cells via `CellEditor`.
3. "Save": call `updateRow(tableName, row._row_id, editBuffer)` → refetch → `setEditingRowId(null)`.
4. "Cancel": `setEditingRowId(null)`.

**Delete flow:**
1. "Delete" button: `window.confirm("Delete this row?")`.
2. On confirm: call `deleteRow(tableName, row._row_id)` → refetch.

**Export flow:**
1. "Export" button: call `exportTable(tableName)`.
2. Create object URL from blob → trigger `<a download>` click → revoke URL.

### 5. Audit Drawer — `src/frontend/src/components/AuditDrawer/AuditDrawer.tsx`

```tsx
interface Props {
  tableName: string
  rowId: string
  onClose: () => void
}
```

- Renders as a fixed right-side panel (`fixed inset-y-0 right-0 w-96 bg-white shadow-xl`).
- Fetches `getAuditLog(tableName, rowId)` on mount.
- Renders a scrollable list of audit entries:
  - Each entry: `[timestamp] column_name: old_value → new_value (operation)`.
- "Close" button (×) calls `onClose`.
- Overlay backdrop dims the main content.

### 6. Add Row Modal — `src/frontend/src/components/DataTable/AddRowModal.tsx`

```tsx
interface Props {
  tableName: string
  columns: ColumnDefinition[]
  onClose: () => void
  onSuccess: () => void
}
```

- Renders a modal overlay with a form.
- One `CellEditor` per column (mandatory columns marked with `*`).
- "Submit": calls `insertRow(tableName, formData)` → `onSuccess()` → `onClose()`.
- "Cancel": `onClose()`.

### 7. Manage Page — `src/frontend/src/pages/ManagePage.tsx`

Replace the T-007 stub:

```tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listSchemas, getSchema } from '../api/schema'
import DataTable from '../components/DataTable/DataTable'

export default function ManagePage() {
  const [selectedTable, setSelectedTable] = useState<string | null>(null)

  const { data: schemasData } = useQuery({
    queryKey: ['schemas'],
    queryFn: () => listSchemas().then(r => r.data),
  })

  const { data: columns } = useQuery({
    queryKey: ['schema', selectedTable],
    queryFn: () => getSchema(selectedTable!).then(r => r.data),
    enabled: !!selectedTable,
  })

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Manage Data</h1>

      {/* Table selector */}
      <div className="mb-4 flex gap-2 flex-wrap">
        {schemasData?.tables.map(t => (
          <button
            key={t}
            onClick={() => setSelectedTable(t)}
            className={`px-4 py-2 rounded border ${selectedTable === t ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {selectedTable && columns && (
        <DataTable tableName={selectedTable} columns={columns} />
      )}

      {!selectedTable && (
        <p className="text-gray-500">Select a table above to manage its data.</p>
      )}
    </div>
  )
}
```

### 8. QueryClient Setup — `src/frontend/src/main.tsx`

Verify `QueryClientProvider` wraps the app. If not present, add:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
)
```

### 9. Directory Structure to Create

```
src/frontend/src/
├── api/
│   └── data.ts                          ← new
├── components/
│   ├── DataTable/
│   │   ├── DataTable.tsx                ← new
│   │   ├── CellEditor.tsx               ← new
│   │   └── AddRowModal.tsx              ← new
│   └── AuditDrawer/
│       └── AuditDrawer.tsx              ← new
└── pages/
    └── ManagePage.tsx                   ← replace stub
```

</instructions>

---

## 📁 Files to Create / Modify
<files>

| Action | File | Notes |
| :--- | :--- | :--- |
| **Create** | `src/frontend/src/api/data.ts` | CRUD + audit + export API calls |
| **Modify** | `src/frontend/src/api/schema.ts` | Add `listSchemas`, `getSchema`, `ColumnDefinition` type |
| **Create** | `src/frontend/src/components/DataTable/DataTable.tsx` | Main grid component |
| **Create** | `src/frontend/src/components/DataTable/CellEditor.tsx` | Type-aware cell input |
| **Create** | `src/frontend/src/components/DataTable/AddRowModal.tsx` | Insert row modal |
| **Create** | `src/frontend/src/components/AuditDrawer/AuditDrawer.tsx` | Audit side panel |
| **Replace** | `src/frontend/src/pages/ManagePage.tsx` | Full implementation (replaces T-007 stub) |
| **Verify/Modify** | `src/frontend/src/main.tsx` | Ensure `QueryClientProvider` wraps app |

</files>

---

## 🚫 Out of Scope
<out_of_scope>

- Schema editing UI (column `display_name` update via `PUT /api/schemas/{table}/columns/{id}`).
- Showing soft-deleted rows toggle (always hidden by default; `include_deleted` param not exposed in UI).
- Multi-table bulk operations.
- Authentication or user identity display.

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T22:43:00Z.*
