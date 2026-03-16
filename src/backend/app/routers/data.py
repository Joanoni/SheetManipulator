import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.schema_definition import SchemaDefinition
from app.schemas.audit import AuditLogRead
from app.schemas.data_row import PaginatedRows, RowInsert, RowUpdate

router = APIRouter()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _verify_table_exists(table_name: str, db: AsyncSession) -> None:
    """Raises HTTP 404 if table_name has no rows in schema_definitions."""
    result = await db.execute(
        select(SchemaDefinition.table_system_name)
        .where(SchemaDefinition.table_system_name == table_name)
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Table not found")


async def _fetch_row(table_name: str, row_id: str, db: AsyncSession) -> dict[str, Any]:
    """Return the raw row dict or raise 404."""
    result = await db.execute(
        text(f'SELECT * FROM "{table_name}" WHERE _row_id = :row_id'),
        {"row_id": row_id},
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Row not found")
    return dict(row)


# ---------------------------------------------------------------------------
# GET /api/tables/{table_name}/rows
# ---------------------------------------------------------------------------

@router.get("/tables/{table_name}/rows", response_model=PaginatedRows)
async def list_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> PaginatedRows:
    await _verify_table_exists(table_name, db)

    where_clause = "" if include_deleted else "WHERE is_deleted = 0"
    offset = (page - 1) * page_size

    count_result = await db.execute(
        text(f'SELECT COUNT(*) FROM "{table_name}" {where_clause}')
    )
    total: int = count_result.scalar_one()

    rows_result = await db.execute(
        text(
            f'SELECT * FROM "{table_name}" {where_clause} '
            f"LIMIT :limit OFFSET :offset"
        ),
        {"limit": page_size, "offset": offset},
    )
    items = [dict(r) for r in rows_result.mappings().all()]

    return PaginatedRows(items=items, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# POST /api/tables/{table_name}/rows
# ---------------------------------------------------------------------------

@router.post("/tables/{table_name}/rows", status_code=201)
async def insert_row(
    table_name: str,
    body: RowInsert,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await _verify_table_exists(table_name, db)

    # Fetch schema columns to validate mandatory fields
    schema_result = await db.execute(
        select(SchemaDefinition).where(
            SchemaDefinition.table_system_name == table_name
        )
    )
    columns = schema_result.scalars().all()

    for col in columns:
        if col.is_mandatory and col.column_system_name not in body.data:
            raise HTTPException(
                status_code=422,
                detail=f"Missing mandatory column: {col.column_system_name}",
            )

    row_id = str(uuid.uuid4())

    # Build INSERT
    user_cols = list(body.data.keys())
    all_col_names = ["_row_id", "is_deleted", "_upload_id"] + user_cols
    all_values: dict[str, Any] = {
        "_row_id": row_id,
        "is_deleted": 0,
        "_upload_id": None,
    }
    all_values.update(body.data)

    col_list = ", ".join(f'"{c}"' for c in all_col_names)
    param_list = ", ".join(f":{c}" for c in all_col_names)

    await db.execute(
        text(f'INSERT INTO "{table_name}" ({col_list}) VALUES ({param_list})'),
        all_values,
    )

    # Audit entries — one per user column
    for col_name, value in body.data.items():
        db.add(
            AuditLog(
                table_name=table_name,
                row_id=row_id,
                column_name=col_name,
                old_value=None,
                new_value=str(value) if value is not None else None,
                operation="INSERT",
            )
        )

    await db.commit()

    # Return inserted row
    inserted = await _fetch_row(table_name, row_id, db)
    return inserted


# ---------------------------------------------------------------------------
# PUT /api/tables/{table_name}/rows/{row_id}
# ---------------------------------------------------------------------------

@router.put("/tables/{table_name}/rows/{row_id}")
async def update_row(
    table_name: str,
    row_id: str,
    body: RowUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await _verify_table_exists(table_name, db)

    current = await _fetch_row(table_name, row_id, db)
    if current.get("is_deleted"):
        raise HTTPException(status_code=404, detail="Row not found")

    changed: dict[str, Any] = {}
    for col_name, new_val in body.data.items():
        old_val = current.get(col_name)
        if str(old_val) != str(new_val) if old_val is not None else new_val is not None:
            changed[col_name] = (old_val, new_val)

    if not changed:
        return current

    set_clause = ", ".join(f'"{c}" = :{c}' for c in changed)
    params: dict[str, Any] = {c: v[1] for c, v in changed.items()}
    params["_row_id"] = row_id

    await db.execute(
        text(f'UPDATE "{table_name}" SET {set_clause} WHERE _row_id = :_row_id'),
        params,
    )

    for col_name, (old_val, new_val) in changed.items():
        db.add(
            AuditLog(
                table_name=table_name,
                row_id=row_id,
                column_name=col_name,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
                operation="UPDATE",
            )
        )

    await db.commit()

    updated = await _fetch_row(table_name, row_id, db)
    return updated


# ---------------------------------------------------------------------------
# DELETE /api/tables/{table_name}/rows/{row_id}
# ---------------------------------------------------------------------------

@router.delete("/tables/{table_name}/rows/{row_id}", status_code=204)
async def delete_row(
    table_name: str,
    row_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _verify_table_exists(table_name, db)

    current = await _fetch_row(table_name, row_id, db)

    if current.get("is_deleted"):
        raise HTTPException(status_code=409, detail="Row already deleted")

    await db.execute(
        text(f'UPDATE "{table_name}" SET is_deleted = 1 WHERE _row_id = :row_id'),
        {"row_id": row_id},
    )

    db.add(
        AuditLog(
            table_name=table_name,
            row_id=row_id,
            column_name="is_deleted",
            old_value="0",
            new_value="1",
            operation="DELETE",
        )
    )

    await db.commit()


# ---------------------------------------------------------------------------
# GET /api/tables/{table_name}/audit
# ---------------------------------------------------------------------------

@router.get("/tables/{table_name}/audit", response_model=list[AuditLogRead])
async def get_audit(
    table_name: str,
    row_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogRead]:
    await _verify_table_exists(table_name, db)

    query = (
        select(AuditLog)
        .where(AuditLog.table_name == table_name)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    if row_id is not None:
        query = query.where(AuditLog.row_id == row_id)

    result = await db.execute(query)
    entries = result.scalars().all()
    return [AuditLogRead.model_validate(e) for e in entries]
