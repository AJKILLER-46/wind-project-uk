"""Analytics endpoints — accuracy metrics and error series."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.schemas.responses import AccuracyResponse, MetricCard, CoverageSummary, ErrorBin, DailyAccuracy
from app.services.data_service import FIXTURE_START, FIXTURE_END, get_actuals, get_forecasts
from app.services.analytics.forecast_selection import select_forecasts
from app.services.analytics.metrics import (
    compute_all_metrics, compute_coverage, compute_error_histogram, compute_daily_metrics
)

router = APIRouter(tags=["analytics"])


@router.get("/analytics/accuracy", response_model=AccuracyResponse)
async def accuracy(
    start_date: date = Query(date(2026, 1, 1)),
    end_date: date = Query(date(2026, 1, 31)),
    cutoff_time: str = Query("11:00"),
):
    """
    Return accuracy metrics over a date range.
    Computes MAE, RMSE, bias, MAPE across all matched periods.
    """
    if start_date < FIXTURE_START or end_date > FIXTURE_END:
        raise HTTPException(status_code=400, detail=f"Date range must be within {FIXTURE_START}–{FIXTURE_END}.")
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date.")

    all_periods = []
    is_fixture = True

    current = start_date
    while current <= end_date:
        actuals, _, fxt = await get_actuals(current)
        forecasts, _, _ = await get_forecasts(current)
        periods, _ = select_forecasts(actuals, forecasts, current, cutoff_time)
        all_periods.extend(periods)
        if not fxt:
            is_fixture = False
        current = date(current.year, current.month, current.day + 1) if current.day < 31 else date(current.year, current.month + 1 if current.month < 12 else 1, 1)

    metrics_raw = compute_all_metrics(all_periods)
    coverage_raw = compute_coverage(all_periods)
    hist = compute_error_histogram(all_periods)
    daily = compute_daily_metrics(all_periods)

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

    error_bins = [ErrorBin(**b) for b in hist]
    daily_acc = [DailyAccuracy(**d) for d in daily]

    from app.services.elexon.fixtures import FIXTURE_NOTE
    return AccuracyResponse(
        period_start=start_date,
        period_end=end_date,
        decision_cutoff_time=cutoff_time,
        data_note=FIXTURE_NOTE if is_fixture else "Live Elexon data",
        is_fixture_data=is_fixture,
        metrics=metrics,
        coverage=CoverageSummary(**coverage_raw),
        error_bins=error_bins,
        daily_accuracy=daily_acc,
    )


@router.get("/analytics/errors")
async def error_series(
    delivery_date: Optional[date] = Query(None),
    cutoff_time: str = Query("11:00"),
):
    """Return the error time series for chart rendering."""
    if delivery_date is None:
        delivery_date = date(2026, 1, 15)

    actuals, _, is_fixture = await get_actuals(delivery_date)
    forecasts, _, _ = await get_forecasts(delivery_date)
    periods, _ = select_forecasts(actuals, forecasts, delivery_date, cutoff_time)

    from app.core.timezone import to_uk
    series = []
    for p in periods:
        if p.forecast_mw is not None and p.actual_mw is not None:
            uk = to_uk(p.start_time_utc)
            series.append({
                "start_time_utc": p.start_time_utc.isoformat(),
                "start_time_uk": uk.strftime("%H:%M"),
                "forecast_mw": p.forecast_mw,
                "actual_mw": p.actual_mw,
                "error_mw": p.error_mw,
                "abs_error_mw": p.abs_error_mw,
            })

    from app.services.elexon.fixtures import FIXTURE_NOTE
    return {
        "delivery_date": delivery_date.isoformat(),
        "is_fixture_data": is_fixture,
        "data_note": FIXTURE_NOTE if is_fixture else "Live Elexon data",
        "series": series,
    }
