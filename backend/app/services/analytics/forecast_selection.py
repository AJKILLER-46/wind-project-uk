"""
Forecast selection engine — point-in-time forecast selection.

For each delivery period, selects the forecast version whose publishTime
is latest among all versions published at or before the configured decision cutoff.

Key invariants:
- The selected forecast must never have been published after the decision cutoff.
- The decision cutoff is on the calendar day BEFORE the delivery date (D-1).
- No future information leakage: later versions are shown only for retrospective analysis.
- Timezone handling uses pytz for DST-correctness. Never hardcodes UTC offset.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app.core.timezone import cutoff_utc, delivery_date_uk, settlement_period_from_start, to_uk
from app.schemas.data_models import (
    ActualRecord,
    ForecastRecord,
    ForecastVersion,
    MatchedPeriod,
)

log = logging.getLogger(__name__)


def select_forecasts(
    actuals: List[ActualRecord],
    forecasts: List[ForecastRecord],
    delivery_date: date,
    cutoff_time_str: str,
) -> Tuple[List[MatchedPeriod], List[ForecastVersion]]:
    """
    Match actuals and forecasts for a delivery date.

    For each half-hourly actual period:
      1. Identify all forecast versions covering that delivery start time.
         (WINDFOR is hourly: forecast at H applies to HH periods H:00 and H:30.)
      2. Compute the decision cutoff UTC for this delivery date.
      3. Filter forecast versions to those with publishTime <= cutoff.
      4. Select the version with the latest publishTime from eligible set.
      5. Record whether forecast is missing, actual is missing, etc.

    Returns:
      - List[MatchedPeriod] for the delivery date
      - List[ForecastVersion] for all unique delivery periods (publication history)
    """
    # Decision date is D-1
    decision_date = delivery_date - timedelta(days=1)
    cutoff_dt_utc = cutoff_utc(decision_date, cutoff_time_str)

    log.info(
        "forecast_selection",
        delivery_date=str(delivery_date),
        cutoff_utc=cutoff_dt_utc.isoformat(),
    )

    # Index actuals by start_time (truncated to minute for matching)
    actuals_by_start: Dict[datetime, ActualRecord] = {}
    for a in actuals:
        key = a.start_time_utc.replace(second=0, microsecond=0)
        actuals_by_start[key] = a  # last write wins; duplicates already deduplicated upstream

    # Index all forecasts by their delivery hour (WINDFOR is hourly)
    # Key: start_time_utc truncated to the hour
    forecasts_by_hour: Dict[datetime, List[ForecastRecord]] = defaultdict(list)
    for f in forecasts:
        hour_key = f.start_time_utc.replace(minute=0, second=0, microsecond=0)
        forecasts_by_hour[hour_key].append(f)

    # Generate expected half-hour delivery periods for the date
    # Jan 2026 = GMT so 48 periods per day
    from app.core.timezone import uk_midnight_utc
    day_start_utc = uk_midnight_utc(delivery_date)
    day_end_utc = uk_midnight_utc(delivery_date + timedelta(days=1))

    expected_periods: List[datetime] = []
    t = day_start_utc
    while t < day_end_utc:
        expected_periods.append(t)
        t += timedelta(minutes=30)

    matched_periods: List[MatchedPeriod] = []

    for period_start in expected_periods:
        period_key = period_start.replace(second=0, microsecond=0)
        hour_key = period_start.replace(minute=0, second=0, microsecond=0)

        # Find actual for this period
        actual = actuals_by_start.get(period_key)
        actual_available = actual is not None

        # Find eligible forecast versions for this delivery hour
        all_versions_for_period = forecasts_by_hour.get(hour_key, [])
        eligible = [f for f in all_versions_for_period if f.publish_time_utc <= cutoff_dt_utc]
        post_cutoff = [f for f in all_versions_for_period if f.publish_time_utc > cutoff_dt_utc]

        # Select latest eligible version
        selected_forecast: Optional[ForecastRecord] = None
        if eligible:
            selected_forecast = max(eligible, key=lambda f: f.publish_time_utc)

        sp = actual.settlement_period if actual and actual.settlement_period else \
            settlement_period_from_start(period_start)

        mp = MatchedPeriod(
            start_time_utc=period_start,
            delivery_date=delivery_date,
            settlement_period=sp,
            decision_cutoff_utc=cutoff_dt_utc,
            forecast_mw=selected_forecast.generation_mw if selected_forecast else None,
            forecast_publish_time_utc=selected_forecast.publish_time_utc if selected_forecast else None,
            forecast_selected=selected_forecast is not None,
            actual_mw=actual.generation_mw if actual else None,
            actual_available=actual_available,
            missing_forecast=selected_forecast is None,
            missing_actual=not actual_available,
        )
        mp.compute_errors()

        if not eligible and all_versions_for_period:
            mp.data_quality_note = (
                f"No forecast published before cutoff; "
                f"{len(post_cutoff)} version(s) exist post-cutoff."
            )

        matched_periods.append(mp)

    return matched_periods, []


def build_version_history(
    forecasts: List[ForecastRecord],
    start_time_utc: datetime,
    cutoff_dt_utc: datetime,
    actual: Optional[ActualRecord] = None,
) -> List[ForecastVersion]:
    """
    Build the publication history for a single delivery period.

    Returns all forecast versions in chronological order, marking:
    - which is selected (latest eligible before cutoff)
    - which are post-cutoff (available retrospectively but not for decision)
    """
    hour_key = start_time_utc.replace(minute=0, second=0, microsecond=0)

    # Filter to versions covering this delivery hour
    versions = [
        f for f in forecasts
        if f.start_time_utc.replace(minute=0, second=0, microsecond=0) == hour_key
    ]
    versions.sort(key=lambda f: f.publish_time_utc)

    if not versions:
        return []

    eligible = [v for v in versions if v.publish_time_utc <= cutoff_dt_utc]
    selected_pub_time = max(eligible, key=lambda f: f.publish_time_utc).publish_time_utc \
        if eligible else None

    result: List[ForecastVersion] = []
    for v in versions:
        is_selected = (
            selected_pub_time is not None
            and v.publish_time_utc == selected_pub_time
        )
        err_mw = (v.generation_mw - actual.generation_mw) if actual else None

        result.append(
            ForecastVersion(
                publish_time_utc=v.publish_time_utc,
                generation_mw=v.generation_mw,
                is_selected_for_decision=is_selected,
                is_post_cutoff=v.publish_time_utc > cutoff_dt_utc,
            )
        )

    return result
