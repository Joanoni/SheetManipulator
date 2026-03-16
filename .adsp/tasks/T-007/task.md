# T-007 — Frontend: Upload Wizard + Schema Mapping UI

> **Layer:** Frontend
> **Dependencies:** T-003, T-004
> **Complexity:** High
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Build the ingestion flow as a multi-step wizard in the React frontend. The wizard guides the user through: (1) uploading an `.xlsx` file, (2) selecting worksheets, (3) defining the schema (table name + column mappings), and (4) triggering background processing with live status polling. The current [`src/frontend/src/App.tsx`](src/frontend/src/App.tsx) is a placeholder — this task replaces it with a routed application shell and implements the `IngestionPage`.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | App renders a top navigation bar with links: "Ingest" and "Manage" | Both links visible on all pages |
| AC-2 | Step 1: User can drag-and-drop or click to select a `.xlsx` file | File input accepts `.xlsx` only |
| AC-3 | Step 1: On file select, `POST /api/upload` is called; `upload_id` is stored in component state | Network tab shows POST request |
| AC-4 | Step 2: Worksheet list is fetched from `GET /api/uploads/{upload_id}/worksheets`; user selects one | Checkboxes or radio buttons for each sheet name |
| AC-5 | Step 3: Schema form renders one row per column with fields: `display_name`, `column_system_name`, `data_type` (select), `is_mandatory` (checkbox), `is_primary_key` (checkbox), `column_order` (auto-incremented, editable) | All fields present and functional |
| AC-6 | Step 3: `POST /api/schemas` is called on "Save Schema" — success advances to Step 4 | Schema saved before processing |
| AC-7 | Step 4: `POST /api/uploads/{upload_id}/process` is called with `{worksheet_name, table_system_name}` | Processing triggered |
| AC-8 | Step 4: Status is polled every 2 seconds via `GET /api/uploads/{upload_id}/status` until `status !== "validating"` | Polling stops on terminal state |
| AC-9 | On `status = "error"`: display error message and a download link for the error report | Link points to error report path |
| AC-10 | On `status = "ingested"`: display success message with a "Go to Manage" button | Button navigates to `/manage` |
| AC-11 | All API errors display a user-friendly toast or inline error message | No unhandled promise rejections |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. Install `react-router-dom`

```bash
cd src/frontend && npm install react-router-dom
```

Add type definitions:
```bash
npm install -D @types/react-router-dom
```

### 2. Application Shell — `src/frontend/src/App.tsx`

Replace the placeholder with a routed shell:

```tsx
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import IngestionPage from './pages/IngestionPage'
import ManagePage from './pages/ManagePage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex gap-6">
          <span className="font-bold text-gray-800 text-lg">SheetManipulator</span>
          <NavLink to="/" className={({ isActive }) => isActive ? 'text-blue-600 font-medium' : 'text-gray-600'}>
            Ingest
          </NavLink>
          <NavLink to="/manage" className={({ isActive }) => isActive ? 'text-blue-600 font-medium' : 'text-gray-600'}>
            Manage
          </NavLink>
        </nav>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<IngestionPage />} />
            <Route path="/manage" element={<ManagePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
```

### 3. Axios API Client — `src/frontend/src/api/client.ts`

```ts
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
})
```

### 4. Typed API Functions — `src/frontend/src/api/ingestion.ts`

```ts
import { api } from './client'

export const uploadFile = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<{ upload_id: string }>('/api/upload', form)
}

export const getWorksheets = (uploadId: string) =>
  api.get<{ worksheets: string[] }>(`/api/uploads/${uploadId}/worksheets`)

export const processUpload = (uploadId: string, worksheetName: string, tableSystemName: string) =>
  api.post(`/api/uploads/${uploadId}/process`, {
    worksheet_name: worksheetName,
    table_system_name: tableSystemName,
  })

export const getUploadStatus = (uploadId: string) =>
  api.get<{ status: string; error_report_path: string | null }>(
    `/api/uploads/${uploadId}/status`
  )
```

### 5. Typed API Functions — `src/frontend/src/api/schema.ts`

```ts
import { api } from './client'

export interface ColumnCreate {
  column_system_name: string
  display_name: string
  data_type: 'String' | 'Integer' | 'Float' | 'Boolean' | 'Date'
  is_mandatory: boolean
  is_primary_key: boolean
  column_order: number
}

export interface SchemaCreate {
  table_system_name: string
  columns: ColumnCreate[]
}

export const createSchema = (payload: SchemaCreate) =>
  api.post('/api/schemas', payload)
```

### 6. Upload Wizard Component — `src/frontend/src/components/UploadWizard/UploadWizard.tsx`

Implement as a controlled multi-step component with local state:

```tsx
type Step = 1 | 2 | 3 | 4

interface WizardState {
  step: Step
  uploadId: string | null
  worksheets: string[]
  selectedSheet: string | null
  tableSystemName: string
  columns: ColumnCreate[]
  status: string | null
  errorReportPath: string | null
  error: string | null
}
```

**Step 1 — File Upload:**
- `<input type="file" accept=".xlsx" />` inside a styled drop zone div.
- On change: call `uploadFile(file)` → store `upload_id` → advance to Step 2.
- Show loading spinner during upload.

**Step 2 — Worksheet Selection:**
- On mount (when `uploadId` is set): call `getWorksheets(uploadId)`.
- Render radio buttons for each worksheet name.
- "Next" button advances to Step 3.

**Step 3 — Schema Definition:**
- Input: `table_system_name` (text, validated against `^[a-z][a-z0-9_]*$` client-side).
- Dynamic column rows: each row has `display_name`, `column_system_name`, `data_type` (select), `is_mandatory` (checkbox), `is_primary_key` (checkbox).
- "Add Column" button appends a new empty row; `column_order` auto-increments.
- "Remove" button on each row (minimum 1 column enforced).
- "Save Schema & Process" button: calls `createSchema()` then `processUpload()` → advance to Step 4.

**Step 4 — Status Polling:**
- On mount: start polling `getUploadStatus(uploadId)` every 2000ms using `setInterval`.
- Clear interval when `status` is `"ingested"` or `"error"`.
- Show animated progress indicator while `status === "validating"`.
- On `"error"`: show red alert with error report download link.
- On `"ingested"`: show green success card with "Go to Manage" `<Link to="/manage">` button.

### 7. Ingestion Page — `src/frontend/src/pages/IngestionPage.tsx`

```tsx
import UploadWizard from '../components/UploadWizard/UploadWizard'

export default function IngestionPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Import Spreadsheet</h1>
      <UploadWizard />
    </div>
  )
}
```

### 8. Manage Page Stub — `src/frontend/src/pages/ManagePage.tsx`

Create a minimal stub (full implementation in T-008):

```tsx
export default function ManagePage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Manage Data</h1>
      <p className="text-gray-500">Data management interface — coming in T-008.</p>
    </div>
  )
}
```

### 9. Step Progress Indicator Component — `src/frontend/src/components/UploadWizard/StepIndicator.tsx`

```tsx
interface Props { current: number; total: number; labels: string[] }

export default function StepIndicator({ current, total, labels }: Props) {
  // Render horizontal step dots with labels
  // Active step: filled blue circle; completed: checkmark; pending: gray
}
```

### 10. Directory Structure to Create

```
src/frontend/src/
├── api/
│   ├── client.ts
│   ├── ingestion.ts
│   └── schema.ts
├── components/
│   └── UploadWizard/
│       ├── UploadWizard.tsx
│       └── StepIndicator.tsx
└── pages/
    ├── IngestionPage.tsx
    └── ManagePage.tsx       ← stub only
```

</instructions>

---

## 📁 Files to Create / Modify
<files>

| Action | File | Notes |
| :--- | :--- | :--- |
| **Replace** | `src/frontend/src/App.tsx` | Routed shell with NavBar |
| **Create** | `src/frontend/src/api/client.ts` | Axios base client |
| **Create** | `src/frontend/src/api/ingestion.ts` | Upload/process API calls |
| **Create** | `src/frontend/src/api/schema.ts` | Schema creation API call |
| **Create** | `src/frontend/src/components/UploadWizard/UploadWizard.tsx` | 4-step wizard |
| **Create** | `src/frontend/src/components/UploadWizard/StepIndicator.tsx` | Progress indicator |
| **Create** | `src/frontend/src/pages/IngestionPage.tsx` | Page wrapper |
| **Create** | `src/frontend/src/pages/ManagePage.tsx` | Stub for T-008 |
| **Modify** | `src/frontend/package.json` | Add `react-router-dom` dependency |

</files>

---

## 🚫 Out of Scope
<out_of_scope>

- DataTable CRUD interface (T-008).
- Audit log viewer (T-008).
- Multi-worksheet batch processing (single sheet per upload session).
- Schema editing after creation (immutable by design per OQ-01).

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T22:43:00Z.*
