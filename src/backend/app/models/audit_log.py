from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False)
    row_id = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    operation = Column(String, nullable=False)  # INSERT|UPDATE|DELETE
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
