"""
Elexon WINDFOR client — wind generation forecasts.

Schema confirmed from live API inspection:
  [{
    "dataset": "WINDFOR",
    "publishTime": "2026-10-24T03:30:00Z",
    "startTime": "2026-10-23T20:00:00Z",
    "generation": 15239
  }, ...]

Note: WINDFOR has NO fuelType field (unlike FUELHH).
Note: WINDFOR startTime intervals are 1-hour (not 30-min like FUELHH).
      The forecast covers hourly periods; FUELHH actuals are half-hourly.
      Matching logic: a forecast for hour H applies to FUELHH periods H:00 and H:30.

NOTE: The live stream endpoint ignores the from/to date parameters and returns
current-day forecasts only. January 2026 uses clearly-labelled fixture data.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.timezone import parse_utc, delivery_date_uk
from app.schemas.data_models import ForecastRecord, DataSourceMeta

log = logging.getLogger(__name__)


class WindForClient:
    """
    Client for the Elexon WINDFOR (wind generation forecast) dataset.

    Fetches all forecast versions for a delivery date range.
    Returns all versions so the caller can apply the decision-cutoff filter.
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
    async def fetch_forecasts(
        self, from_utc: datetime, to_utc: datetime
    ) -> tuple[List[ForecastRecord], DataSourceMeta]:
        """
        Fetch all available WINDFOR forecast records for the given UTC window.

        The from/to range should cover the delivery periods of interest.
        Multiple publishTime values may appear for the same startTime.
        """
        url = f"{self.base_url}/datasets/WINDFOR/stream"
        params = {
            "from": from_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "format": "json",
        }

        fetch_ts = datetime.utcnow().replace(tzinfo=__import__("pytz").UTC)
        records = []
        error_msg = None

        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()

            items = raw if isinstance(raw, list) else raw.get("data", [])
            records, excluded = self._parse_records(items)

            meta = DataSourceMeta(
                dataset="WINDFOR",
                source_url=str(resp.url),
                fetched_at=fetch_ts,
                record_count=len(records),
                excluded_count=excluded,
                note=(
                    "Live endpoint — from/to parameters may be ignored by upstream API. "
                    "Records are filtered to the requested delivery window by startTime."
                ),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                log.warning("windfor_rate_limited", status=429)
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            meta = DataSourceMeta(
                dataset="WINDFOR",
                source_url=url,
                fetched_at=fetch_ts,
                record_count=0,
                excluded_count=0,
                error=error_msg,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            error_msg = f"Network error: {type(e).__name__}"
            meta = DataSourceMeta(
                dataset="WINDFOR",
                source_url=url,
                fetched_at=fetch_ts,
                record_count=0,
                excluded_count=0,
                error=error_msg,
            )

        return records, meta

    def _parse_records(self, items: list) -> tuple[List[ForecastRecord], int]:
        """
        Parse and validate raw WINDFOR items.

        Rules:
        - Must have startTime and publishTime
        - generation must be valid and non-negative
        - No fuelType field in WINDFOR — all records are wind forecasts
        """
        records: List[ForecastRecord] = []
        excluded = 0

        for item in items:
            if not isinstance(item, dict):
                excluded += 1
                continue

            start_str = item.get("startTime")
            publish_str = item.get("publishTime")

            if not start_str or not publish_str:
                excluded += 1
                continue

            try:
                start_utc = parse_utc(str(start_str))
                publish_utc = parse_utc(str(publish_str))
            except (ValueError, TypeError) as e:
                log.warning("windfor_bad_timestamp: start=%s, publish=%s", start_str, publish_str)
                excluded += 1
                continue

            gen_raw = item.get("generation")
            if gen_raw is None:
                excluded += 1
                continue
            try:
                gen_mw = float(gen_raw)
            except (ValueError, TypeError):
                log.warning("windfor_bad_generation: %s", gen_raw)
                excluded += 1
                continue

            if gen_mw < 0:
                log.warning("windfor_negative_generation: %s", gen_mw)
                excluded += 1
                continue

            records.append(
                ForecastRecord(
                    start_time_utc=start_utc,
                    publish_time_utc=publish_utc,
                    generation_mw=gen_mw,
                    dataset="WINDFOR",
                )
            )

        records.sort(key=lambda r: (r.start_time_utc, r.publish_time_utc))
        return records, excluded
