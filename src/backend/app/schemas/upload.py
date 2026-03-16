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
