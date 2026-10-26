"""Health check endpoint."""
from datetime import datetime
import pytz
from fastapi import APIRouter
from app.schemas.responses import HealthResponse
from app.core.config import settings
from app.core.cache import cache_manager

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """Application health check with upstream status indicators."""
    from app.services.data_service import check_upstream_status
    upstream = await check_upstream_status()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.environment,
        timestamp=datetime.now(pytz.UTC),
        upstream_fuelhh=upstream.get("FUELHH", "unknown"),
        upstream_windfor=upstream.get("WINDFOR", "unknown"),
        data_note=(
            "January 2026 analysis uses fixture data (Elexon stream endpoints "
            "do not serve historical dates). Live API used for current-day data."
        ),
        cache_info=cache_manager.info(),
    )
