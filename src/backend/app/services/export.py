"""
Export service — generates Excel error reports from validation failures.
Full clean-data export (T-006) will be added in a later task.
"""
from __future__ import annotations

import openpyxl

from app.services.validation import ValidationError


def generate_error_report(errors: list[ValidationError], upload_id: str) -> str:
    """
    Write an Excel error report for a failed ingestion.

    Columns: original_line_index | column | original_value | error_reason

    Args:
        errors: List of ValidationError instances (≤ 1,000).
        upload_id: UUID string used to build the output path.

    Returns:
        Absolute path to the saved error report file.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Validation Errors"

    # Header row
    ws.append(["original_line_index", "column", "original_value", "error_reason"])

    for e in errors:
        ws.append([e.original_line_index, e.column, e.original_value, e.error_reason])

    path = f"/data/uploads/{upload_id}/error_report_{upload_id}.xlsx"
    wb.save(path)
    return path
