from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/tables/{table_name}/export", status_code=501)
async def export_table(table_name: str):
    """GET /api/tables/{table_name}/export — stream .xlsx of non-deleted rows. Implemented in T-006."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})
