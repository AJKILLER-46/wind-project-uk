"""Settlement periods table endpoint with pagination and CSV export."""
import csv
import io
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.responses import SettlementResponse, SettlementPeriodRow
from app.services.data_service import FIXTURE_START, FIXTURE_END, get_actuals, get_forecasts
from app.services.analytics.forecast_selection import select_forecasts
from app.core.timezone import to_uk

router = APIRouter(tags=["settlement"])


async def _get_rows(start_date: date, end_date: date, cutoff_time: str):
    rows = []
    current = start_date
    while current <= end_date:
        actuals, _, _ = await get_actuals(current)
        forecasts, _, _ = await get_forecasts(current)
        periods, _ = select_forecasts(actuals, forecasts, current, cutoff_time)
        for p in periods:
            if p.missing_forecast and p.missing_actual:
                status = "missing_both"
            elif p.missing_forecast:
                status = "missing_forecast"
            elif p.missing_actual:
                status = "missing_actual"
            elif not p.forecast_selected:
                status = "no_eligible_forecast"
            else:
                status = "matched"

            uk_dt = to_uk(p.start_time_utc)
            rows.append(SettlementPeriodRow(
                delivery_date=current,
                start_time_utc=p.start_time_utc,
                start_time_uk=uk_dt.strftime("%Y-%m-%d %H:%M %Z"),
                settlement_period=p.settlement_period,
                decision_cutoff_utc=p.decision_cutoff_utc,
                forecast_publish_time_utc=p.forecast_publish_time_utc,
                forecast_mw=p.forecast_mw,
                actual_mw=p.actual_mw,
                error_mw=p.error_mw,
                abs_error_mw=p.abs_error_mw,
                status=status,
            ))

        # Increment date
        current = current + timedelta(days=1)

    return rows


@router.get("/settlement-periods", response_model=SettlementResponse)
async def settlement_periods(
    start_date: date = Query(date(2026, 1, 1)),
    end_date: date = Query(date(2026, 1, 31)),
    cutoff_time: str = Query("11:00"),
    page: int = Query(1, ge=1),
    page_size: int = Query(48, ge=1, le=500),
):
    if start_date < FIXTURE_START or end_date > FIXTURE_END:
        raise HTTPException(status_code=400, detail="Date range out of supported period.")

    rows = await _get_rows(start_date, end_date, cutoff_time)
    total = len(rows)
    start_idx = (page - 1) * page_size
    page_rows = rows[start_idx: start_idx + page_size]

    from app.services.elexon.fixtures import FIXTURE_NOTE
    return SettlementResponse(
        total=total,
        page=page,
        page_size=page_size,
        data_note=FIXTURE_NOTE,
        is_fixture_data=True,
        rows=page_rows,
    )


@router.get("/settlement-periods/export")
async def export_csv(
    start_date: date = Query(date(2026, 1, 1)),
    end_date: date = Query(date(2026, 1, 31)),
    cutoff_time: str = Query("11:00"),
):
    """Export settlement period table as CSV."""
    if start_date < FIXTURE_START or end_date > FIXTURE_END:
        raise HTTPException(status_code=400, detail="Date range out of supported period.")

    rows = await _get_rows(start_date, end_date, cutoff_time)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "delivery_date", "start_time_uk", "settlement_period",
        "decision_cutoff_utc", "forecast_publish_time_utc",
        "forecast_mw", "actual_mw", "error_mw", "abs_error_mw", "status",
        "data_note",
    ])
    from app.services.elexon.fixtures import FIXTURE_NOTE
    for r in rows:
        writer.writerow([
            r.delivery_date, r.start_time_uk, r.settlement_period or "",
            r.decision_cutoff_utc.isoformat() if r.decision_cutoff_utc else "",
            r.forecast_publish_time_utc.isoformat() if r.forecast_publish_time_utc else "",
            r.forecast_mw if r.forecast_mw is not None else "",
            r.actual_mw if r.actual_mw is not None else "",
            r.error_mw if r.error_mw is not None else "",
            r.abs_error_mw if r.abs_error_mw is not None else "",
            r.status,
            "FIXTURE DATA",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=windlens_settlement_{start_date}_{end_date}.csv"},
    )
