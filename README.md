# SheetManipulator

> **Configuration Sovereignty** — one JSON file to rule your entire stack.

SheetManipulator is a full-stack, configuration-driven web application that provides a secure, validated, and dynamic CRUD interface directly over physical spreadsheet files (`.xlsx` and `.csv`). It deliberately **avoids any relational database** — the spreadsheet *is* the database — while still delivering enterprise-grade data integrity, concurrency control, and a modern React UI.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Tech Stack](#-tech-stack)
3. [Architecture & Rules](#-architecture--rules)
4. [How to Run](#-how-to-run)

---

## 🗂 Project Overview

### What Is SheetManipulator?

SheetManipulator allows non-technical users and developers alike to perform full CRUD operations on `.xlsx` and `.csv` files through a modern web interface — without ever touching a database engine like PostgreSQL or SQLite.

### Core Philosophy: Configuration Sovereignty

The entire application — backend validation schemas, API routing, frontend form fields, dropdown options, data grid columns — is driven by a **single source of truth**: [`src/config.json`](src/config.json).

This means:

- **Adding a new "entity"** (a new spreadsheet/tab) requires only editing the JSON. No code changes, no recompilation, no migrations.
- **Changing a field type** from `string` to `int` in the JSON automatically propagates to Pydantic validators on the backend and React inputs on the frontend on next reload.
- **No hardcoded business logic** exists in the frontend. The React layer is purely presentational.

### Key Capabilities

| Capability | Description |
|---|---|
| Direct File Manipulation | Operates on `.xlsx` and `.csv` files as the primary data store |
| Dynamic Architecture | Backend schemas and frontend UI are generated at runtime from `config.json` |
| Universal File Locking | Atomic `O_CREAT\|O_EXCL` lock files prevent data corruption under concurrent writes |
| Pydantic v2 Validation | Dynamic models with `Literal[...]` enum constraints reject invalid data before it touches files |
| Startup Integrity Check | Pre-flight validation ensures physical files match config schema and unique ID constraints before the server boots |
| Server-Side Pagination | All data slicing happens on the backend; browser DOM is never loaded with thousands of rows |
| Audit Logging | Every write operation is recorded in JSONL format via a rotating file handler |

---

## 🛠 Tech Stack

### Backend — Sovereign Data Layer

| Technology | Role |
|---|---|
| **Python 3.11+** | Runtime |
| **FastAPI 0.135+** | REST API framework with lifespan hooks |
| **Pydantic v2** | Dynamic model generation via `create_model` and `Literal` constraints |
| **openpyxl** | Read/write `.xlsx` Excel files |
| **uvicorn** | ASGI server |
| **httpx** | HTTP client used by the test suite |

### Frontend — Dynamic Presentation Layer

| Technology | Role |
|---|---|
| **React 18 + TypeScript** | UI framework |
| **Vite 5** | Build tooling and dev server |
| **Tailwind CSS 3** | Utility-first styling |
| **react-hook-form** | Form state management |
| **@tanstack/react-table v8** | Headless data grid with server-side pagination |
| **axios** | HTTP client for API calls |
| **react-router-dom v6** | Client-side routing |

---

## 🏗 Architecture & Rules

### How It Works (No SQL Database)

```
┌──────────────┐        GET /api/config         ┌──────────────────┐
│              │ ─────────────────────────────► │                  │
│  React UI    │                                │  FastAPI Backend │
│  (Vite/TS)   │ ◄───────────────────────────── │                  │
│              │   JSON: entities, fields, opts  │                  │
│  Renders:    │                                │  On startup:     │
│  - Forms     │   POST/PUT/DELETE /api/{entity} │  1. Integrity    │
│  - Tables    │ ─────────────────────────────► │     Check        │
│  - Dropdowns │                                │  2. Build Pydantic│
└──────────────┘ ◄───────────────────────────── │     models       │
                      200 OK / 422 / 409         │  3. Init services│
                                                 └────────┬─────────┘
                                                          │ read/write (with FileLock)
                                                          ▼
                                               ┌─────────────────────┐
                                               │  .xlsx  /  .csv     │
                                               │  (flat file storage)│
                                               └─────────────────────┘
```

### The Six Core Rules

1. **Configuration Sovereignty** — `src/config.json` is the sole authority for UI generation, schema validation, and routing. No entity or field may exist outside of it.

2. **Logical Primary Keys** — Every entity must define exactly one field with `"is_primary_id": true`. CRUD operations use this logical key, never physical row indices, to prevent concurrency corruption.

3. **Concurrency Control** — Any write operation (`create`, `update`, `delete`) acquires an atomic `.lock` file via `os.open(O_CREAT|O_EXCL)` before touching the spreadsheet. Concurrent writers queue or timeout with HTTP 423.

4. **Backend Sovereignty** — Zero business logic or data validation lives in the React frontend. The frontend fetches the config and renders accordingly.

5. **No-SQLite Policy** — SQLite/relational databases are deliberately excluded to keep the architecture lean and aligned with direct file manipulation goals (AgDR-004).

6. **Pre-Flight Integrity Check** — On every startup, `run_startup_integrity_check()` reads all configured files, verifies columns match the schema, and asserts no duplicate primary IDs exist before the server accepts traffic.

### Project Structure

```
SheetManipulator/
├── src/
│   ├── config.json              # ← Single Source of Truth
│   ├── backend/
│   │   ├── main.py              # FastAPI app factory + lifespan
│   │   ├── api/routes.py        # Dynamic CRUD endpoints (/api/{entity})
│   │   ├── core/
│   │   │   ├── integrity.py     # Startup integrity check
│   │   │   ├── locking.py       # FileLock context manager
│   │   │   ├── audit.py         # JSONL audit logger
│   │   │   └── model_factory.py # Pydantic dynamic model builder
│   │   ├── services/
│   │   │   └── data_service.py  # Business logic (CRUD, ID resolution)
│   │   └── storage/
│   │       └── adapters.py      # CSV & Excel read/write adapters
│   ├── frontend/                # React + Vite application
│   │   ├── src/
│   │   │   ├── components/      # DynamicForm, DynamicDataGrid, Navbar…
│   │   │   ├── hooks/           # useConfig, useRecords
│   │   │   ├── services/api.ts  # axios wrapper
│   │   │   └── types/config.ts  # TypeScript interfaces for config shape
│   │   └── package.json
│   └── tests/                   # pytest suite (one file per task)
├── logs/audit.jsonl             # Runtime audit log (git-ignored)
└── agent_framework/             # AI agent governance (core_rules, decision_log…)
```

---

## 🚀 How to Run

### Prerequisites

- Python **3.11+** with `pip`
- Node.js **18+** with `npm`

---

### 1 — Clone the Repository

```bash
git clone https://github.com/Joanoni/SheetManipulator.git
cd SheetManipulator
```

---

### 2 — Backend Setup (FastAPI)

#### 2a. Create and activate a virtual environment

```bash
# Windows (cmd.exe)
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 2b. Install Python dependencies

```bash
pip install fastapi==0.135.1 uvicorn==0.41.0 pydantic httpx openpyxl
```

> **Note:** A `requirements.txt` is planned. Until then, install the packages above manually.

#### 2c. (Optional) Configure paths via environment variables

By default, the backend resolves `src/config.json` automatically. Override if needed:

```bash
# Windows
set SM_CONFIG_PATH=C:\path\to\your\config.json
set SM_BASE_DIR=C:\path\to\project\root

# macOS / Linux
export SM_CONFIG_PATH=/path/to/your/config.json
export SM_BASE_DIR=/path/to/project/root
```

#### 2d. Start the backend server

```bash
# From the project root
python -m uvicorn src.backend.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **REST API**: `http://localhost:8000/api/`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

### 3 — Frontend Setup (React + Vite)

#### 3a. Install Node.js dependencies

```bash
cd src/frontend
npm install
```

#### 3b. Configure the API base URL

```bash
# Copy the example env file
cp .env.example .env
```

Edit `src/frontend/.env` and confirm `VITE_API_BASE_URL` points to the backend:

```
VITE_API_BASE_URL=http://localhost:8000
```

#### 3c. Start the Vite development server

```bash
# Still inside src/frontend/
npm run dev
```

The frontend will be available at **`http://localhost:5173`**.

---

### 4 — Run the Test Suite

```bash
# From the project root, with the virtual environment active
python -m pytest src/tests/ -v
```

For the concurrency stress test specifically:

```bash
python -m pytest src/tests/stress_test.py -v
```

---

### Quick-Start Summary

```bash
# Terminal 1 — Backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install fastapi uvicorn pydantic httpx openpyxl
python -m uvicorn src.backend.main:create_app --factory --port 8000 --reload

# Terminal 2 — Frontend
cd src/frontend && npm install && npm run dev
```

Open `http://localhost:5173` — the UI auto-generates forms and tables from your `src/config.json`.

---

## 📄 License

This project is proprietary. All rights reserved.
