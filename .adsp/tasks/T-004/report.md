# T-004 Report — Schema Management API + Dynamic DDL

> **Status:** ✅ Complete
> **Builder Run:** 2026-03-16T22:14:00Z

---

## Actions Performed

1. **Created `src/backend/app/services/dynamic_ddl.py`**
   - `DATA_TYPE_MAP` dict: `String→TEXT`, `Integer→INTEGER`, `Float→REAL`, `Boolean→INTEGER`, `Date→TEXT`.
   - `ensure_table_exists(table_system_name, columns, db)` — builds `CREATE TABLE IF NOT EXISTS` DDL with system columns (`_row_id TEXT PRIMARY KEY`, `is_deleted INTEGER NOT NULL DEFAULT 0`, `_upload_id TEXT`) prepended, then user columns sorted by `column_order`. Fully idempotent.

2. **Updated `src/backend/app/schemas/schema_definition.py`**
   - Added `ColumnDisplayNameUpdate(BaseModel)` with single field `display_name: str`.

3. **Replaced stub `src/backend/app/routers/schema.py`** with full implementation:
   - `GET /api/schemas` — returns `{"tables": [...]}` of distinct `table_system_name` values.
   - `POST /api/schemas` — validates naming rules (`^[a-z][a-z0-9_]*$`, max 64 chars), rejects reserved system column names (`_row_id`, `is_deleted`, `_upload_id`), checks for duplicate `column_system_name` and `column_order` within submission, returns `409` if schema already exists, inserts all rows in one transaction, calls `dynamic_ddl.ensure_table_exists()`, returns `201` with full schema.
   - `GET /api/schemas/{table_name}` — returns columns ordered by `column_order`; `404` if not found.
   - `PUT /api/schemas/{table_name}/columns/{column_id}` — rejects body containing `column_system_name` with `400`; updates only `display_name`; `404` if column not found.

4. **Updated `src/backend/app/services/ingestion.py`**
   - Removed inline `_ensure_table_exists()` stub.
   - Removed unused imports (`json`, `os`, `datetime`, `timezone`, `text`).
   - Wired `await dynamic_ddl.ensure_table_exists(table_system_name, schema, session)` in the success path.

---

## Acceptance Criteria Verification

| # | Criterion | Result |
| :--- | :--- | :--- |
| AC-1 | `POST /api/schemas` creates rows + triggers DDL | ✅ `ensure_table_exists()` called after flush |
| AC-2 | `GET /api/schemas` returns distinct table names | ✅ `SELECT DISTINCT table_system_name` |
| AC-3 | `GET /api/schemas/{table_name}` ordered by `column_order` | ✅ `.order_by(SchemaDefinition.column_order)` |
| AC-4 | `PUT` updates only `display_name` | ✅ Only `row.display_name` is mutated |
| AC-5 | `column_system_name` in PUT body → `400` | ✅ Raw JSON body inspection before parsing |
| AC-6 | `ensure_table_exists()` is idempotent | ✅ `CREATE TABLE IF NOT EXISTS` |
| AC-7 | System columns always present | ✅ `_SYSTEM_COLUMNS` prepended unconditionally |
| AC-8 | `data_type` mapping correct | ✅ `DATA_TYPE_MAP` covers all 5 types |

---

## Manual Validation Checklist

- [ ] `docker compose up --build` starts without errors.
- [ ] `POST /api/schemas` with valid body returns `201` and column list.
- [ ] `sqlite3 /data/database.sqlite .tables` shows the new table name.
- [ ] `PRAGMA table_info(<table>)` shows `_row_id`, `is_deleted`, `_upload_id` plus user columns.
- [ ] `GET /api/schemas` returns `{"tables": ["<table_name>"]}`.
- [ ] `GET /api/schemas/<table_name>` returns columns in `column_order` sequence.
- [ ] `PUT /api/schemas/<table_name>/columns/1` with `{"display_name": "New Label"}` returns `200`.
- [ ] `PUT` with `{"column_system_name": "x", "display_name": "y"}` returns `400`.
- [ ] `POST /api/schemas` with same `table_system_name` twice returns `409`.
- [ ] `POST /api/schemas` with `column_system_name: "_row_id"` returns `400`.
- [ ] `POST /api/schemas` with `column_system_name: "1invalid"` returns `422`.
- [ ] Calling `ensure_table_exists()` twice on the same table does not raise an error.
