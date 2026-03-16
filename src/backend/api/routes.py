"""
Dynamic CRUD API Routes for SheetManipulator.

All endpoints are entity-agnostic; the entity name is derived from the URL path.
Validation uses the dynamic Pydantic models from ModelFactory.
Dependencies are accessed via request.app.state (no module-level globals).
"""
import math
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import ValidationError

from backend.services.data_service import (
    DuplicateRecordError,
    RecordNotFoundError,
)

router = APIRouter()


def _entity_exists(app_state, entity_name: str) -> bool:
    """Check if entity_name is defined in the loaded config."""
    return any(e["name"] == entity_name for e in app_state.config.get("entities", []))


# ---------------------------------------------------------------------------
# Metadata Endpoint
# ---------------------------------------------------------------------------

@router.get("/api/config", summary="Get full config metadata")
def get_config(request: Request):
    """
    Returns the full configuration structure so the frontend can
    dynamically render forms, tables, and dropdowns.
    """
    return request.app.state.config


# ---------------------------------------------------------------------------
# Dynamic CRUD Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/{entity}", summary="List all records with pagination")
def list_records(
    entity: str,
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=1000, description="Records per page"),
):
    """Return paginated records for the given entity."""
    if not _entity_exists(request.app.state, entity):
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found in config.")

    service = request.app.state.data_service
    all_rows = service.get_all(entity)
    total = len(all_rows)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    page_data = all_rows[start:end]

    return {
        "entity": entity,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": page_data,
    }


@router.get("/api/{entity}/{record_id}", summary="Get a record by primary ID")
def get_record(entity: str, record_id: str, request: Request):
    """Return a single record identified by its primary ID."""
    if not _entity_exists(request.app.state, entity):
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found in config.")

    service = request.app.state.data_service
    try:
        record = service.get_by_id(entity, record_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return record


@router.post("/api/{entity}", summary="Create a new record", status_code=201)
async def create_record(entity: str, request: Request):
    """
    Create a new record for the given entity.
    The request body is validated against the dynamically generated Pydantic model.
    """
    if not _entity_exists(request.app.state, entity):
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found in config.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body.")

    # Validate against dynamic Pydantic model
    factory = request.app.state.model_factory
    try:
        Model = factory.get_model_for_entity(entity)
        validated = Model(**body)
        data = validated.model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    service = request.app.state.data_service
    try:
        result = service.create(entity, data)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return result


@router.put("/api/{entity}/{record_id}", summary="Update an existing record")
async def update_record(entity: str, record_id: str, request: Request):
    """
    Update a record identified by its primary ID.
    Accepts a partial or full body; primary key is always preserved.
    """
    if not _entity_exists(request.app.state, entity):
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found in config.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body.")

    service = request.app.state.data_service
    try:
        result = service.update(entity, record_id, body)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return result


@router.delete("/api/{entity}/{record_id}", summary="Delete a record")
def delete_record(entity: str, record_id: str, request: Request):
    """
    Delete a record identified by its primary ID.
    Returns the deleted record.
    """
    if not _entity_exists(request.app.state, entity):
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found in config.")

    service = request.app.state.data_service
    try:
        deleted = service.delete(entity, record_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"deleted": deleted}
