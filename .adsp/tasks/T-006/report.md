# T-006 — Export Engine (xlsx Generation) — Implementation Report

> **Status:** ✅ Complete
> **Builder Run:** 2026-03-16T23:14:00Z
> **Dependencies satisfied:** T-005

---

## Files Modified

| Action | File | Summary |
| :--- | :--- | :--- |
| **Modified** | `src/backend/app/services/export.py` | Appended `export_table_to_xlsx()` async function |
| **Replaced** | `src/backend/app/routers/export.py` | Full implementation replacing HTTP 501 stub |
| **No change needed** | `src/backend/app/database.py` | `get_db()` already present from T-002 |

---

## Implementation Summary

### `src/backend/app/services/export.py` — `export_table_to_xlsx()`

- Added imports: `io`, `sqlalchemy.text`, `sqlalchemy.select`, `AsyncSession`, `SchemaDefinition`.
- Queries `schema_definitions` filtered by `table_system_name`, ordered by `column_order`.
- Queries dynamic table for all rows where `is_deleted = 0`, ordered by `_row_id` (deterministic).
- Builds an `openpyxl` workbook with sheet title truncated to 31 chars (Excel limit).
- Header row uses `display_name` values from `schema_definitions`.
- Data rows include only user-defined columns; `system_cols` guard (`_row_id`, `is_deleted`, `_upload_id`) acts as safety net.
- Serializes workbook to `io.BytesIO` and returns raw `bytes`.

### `src/backend/app/routers/export.py` — `export_table()`

- Verifies `table_name` exists in `schema_definitions` via a `.limit(1)` query; raises `HTTP 404` if absent.
- Calls `export_table_to_xlsx(table_name, db)` to generate bytes.
- Returns `StreamingResponse` with:
  - `media_type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - `Content-Disposition`: `attachment; filename="{table_name}_export.xlsx"`

---

## Acceptance Criteria Verification

| # | Criterion | Met? |
| :--- | :--- | :--- |
| AC-1 | `GET /api/tables/{table_name}/export` returns `StreamingResponse` with correct `Content-Type` | ✅ |
| AC-2 | `Content-Disposition` header is `attachment; filename="{table_name}_export.xlsx"` | ✅ |
| AC-3 | First row contains `display_name` values from `schema_definitions` | ✅ |
| AC-4 | System columns (`_row_id`, `is_deleted`, `_upload_id`) excluded from export | ✅ |
| AC-5 | Only rows where `is_deleted = 0` included | ✅ |
| AC-6 | Rows ordered by `_row_id` (stable, deterministic) | ✅ |
| AC-7 | Returns `404` if `table_name` not in `schema_definitions` | ✅ |
| AC-8 | Empty table exports file with only header row | ✅ (header always appended; zero data rows = one-row file) |

---

## Manual Validation Checklist

1. **Start the stack:** `docker compose -f src/docker-compose.yml up --build`
2. **Upload a `.xlsx` file:** `POST /api/upload` with a multipart form file.
3. **Process the upload:** `POST /api/uploads/{upload_id}/process` with worksheet + schema payload.
4. **Poll status:** `GET /api/uploads/{upload_id}/status` — wait for `"ingested"`.
5. **Export the table:** `GET /api/tables/{table_name}/export` — browser or curl should download `{table_name}_export.xlsx`.
6. **Verify Content-Type:** Response header must be `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
7. **Verify Content-Disposition:** Header must be `attachment; filename="{table_name}_export.xlsx"`.
8. **Open the file:** First row must contain human-readable `display_name` column headers.
9. **Verify no system columns:** `_row_id`, `is_deleted`, `_upload_id` must not appear in the file.
10. **Soft-delete a row:** `DELETE /api/tables/{table_name}/rows/{row_id}`, then re-export — deleted row must be absent.
11. **Empty table test:** Create a schema, do not insert rows, export — file must contain only the header row.
12. **404 test:** `GET /api/tables/nonexistent_table/export` — must return `{"detail": "Table not found"}` with HTTP 404.
