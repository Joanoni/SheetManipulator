from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/upload", status_code=501)
async def upload_file():
    """POST /api/upload — multipart .xlsx upload. Implemented in T-003."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.get("/uploads/{upload_id}/worksheets", status_code=501)
async def list_worksheets(upload_id: str):
    """GET /api/uploads/{upload_id}/worksheets — list sheet names. Implemented in T-003."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.post("/uploads/{upload_id}/process", status_code=501)
async def process_upload(upload_id: str):
    """POST /api/uploads/{upload_id}/process — trigger ingestion. Implemented in T-003."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})


@router.get("/uploads/{upload_id}/status", status_code=501)
async def upload_status(upload_id: str):
    """GET /api/uploads/{upload_id}/status — poll ingestion status. Implemented in T-003."""
    return JSONResponse(status_code=501, content={"detail": "not implemented"})
