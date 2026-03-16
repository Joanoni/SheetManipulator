# SheetManipulator Context

> A robust data governance system designed to ingest, validate, and manage spreadsheet data through a web-based interface, using a Database-First approach to ensure data integrity.

## Project Goal
To transition from fragile, manual spreadsheet editing to a controlled environment where the system acts as the "Source of Truth," providing a dynamic CRUD interface while enforcing strict business and validation rules.

## Core Architecture
- **Database-First Strategy:** All operations are performed against a SQLite database. The original spreadsheets are used only for initial ingestion and final data export.
- **Dynamic Schema Mapping:** Instead of a static config file, the system provides a UI for users to map spreadsheet columns to database fields, defining:
    - **Display Names:** Human-readable labels for tables and columns.
    - **System Names:** Immutable internal identifiers for backend stability.
    - **Data Types:** String, Integer, Float, Boolean, Date.
    - **Constraints:** Mandatory (required) fields and Primary Keys.
- **Asynchronous Ingestion:** Large file processing is handled via background tasks (FastAPI `BackgroundTasks`) to maintain UI responsiveness.
- **Cold Storage:** Original uploaded files are preserved in a structured directory: `/data/uploads/{upload_id}/`, accompanied by a `metadata.json` (timestamp, original filename).

## Data Integrity & Governance
- **Soft Deletes:** Records are never physically deleted. An `is_deleted` flag is used to allow for data recovery and historical consistency.
- **Audit Trail:** A centralized logging table tracks every modification (table, row_id, column, old_value, new_value, timestamp).
- **Validation Engine:**
    - **Short-circuit Logic:** The validation process stops after 1000 errors to prevent system exhaustion.
    - **Error Reporting:** Generates a specific Excel report containing only the failed rows. Format: `[Original Line Index] | [Column] | [Original Value] | [Error Reason]`.
    - **Granularity:** One row per error (if a single row has 3 errors, it appears 3 times in the report).

## Technical Constraints
- **Backend:** Python (FastAPI).
- **Frontend:** React (Vite + Tailwind CSS), dynamically rendered based on database metadata.
- **Database:** SQLite (stored at `/data/database.sqlite`).
- **Orchestration:** Docker Compose (Service: backend, frontend, db-volume).
- **Volume Mapping:** Root `/data` folder for persistence.

## Workflow Pipeline
1. **Upload:** User uploads an `.xlsx` file and selects target worksheets.
2. **Mapping:** User defines table/column metadata (Types, Labels, Keys, Requirements).
3. **Validation:** System performs a full scan in the background.
4. **Ingestion:** Validated data is moved to the SQLite database.
5. **Management:** Users edit/view data through the React CRUD interface.
6. **Export:** System generates updated spreadsheets upon request.