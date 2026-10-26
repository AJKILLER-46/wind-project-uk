"""
Vercel Serverless Function entrypoint for WindLens UK FastAPI backend.
"""
import sys
import os

# Ensure backend directory is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for path in [CURRENT_DIR, BACKEND_DIR, ROOT_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

from app.main import app
from app.api import health, overview, forecast, analytics, settlement, scenarios

# Support both /api/* and direct path routes seamlessly regardless of Vercel rewrite
app.include_router(health.router)
app.include_router(overview.router)
app.include_router(forecast.router)
app.include_router(analytics.router)
app.include_router(settlement.router)
app.include_router(scenarios.router)

@app.get("/")
@app.get("/api")
async def root_status():
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
        ]
    }
