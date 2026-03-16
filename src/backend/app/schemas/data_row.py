from pydantic import BaseModel
from typing import Any


class RowInsert(BaseModel):
    data: dict[str, Any]  # {column_system_name: value}


class RowUpdate(BaseModel):
    data: dict[str, Any]  # Only fields to update


class RowRead(BaseModel):
    _row_id: str
    is_deleted: bool
    _upload_id: str | None
    data: dict[str, Any]  # All user-defined columns


class PaginatedRows(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
