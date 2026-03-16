"""
Schema Management API router.

Routes:
  GET    /api/schemas                                   → list_schemas()
  POST   /api/schemas                                   → create_schema()
  GET    /api/schemas/{table_name}                      → get_schema()
  PUT    /api/schemas/{table_name}/columns/{column_id}  → update_column()
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schema_definition import SchemaDefinition
from app.schemas.schema_definition import (
    ColumnDefinitionRead,
    ColumnDisplayNameUpdate,
    SchemaCreate,
)
from app.services import dynamic_ddl

router = APIRouter()

# ── Validation helpers ────────────────────────────────────────────────────────

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_RESERVED_NAMES = {"_row_id", "is_deleted", "_upload_id"}
_MAX_NAME_LEN = 64
_VALID_DATA_TYPES = {"String", "Integer", "Float", "Boolean", "Date"}


def _validate_system_name(name: str, field: str) -> None:
    """Raise 422 if name does not match naming rules."""
    if len(name) > _MAX_NAME_LEN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} '{name}' exceeds maximum length of {_MAX_NAME_LEN} characters.",
        )
    if not _NAME_RE.match(name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"{field} '{name}' is invalid. "
                "Must match ^[a-z][a-z0-9_]*$ (lowercase letters, digits, underscores; "
                "must start with a letter)."
            ),
        )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/schemas", status_code=status.HTTP_200_OK)
async def list_schemas(db: AsyncSession = Depends(get_db)) -> dict[str, list[str]]:
    """Return all distinct table_system_name values."""
    result = await db.execute(
        select(SchemaDefinition.table_system_name).distinct()
    )
    tables: list[str] = [row[0] for row in result.all()]
    return {"tables": tables}


@router.post("/schemas", status_code=status.HTTP_201_CREATED)
async def create_schema(
    body: SchemaCreate,
    db: AsyncSession = Depends(get_db),
) -> list[ColumnDefinitionRead]:
    """
    Create a new table schema and trigger DDL.

    Validates naming rules, checks for duplicates, inserts all column
    definitions in a single transaction, then calls ensure_table_exists().
    """
    # ── Validate table name ───────────────────────────────────────────────────
    _validate_system_name(body.table_system_name, "table_system_name")

    # ── Validate columns ──────────────────────────────────────────────────────
    if not body.columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one column definition is required.",
        )

    seen_names: set[str] = set()
    seen_orders: set[int] = set()

    for col in body.columns:
        # Reserved system column names
        if col.column_system_name in _RESERVED_NAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"column_system_name '{col.column_system_name}' is reserved "
                    "and cannot be used as a user-defined column name."
                ),
            )
        # Naming pattern
        _validate_system_name(col.column_system_name, "column_system_name")

        # Duplicate column_system_name within submission
        if col.column_system_name in seen_names:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Duplicate column_system_name '{col.column_system_name}' in request.",
            )
        seen_names.add(col.column_system_name)

        # Duplicate column_order within submission
        if col.column_order in seen_orders:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Duplicate column_order '{col.column_order}' in request.",
            )
        seen_orders.add(col.column_order)

    # ── Check for existing schema (conflict) ──────────────────────────────────
    existing = await db.execute(
        select(SchemaDefinition).where(
            SchemaDefinition.table_system_name == body.table_system_name
        )
    )
    if existing.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Schema for table '{body.table_system_name}' already exists. "
                "Use PUT to update individual columns."
            ),
        )

    # ── Insert all column definitions ─────────────────────────────────────────
    new_rows: list[SchemaDefinition] = []
    for col in body.columns:
        row = SchemaDefinition(
            table_system_name=body.table_system_name,
            column_system_name=col.column_system_name,
            display_name=col.display_name,
            data_type=col.data_type,
            is_mandatory=col.is_mandatory,
            is_primary_key=col.is_primary_key,
            column_order=col.column_order,
        )
        db.add(row)
        new_rows.append(row)

    await db.flush()  # Assign IDs without committing yet

    # ── Trigger DDL ───────────────────────────────────────────────────────────
    await dynamic_ddl.ensure_table_exists(body.table_system_name, new_rows, db)
    # ensure_table_exists commits internally; no extra commit needed here.

    await db.refresh(new_rows[0])  # Ensure IDs are populated
    for row in new_rows:
        await db.refresh(row)

    return [ColumnDefinitionRead.model_validate(row) for row in new_rows]


@router.get("/schemas/{table_name}", status_code=status.HTTP_200_OK)
async def get_schema(
    table_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[ColumnDefinitionRead]:
    """Return all column definitions for a table, ordered by column_order."""
    result = await db.execute(
        select(SchemaDefinition)
        .where(SchemaDefinition.table_system_name == table_name)
        .order_by(SchemaDefinition.column_order)
    )
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schema found for table '{table_name}'.",
        )

    return [ColumnDefinitionRead.model_validate(row) for row in rows]


@router.put(
    "/schemas/{table_name}/columns/{column_id}",
    status_code=status.HTTP_200_OK,
)
async def update_column(
    table_name: str,
    column_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ColumnDefinitionRead:
    """
    Update display_name for a column definition.

    Only `display_name` is mutable. Attempting to pass `column_system_name`
    returns 400 Bad Request.
    """
    # ── Guard: reject immutable field in body ─────────────────────────────────
    raw_body: dict[str, Any] = await request.json()
    if "column_system_name" in raw_body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="column_system_name is immutable and cannot be updated.",
        )

    # Parse and validate the allowed body
    body = ColumnDisplayNameUpdate(**raw_body)

    # ── Fetch the target row ──────────────────────────────────────────────────
    result = await db.execute(
        select(SchemaDefinition).where(
            SchemaDefinition.id == column_id,
            SchemaDefinition.table_system_name == table_name,
        )
    )
    row: SchemaDefinition | None = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column id={column_id} not found in table '{table_name}'.",
        )

    # ── Apply update ──────────────────────────────────────────────────────────
    row.display_name = body.display_name
    await db.commit()
    await db.refresh(row)

    return ColumnDefinitionRead.model_validate(row)
