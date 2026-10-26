"""Forecast endpoints — half-hourly data and version history."""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.schemas.responses import ForecastResponse, HalfHourPoint, ForecastVersionsResponse, ForecastVersionItem
from app.services.data_service import get_actuals, get_forecasts, FIXTURE_START, FIXTURE_END
from app.services.analytics.forecast_selection import select_forecasts, build_version_history
from app.core.timezone import to_uk, cutoff_utc, parse_utc
from datetime import datetime
import pytz

router = APIRouter(tags=["forecast"])


def _fmt_uk(dt: datetime) -> str:
    uk = to_uk(dt)
    return uk.strftime("%Y-%m-%d %H:%M %Z")


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    delivery_date: Optional[date] = Query(None),
    cutoff_time: str = Query("11:00"),
):
    """Return selected forecasts and actuals for every half-hour period of a delivery date."""
    if delivery_date is None:
        delivery_date = date(2026, 1, 15)

    if not (FIXTURE_START <= delivery_date <= FIXTURE_END):
        raise HTTPException(status_code=400, detail="Date out of supported range.")

    actuals, _, is_fixture = await get_actuals(delivery_date)
    forecasts, _, _ = await get_forecasts(delivery_date)
    periods, _ = select_forecasts(actuals, forecasts, delivery_date, cutoff_time)

    from datetime import timedelta
    decision_date = delivery_date - timedelta(days=1)
    cutoff_dt = cutoff_utc(decision_date, cutoff_time)

    points = []
    for p in periods:
        points.append(HalfHourPoint(
            start_time_utc=p.start_time_utc,
            start_time_uk=_fmt_uk(p.start_time_utc),
            settlement_period=p.settlement_period,
            forecast_mw=p.forecast_mw,
            actual_mw=p.actual_mw,
            error_mw=p.error_mw,
            forecast_publish_time_utc=p.forecast_publish_time_utc,
            missing_forecast=p.missing_forecast,
            missing_actual=p.missing_actual,
        ))

    from app.services.elexon.fixtures import FIXTURE_NOTE
    return ForecastResponse(
        delivery_date=delivery_date,
        decision_cutoff_utc=cutoff_dt,
        decision_cutoff_time=cutoff_time,
        data_note=FIXTURE_NOTE if is_fixture else "Live Elexon data",
        is_fixture_data=is_fixture,
        periods=points,
        period_count=len(points),
    )


@router.get("/forecast/versions", response_model=ForecastVersionsResponse)
async def get_forecast_versions(
    delivery_date: date = Query(...),
    start_time_utc: Optional[str] = Query(None, description="Delivery period start time in UTC ISO 8601"),
    start_time: Optional[str] = Query(None, description="Alias for start_time_utc"),
    cutoff_time: str = Query("11:00"),
):
    """Return publication history for a single delivery period."""
    if not (FIXTURE_START <= delivery_date <= FIXTURE_END):
        raise HTTPException(status_code=400, detail="Date out of supported range.")

    raw_time = start_time_utc or start_time
    if not raw_time:
        raise HTTPException(status_code=400, detail="start_time_utc is required.")

    try:
        start_dt = parse_utc(raw_time)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid start_time_utc format.")

    actuals, _, is_fixture = await get_actuals(delivery_date)
    forecasts, _, _ = await get_forecasts(delivery_date)

    decision_date = delivery_date - timedelta(days=1)
    cutoff_dt = cutoff_utc(decision_date, cutoff_time)

    # Find actual for this period
    actual = next(
        (a for a in actuals if a.start_time_utc.replace(second=0, microsecond=0) == start_dt.replace(second=0, microsecond=0)),
        None,
    )

    versions_raw = build_version_history(forecasts, start_dt, cutoff_dt, actual)

    post_cutoff = sum(1 for v in versions_raw if v.is_post_cutoff)
    selected = next((v for v in versions_raw if v.is_selected_for_decision), None)

    def to_item(v):
        err = None
        abs_err = None
        if actual and v.generation_mw is not None:
            err = round(v.generation_mw - actual.generation_mw, 1)
            abs_err = round(abs(err), 1)
        return ForecastVersionItem(
            publish_time_utc=v.publish_time_utc,
            publish_time_uk=_fmt_uk(v.publish_time_utc),
            generation_mw=v.generation_mw,
            is_selected_for_decision=v.is_selected_for_decision,
            is_post_cutoff=v.is_post_cutoff,
            error_mw=err,
            abs_error_mw=abs_err,
        )

    from app.services.elexon.fixtures import FIXTURE_NOTE
    return ForecastVersionsResponse(
        delivery_date=delivery_date,
        start_time_utc=start_dt,
        start_time_uk=_fmt_uk(start_dt),
        decision_cutoff_utc=cutoff_dt,
        decision_cutoff_time=cutoff_time,
        actual_mw=actual.generation_mw if actual else None,
        versions=[to_item(v) for v in versions_raw],
        selected_version=to_item(selected) if selected else None,
        total_versions=len(versions_raw),
        post_cutoff_versions=post_cutoff,
        data_note=FIXTURE_NOTE if is_fixture else "Live Elexon data",
        is_fixture_data=is_fixture,
    )
