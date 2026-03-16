"""
Pydantic schemas for the Data CRUD API (T-005).

RowInsert  — body for POST /api/tables/{table_name}/rows
RowUpdate  — body for PUT  /api/tables/{table_name}/rows/{row_id}
PaginatedRows — response for GET /api/tables/{table_name}/rows
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class RowInsert(BaseModel):
    """Payload for inserting a new row into a dynamic table.

    ``data`` maps column_system_name → value.
    System columns (_row_id, is_deleted, _upload_id) must NOT be included;
    they are managed by the server.
    """

    data: dict[str, Any]


class RowUpdate(BaseModel):
    """Payload for updating an existing row.

    Only the fields present in ``data`` are updated.
    System columns are ignored even if supplied.
    """

    data: dict[str, Any]


class PaginatedRows(BaseModel):
    """Paginated response for list-rows endpoint."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
