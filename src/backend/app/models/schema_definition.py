from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from app.database import Base


class SchemaDefinition(Base):
    __tablename__ = "schema_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_system_name = Column(String, nullable=False)
    column_system_name = Column(String, nullable=False)  # IMMUTABLE after creation
    display_name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)  # String|Integer|Float|Boolean|Date
    is_mandatory = Column(Boolean, nullable=False, default=False)
    is_primary_key = Column(Boolean, nullable=False, default=False)
    column_order = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("table_system_name", "column_system_name"),
    )
