from pydantic import BaseModel
from typing import Literal


DataType = Literal["String", "Integer", "Float", "Boolean", "Date"]


class ColumnDefinitionCreate(BaseModel):
    column_system_name: str
    display_name: str
    data_type: DataType
    is_mandatory: bool = False
    is_primary_key: bool = False
    column_order: int


class SchemaCreate(BaseModel):
    table_system_name: str
    columns: list[ColumnDefinitionCreate]


class ColumnDefinitionRead(ColumnDefinitionCreate):
    id: int
    table_system_name: str

    model_config = {"from_attributes": True}
