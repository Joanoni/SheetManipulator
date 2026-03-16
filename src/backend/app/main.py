from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import upload, schema, data, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="SheetManipulator API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(schema.router, prefix="/api", tags=["schema"])
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
