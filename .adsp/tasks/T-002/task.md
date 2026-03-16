# T-002 — Backend Core: DB Models + FastAPI App Factory

> **Layer:** Backend
> **Dependencies:** T-001
> **Complexity:** Medium
> **Status:** 🟡 Pending

---

## 🎯 Objective
<objective>

Implement the SQLAlchemy ORM models for all static tables (`upload_registry`, `schema_definitions`, `audit_log`), wire up the async database engine, and register the router skeleton so the application is ready to receive feature implementations in T-003 and T-004.

</objective>

---

## 📋 Acceptance Criteria
<acceptance_criteria>

| # | Criterion | Verification |
| :--- | :--- | :--- |
| AC-1 | `database.py` creates async engine from `DATABASE_URL` env var | App starts without error |
| AC-2 | All 3 static ORM models are defined and importable | `python -c "from app.models import *"` |
| AC-3 | `alembic` or startup `create_all` creates tables in `/data/database.sqlite` on first run | `sqlite3 /data/database.sqlite .tables` shows all 3 tables |
| AC-4 | Pydantic schemas exist for `UploadRegistry`, `SchemaDefinition`, `AuditLog` | Import check passes |
| AC-5 | Router modules (`upload`, `schema`, `data`, `export`) are registered on the app with correct prefixes | `GET /docs` shows all route groups |
| AC-6 | `GET /health` still returns `{"status": "ok"}` | `curl http://localhost:8000/health` |

</acceptance_criteria>

---

## 🔩 Implementation Instructions
<instructions>

### 1. `src/backend/app/database.py`
```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////data/database.sqlite")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 2. `src/backend/app/models/upload_registry.py`
```python
from sqlalchemy import Column, String, DateTime, func
from app.database import Base

class UploadRegistry(Base):
    __tablename__ = "upload_registry"
    upload_id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="pending")
    # status values: pending | validating | error | ingested
    error_report_path = Column(String, nullable=True)
```

### 3. `src/backend/app/models/schema_definition.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from app.database import Base

class SchemaDefinition(Base):
    __tablename__ = "schema_definitions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_system_name = Column(String, nullable=False)
    column_system_name = Column(String, nullable=False)  # IMMUTABLE
    display_name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)  # String|Integer|Float|Boolean|Date
    is_mandatory = Column(Boolean, nullable=False, default=False)
    is_primary_key = Column(Boolean, nullable=False, default=False)
    column_order = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("table_system_name", "column_system_name"),)
```

### 4. `src/backend/app/models/audit_log.py`
```python
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
```

### 5. `src/backend/app/models/__init__.py`
```python
from .upload_registry import UploadRegistry
from .schema_definition import SchemaDefinition
from .audit_log import AuditLog
```

### 6. Pydantic Schemas (`src/backend/app/schemas/`)

**`upload.py`**
```python
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
```

**`schema_definition.py`**
```python
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
```

**`audit.py`**
```python
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
```

### 7. Router Registration in `src/backend/app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import upload, schema, data, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="SheetManipulator API", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(schema.router, prefix="/api", tags=["schema"])
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(export.router, prefix="/api", tags=["export"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 8. Router Stubs
Each router file in `src/backend/app/routers/` must exist with an `APIRouter` instance and at least one placeholder route returning `{"detail": "not implemented"}` with HTTP 501. This ensures `/docs` renders all route groups.

</instructions>

---

## 🚫 Out of Scope
<out_of_scope>

- No actual route logic (handled in T-003, T-004, T-005, T-006).
- No dynamic table creation (handled in T-004).
- No frontend changes.

</out_of_scope>

---

*Task authored by ADSP-Architect on 2026-03-16T21:34:15Z.*
