"""
Export service — generates Excel error reports from validation failures
and live-data exports from dynamic tables.
"""
from __future__ import annotations

import io
import openpyxl
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema_definition import SchemaDefinition
from app.services.validation import ValidationError


def generate_error_report(errors: list[ValidationError], upload_id: str) -> str:
    """
    Write an Excel error report for a failed ingestion.

    Columns: original_line_index | column | original_value | error_reason

    Args:
        errors: List of ValidationError instances (≤ 1,000).
        upload_id: UUID string used to build the output path.

    Returns:
        Relative URL path to the saved error report file, suitable for use
        with the /files/uploads static mount.
        Format: ``uploads/{upload_id}/error_report_{upload_id}.xlsx``
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Validation Errors"

    # Header row
    ws.append(["original_line_index", "column", "original_value", "error_reason"])

    for e in errors:
        ws.append([e.original_line_index, e.column, e.original_value, e.error_reason])

    abs_path = f"/data/uploads/{upload_id}/error_report_{upload_id}.xlsx"
    wb.save(abs_path)
    # Return a relative URL path so upload_registry.error_report_path is URL-ready
    return f"uploads/{upload_id}/error_report_{upload_id}.xlsx"


async def export_table_to_xlsx(
    table_name: str,
    db: AsyncSession,
) -> bytes:
    """
    Generates an in-memory .xlsx file from all non-deleted rows of a dynamic table.

    Column headers use display_name from schema_definitions.
    System columns (_row_id, is_deleted, _upload_id) are excluded.
    Returns raw bytes suitable for StreamingResponse.

    Args:
        table_name: The system name of the dynamic table.
        db: Active async database session.

    Returns:
        Raw bytes of the generated .xlsx workbook.
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
    # system_cols guard is a safety net; schema_definitions never stores system cols
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
