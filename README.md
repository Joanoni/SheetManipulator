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
│   │   ├── main.py              # FastAPI app factory, lifespan, router registration
│   │   ├── database.py          # SQLAlchemy async engine + init_db()
│   │   ├── models/
│   │   │   ├── upload_registry.py   # ORM: upload_registry table
│   │   │   ├── schema_definition.py # ORM: schema_definitions table
│   │   │   └── audit_log.py         # ORM: audit_log table
│   │   ├── routers/
│   │   │   ├── upload.py        # POST /upload, GET /uploads/... (T-003)
│   │   │   ├── schema.py        # CRUD /schemas (T-004)
│   │   │   ├── data.py          # Stub: CRUD /tables/{name}/rows
│   │   │   └── export.py        # Stub: GET /tables/{name}/export
│   │   ├── services/
│   │   │   ├── ingestion.py     # Background ingestion pipeline (T-003)
│   │   │   ├── validation.py    # Validation engine, short-circuit @ 1,000 (T-003)
│   │   │   ├── export.py        # Error report generator (T-003)
│   │   │   └── dynamic_ddl.py   # CREATE TABLE from schema_definitions (T-004)
│   │   └── schemas/
│   │       ├── upload.py        # Pydantic: UploadRegistryRead, ProcessRequest
│   │       ├── schema_definition.py # Pydantic: SchemaCreate, ColumnDefinitionRead, ColumnDisplayNameUpdate
│   │       └── audit.py         # Pydantic: AuditLogRead
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   └── App.tsx              # Placeholder
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
| T-005 | Data CRUD API + Audit Trail | ⬜ Queued |
| T-006 | Export Engine (xlsx generation) | ⬜ Queued |
| T-007 | Frontend: Upload Wizard + Schema Mapping UI | ⬜ Queued |
| T-008 | Frontend: Dynamic DataTable CRUD + Audit Drawer | ⬜ Queued |

---

*Managed by the ADSP Framework.*
