# SheetManipulator — Technical Specification

> **Derived from:** `.adsp/blueprints/blueprint.md`
> **Architect Run:** 2026-03-16T21:34:15Z

---

## 1. Stack Decision
<stack>

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3.12 + FastAPI | Async-native, BackgroundTasks built-in, strong typing via Pydantic |
| **Frontend** | React 18 + Vite + Tailwind CSS | Fast HMR, utility-first styling, metadata-driven rendering |
| **Database** | SQLite (via SQLAlchemy 2.x async) | Zero-config, file-based, sufficient for single-tenant governance |
| **Spreadsheet I/O** | `openpyxl` | Read/write `.xlsx` without external dependencies |
| **Orchestration** | Docker Compose v2 | Services: `backend`, `frontend` |
| **Data Volume** | Docker named volume → `/data` | Persists `database.sqlite` and `/data/uploads/` |

</stack>

---

## 2. Repository Structure
<structure>

```
src/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, CORS, router registration
│   │   ├── database.py              # SQLAlchemy async engine + session factory
│   │   ├── models/
│   │   │   ├── upload_registry.py   # ORM: upload_registry table
│   │   │   ├── schema_definition.py # ORM: schema_definitions table
│   │   │   ├── audit_log.py         # ORM: audit_log table
│   │   │   └── dynamic_table.py     # Helpers for dynamic table DDL
│   │   ├── routers/
│   │   │   ├── upload.py            # POST /upload, GET /uploads
│   │   │   ├── schema.py            # CRUD /schemas
│   │   │   ├── data.py              # CRUD /tables/{table_name}/rows
│   │   │   └── export.py            # GET /tables/{table_name}/export
│   │   ├── services/
│   │   │   ├── ingestion.py         # Background ingestion pipeline
│   │   │   ├── validation.py        # Validation engine (short-circuit @ 1000)
│   │   │   ├── dynamic_ddl.py       # CREATE TABLE from schema_definitions
│   │   │   └── export.py            # xlsx export from live DB state
│   │   └── schemas/                 # Pydantic request/response models
│   │       ├── upload.py
│   │       ├── schema_definition.py
│   │       ├── data_row.py
│   │       └── audit.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                     # Axios client + typed API hooks
│   │   ├── components/
│   │   │   ├── UploadWizard/        # Step 1: file upload + worksheet selection
│   │   │   ├── SchemaMappingUI/     # Step 2: define columns interactively
│   │   │   ├── DataTable/           # Dynamic CRUD grid
│   │   │   └── AuditDrawer/         # Audit log side panel
│   │   └── pages/
│   │       ├── IngestionPage.tsx
│   │       ├── ManagePage.tsx
│   │       └── AuditPage.tsx
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
└── docker-compose.yml
```

</structure>

---

## 3. Database Schema
<database>

### 3.1 Static Tables (created at startup)

#### `upload_registry`
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `upload_id` | TEXT | PRIMARY KEY (UUID) |
| `original_filename` | TEXT | NOT NULL |
| `timestamp` | DATETIME | NOT NULL, DEFAULT now() |
| `status` | TEXT | NOT NULL — `pending | validating | error | ingested` |
| `error_report_path` | TEXT | NULLABLE |

#### `schema_definitions`
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `table_system_name` | TEXT | NOT NULL |
| `column_system_name` | TEXT | NOT NULL, IMMUTABLE |
| `display_name` | TEXT | NOT NULL |
| `data_type` | TEXT | NOT NULL — `String|Integer|Float|Boolean|Date` |
| `is_mandatory` | BOOLEAN | NOT NULL, DEFAULT FALSE |
| `is_primary_key` | BOOLEAN | NOT NULL, DEFAULT FALSE |
| `column_order` | INTEGER | NOT NULL |
| UNIQUE | (`table_system_name`, `column_system_name`) | — |

#### `audit_log`
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `table_name` | TEXT | NOT NULL |
| `row_id` | TEXT | NOT NULL |
| `column_name` | TEXT | NOT NULL |
| `old_value` | TEXT | NULLABLE |
| `new_value` | TEXT | NULLABLE |
| `operation` | TEXT | NOT NULL — `INSERT|UPDATE|DELETE` |
| `timestamp` | DATETIME | NOT NULL, DEFAULT now() |

### 3.2 Dynamic Tables
- Created at runtime via `dynamic_ddl.py` from `schema_definitions`.
- Every dynamic table includes: `_row_id TEXT PRIMARY KEY`, `is_deleted BOOLEAN DEFAULT FALSE`, `_upload_id TEXT` (FK → `upload_registry`).
- Column names use `column_system_name` — **never mutated after creation**.

</database>

---

## 4. API Contract
<api>

### 4.1 Ingestion

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Multipart upload of `.xlsx`; returns `upload_id` |
| `GET` | `/api/uploads/{upload_id}/worksheets` | List sheet names in uploaded file |
| `POST` | `/api/uploads/{upload_id}/process` | Trigger background ingestion for selected sheets |
| `GET` | `/api/uploads/{upload_id}/status` | Poll ingestion status + error report URL |

### 4.2 Schema Management

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/schemas` | List all table schemas |
| `POST` | `/api/schemas` | Create new table schema + trigger DDL |
| `GET` | `/api/schemas/{table_name}` | Get column definitions for a table |
| `PUT` | `/api/schemas/{table_name}/columns/{column_id}` | Update `display_name` only (system_name immutable) |

### 4.3 Data CRUD

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/tables/{table_name}/rows` | Paginated rows (excludes `is_deleted=true` by default) |
| `POST` | `/api/tables/{table_name}/rows` | Insert row; writes audit entry |
| `PUT` | `/api/tables/{table_name}/rows/{row_id}` | Update row; writes audit entry per changed column |
| `DELETE` | `/api/tables/{table_name}/rows/{row_id}` | Soft delete (`is_deleted=true`); writes audit entry |

### 4.4 Export

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/tables/{table_name}/export` | Stream `.xlsx` of current non-deleted rows |

</api>

---

## 5. Validation Engine Specification
<validation>

- **Trigger:** Called inside `BackgroundTasks` after file is archived to cold storage.
- **Input:** Raw `openpyxl` worksheet rows + `schema_definitions` for the target table.
- **Short-circuit:** Accumulates errors; **halts at 1,000 errors** — does not process further rows.
- **Error Row Format:**

| Field | Source |
| :--- | :--- |
| `original_line_index` | 1-based row number in source sheet |
| `column` | `display_name` of the failing column |
| `original_value` | Raw cell value as string |
| `error_reason` | Human-readable: `"Missing required value"`, `"Expected Integer, got 'abc'"`, etc. |

- **Output:** If errors exist → generate `error_report_{upload_id}.xlsx` → save to `/data/uploads/{upload_id}/` → update `upload_registry.status = 'error'` + `error_report_path`.
- **Success path:** If zero errors → call `dynamic_ddl.py` to ensure table exists → bulk-insert rows → `status = 'ingested'`.

</validation>

---

## 6. Frontend Architecture
<frontend>

### 6.1 Metadata-Driven Rendering
- `DataTable` component fetches `GET /api/schemas/{table_name}` on mount.
- Columns are rendered dynamically from `schema_definitions` — no hardcoded field names.
- Cell editors are typed: text input for `String`, number input for `Integer/Float`, date picker for `Date`, checkbox for `Boolean`.

### 6.2 Upload Wizard Flow
```
Step 1: Drop/select .xlsx file → POST /api/upload
Step 2: Select worksheets from returned list
Step 3: Map schema (table name, column definitions)
Step 4: Submit → POST /api/uploads/{id}/process
Step 5: Poll status → show progress bar or error report download
```

### 6.3 State Management
- Local React state + `useQuery`/`useMutation` (TanStack Query v5) for server state.
- No global store required at this scale.

</frontend>

---

## 7. Docker Compose Architecture
<docker>

```yaml
# Logical service map (not final syntax)
services:
  backend:
    build: ./src/backend
    volumes: [data-volume:/data]
    ports: ["8000:8000"]
    environment: [DATABASE_URL=sqlite+aiosqlite:////data/database.sqlite]

  frontend:
    build: ./src/frontend
    ports: ["5173:5173"]
    environment: [VITE_API_URL=http://localhost:8000]

volumes:
  data-volume:
```

</docker>

---

## 8. Task Decomposition Grid
<task_grid>

| Task ID | Title | Layer | Dependencies | Estimated Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **T-001** | Project Scaffold & Docker Compose | Infra | None | Low |
| **T-002** | Backend Core: DB Models + FastAPI App Factory | Backend | T-001 | Medium |
| **T-003** | Ingestion Pipeline: Upload, Cold Storage, Validation Engine | Backend | T-002 | High |
| **T-004** | Schema Management API + Dynamic DDL | Backend | T-002 | Medium |
| **T-005** | Data CRUD API + Audit Trail | Backend | T-004 | Medium |
| **T-006** | Export Engine (xlsx generation) | Backend | T-005 | Low |
| **T-007** | Frontend: Upload Wizard + Schema Mapping UI | Frontend | T-003, T-004 | High |
| **T-008** | Frontend: Dynamic DataTable CRUD + Audit Drawer | Frontend | T-005, T-006 | High |

> **Next 4 tasks for Builder:** T-001 → T-002 → T-003 → T-004

</task_grid>

---

*Specification authored by ADSP-Architect on 2026-03-16T21:34:15Z.*
