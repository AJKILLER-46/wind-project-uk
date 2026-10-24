"""
Data service — orchestrates Elexon data fetching, caching, and fixture fallback.

For the January 2026 analysis period, fixture data is used (clearly labelled)
because the Elexon stream endpoints do not serve historical dates.

For live/current-day requests, the real Elexon API is used.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional, Tuple

from app.core.cache import cache_manager
from app.core.timezone import uk_midnight_utc
from app.schemas.data_models import ActualRecord, ForecastRecord, DataSourceMeta
from app.services.elexon.fuelhh_client import FuelHHClient
from app.services.elexon.windfor_client import WindForClient
from app.services.elexon.fixtures import (
    generate_fuelhh_records,
    generate_windfor_records,
    FIXTURE_NOTE,
)

log = logging.getLogger(__name__)

# Date range that fixture data covers
FIXTURE_START = date(2026, 1, 1)
FIXTURE_END = date(2026, 1, 31)

_fuelhh_client = FuelHHClient()
_windfor_client = WindForClient()


def _is_fixture_date(d: date) -> bool:
    return FIXTURE_START <= d <= FIXTURE_END


def _parse_fixtures_fuelhh(raw: list, target_date: date) -> List[ActualRecord]:
    """Parse fixture FUELHH records using the same parser as the real client."""
    records, _ = _fuelhh_client._parse_records(raw, target_date)
    return records


def _parse_fixtures_windfor(raw: list) -> List[ForecastRecord]:
    """Parse fixture WINDFOR records using the same parser as the real client."""
    records, _ = _windfor_client._parse_records(raw)
    return records


async def get_actuals(
    delivery_date: date,
) -> Tuple[List[ActualRecord], DataSourceMeta, bool]:
    """
    Return actual wind generation records for a delivery date.

    Returns (records, meta, is_fixture).
    """
    cache_key = f"actuals:{delivery_date.isoformat()}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    is_fixture = _is_fixture_date(delivery_date)

    if is_fixture:
        raw = generate_fuelhh_records(delivery_date)
        records = _parse_fixtures_fuelhh(raw, delivery_date)
        import datetime as _dt
        meta = DataSourceMeta(
            dataset="FUELHH",
            source_url="fixture://january-2026-wind-generation",
            fetched_at=_dt.datetime.now(_dt.timezone.utc),
            record_count=len(records),
            excluded_count=0,
            is_fixture=True,
            note=FIXTURE_NOTE,
        )
    else:
        records, meta = await _fuelhh_client.fetch_wind_actuals(delivery_date)

    result = (records, meta, is_fixture)
    cache_manager.set(cache_key, result)
    return result


async def get_forecasts(
    delivery_date: date,
) -> Tuple[List[ForecastRecord], DataSourceMeta, bool]:
    """
    Return all WINDFOR forecast versions covering a delivery date.

    For historical January 2026 dates, returns fixture data.
    For live dates, fetches from Elexon API.
    Returns (records, meta, is_fixture).
    """
    cache_key = f"forecasts:{delivery_date.isoformat()}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    is_fixture = _is_fixture_date(delivery_date)

    if is_fixture:
        raw = generate_windfor_records(delivery_date)
        records = _parse_fixtures_windfor(raw)
        import datetime as _dt
        meta = DataSourceMeta(
            dataset="WINDFOR",
            source_url="fixture://january-2026-wind-forecast",
            fetched_at=_dt.datetime.now(_dt.timezone.utc),
            record_count=len(records),
            excluded_count=0,
            is_fixture=True,
            note=FIXTURE_NOTE,
        )
    else:
        from_utc = uk_midnight_utc(delivery_date)
        to_utc = uk_midnight_utc(delivery_date + timedelta(days=1))
        records, meta = await _windfor_client.fetch_forecasts(from_utc, to_utc)

    result = (records, meta, is_fixture)
    cache_manager.set(cache_key, result)
    return result


_upstream_cache = {}
_upstream_cache_time = 0.0

async def check_upstream_status() -> dict:
    """Quick check of upstream API reachability (concurrent, cached for 60s)."""
    import httpx
    import time
    import asyncio

    global _upstream_cache, _upstream_cache_time
    now = time.time()
    if _upstream_cache and (now - _upstream_cache_time < 60.0):
        return _upstream_cache

    async def check_one(name: str, url: str) -> tuple:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                r = await client.get(url)
                return (name, "ok" if r.status_code < 400 else f"error:{r.status_code}")
        except Exception as e:
            return (name, f"unreachable:{type(e).__name__}")

    endpoints = [
        ("FUELHH", f"{_fuelhh_client.base_url}/datasets/FUELHH/stream?format=json"),
        ("WINDFOR", f"{_windfor_client.base_url}/datasets/WINDFOR/stream?format=json"),
    ]

    checks = await asyncio.gather(*(check_one(name, url) for name, url in endpoints))
    _upstream_cache = dict(checks)
    _upstream_cache_time = now
    return _upstream_cache

