# T-004 — Schema Management API + Dynamic DDL

> **Layer:** Backend
> **Dependencies:** T-002
> **Complexity:** Medium
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Implement the Schema Management API that allows users to define table/column metadata, and the Dynamic DDL service that translates those definitions into real SQLite tables at runtime. This is the governance core — all downstream CRUD and ingestion depend on it.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `POST /api/schemas` creates `schema_definitions` rows and triggers DDL | `sqlite3 /data/database.sqlite .tables` shows new table |
| AC-2 | `GET /api/schemas` returns all distinct `table_system_name` values | Response is a list of table names |
| AC-3 | `GET /api/schemas/{table_name}` returns all column definitions ordered by `column_order` | Response matches inserted schema |
| AC-4 | `PUT /api/schemas/{table_name}/columns/{column_id}` updates only `display_name` | `column_system_name` unchanged after PUT |
| AC-5 | Attempting to update `column_system_name` via PUT returns `400 Bad Request` | Error response with message |
| AC-6 | `ensure_table_exists()` is idempotent — calling it twice does not raise an error | No exception on second call |
| AC-7 | Dynamic table always includes `_row_id`, `is_deleted`, `_upload_id` system columns | `PRAGMA table_info({table})` shows all 3 |
| AC-8 | `data_type` mapping is correct: `String→TEXT`, `Integer→INTEGER`, `Float→REAL`, `Boolean→INTEGER`, `Date→TEXT` | `PRAGMA table_info` shows correct SQLite types |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. `src/backend/app/routers/schema.py`

```python
# Routes to implement:
# GET    /api/schemas                                      → list_schemas()
# POST   /api/schemas                                      → create_schema()
# GET    /api/schemas/{table_name}                         → get_schema()
# PUT    /api/schemas/{table_name}/columns/{column_id}     → update_column()
```

**`POST /api/schemas`**
- Accept `SchemaCreate` body.
- Validate: `table_system_name` must be alphanumeric + underscores only (regex: `^[a-z][a-z0-9_]*$`).
- Validate: `column_system_name` for each column must match same pattern.
- Insert all `SchemaDefinition` rows in a single transaction.
- Call `await dynamic_ddl.ensure_table_exists(table_system_name, columns, db)`.
- Return `201 Created` with the full schema.

**`GET /api/schemas`**
- Query `SELECT DISTINCT table_system_name FROM schema_definitions`.
- Return `{"tables": ["table_a", "table_b"]}`.

**`GET /api/schemas/{table_name}`**
- Query all `SchemaDefinition` rows for `table_system_name`, ordered by `column_order`.
- Return list of `ColumnDefinitionRead`.

**`PUT /api/schemas/{table_name}/columns/{column_id}`**
- Accept body: `{"display_name": str}` — **only this field is mutable**.
- If request body contains `column_system_name`, return `400` with `{"detail": "column_system_name is immutable"}`.
- Update `display_name` in DB.
- Return updated `ColumnDefinitionRead`.

### 2. `src/backend/app/services/dynamic_ddl.py`

```python
DATA_TYPE_MAP = {
    "String": "TEXT",
    "Integer": "INTEGER",
    "Float": "REAL",
    "Boolean": "INTEGER",
    "Date": "TEXT",
}

async def ensure_table_exists(
    table_system_name: str,
    columns: list[SchemaDefinition],
    db: AsyncSession
) -> None:
    """
    Creates the dynamic table if it does not already exist.
    Always includes system columns: _row_id, is_deleted, _upload_id.
    Uses CREATE TABLE IF NOT EXISTS — fully idempotent.
    """
    col_defs = ["_row_id TEXT PRIMARY KEY", "is_deleted INTEGER NOT NULL DEFAULT 0", "_upload_id TEXT"]
    for col in sorted(columns, key=lambda c: c.column_order):
        sqlite_type = DATA_TYPE_MAP[col.data_type]
        nullable = "" if col.is_mandatory else ""
        col_defs.append(f'"{col.column_system_name}" {sqlite_type}')

    ddl = f'CREATE TABLE IF NOT EXISTS "{table_system_name}" ({", ".join(col_defs)})'
    await db.execute(text(ddl))
    await db.commit()
```

### 3. Input Validation Rules

| Field | Rule |
| :--- | :--- |
| `table_system_name` | Regex `^[a-z][a-z0-9_]*$`, max 64 chars |
| `column_system_name` | Regex `^[a-z][a-z0-9_]*$`, max 64 chars |
| `data_type` | Must be one of `String`, `Integer`, `Float`, `Boolean`, `Date` |
| `column_order` | Must be unique within a table schema submission |
| Duplicate `column_system_name` | Return `409 Conflict` if already exists for that table |

### 4. Reserved System Column Names
The following names are **forbidden** as `column_system_name` values (return `400`):
- `_row_id`
- `is_deleted`
- `_upload_id`

### 5. Pydantic Schema Update (`src/backend/app/schemas/schema_definition.py`)
Add:
```python
class ColumnDisplayNameUpdate(BaseModel):
    display_name: str
```

</instructions>

---

## 🚫 Out of Scope
<out_of_scope>

- Schema re-mapping after ingestion (OQ-01 deferred — `column_system_name` is immutable by design).
- Adding new columns to an existing table after creation (ALTER TABLE — deferred).
- Deleting a schema or table (deferred).
- Frontend schema mapping UI (T-007).

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T21:34:15Z.*
