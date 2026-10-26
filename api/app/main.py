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

# Register routers under both /api and root paths for seamless local and Vercel execution
for prefix in ["/api", ""]:
    app.include_router(health.router, prefix=prefix)
    app.include_router(overview.router, prefix=prefix)
    app.include_router(forecast.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(settlement.router, prefix=prefix)
    app.include_router(scenarios.router, prefix=prefix)

# Serve built frontend SPA if frontend/dist exists
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

dist_candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist")),
]
dist_dir = next((d for d in dist_candidates if os.path.exists(d)), None)

if dist_dir:
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Root API info routes
@app.get("/api")
@app.get("/api/index")
@app.get("/api/index.py")
async def api_root():
    return {
        "status": "online",
        "service": "WindLens UK API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": [
            "/api/health",
            "/api/overview",
            "/api/forecast",
            "/api/forecast/versions",
            "/api/analytics/accuracy",
            "/api/analytics/errors",
            "/api/settlement",
            "/api/settlement/export",
            "/api/scenarios/residual-demand",
        ],
    }

# Root route: serve frontend SPA index.html when available, otherwise API info
@app.get("/")
async def root_index():
    if dist_dir and os.path.isfile(os.path.join(dist_dir, "index.html")):
        return FileResponse(os.path.join(dist_dir, "index.html"))
    return await api_root()

@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")

if dist_dir:
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        clean_path = full_path.lstrip("/")
        # Never intercept API routes or documentation
        api_prefixes = (
            "api", "health", "overview", "forecast", "analytics",
            "settlement", "scenarios", "docs", "redoc", "openapi",
        )
        if any(clean_path.startswith(p) for p in api_prefixes):
            raise HTTPException(status_code=404, detail=f"API endpoint '/{clean_path}' not found")

        file_path = os.path.join(dist_dir, clean_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        index_file = os.path.join(dist_dir, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Not Found")




