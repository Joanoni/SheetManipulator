# T-005 — Implementation Report: Data CRUD API + Audit Trail

> **Builder Run:** 2026-03-16T22:22:00Z
> **Status:** ✅ Complete

---

## Files Created / Modified

| File | Action | Description |
| :--- | :--- | :--- |
| `src/backend/app/schemas/data_row.py` | Created | `RowInsert`, `RowUpdate`, `PaginatedRows` Pydantic models |
| `src/backend/app/routers/data.py` | Modified | Full CRUD implementation replacing 501 stubs |

---

## Implementation Summary

### `src/backend/app/schemas/data_row.py`
- **`RowInsert`** — `data: dict[str, Any]` for POST body; system columns excluded by server.
- **`RowUpdate`** — `data: dict[str, Any]` for PUT body; partial update (only supplied keys updated).
- **`PaginatedRows`** — `items`, `total`, `page`, `page_size` for list response.

### `src/backend/app/routers/data.py`

#### Internal helpers
- **`_validate_table_name()`** — regex guard `^[a-z][a-z0-9_]*$` to prevent SQL injection via table name parameter.
- **`_table_exists()`** — queries `sqlite_master` to confirm table presence before any DML.
- **`_fetch_row()`** — parameterized `SELECT * WHERE _row_id = :row_id`; returns `dict` or `None`.
- **`_write_audit()`** — appends an `AuditLog` ORM instance to the session (not yet committed).

#### `GET /api/tables/{table_name}/rows`
- Query params: `page` (default 1), `page_size` (default 50, max 500), `include_deleted` (default false).
- Two queries: `COUNT(*)` for total, then `SELECT * LIMIT/OFFSET` for page.
- Returns `PaginatedRows`.

#### `POST /api/tables/{table_name}/rows`
- Strips system columns from payload.
- Auto-generates `_row_id` via `uuid4()`.
- Parameterized `INSERT` with positional bind params (`p0`, `p1`, …).
- Writes one `INSERT` audit entry per user column (`old_value=None`).
- Returns `201` with the freshly fetched row dict.

#### `PUT /api/tables/{table_name}/rows/{row_id}`
- Fetches current row; returns `404` if absent.
- Computes diff: only columns where `str(old) != str(new)` are updated.
- Parameterized `UPDATE SET … WHERE _row_id = :row_id`.
- Writes one `UPDATE` audit entry per changed column with correct `old_value`/`new_value`.
- Returns updated row dict.

#### `DELETE /api/tables/{table_name}/rows/{row_id}`
- Fetches current row; returns `404` if absent.
- `UPDATE … SET is_deleted = 1`.
- Writes one `DELETE` audit entry on `is_deleted` column.
- Returns `204 No Content`.

---

## Manual Validation Checklist

| # | Step | Expected Result |
| :--- | :--- | :--- |
| 1 | `POST /api/schemas` to create a table `test_table` with columns `name` (String) and `age` (Integer) | `201` response; `test_table` visible in SQLite |
| 2 | `POST /api/tables/test_table/rows` with `{"data": {"name": "Alice", "age": 30}}` | `201` response; row returned with `_row_id` UUID |
| 3 | `GET /api/tables/test_table/rows` | `items` contains the inserted row; `total=1` |
| 4 | `PUT /api/tables/test_table/rows/{row_id}` with `{"data": {"age": 31}}` | `200` response; `age` updated to `31` |
| 5 | `GET /api/tables/test_table/rows` after PUT | Row shows `age=31` |
| 6 | `DELETE /api/tables/test_table/rows/{row_id}` | `204` response |
| 7 | `GET /api/tables/test_table/rows` after DELETE | `items=[]`, `total=0` |
| 8 | `GET /api/tables/test_table/rows?include_deleted=true` | Deleted row appears with `is_deleted=1` |
| 9 | Query `audit_log` table | Entries for INSERT (2 cols), UPDATE (1 col), DELETE (1 col) = 4 rows total |
| 10 | `GET /api/tables/nonexistent/rows` | `404` response |
| 11 | `DELETE /api/tables/test_table/rows/bad-uuid` | `404` response |
| 12 | `POST /api/tables/INVALID!/rows` | `400` response (invalid table name) |
