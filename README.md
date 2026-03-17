# SheetManipulator

> A Database-First data governance system that transforms `.xlsx` spreadsheets into a governed, auditable SQLite database with a full React CRUD interface.

---

## Quickstart (Docker)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2

### Run

```bash
git clone https://github.com/Joanoni/SheetManipulator.git
cd SheetManipulator
docker compose -f src/docker-compose.yml up --build
```

> **Re-running after an update?** Run `git pull` first to ensure your local files are current before rebuilding:
> ```bash
> git pull
> docker compose -f src/docker-compose.yml up --build
> ```

The first build downloads base images and installs dependencies — subsequent starts are fast.

### Service URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend** | http://localhost:5173 | React UI (Ingest · Manage · History) |
| **Backend API** | http://localhost:8000 | FastAPI JSON API |
| **Swagger UI** | http://localhost:8000/docs | Interactive API documentation |
| **Health check** | http://localhost:8000/health | Returns `{"status": "ok"}` |

---

## Development (Local, without Docker)

### Backend

```bash
cd src/backend
pip install -r requirements.txt
DATABASE_URL=sqlite+aiosqlite:////tmp/dev.sqlite uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd src/frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

The Vite dev server starts at http://localhost:5173 with hot-module replacement enabled.

---

## Environment Variables

| Variable | Service | Default (Docker) | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | backend | `sqlite+aiosqlite:////data/database.sqlite` | SQLAlchemy async connection string |
| `VITE_API_URL` | frontend | `http://localhost:8000` | Base URL for the Axios API client |

> **Data persistence:** The Docker Compose setup mounts a named volume (`data-volume`) at `/data` inside the backend container. This persists `database.sqlite` and all uploaded files across container restarts.

---

## How It Works

```
[Upload .xlsx] → [Select Worksheet] → [Map Schema] → [Background Validation]
      ↓                                                        ↓
[Cold Storage]                                   [Error Report .xlsx (if failures)]
                                                              ↓
                                                  [Ingest to SQLite (if clean)]
                                                              ↓
                                              [CRUD Management via React UI]
                                                              ↓
                                                    [Export to .xlsx]
```

1. **Ingest** — Upload an `.xlsx` file, select a worksheet, define the schema (column names, types, constraints), and submit. Validation runs in the background.
2. **Manage** — Browse, insert, edit, and soft-delete rows in any ingested table. Rename column display names. View per-row audit history.
3. **History** — See all past uploads with their status. Download error reports for failed ingestions.

---

## Project Structure

```
src/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, lifespan, CORS, router registration,
│   │   │                            #   StaticFiles mount at /files/uploads (T-009)
│   │   ├── database.py              # SQLAlchemy async engine + session factory + init_db()
│   │   ├── models/
│   │   │   ├── upload_registry.py   # ORM: upload_registry table
│   │   │   ├── schema_definition.py # ORM: schema_definitions table
│   │   │   └── audit_log.py         # ORM: audit_log table
│   │   ├── routers/
│   │   │   ├── upload.py            # POST /upload, GET /uploads, GET /uploads/{id}/...
│   │   │   ├── schema.py            # CRUD /schemas + PUT /schemas/{name}/columns/{id}
│   │   │   ├── data.py              # CRUD /tables/{name}/rows + GET /tables/{name}/audit
│   │   │   └── export.py            # GET /tables/{name}/export → StreamingResponse .xlsx
│   │   ├── services/
│   │   │   ├── ingestion.py         # Background ingestion pipeline
│   │   │   ├── validation.py        # Validation engine, short-circuit at 1,000 errors
│   │   │   ├── export.py            # Error report generator + export_table_to_xlsx()
│   │   │   └── dynamic_ddl.py       # CREATE TABLE IF NOT EXISTS from schema_definitions
│   │   └── schemas/
│   │       ├── upload.py            # Pydantic: UploadRegistryRead, ProcessRequest
│   │       ├── schema_definition.py # Pydantic: SchemaCreate, ColumnDefinitionRead, ColumnDisplayNameUpdate
│   │       ├── data_row.py          # Pydantic: RowInsert, RowUpdate, RowRead, PaginatedRows
│   │       └── audit.py             # Pydantic: AuditLogRead
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx                 # React entry point + QueryClientProvider
│   │   ├── App.tsx                  # BrowserRouter + NavBar (Ingest · Manage · History)
│   │   ├── api/
│   │   │   ├── client.ts            # Axios base client (reads VITE_API_URL)
│   │   │   ├── ingestion.ts         # uploadFile, listUploads, getWorksheets, processUpload, getUploadStatus
│   │   │   ├── schema.ts            # createSchema, listSchemas, getSchema, updateColumnDisplayName
│   │   │   └── data.ts              # listRows, insertRow, updateRow, deleteRow, exportTable, getAuditLog
│   │   ├── components/
│   │   │   ├── UploadWizard/
│   │   │   │   ├── UploadWizard.tsx  # 4-step ingestion wizard (drag-drop → worksheet → schema → status)
│   │   │   │   └── StepIndicator.tsx # Horizontal step progress bar
│   │   │   ├── DataTable/
│   │   │   │   ├── DataTable.tsx     # Dynamic CRUD grid with pagination, inline edit, export
│   │   │   │   ├── CellEditor.tsx    # Type-aware cell input (text/number/date/checkbox)
│   │   │   │   └── AddRowModal.tsx   # Insert row modal form
│   │   │   ├── AuditDrawer/
│   │   │   │   └── AuditDrawer.tsx   # Audit log side panel (per-row history)
│   │   │   └── SchemaPanel/
│   │   │       └── SchemaPanel.tsx   # Inline column display name editor
│   │   └── pages/
│   │       ├── IngestionPage.tsx     # Upload wizard page (route: /)
│   │       ├── ManagePage.tsx        # Table selector + SchemaPanel + DataTable (route: /manage)
│   │       └── HistoryPage.tsx       # Upload history table with auto-refresh (route: /history)
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
└── docker-compose.yml
```

---

## API Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Upload `.xlsx` file; returns `upload_id` |
| `GET` | `/api/uploads` | List all uploads ordered by timestamp DESC |
| `GET` | `/api/uploads/{id}/worksheets` | List worksheet names in uploaded file |
| `POST` | `/api/uploads/{id}/process` | Trigger background ingestion |
| `GET` | `/api/uploads/{id}/status` | Poll ingestion status |
| `GET` | `/api/schemas` | List all table schemas |
| `POST` | `/api/schemas` | Create table schema + run DDL |
| `GET` | `/api/schemas/{table}` | Get column definitions |
| `PUT` | `/api/schemas/{table}/columns/{id}` | Update column display name |
| `GET` | `/api/tables/{table}/rows` | Paginated rows (soft-deleted excluded by default) |
| `POST` | `/api/tables/{table}/rows` | Insert row + audit entry |
| `PUT` | `/api/tables/{table}/rows/{row_id}` | Update row + audit entries per changed column |
| `DELETE` | `/api/tables/{table}/rows/{row_id}` | Soft delete row + audit entry |
| `GET` | `/api/tables/{table}/audit` | Audit log for table (optional `row_id` filter) |
| `GET` | `/api/tables/{table}/export` | Stream `.xlsx` of current non-deleted rows |
| `GET` | `/files/uploads/{id}/...` | Static file serving for error reports |

---

## Development Status

| Task | Title | Status |
| :--- | :--- | :--- |
| T-001 | Project Scaffold & Docker Compose | ✅ Done |
| T-002 | Backend Core: DB Models + FastAPI App Factory | ✅ Done |
| T-003 | Ingestion Pipeline: Upload, Cold Storage & Validation Engine | ✅ Done |
| T-004 | Schema Management API + Dynamic DDL | ✅ Done |
| T-005 | Data CRUD API + Audit Trail | ✅ Done |
| T-006 | Export Engine (xlsx generation) | ✅ Done |
| T-007 | Frontend: Upload Wizard + Schema Mapping UI | ✅ Done |
| T-008 | Frontend: Dynamic DataTable CRUD + Audit Drawer | ✅ Done |
| T-009 | Static File Serving for Error Reports | ✅ Done |
| T-010 | Schema Column Display Name Edit UI | ✅ Done |
| T-011 | Upload History Page | ✅ Done |
| T-012 | README Quickstart & Docker Compose Run Guide | ✅ Done |
| R-001 | Fix: Docker Volume Shadowing — Frontend `node_modules` | ✅ Done |
| R-002 | Fix: Vite Dev Cache Staleness — `ColumnDefinition` Not Found in Docker | ✅ Done |
| R-003 | Fix: Stale Local Working Tree — `git pull` step + Production Build Dockerfile | ✅ Done |

---

## Known Limitations

The following open questions from the original blueprint are **not yet addressed** in the current implementation:

| # | Question | Impact |
| :--- | :--- | :--- |
| OQ-01 | Should schema re-mapping be allowed after initial ingestion? | High — affects data migration strategy. Currently, `column_system_name` is immutable and no migration tooling exists. |
| OQ-02 | Is multi-user / role-based access required? | Medium — no authentication or authorization layer is implemented. The API is open. |
| OQ-03 | What is the expected maximum file size for uploads? | Medium — uploads are read fully into memory. No chunked upload strategy is implemented. |
| OQ-04 | Should the export preserve original formatting/styles from the source `.xlsx`? | Low — exports use plain `openpyxl` with no style preservation. |

---

## Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.12 + FastAPI + SQLAlchemy 2.x async |
| **Frontend** | React 19 + Vite 8 + Tailwind CSS v4 + TanStack Query v5 |
| **Database** | SQLite via `aiosqlite` |
| **Spreadsheet I/O** | `openpyxl` |
| **Orchestration** | Docker Compose v2 |

---

*Managed by the [ADSP Framework](https://github.com/Joanoni/SheetManipulator).*
