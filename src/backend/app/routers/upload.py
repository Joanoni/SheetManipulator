"""
Upload router — Ingestion Pipeline endpoints.

Routes:
  POST   /api/upload                          → upload_file()
  GET    /api/uploads/{upload_id}/worksheets  → get_worksheets()
  POST   /api/uploads/{upload_id}/process     → process_upload()
  GET    /api/uploads/{upload_id}/status      → get_status()
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

import openpyxl
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.upload_registry import UploadRegistry
from app.schemas.upload import ProcessRequest, UploadRegistryRead
from app.services.ingestion import run_ingestion_pipeline

router = APIRouter()

# Base directory for cold storage (matches Docker volume mount)
UPLOADS_BASE = "/data/uploads"


# ── POST /api/upload ──────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a multipart .xlsx upload.
    Archives the original file to cold storage and creates an upload_registry record.
    Returns: {"upload_id": str, "status": "pending"}
    """
    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are accepted.",
        )

    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(UPLOADS_BASE, upload_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Save original file
    file_path = os.path.join(upload_dir, "original.xlsx")
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Write metadata sidecar
    metadata = {
        "original_filename": file.filename,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(upload_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Persist to upload_registry
    record = UploadRegistry(
        upload_id=upload_id,
        original_filename=file.filename,
        status="pending",
    )
    db.add(record)
    await db.commit()

    return {"upload_id": upload_id, "status": "pending"}


# ── GET /api/uploads/{upload_id}/worksheets ───────────────────────────────────

@router.get("/uploads/{upload_id}/worksheets")
async def get_worksheets(upload_id: str):
    """
    Return the list of worksheet names in the uploaded workbook.
    """
    file_path = os.path.join(UPLOADS_BASE, upload_id, "original.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Upload not found.")

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        sheet_names = wb.sheetnames
        wb.close()
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not read workbook: {exc}",
        ) from exc

    return {"worksheets": sheet_names}


# ── POST /api/uploads/{upload_id}/process ────────────────────────────────────

@router.post("/uploads/{upload_id}/process", status_code=202)
async def process_upload(
    upload_id: str,
    body: ProcessRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger background ingestion for the selected worksheet.
    Immediately returns 202 Accepted; processing continues asynchronously.
    """
    # Verify upload exists
    result = await db.execute(
        select(UploadRegistry).where(UploadRegistry.upload_id == upload_id)
    )
    record: UploadRegistry | None = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Upload not found.")

    # Mark as validating
    record.status = "validating"
    await db.commit()

    # Dispatch background task
    background_tasks.add_task(
        run_ingestion_pipeline,
        upload_id,
        body.worksheet_name,
        body.table_system_name,
    )

    return JSONResponse(
        status_code=202,
        content={
            "upload_id": upload_id,
            "status": "validating",
            "detail": "Ingestion pipeline started.",
        },
    )


# ── GET /api/uploads/{upload_id}/status ──────────────────────────────────────

@router.get("/uploads/{upload_id}/status", response_model=UploadRegistryRead)
async def get_status(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Poll the current ingestion status for an upload.
    Returns the full UploadRegistryRead schema.
    """
    result = await db.execute(
        select(UploadRegistry).where(UploadRegistry.upload_id == upload_id)
    )
    record: UploadRegistry | None = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Upload not found.")

    return record
