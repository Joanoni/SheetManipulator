from sqlalchemy import Column, String, DateTime, func
from app.database import Base


class UploadRegistry(Base):
    __tablename__ = "upload_registry"

    upload_id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    # status values: pending | validating | error | ingested
    status = Column(String, nullable=False, default="pending")
    error_report_path = Column(String, nullable=True)
