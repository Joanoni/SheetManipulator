"""
Validation engine for ingested worksheet data.
Short-circuits at MAX_ERRORS (1,000) to avoid unbounded processing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

MAX_ERRORS = 1000

# Accepted truthy/falsy string representations for Boolean columns
_BOOL_VALUES = {True, False, 1, 0, "true", "false", "1", "0"}

# Date formats tried in order for Date columns
_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
]


@dataclass
class ValidationError:
    original_line_index: int
    column: str          # display_name of the failing column
    original_value: str
    error_reason: str


def _get_cell(row: tuple, headers: list, column_system_name: str) -> Any:
    """Return the cell value for a given column_system_name from a row tuple."""
    try:
        idx = headers.index(column_system_name)
        return row[idx] if idx < len(row) else None
    except ValueError:
        return None


def _validate_cell(value: Any, col_def) -> str | None:
    """
    Validate a single cell value against its column definition.
    Returns an error message string, or None if valid.
    """
    # Mandatory check (applies to all types)
    if col_def.is_mandatory and (value is None or str(value).strip() == ""):
        return "Missing required value"

    # If value is empty/None and not mandatory, skip type checks
    if value is None or str(value).strip() == "":
        return None

    data_type = col_def.data_type

    if data_type == "Integer":
        try:
            int(value)
        except (ValueError, TypeError):
            return f"Expected Integer, got '{value}'"

    elif data_type == "Float":
        try:
            float(value)
        except (ValueError, TypeError):
            return f"Expected Float, got '{value}'"

    elif data_type == "Boolean":
        # Accept native bool, int 0/1, and string representations
        if isinstance(value, bool):
            return None
        if isinstance(value, int) and value in (0, 1):
            return None
        if str(value).lower() not in {"true", "false", "1", "0"}:
            return f"Expected Boolean, got '{value}'"

    elif data_type == "Date":
        str_value = str(value).strip()
        parsed = False
        for fmt in _DATE_FORMATS:
            try:
                datetime.strptime(str_value, fmt)
                parsed = True
                break
            except ValueError:
                continue
        if not parsed:
            return f"Expected Date (YYYY-MM-DD), got '{value}'"

    # String type — no additional validation beyond mandatory check
    return None


def validate_worksheet(ws, schema: list) -> list[ValidationError]:
    """
    Validate all rows in an openpyxl worksheet against the provided schema.

    Args:
        ws: An openpyxl worksheet object (read-only or normal).
        schema: List of SchemaDefinition ORM instances for the target table.

    Returns:
        A list of ValidationError instances. Empty list means data is clean.
        Halts accumulation after MAX_ERRORS errors.
    """
    errors: list[ValidationError] = []

    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        # Empty worksheet — nothing to validate
        return errors

    headers = [cell for cell in header_row]

    for row_idx, row in enumerate(rows_iter, start=2):
        if len(errors) >= MAX_ERRORS:
            break

        for col_def in schema:
            cell_value = _get_cell(row, headers, col_def.column_system_name)
            error_msg = _validate_cell(cell_value, col_def)
            if error_msg:
                errors.append(
                    ValidationError(
                        original_line_index=row_idx,
                        column=col_def.display_name,
                        original_value=str(cell_value),
                        error_reason=error_msg,
                    )
                )
                if len(errors) >= MAX_ERRORS:
                    break

    return errors
