from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UploadRegistryRead(BaseModel):
    upload_id: str
    original_filename: str
    timestamp: datetime
    status: str
    error_report_path: Optional[str] = None

    model_config = {"from_attributes": True}


class ProcessRequest(BaseModel):
    """Body for POST /api/uploads/{upload_id}/process."""
    worksheet_name: str
    table_system_name: str
