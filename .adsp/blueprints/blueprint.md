# SheetManipulator — Conceptual Blueprint

> **Vision:** Transform fragile, manual spreadsheet workflows into a governed, auditable data management system where the database is the single Source of Truth.

---

## 🎯 Goals
<goals>

| # | Goal | Priority |
| :--- | :--- | :--- |
| G-01 | Provide a web-based CRUD interface for spreadsheet data | Critical |
| G-02 | Enforce data integrity through schema mapping and validation | Critical |
| G-03 | Preserve original files and maintain a full audit trail | High |
| G-04 | Support asynchronous ingestion of large `.xlsx` files | High |
| G-05 | Enable bidirectional flow: import from and export to spreadsheets | Medium |

</goals>

---

## 🏛️ Conceptual Architecture
<architecture>

The system is composed of three primary layers:

### 1. Ingestion Layer
Handles the entry point for raw spreadsheet data.
- User uploads `.xlsx` files via the web UI.
- User selects target worksheets for processing.
- Original files are archived to **Cold Storage**: `/data/uploads/{upload_id}/` with a `metadata.json` (timestamp, original filename).
- Processing is dispatched as a **background task** (FastAPI `BackgroundTasks`) to keep the UI responsive.

### 2. Governance Layer
The core intelligence of the system — defines and enforces the rules.
- **Dynamic Schema Mapping UI:** Users define table/column metadata interactively:
  - `display_name`: Human-readable label.
  - `system_name`: Immutable internal identifier.
  - `data_type`: `String | Integer | Float | Boolean | Date`.
  - `constraints`: `mandatory` (required) and `primary_key`.
- **Validation Engine:**
  - Full-scan validation runs in the background.
  - **Short-circuit:** Halts after **1,000 errors** to prevent system exhaustion.
  - **Error Report:** Generates an Excel file containing only failed rows.
    - Format per row: `[Original Line Index] | [Column] | [Original Value] | [Error Reason]`.
    - Granularity: one row per error (a row with 3 errors appears 3 times).
- **Soft Deletes:** Records are never physically removed; an `is_deleted` flag enables recovery.
- **Audit Trail:** A centralized log table records every mutation: `table`, `row_id`, `column`, `old_value`, `new_value`, `timestamp`.

### 3. Management Layer
The operational surface for day-to-day data governance.
- **React CRUD Interface:** Dynamically rendered from database metadata — no hardcoded schemas.
- **Export Engine:** Generates updated `.xlsx` spreadsheets from the current database state on demand.

</architecture>

---

## 🔩 Technical Constraints
<constraints>

| Concern | Decision |
| :--- | :--- |
| **Backend** | Python — FastAPI |
| **Frontend** | React (Vite + Tailwind CSS), dynamically driven by DB metadata |
| **Database** | SQLite — stored at `/data/database.sqlite` |
| **Orchestration** | Docker Compose — services: `backend`, `frontend`, `db-volume` |
| **Persistence** | Root `/data` volume mapped via Docker |

</constraints>

---

## 🔄 Workflow Pipeline
<workflow>

```
[Upload .xlsx] → [Select Worksheets] → [Map Schema] → [Background Validation]
      ↓                                                         ↓
[Cold Storage]                                    [Error Report (if failures)]
                                                              ↓
                                                  [Ingest to SQLite (if clean)]
                                                              ↓
                                              [CRUD Management via React UI]
                                                              ↓
                                                    [Export to .xlsx]
```

</workflow>

---

## 📦 Data Model Concepts
<data_model>

### Core Entities

| Entity | Purpose |
| :--- | :--- |
| `upload_registry` | Tracks each uploaded file: `upload_id`, `original_filename`, `timestamp`, `status` |
| `schema_definitions` | Stores user-defined table/column mappings: `system_name`, `display_name`, `data_type`, `is_mandatory`, `is_primary_key` |
| `audit_log` | Immutable record of all data mutations |
| `[dynamic_tables]` | User-defined tables created from schema mappings, each with `is_deleted` flag |

### Key Invariants
- `system_name` is **immutable** once set — it is the stable backend identifier.
- No record is ever `DELETE`d from the database — only soft-deleted.
- Every write operation produces an `audit_log` entry.

</data_model>

---

## 🚧 Open Conceptual Questions
<open_questions>

| # | Question | Impact |
| :--- | :--- | :--- |
| OQ-01 | Should schema re-mapping be allowed after initial ingestion? | High — affects data migration strategy |
| OQ-02 | Is multi-user / role-based access required? | Medium — affects auth layer design |
| OQ-03 | What is the expected maximum file size for uploads? | Medium — affects chunked upload strategy |
| OQ-04 | Should the export preserve original formatting/styles from the source `.xlsx`? | Low — affects export engine complexity |

</open_questions>

---

*Blueprint synthesized by ADSP-Visionary on 2026-03-16T21:32:03Z from `.adsp/inbox/project.md`.*
