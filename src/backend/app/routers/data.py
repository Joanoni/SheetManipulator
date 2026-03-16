from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/tables/{table_name}/rows", status_code=501)
async def list_rows(table_name: str):
    """GET /api/tables/{table_name}/rows — paginated rows. Implemented in T-005."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.post("/tables/{table_name}/rows", status_code=501)
async def insert_row(table_name: str):
    """POST /api/tables/{table_name}/rows — insert row + audit entry. Implemented in T-005."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.put("/tables/{table_name}/rows/{row_id}", status_code=501)
async def update_row(table_name: str, row_id: str):
    """PUT /api/tables/{table_name}/rows/{row_id} — update row + audit entries. Implemented in T-005."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.delete("/tables/{table_name}/rows/{row_id}", status_code=501)
async def delete_row(table_name: str, row_id: str):
    """DELETE /api/tables/{table_name}/rows/{row_id} — soft delete + audit entry. Implemented in T-005."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})
