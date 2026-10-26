"""
January 2026 fixture data for WindLens UK pilot.

IMPORTANT: This module contains clearly-labelled fixture data representing
realistic January 2026 UK wind generation patterns.

WHY FIXTURES ARE NEEDED:
The Elexon BMRS FUELHH and WINDFOR stream endpoints (as verified during build,
October 2026) return only live/current data and ignore historical date parameters.
The January 2026 historical period is therefore not directly accessible via the
live stream endpoints.

These fixtures are:
- Based on realistic UK winter wind generation levels (5,000–15,000 MW range)
- Structured to demonstrate the full application workflow including forecast errors,
  publication history, and over/under-forecast patterns
- Explicitly labeled as FIXTURE DATA throughout the application UI and API responses
- NOT presented as authoritative historical observations

For a production deployment with access to historical Elexon data (e.g. via
a data warehouse, Elexon portal download, or future API changes), replace this
module with real data ingestion.

Data structure mirrors the real API schema exactly so code paths are identical.
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import random

# Seed for reproducibility — fixture data must be deterministic
_RNG = random.Random(20260101)

# January 2026 in UTC: Jan 1 00:00 UTC = Jan 1 00:00 London (GMT, no DST)
JAN_2026_START_UTC = datetime(2026, 1, 1, 0, 0, 0)
JAN_2026_END_UTC = datetime(2026, 2, 1, 0, 0, 0)

# Realistic daily wind generation profiles (MW) — hourly baseline
# Winter 2026: mix of high-wind and low-wind periods
_DAILY_BASE_MW = {
    1: 8500, 2: 9200, 3: 11000, 4: 10500, 5: 7800,
    6: 6200, 7: 5100, 8: 4800, 9: 5500, 10: 7200,
    11: 9800, 12: 12100, 13: 13500, 14: 11200, 15: 8900,
    16: 7400, 17: 6100, 18: 5800, 19: 7000, 20: 9500,
    21: 11800, 22: 13200, 23: 14100, 24: 12800, 25: 10200,
    26: 8100, 27: 7300, 28: 8800, 29: 10400, 30: 11500, 31: 9700,
}

# Intraday multipliers by hour (0–23) — wind typically higher at night in UK
_HOURLY_MULTIPLIER = [
    1.05, 1.08, 1.10, 1.09, 1.07, 1.04,  # 00-05
    0.98, 0.93, 0.90, 0.91, 0.94, 0.97,  # 06-11
    0.99, 1.00, 1.01, 1.02, 1.03, 1.04,  # 12-17
    1.06, 1.07, 1.08, 1.07, 1.06, 1.05,  # 18-23
]


def _add_noise(base: float, scale: float = 0.08) -> float:
    """Add bounded Gaussian noise to a base value."""
    noise = _RNG.gauss(0, scale * base)
    return max(100.0, base + noise)


def generate_fuelhh_records(target_date: date) -> List[Dict[str, Any]]:
    """
    Generate FUELHH-format actual wind generation records for a specific date.
    Records are half-hourly (48 per day in winter, 46 on spring clock change).
    """
    day = target_date.day
    base_mw = _DAILY_BASE_MW.get(day, 8000)
    records = []

    # January is GMT so UTC == local time
    day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)

    period = 1
    t = day_start
    while t < day_start + timedelta(hours=24):
        hour = t.hour
        gen = _add_noise(base_mw * _HOURLY_MULTIPLIER[hour % 24])
        pub_time = t + timedelta(minutes=30)

        records.append({
            "dataset": "FUELHH",
            "publishTime": pub_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "startTime": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "settlementDate": target_date.isoformat(),
            "settlementPeriod": period,
            "fuelType": "WIND",
            "generation": round(gen),
        })
        period += 1
        t += timedelta(minutes=30)

    return records


def generate_windfor_records(delivery_date: date, num_versions: int = 6) -> List[Dict[str, Any]]:
    """
    Generate WINDFOR-format forecast records for a delivery date.

    Multiple forecast versions are generated to simulate the real publication history.
    The day-ahead decision cutoff is typically ~11:00 on D-1 (decision day).

    Forecast versions are published at:
      D-2: 14:00 (early outlooks, less accurate)
      D-1: 02:00, 06:00, 08:00, 10:30, 11:00, 14:00, 17:00 (day-ahead editions)
    """
    day = delivery_date.day
    base_mw = _DAILY_BASE_MW.get(day, 8000)

    # Decision day is D-1
    d_minus_1 = date(delivery_date.year, delivery_date.month, delivery_date.day - 1) \
        if day > 1 else date(2025, 12, 31)

    # Publication timestamps (UTC) — January is GMT so UTC == local
    pub_times_utc = [
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 2, 0, 0),
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 6, 0, 0),
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 8, 0, 0),
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 10, 30, 0),
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 11, 0, 0),
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 14, 0, 0),
        datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 17, 30, 0),
    ][:num_versions]

    # Forecast accuracy improves closer to delivery — systematic bias added to earlier versions
    version_biases = [0.12, 0.08, 0.05, 0.02, 0.01, -0.01, -0.02]

    records = []
    day_start = datetime(delivery_date.year, delivery_date.month, delivery_date.day, 0, 0, 0)

    for v_idx, pub_utc in enumerate(pub_times_utc):
        bias = version_biases[v_idx % len(version_biases)]
        t = day_start
        while t < day_start + timedelta(hours=24):
            hour = t.hour
            gen = _add_noise(base_mw * _HOURLY_MULTIPLIER[hour % 24] * (1 + bias), scale=0.06)
            records.append({
                "dataset": "WINDFOR",
                "publishTime": pub_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "startTime": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "generation": round(gen),
            })
            t += timedelta(hours=1)  # WINDFOR is hourly

    records.sort(key=lambda r: (r["startTime"], r["publishTime"]))
    return records


def get_all_january_fuelhh() -> List[Dict[str, Any]]:
    """Return FUELHH fixture records for all January 2026 days."""
    all_records = []
    for day in range(1, 32):
        d = date(2026, 1, day)
        all_records.extend(generate_fuelhh_records(d))
    return all_records


def get_all_january_windfor() -> List[Dict[str, Any]]:
    """Return WINDFOR fixture records for all January 2026 delivery days."""
    all_records = []
    for day in range(1, 32):
        d = date(2026, 1, day)
        all_records.extend(generate_windfor_records(d))
    return all_records


FIXTURE_NOTE = (
    "⚠️ FIXTURE DATA: The Elexon BMRS stream endpoints verified during build (Oct 2026) "
    "return live data only and do not serve January 2026 historical records. "
    "This dataset uses clearly-labelled fixture data with realistic UK winter wind profiles "
    "to demonstrate the full application workflow. "
    "Replace with real historical data for production use."
)
