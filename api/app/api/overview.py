"""Overview endpoint — summary metrics for the reporting period."""
from datetime import date, datetime
from typing import Optional
import pytz

from fastapi import APIRouter, Query, HTTPException
from app.schemas.responses import OverviewResponse, MetricCard, CoverageSummary
from app.services.data_service import get_actuals, get_forecasts, FIXTURE_START, FIXTURE_END
from app.services.analytics.forecast_selection import select_forecasts
from app.services.analytics.metrics import compute_all_metrics, compute_coverage
from app.core.timezone import to_uk

router = APIRouter(tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    delivery_date: Optional[date] = Query(None, description="Delivery date (YYYY-MM-DD)"),
    cutoff_time: str = Query("11:00", description="Decision cutoff time HH:MM (Europe/London)"),
):
    """
    Return executive overview: metrics, coverage, and data source info
    for the selected delivery date within the January 2026 reporting period.
    """
    if delivery_date is None:
        delivery_date = date(2026, 1, 15)

    if not (FIXTURE_START <= delivery_date <= FIXTURE_END):
        raise HTTPException(
            status_code=400,
            detail=f"Delivery date must be within {FIXTURE_START} – {FIXTURE_END}.",
        )

    actuals, actual_meta, is_fixture = await get_actuals(delivery_date)
    forecasts, forecast_meta, _ = await get_forecasts(delivery_date)

    periods, _ = select_forecasts(actuals, forecasts, delivery_date, cutoff_time)

    metrics_raw = compute_all_metrics(periods)
    coverage_raw = compute_coverage(periods)

    metrics = []
    for key, m in metrics_raw.items():
        metrics.append(MetricCard(
            name=key.upper(),
            value=m["value"],
            unit=m["unit"],
            n_observations=m["n"],
            definition=m["definition"],
            interpretation=m["interpretation"],
            excluded_count=m.get("n_excluded", 0),
            excluded_reason=m.get("excluded_reason"),
        ))

    coverage = CoverageSummary(**coverage_raw)

    matched = [p for p in periods if p.forecast_mw is not None and p.actual_mw is not None]
    avg_forecast = round(sum(p.forecast_mw for p in matched) / len(matched), 1) if matched else None
    avg_actual = round(sum(p.actual_mw for p in matched) / len(matched), 1) if matched else None

    from app.services.elexon.fixtures import FIXTURE_NOTE

    return OverviewResponse(
        reporting_period_start=FIXTURE_START,
        reporting_period_end=FIXTURE_END,
        selected_delivery_date=delivery_date,
        decision_cutoff_time=cutoff_time,
        data_note=FIXTURE_NOTE if is_fixture else "Live Elexon data",
        is_fixture_data=is_fixture,
        fetched_at=datetime.now(pytz.UTC),
        avg_forecast_mw=avg_forecast,
        avg_actual_mw=avg_actual,
        metrics=metrics,
        coverage=coverage,
        source_meta=[actual_meta.model_dump(mode="json"), forecast_meta.model_dump(mode="json")],
    )
