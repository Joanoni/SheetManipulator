from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuditLogRead(BaseModel):
    id: int
    table_name: str
    row_id: str
    column_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    operation: str
    timestamp: datetime

    model_config = {"from_attributes": True}
