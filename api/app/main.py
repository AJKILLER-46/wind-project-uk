"""
WindLens UK - FastAPI backend entry point.
"""
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, overview, forecast, analytics, settlement, scenarios
from app.core.config import settings
from app.core.cache import cache_manager

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("windlens_startup", version="1.0.0", env=settings.environment)
    yield
    log.info("windlens_shutdown")


app = FastAPI(
    title="WindLens UK API",
    description=(
        "Day-ahead wind forecast and procurement intelligence platform. "
        "Data sourced from Elexon BMRS (FUELHH, WINDFOR datasets)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS - allow configured origins or wildcard
cors_origins = settings.cors_origins
if "*" in cors_origins or not cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(settlement.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")

# Serve built frontend SPA if frontend/dist exists
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
assets_dir = os.path.join(dist_dir, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return None
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

