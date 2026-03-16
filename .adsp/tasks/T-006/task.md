# T-006 — Export Engine (xlsx Generation)

> **Layer:** Backend
> **Dependencies:** T-005
> **Complexity:** Low
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Replace the HTTP 501 stub in [`src/backend/app/routers/export.py`](src/backend/app/routers/export.py) with a working export endpoint that streams a `.xlsx` file containing all non-deleted rows from a dynamic table. Column headers must use `display_name` values from `schema_definitions` (not raw `column_system_name`). The existing [`src/backend/app/services/export.py`](src/backend/app/services/export.py) already handles error-report generation — add a second function for live-data export.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `GET /api/tables/{table_name}/export` returns a `StreamingResponse` with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Browser downloads a `.xlsx` file |
| AC-2 | `Content-Disposition` header is `attachment; filename="{table_name}_export.xlsx"` | Filename matches table name |
| AC-3 | First row of the worksheet contains `display_name` values from `schema_definitions` | Headers are human-readable |
| AC-4 | System columns (`_row_id`, `is_deleted`, `_upload_id`) are **excluded** from the export | Only user-defined columns appear |
| AC-5 | Only rows where `is_deleted = 0` are included | Soft-deleted rows absent from file |
| AC-6 | Rows are ordered by `_row_id` (stable, deterministic order) | Row order is consistent across calls |
| AC-7 | Returns `404` if `table_name` does not exist in `schema_definitions` | Error response `{"detail": "Table not found"}` |
| AC-8 | Empty table (zero data rows) exports a file with only the header row | Valid `.xlsx` with one row |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. Add `export_table_to_xlsx()` to `src/backend/app/services/export.py`

The existing file already contains `generate_error_report()`. Append a second function:

```python
import io
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schema_definition import SchemaDefinition

async def export_table_to_xlsx(
    table_name: str,
    db: AsyncSession,
) -> bytes:
    """
    Generates an in-memory .xlsx file from all non-deleted rows of a dynamic table.

    Column headers use display_name from schema_definitions.
    System columns (_row_id, is_deleted, _upload_id) are excluded.
    Returns raw bytes suitable for StreamingResponse.
    """
    # 1. Fetch schema ordered by column_order
    result = await db.execute(
        select(SchemaDefinition)
        .where(SchemaDefinition.table_system_name == table_name)
        .order_by(SchemaDefinition.column_order)
    )
    columns: list[SchemaDefinition] = list(result.scalars().all())

    # 2. Fetch non-deleted rows ordered by _row_id
    rows_result = await db.execute(
        text(f'SELECT * FROM "{table_name}" WHERE is_deleted = 0 ORDER BY "_row_id"')
    )
    rows = rows_result.mappings().all()

    # 3. Build workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = table_name[:31]  # Excel sheet name limit: 31 chars

    # Header row — display_name values only
    headers = [col.display_name for col in columns]
    ws.append(headers)

    # Data rows — user columns only, in column_order sequence
    system_cols = {"_row_id", "is_deleted", "_upload_id"}
    for row in rows:
        row_data = [
            row.get(col.column_system_name)
            for col in columns
            if col.column_system_name not in system_cols
        ]
        ws.append(row_data)

    # 4. Serialize to bytes
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
```

### 2. Replace `src/backend/app/routers/export.py`

```python
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.schema_definition import SchemaDefinition
from app.services.export import export_table_to_xlsx

router = APIRouter()

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/tables/{table_name}/export")
async def export_table(
    table_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream a .xlsx file of all non-deleted rows for the given table."""
    # Verify table exists
    result = await db.execute(
        select(SchemaDefinition.table_system_name)
        .where(SchemaDefinition.table_system_name == table_name)
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Table not found")

    xlsx_bytes = await export_table_to_xlsx(table_name, db)

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{table_name}_export.xlsx"'
        },
    )
```

### 3. Verify `get_db` dependency exists in `src/backend/app/database.py`

The `data.py` router (T-005) will also need `get_db`. Confirm it is defined as:

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

If it does not exist, add it to [`src/backend/app/database.py`](src/backend/app/database.py) as part of this task.

### 4. Column Filtering Logic

The `columns` list from `schema_definitions` contains only user-defined columns — system columns (`_row_id`, `is_deleted`, `_upload_id`) are **never** stored in `schema_definitions`. The `system_cols` guard in the service function is a safety net only.

</instructions>

---

## 📁 Files to Create / Modify
<files>

| Action | File | Notes |
| :--- | :--- | :--- |
| **Modify** | `src/backend/app/services/export.py` | Append `export_table_to_xlsx()` function |
| **Replace** | `src/backend/app/routers/export.py` | Full implementation (replaces 501 stub) |
| **Modify (if needed)** | `src/backend/app/database.py` | Add `get_db()` async generator if absent |

</files>

---

## 🚫 Out of Scope
<out_of_scope>

- Preserving original `.xlsx` formatting or styles from the source file.
- Exporting soft-deleted rows (always excluded).
- Filtering/sorting query parameters on the export endpoint.
- Frontend export button (T-008).

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T22:43:00Z.*
