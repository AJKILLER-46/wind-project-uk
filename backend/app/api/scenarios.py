"""Residual demand scenario calculator endpoint."""
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from app.schemas.responses import ScenarioInput, ScenarioResponse, ScenarioPeriod
from app.services.data_service import FIXTURE_START, FIXTURE_END, get_actuals, get_forecasts
from app.services.analytics.forecast_selection import select_forecasts
from app.core.timezone import to_uk

router = APIRouter(tags=["scenarios"])

SCENARIO_DISCLAIMER = (
    "⚠️ ILLUSTRATIVE ONLY: This calculator uses wind generation data only. "
    "A real procurement requirement depends on total demand forecasts, contracted positions, "
    "other generation (nuclear, gas, hydro, solar, imports), network losses, balancing constraints, "
    "and applicable trading and auction rules. "
    "This output is NOT a trading recommendation or financial forecast. "
    "Real trading workflows must use the client's approved models and auction-specific cutoffs."
)


@router.post("/scenarios/residual-demand", response_model=ScenarioResponse)
async def residual_demand(body: ScenarioInput):
    """
    Illustrative residual demand calculator.

    residual = max(0, assumed_demand - wind_forecast - other_supply)

    Compares forecast-based vs actual-based scenarios for retrospective analysis.
    """
    if not (FIXTURE_START <= body.delivery_date <= FIXTURE_END):
        raise HTTPException(status_code=400, detail="Date out of supported range.")

    actuals, _, is_fixture = await get_actuals(body.delivery_date)
    forecasts, _, _ = await get_forecasts(body.delivery_date)
    periods, _ = select_forecasts(actuals, forecasts, body.delivery_date, body.decision_cutoff_time)

    scenario_periods = []
    residuals_forecast = []
    residuals_actual = []

    for p in periods:
        uk_time = to_uk(p.start_time_utc).strftime("%H:%M")
        res_f = None
        res_a = None

        if p.forecast_mw is not None:
            res_f = max(0.0, body.assumed_demand_mw - p.forecast_mw - body.assumed_other_supply_mw)
            residuals_forecast.append(res_f)

        if p.actual_mw is not None:
            res_a = max(0.0, body.assumed_demand_mw - p.actual_mw - body.assumed_other_supply_mw)
            residuals_actual.append(res_a)

        scenario_periods.append(ScenarioPeriod(
            start_time_uk=uk_time,
            forecast_mw=p.forecast_mw,
            actual_mw=p.actual_mw,
            residual_forecast=round(res_f, 1) if res_f is not None else None,
            residual_actual=round(res_a, 1) if res_a is not None else None,
        ))

    matched = [p for p in periods if p.forecast_mw is not None and p.actual_mw is not None]
    avg_f = round(sum(p.forecast_mw for p in matched) / len(matched), 1) if matched else None
    avg_a = round(sum(p.actual_mw for p in matched) / len(matched), 1) if matched else None
    avg_rf = round(sum(residuals_forecast) / len(residuals_forecast), 1) if residuals_forecast else None
    avg_ra = round(sum(residuals_actual) / len(residuals_actual), 1) if residuals_actual else None

    from app.services.elexon.fixtures import FIXTURE_NOTE
    return ScenarioResponse(
        assumed_demand_mw=body.assumed_demand_mw,
        assumed_other_supply_mw=body.assumed_other_supply_mw,
        delivery_date=body.delivery_date,
        decision_cutoff_time=body.decision_cutoff_time,
        avg_forecast_mw=avg_f,
        avg_actual_mw=avg_a,
        avg_residual_forecast=avg_rf,
        avg_residual_actual=avg_ra,
        periods=scenario_periods,
        disclaimer=SCENARIO_DISCLAIMER,
        data_note=FIXTURE_NOTE if is_fixture else "Live Elexon data",
        is_fixture_data=is_fixture,
    )
