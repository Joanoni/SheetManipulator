from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/schemas", status_code=501)
async def list_schemas():
    """GET /api/schemas — list all table schemas. Implemented in T-004."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.post("/schemas", status_code=501)
async def create_schema():
    """POST /api/schemas — create new table schema + trigger DDL. Implemented in T-004."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.get("/schemas/{table_name}", status_code=501)
async def get_schema(table_name: str):
    """GET /api/schemas/{table_name} — get column definitions. Implemented in T-004."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.put("/schemas/{table_name}/columns/{column_id}", status_code=501)
async def update_column(table_name: str, column_id: int):
    """PUT /api/schemas/{table_name}/columns/{column_id} — update display_name. Implemented in T-004."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})
