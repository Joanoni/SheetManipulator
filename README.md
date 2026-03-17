# SheetManipulator

> A Database-First data governance system for `.xlsx` ingestion, schema management, and CRUD operations.

---

## Overview

SheetManipulator ingests Excel files, maps schemas dynamically via a UI, validates data with short-circuit logic (max 1,000 errors), persists to SQLite with soft deletes and a full audit trail, and exposes a React CRUD interface for ongoing data management.

---

## Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.12 + FastAPI + SQLAlchemy 2.x async |
| **Frontend** | React 18 + Vite + Tailwind CSS v4 |
| **Database** | SQLite via `aiosqlite` |
| **Spreadsheet I/O** | `openpyxl` |
| **Orchestration** | Docker Compose v2 |

---

## Getting Started

### Prerequisites
- Docker & Docker Compose v2

### Run

```bash
cd src
docker compose up --build
```

| Service | URL |
| :--- | :--- |
| Backend API | http://localhost:8000 |
| API Health | http://localhost:8000/health |
| Frontend | http://localhost:5173 |

---

## Project Structure

```
src/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, lifespan, router registration, StaticFiles mount (T-009)
│   │   ├── database.py          # SQLAlchemy async engine + init_db()
│   │   ├── models/
│   │   │   ├── upload_registry.py   # ORM: upload_registry table
│   │   │   ├── schema_definition.py # ORM: schema_definitions table
│   │   │   └── audit_log.py         # ORM: audit_log table
│   │   ├── routers/
│   │   │   ├── upload.py        # POST /upload, GET /uploads, GET /uploads/... (T-003, T-011)
│   │   │   ├── schema.py        # CRUD /schemas (T-004)
│   │   │   ├── data.py          # CRUD /tables/{name}/rows + audit (T-005)
│   │   │   └── export.py        # GET /tables/{name}/export → StreamingResponse .xlsx (T-006)
│   │   ├── services/
│   │   │   ├── ingestion.py     # Background ingestion pipeline (T-003)
│   │   │   ├── validation.py    # Validation engine, short-circuit @ 1,000 (T-003)
│   │   │   ├── export.py        # Error report generator + export_table_to_xlsx() (T-003, T-006)
│   │   │   └── dynamic_ddl.py   # CREATE TABLE from schema_definitions (T-004)
│   │   └── schemas/
│   │       ├── upload.py        # Pydantic: UploadRegistryRead, ProcessRequest
│   │       ├── schema_definition.py # Pydantic: SchemaCreate, ColumnDefinitionRead, ColumnDisplayNameUpdate
│   │       ├── data_row.py      # Pydantic: RowInsert, RowUpdate, RowRead, PaginatedRows (T-005)
│   │       └── audit.py         # Pydantic: AuditLogRead
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx              # BrowserRouter shell + NavBar (T-007)
│   │   ├── api/
│   │   │   ├── client.ts        # Axios base client (T-007)
│   │   │   ├── ingestion.ts     # Upload/process/status/listUploads API calls (T-007, T-011)
│   │   │   ├── schema.ts        # Schema CRUD API calls + TypeScript interfaces (T-007, T-008, T-010)
│   │   │   └── data.ts          # Row CRUD + audit + export API calls (T-008)
│   │   ├── components/
│   │   │   ├── UploadWizard/
│   │   │   │   ├── UploadWizard.tsx   # 4-step ingestion wizard (T-007)
│   │   │   │   └── StepIndicator.tsx  # Horizontal step progress bar (T-007)
│   │   │   ├── DataTable/
│   │   │   │   ├── DataTable.tsx      # Dynamic CRUD grid with pagination (T-008)
│   │   │   │   ├── CellEditor.tsx     # Type-aware cell input (T-008)
│   │   │   │   └── AddRowModal.tsx    # Insert row modal form (T-008)
│   │   │   ├── AuditDrawer/
│   │   │   │   └── AuditDrawer.tsx    # Audit log side panel (T-008)
│   │   │   └── SchemaPanel/
│   │   │       └── SchemaPanel.tsx    # Inline column display name editor (T-010)
│   │   └── pages/
│   │       ├── IngestionPage.tsx # Upload wizard page (T-007)
│   │       ├── ManagePage.tsx    # Table selector + SchemaPanel + DataTable (T-008, T-010)
│   │       └── HistoryPage.tsx   # Upload history table with auto-refresh (T-011)
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
└── docker-compose.yml
```

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
| T-012 | README Quickstart & Docker Compose Run Guide | ⏳ Pending |

---

*Managed by the ADSP Framework.*
