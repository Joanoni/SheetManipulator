"""
Dynamic DDL service.

Translates schema_definitions rows into real SQLite tables at runtime.
Uses CREATE TABLE IF NOT EXISTS — fully idempotent.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema_definition import SchemaDefinition

DATA_TYPE_MAP: dict[str, str] = {
    "String": "TEXT",
    "Integer": "INTEGER",
    "Float": "REAL",
    "Boolean": "INTEGER",  # SQLite stores booleans as 0/1
    "Date": "TEXT",
}

# System columns always prepended to every dynamic table
_SYSTEM_COLUMNS = [
    '"_row_id" TEXT PRIMARY KEY',
    '"is_deleted" INTEGER NOT NULL DEFAULT 0',
    '"_upload_id" TEXT',
]


async def ensure_table_exists(
    table_system_name: str,
    columns: list[SchemaDefinition],
    db: AsyncSession,
) -> None:
    """
    Creates the dynamic table if it does not already exist.

    Always includes system columns: _row_id, is_deleted, _upload_id.
    User-defined columns are appended in column_order sequence.
    Uses CREATE TABLE IF NOT EXISTS — calling this function twice is safe.
    """
    col_defs = list(_SYSTEM_COLUMNS)

    for col in sorted(columns, key=lambda c: c.column_order):
        sqlite_type = DATA_TYPE_MAP.get(col.data_type, "TEXT")
        col_defs.append(f'"{col.column_system_name}" {sqlite_type}')

    ddl = (
        f'CREATE TABLE IF NOT EXISTS "{table_system_name}" '
        f"({', '.join(col_defs)})"
    )
    await db.execute(text(ddl))
    await db.commit()
