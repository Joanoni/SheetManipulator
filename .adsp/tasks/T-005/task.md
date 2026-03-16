# T-005 — Data CRUD API + Audit Trail

> **Layer:** Backend
> **Dependencies:** T-004
> **Complexity:** Medium
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Replace the four HTTP 501 stubs in [`src/backend/app/routers/data.py`](src/backend/app/routers/data.py) with a fully functional CRUD API that operates on dynamic tables. Every write operation (INSERT, UPDATE, soft-DELETE) must produce one or more rows in the `audit_log` table. The router must also expose a `GET /api/tables/{table_name}/audit` endpoint for querying the audit trail.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `GET /api/tables/{table_name}/rows` returns paginated non-deleted rows | Response includes `items`, `total`, `page`, `page_size` |
| AC-2 | `include_deleted=true` query param returns all rows including soft-deleted | Deleted rows appear in response |
| AC-3 | `POST /api/tables/{table_name}/rows` inserts a row with a new UUID `_row_id` | Row appears in subsequent GET |
| AC-4 | `POST` writes one `audit_log` entry per column with `operation="INSERT"` | `audit_log` row count equals number of columns |
| AC-5 | `PUT /api/tables/{table_name}/rows/{row_id}` updates only supplied fields | Unchanged columns retain original values |
| AC-6 | `PUT` writes one `audit_log` entry per **changed** column with `operation="UPDATE"` | Only modified columns appear in audit log |
| AC-7 | `DELETE /api/tables/{table_name}/rows/{row_id}` sets `is_deleted=1`, does not remove row | `SELECT * FROM {table}` still shows row with `is_deleted=1` |
| AC-8 | `DELETE` writes one `audit_log` entry with `column_name="is_deleted"`, `new_value="1"` | Audit log entry present |
| AC-9 | `GET /api/tables/{table_name}/audit` returns audit entries for that table, newest first | Response is ordered by `timestamp DESC` |
| AC-10 | All endpoints return `404` if `table_name` does not exist in `schema_definitions` | Error response with `{"detail": "Table not found"}` |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. New Pydantic Schema — `src/backend/app/schemas/data_row.py`

Create this file (it does not yet exist):

```python
from pydantic import BaseModel
from typing import Any

class RowInsert(BaseModel):
    data: dict[str, Any]  # {column_system_name: value}

class RowUpdate(BaseModel):
    data: dict[str, Any]  # Only fields to update

class RowRead(BaseModel):
    _row_id: str
    is_deleted: bool
    _upload_id: str | None
    data: dict[str, Any]  # All user-defined columns

class PaginatedRows(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
```

### 2. Replace `src/backend/app/routers/data.py`

Full implementation of all routes. Use `AsyncSession` from `app.database` via `Depends`.

#### `GET /api/tables/{table_name}/rows`

```python
# Query params: page: int = 1, page_size: int = 50, include_deleted: bool = False
# 1. Verify table_name exists in schema_definitions → 404 if not.
# 2. SELECT * FROM "{table_name}" WHERE is_deleted = 0 (unless include_deleted=True)
#    with LIMIT {page_size} OFFSET {(page-1)*page_size}
# 3. COUNT(*) for total.
# 4. Return PaginatedRows.
```

**Important:** Use `sqlalchemy.text()` with bound parameters for all dynamic table queries. Never use f-strings for user-supplied values — only for validated `table_name` (already validated against `schema_definitions`).

#### `POST /api/tables/{table_name}/rows`

```python
# Body: RowInsert
# 1. Verify table_name exists → 404 if not.
# 2. Fetch schema columns for the table.
# 3. Validate that all mandatory columns are present in body.data → 422 if missing.
# 4. Generate _row_id = str(uuid.uuid4()).
# 5. Build INSERT with system columns + user columns.
# 6. Write audit_log entries: one per column in body.data, operation="INSERT",
#    old_value=None, new_value=str(value).
# 7. Commit in a single transaction.
# 8. Return 201 with the inserted row.
```

#### `PUT /api/tables/{table_name}/rows/{row_id}`

```python
# Body: RowUpdate
# 1. Verify table_name exists → 404 if not.
# 2. SELECT current row by _row_id → 404 if not found or is_deleted=1.
# 3. For each field in body.data:
#    a. Compare new value to current value.
#    b. If changed: add to UPDATE SET clause + write audit_log entry (operation="UPDATE").
# 4. If no fields changed: return 200 with current row (no-op).
# 5. Execute UPDATE, commit.
# 6. Return 200 with updated row.
```

#### `DELETE /api/tables/{table_name}/rows/{row_id}`

```python
# 1. Verify table_name exists → 404 if not.
# 2. SELECT current row → 404 if not found.
# 3. If already is_deleted=1 → return 409 Conflict {"detail": "Row already deleted"}.
# 4. UPDATE "{table_name}" SET is_deleted=1 WHERE _row_id=:row_id
# 5. Write audit_log: column_name="is_deleted", old_value="0", new_value="1", operation="DELETE".
# 6. Commit, return 204 No Content.
```

#### `GET /api/tables/{table_name}/audit`

```python
# Query params: row_id: str | None = None, limit: int = 100
# 1. Verify table_name exists → 404 if not.
# 2. SELECT * FROM audit_log WHERE table_name=:table_name
#    (AND row_id=:row_id if provided)
#    ORDER BY timestamp DESC LIMIT :limit
# 3. Return list[AuditLogRead].
```

### 3. Helper — `_verify_table_exists()`

Add a private async helper at the bottom of `data.py`:

```python
async def _verify_table_exists(table_name: str, db: AsyncSession) -> None:
    """Raises HTTP 404 if table_name has no rows in schema_definitions."""
    result = await db.execute(
        select(SchemaDefinition.table_system_name)
        .where(SchemaDefinition.table_system_name == table_name)
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Table not found")
```

### 4. Audit Log Write Pattern

Every write must use this pattern (single transaction with the data mutation):

```python
audit_entry = AuditLog(
    table_name=table_name,
    row_id=row_id,
    column_name=col_name,
    old_value=str(old_val) if old_val is not None else None,
    new_value=str(new_val) if new_val is not None else None,
    operation="INSERT",  # or "UPDATE" or "DELETE"
)
db.add(audit_entry)
# ... commit once after all entries are added
```

### 5. Router Registration

`data.py` router is already registered in [`src/backend/app/main.py`](src/backend/app/main.py) under `/api` prefix — **no changes needed to `main.py`**.

</instructions>

---

## 📁 Files to Create / Modify
<files>

| Action | File | Notes |
| :--- | :--- | :--- |
| **Create** | `src/backend/app/schemas/data_row.py` | New Pydantic models |
| **Replace** | `src/backend/app/routers/data.py` | Full implementation (replaces 501 stubs) |

</files>

---

## 🚫 Out of Scope
<out_of_scope>

- Bulk insert/update endpoints (single-row operations only).
- Row-level permissions or user identity in audit log.
- Frontend DataTable (T-008).
- Export endpoint (T-006).

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T22:43:00Z.*
