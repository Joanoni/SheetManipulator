"""
SheetManipulator FastAPI Application Entry Point.

Initialises the app, wires up the lifespan (Startup Integrity Check),
configures CORS, global exception handlers, and registers the router.
"""
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.api.routes import router
from backend.core.integrity import IntegrityCheckError, run_startup_integrity_check
from backend.core.locking import LockTimeoutException
from backend.core.model_factory import ModelFactory
from backend.services.data_service import (
    DataService,
    DuplicateRecordError,
    RecordNotFoundError,
)

# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------

# By default, config.json is at src/config.json relative to this file
_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
_DEFAULT_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")


def _resolve_config_path() -> str:
    return os.environ.get("SM_CONFIG_PATH", os.path.abspath(_DEFAULT_CONFIG_PATH))


def _resolve_base_dir() -> str:
    return os.environ.get("SM_BASE_DIR", os.path.abspath(_DEFAULT_BASE_DIR))


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(config_path: str = None, base_dir: str = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        config_path: Override config path (useful for testing).
        base_dir: Override base directory (useful for testing).
    """
    # Resolve final paths
    final_config_path = os.path.abspath(config_path) if config_path else _resolve_config_path()
    final_base_dir = os.path.abspath(base_dir) if base_dir else _resolve_base_dir()

    # ------------------------------------------------------------------
    # Lifespan
    # ------------------------------------------------------------------
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        On startup: run integrity check, init services, store in app.state.
        """
        # 1. Startup Integrity Check (Task 03)
        run_startup_integrity_check(final_config_path, base_dir=final_base_dir)

        # 2. Load config
        with open(final_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 3. Init services
        app.state.config = config
        app.state.data_service = DataService(final_config_path, base_dir=final_base_dir)
        app.state.model_factory = ModelFactory(final_config_path)

        yield
        # Cleanup (if needed in future)

    # ------------------------------------------------------------------
    # App Instance
    # ------------------------------------------------------------------
    application = FastAPI(
        title="SheetManipulator API",
        description=(
            "A configuration-driven CRUD API for .xlsx and .csv files. "
            "All schemas are generated dynamically from config.json."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Global Exception Handlers
    # ------------------------------------------------------------------

    @application.exception_handler(RecordNotFoundError)
    async def record_not_found_handler(request: Request, exc: RecordNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "entity": exc.entity_name, "id": str(exc.record_id)},
        )

    @application.exception_handler(DuplicateRecordError)
    async def duplicate_record_handler(request: Request, exc: DuplicateRecordError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "entity": exc.entity_name, "id": str(exc.record_id)},
        )

    @application.exception_handler(LockTimeoutException)
    async def lock_timeout_handler(request: Request, exc: LockTimeoutException):
        return JSONResponse(
            status_code=423,
            content={"detail": str(exc), "file": exc.file_path},
        )

    @application.exception_handler(IntegrityCheckError)
    async def integrity_check_handler(request: Request, exc: IntegrityCheckError):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    @application.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    # ------------------------------------------------------------------
    # Router
    # ------------------------------------------------------------------
    application.include_router(router)

    return application


# ---------------------------------------------------------------------------
# Module-level app for uvicorn (only created when running as a server,
# not on bare import during tests)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
