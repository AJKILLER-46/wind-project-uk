"""
Elexon FUELHH client — actual half-hourly generation by fuel type.

Schema confirmed from live API inspection:
  [{
    "dataset": "FUELHH",
    "publishTime": "2026-10-24T05:00:00Z",
    "startTime": "2026-10-24T04:30:00Z",
    "settlementDate": "2026-10-24",
    "settlementPeriod": 12,
    "fuelType": "WIND",
    "generation": 11871
  }, ...]

Stream endpoint returns a JSON array directly.
Non-stream endpoint wraps in {"data": [...]}.

NOTE: The stream endpoint ignores date query parameters and returns live/current data only.
For the January 2026 analysis period, fixture data is used and clearly labelled.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.timezone import parse_utc, delivery_date_uk
from app.schemas.data_models import ActualRecord, DataSourceMeta

log = logging.getLogger(__name__)

FUEL_TYPE_WIND = "WIND"


class FuelHHClient:
    """
    Client for the Elexon FUELHH (half-hourly generation by fuel type) dataset.

    Fetches actual wind generation records. Filters to fuelType == 'WIND'.
    Handles both stream (array) and paginated ({"data": [...]}) response envelopes.
    """

    def __init__(self, base_url: str = None, timeout: float = None):
        self.base_url = base_url or settings.elexon_base_url
        self.timeout = timeout or settings.elexon_timeout_seconds
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def aclose(self):
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(settings.elexon_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def fetch_wind_actuals(
        self, settlement_date: date
    ) -> tuple[List[ActualRecord], DataSourceMeta]:
        """
        Fetch actual wind generation for a settlement date.

        Returns parsed records filtered to WIND fuel type.
        """
        url = f"{self.base_url}/datasets/FUELHH/stream"
        params = {
            "settlementDate": settlement_date.isoformat(),
            "fuelType": FUEL_TYPE_WIND,
            "format": "json",
        }

        fetch_ts = datetime.utcnow().replace(tzinfo=__import__("pytz").UTC)
        records = []
        error_msg = None

        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()

            # Handle both envelope types
            items = raw if isinstance(raw, list) else raw.get("data", [])
            records, excluded = self._parse_records(items, settlement_date)

            meta = DataSourceMeta(
                dataset="FUELHH",
                source_url=str(resp.url),
                fetched_at=fetch_ts,
                record_count=len(records),
                excluded_count=excluded,
                note=(
                    "Live endpoint — date parameter may be ignored by upstream API. "
                    "Records are filtered by startTime to the requested settlement date."
                ),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                log.warning("fuelhh_rate_limited", status=429)
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            meta = DataSourceMeta(
                dataset="FUELHH",
                source_url=url,
                fetched_at=fetch_ts,
                record_count=0,
                excluded_count=0,
                error=error_msg,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            error_msg = f"Network error: {type(e).__name__}"
            meta = DataSourceMeta(
                dataset="FUELHH",
                source_url=url,
                fetched_at=fetch_ts,
                record_count=0,
                excluded_count=0,
                error=error_msg,
            )

        return records, meta

    def _parse_records(
        self, items: list, target_date: date
    ) -> tuple[List[ActualRecord], int]:
        """
        Parse and validate raw FUELHH items.

        Rules:
        - Must have fuelType == 'WIND' (case-insensitive)
        - Must have valid, non-negative numeric generation
        - startTime must be parseable
        - Filter to records whose delivery date matches target_date
        """
        records: List[ActualRecord] = []
        excluded = 0

        seen_start_times: set = set()

        for item in items:
            if not isinstance(item, dict):
                excluded += 1
                continue

            # Validate fuelType
            fuel = item.get("fuelType", "")
            if not isinstance(fuel, str) or fuel.upper() != FUEL_TYPE_WIND:
                excluded += 1
                continue

            # Parse startTime
            start_str = item.get("startTime")
            if not start_str:
                excluded += 1
                continue
            try:
                start_utc = parse_utc(str(start_str))
            except (ValueError, TypeError):
                log.warning("fuelhh_bad_start_time: %s", start_str)
                excluded += 1
                continue

            # Filter to target date
            if delivery_date_uk(start_utc) != target_date:
                # Record is for a different date — skip silently
                excluded += 1
                continue

            # Validate generation
            gen_raw = item.get("generation")
            if gen_raw is None:
                excluded += 1
                continue
            try:
                gen_mw = float(gen_raw)
            except (ValueError, TypeError):
                log.warning("fuelhh_bad_generation: %s", gen_raw)
                excluded += 1
                continue

            if gen_mw < 0:
                log.warning("fuelhh_negative_generation: %s (start_time=%s)", gen_mw, start_str)
                excluded += 1
                continue

            # Deduplicate on startTime — keep first occurrence
            key = start_utc.isoformat()
            if key in seen_start_times:
                excluded += 1
                continue
            seen_start_times.add(key)

            settlement_period = item.get("settlementPeriod")
            if isinstance(settlement_period, (int, float)):
                settlement_period = int(settlement_period)
            else:
                settlement_period = None

            records.append(
                ActualRecord(
                    start_time_utc=start_utc,
                    generation_mw=gen_mw,
                    settlement_period=settlement_period,
                    dataset="FUELHH",
                )
            )

        # Sort by start time
        records.sort(key=lambda r: r.start_time_utc)
        return records, excluded
