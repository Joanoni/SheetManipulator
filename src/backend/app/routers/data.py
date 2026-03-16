"""
Data CRUD API — T-005.

Routes:
  GET    /api/tables/{table_name}/rows              → list_rows()
  POST   /api/tables/{table_name}/rows              → insert_row()
  PUT    /api/tables/{table_name}/rows/{row_id}     → update_row()
  DELETE /api/tables/{table_name}/rows/{row_id}     → delete_row()

Every write operation produces one or more audit_log entries.
Soft deletes only — no physical row removal.
"""
from __future__ import annotations

import re
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.data_row import PaginatedRows, RowInsert, RowUpdate

router = APIRouter()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SYSTEM_COLUMNS = {"_row_id", "is_deleted", "_upload_id"}
_VALID_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_table_name(table_name: str) -> None:
    """Raise 400 if table_name contains characters that could enable SQL injection."""
    if not _VALID_NAME_RE.match(table_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name '{table_name}'. Must match ^[a-z][a-z0-9_]*$.",
        )


async def _table_exists(table_name: str, db: AsyncSession) -> bool:
    """Return True if the SQLite table exists."""
    result = await db.execute(
        text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
        ),
        {"name": table_name},
    )
    return result.fetchone() is not None


async def _fetch_row(
    table_name: str, row_id: str, db: AsyncSession
) -> Optional[dict[str, Any]]:
    """Return the row as a dict, or None if not found."""
    result = await db.execute(
        text(f'SELECT * FROM "{table_name}" WHERE _row_id = :row_id'),
        {"row_id": row_id},
    )
    row = result.fetchone()
    if row is None:
        return None
    return dict(row._mapping)


async def _write_audit(
    db: AsyncSession,
    table_name: str,
    row_id: str,
    column_name: str,
    old_value: Any,
    new_value: Any,
    operation: str,
) -> None:
    """Append a single audit_log entry (not yet committed)."""
    entry = AuditLog(
        table_name=table_name,
        row_id=row_id,
        column_name=column_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        operation=operation,
    )
    db.add(entry)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/tables/{table_name}/rows", response_model=PaginatedRows)
async def list_rows(
    table_name: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    include_deleted: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> PaginatedRows:
    """Return paginated rows from a dynamic table.

    By default only non-deleted rows are returned.
    Pass ``include_deleted=true`` to include soft-deleted rows.
    """
    _validate_table_name(table_name)

    if not await _table_exists(table_name, db):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    where_clause = "" if include_deleted else "WHERE is_deleted = 0"
    offset = (page - 1) * page_size

    # Total count
    count_result = await db.execute(
        text(f'SELECT COUNT(*) FROM "{table_name}" {where_clause}')
    )
    total: int = count_result.scalar_one()

    # Paginated rows
    rows_result = await db.execute(
        text(
            f'SELECT * FROM "{table_name}" {where_clause} '
            f"LIMIT :limit OFFSET :offset"
        ),
        {"limit": page_size, "offset": offset},
    )
    items = [dict(row._mapping) for row in rows_result.fetchall()]

    return PaginatedRows(items=items, total=total, page=page, page_size=page_size)


@router.post("/tables/{table_name}/rows", status_code=201)
async def insert_row(
    table_name: str,
    body: RowInsert,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Insert a new row into a dynamic table.

    - Auto-generates ``_row_id`` (UUID4).
    - Writes one ``INSERT`` audit entry per user-supplied column.
    - System columns in ``body.data`` are silently ignored.
    """
    _validate_table_name(table_name)

    if not await _table_exists(table_name, db):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    # Strip system columns from user payload
    user_data = {k: v for k, v in body.data.items() if k not in _SYSTEM_COLUMNS}

    row_id = str(uuid4())

    # Build INSERT
    all_columns = ["_row_id", "is_deleted"] + list(user_data.keys())
    all_values = [row_id, 0] + list(user_data.values())

    col_placeholders = ", ".join(f'"{c}"' for c in all_columns)
    val_placeholders = ", ".join(f":p{i}" for i in range(len(all_values)))
    params = {f"p{i}": v for i, v in enumerate(all_values)}

    await db.execute(
        text(
            f'INSERT INTO "{table_name}" ({col_placeholders}) '
            f"VALUES ({val_placeholders})"
        ),
        params,
    )

    # Audit: one entry per user column
    for col, val in user_data.items():
        await _write_audit(
            db,
            table_name=table_name,
            row_id=row_id,
            column_name=col,
            old_value=None,
            new_value=val,
            operation="INSERT",
        )

    await db.commit()

    # Return the freshly inserted row
    inserted = await _fetch_row(table_name, row_id, db)
    return inserted  # type: ignore[return-value]


@router.put("/tables/{table_name}/rows/{row_id}")
async def update_row(
    table_name: str,
    row_id: str,
    body: RowUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update specific columns of an existing row.

    - Only columns present in ``body.data`` are updated.
    - System columns are silently ignored.
    - Writes one ``UPDATE`` audit entry per **changed** column.
    - Returns ``404`` if the row does not exist.
    """
    _validate_table_name(table_name)

    if not await _table_exists(table_name, db):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    current = await _fetch_row(table_name, row_id, db)
    if current is None:
        raise HTTPException(
            status_code=404,
            detail=f"Row '{row_id}' not found in table '{table_name}'.",
        )

    # Strip system columns
    user_data = {k: v for k, v in body.data.items() if k not in _SYSTEM_COLUMNS}

    if not user_data:
        # Nothing to update — return current row unchanged
        return current

    # Identify changed columns only
    changed: dict[str, tuple[Any, Any]] = {}  # col → (old, new)
    for col, new_val in user_data.items():
        old_val = current.get(col)
        if str(old_val) != str(new_val):
            changed[col] = (old_val, new_val)

    if not changed:
        return current

    # Build UPDATE
    set_clauses = ", ".join(f'"{col}" = :v{i}' for i, col in enumerate(changed))
    params: dict[str, Any] = {f"v{i}": new for i, (_, new) in enumerate(changed.values())}
    params["row_id"] = row_id

    await db.execute(
        text(
            f'UPDATE "{table_name}" SET {set_clauses} WHERE "_row_id" = :row_id'
        ),
        params,
    )

    # Audit entries for changed columns
    for col, (old_val, new_val) in changed.items():
        await _write_audit(
            db,
            table_name=table_name,
            row_id=row_id,
            column_name=col,
            old_value=old_val,
            new_value=new_val,
            operation="UPDATE",
        )

    await db.commit()

    updated = await _fetch_row(table_name, row_id, db)
    return updated  # type: ignore[return-value]


@router.delete("/tables/{table_name}/rows/{row_id}", status_code=204)
async def delete_row(
    table_name: str,
    row_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a row by setting ``is_deleted = 1``.

    - Returns ``404`` if the row does not exist.
    - Writes one ``DELETE`` audit entry on ``is_deleted`` column.
    - Returns ``204 No Content`` on success.
    """
    _validate_table_name(table_name)

    if not await _table_exists(table_name, db):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    current = await _fetch_row(table_name, row_id, db)
    if current is None:
        raise HTTPException(
            status_code=404,
            detail=f"Row '{row_id}' not found in table '{table_name}'.",
        )

    await db.execute(
        text(
            f'UPDATE "{table_name}" SET "is_deleted" = 1 WHERE "_row_id" = :row_id'
        ),
        {"row_id": row_id},
    )

    await _write_audit(
        db,
        table_name=table_name,
        row_id=row_id,
        column_name="is_deleted",
        old_value=current.get("is_deleted", 0),
        new_value=1,
        operation="DELETE",
    )

    await db.commit()
