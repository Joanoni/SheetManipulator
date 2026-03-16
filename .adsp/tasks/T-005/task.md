# T-005 — Data CRUD API + Audit Trail

> **Layer:** Backend
> **Dependencies:** T-004
> **Complexity:** Medium
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Implement the Data CRUD API that allows reading, inserting, updating, and soft-deleting rows in any dynamic table. Every write operation must produce one or more `audit_log` entries. Pagination is required for list endpoints.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `GET /api/tables/{table_name}/rows` returns paginated non-deleted rows | Response includes `items`, `total`, `page`, `page_size` |
| AC-2 | `GET /api/tables/{table_name}/rows?include_deleted=true` returns all rows | Deleted rows appear in response |
| AC-3 | `POST /api/tables/{table_name}/rows` inserts a row and writes one `INSERT` audit entry per column | `audit_log` has N rows for N columns |
| AC-4 | `PUT /api/tables/{table_name}/rows/{row_id}` updates only changed columns and writes one `UPDATE` audit entry per changed column | `audit_log` entries have correct `old_value`/`new_value` |
| AC-5 | `DELETE /api/tables/{table_name}/rows/{row_id}` sets `is_deleted=1` and writes one `DELETE` audit entry | Row not returned in default list; audit entry exists |
| AC-6 | `404` returned when `row_id` does not exist or table does not exist | Error response with detail |
| AC-7 | `_row_id` is auto-generated UUID on insert if not provided | UUID format in response |
| AC-8 | System columns (`_row_id`, `is_deleted`, `_upload_id`) are excluded from user-facing payloads | Not present in request body schema |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. `src/backend/app/schemas/data_row.py`

```python
class RowInsert(BaseModel):
    data: dict[str, Any]  # column_system_name → value

class RowUpdate(BaseModel):
    data: dict[str, Any]  # only fields to change

class RowRead(BaseModel):
    _row_id: str
    is_deleted: bool
    _upload_id: Optional[str]
    data: dict[str, Any]  # all user columns

class PaginatedRows(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
```

### 2. `src/backend/app/routers/data.py`

**`GET /api/tables/{table_name}/rows`**
- Query params: `page=1`, `page_size=50`, `include_deleted=false`
- Execute raw `SELECT * FROM "{table_name}" WHERE is_deleted=0` (or without filter if `include_deleted=true`)
- Return `PaginatedRows`.

**`POST /api/tables/{table_name}/rows`**
- Accept `RowInsert` body.
- Generate `_row_id = str(uuid4())`.
- Build parameterized `INSERT INTO "{table_name}" ...`.
- Write one `AuditLog` entry per column with `operation="INSERT"`, `old_value=None`, `new_value=str(value)`.
- Return `201` with inserted row dict.

**`PUT /api/tables/{table_name}/rows/{row_id}`**
- Accept `RowUpdate` body.
- Fetch current row; return `404` if not found.
- Build parameterized `UPDATE "{table_name}" SET ... WHERE _row_id=:row_id`.
- Write one `AuditLog` entry per **changed** column with `operation="UPDATE"`.
- Return updated row dict.

**`DELETE /api/tables/{table_name}/rows/{row_id}`**
- Execute `UPDATE "{table_name}" SET is_deleted=1 WHERE _row_id=:row_id`.
- Return `404` if row not found.
- Write one `AuditLog` entry with `column_name="is_deleted"`, `old_value="0"`, `new_value="1"`, `operation="DELETE"`.
- Return `204 No Content`.

### 3. Audit Helper

```python
async def _write_audit(db, table_name, row_id, column_name, old_value, new_value, operation):
    entry = AuditLog(
        table_name=table_name,
        row_id=row_id,
        column_name=column_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        operation=operation,
    )
    db.add(entry)
```

</instructions>

---

## 🚫 Out of Scope
<out_of_scope>

- Schema validation of inserted values against `schema_definitions` (deferred — ingestion pipeline handles this at upload time).
- Filtering/sorting beyond `include_deleted` (deferred to T-008 frontend needs).
- Export endpoint (T-006).
- Frontend DataTable (T-008).

</out_of_scope>

---

*Task authored by ADSP-Builder on 2026-03-16T22:21:00Z.*
