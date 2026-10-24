"""
Pydantic data models for WindLens UK.

These models normalize the two distinct Elexon data sources into a
shared internal representation used throughout the analytics pipeline.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ActualRecord(BaseModel):
    """Normalized actual wind generation record (from FUELHH, filtered to WIND)."""
    start_time_utc: datetime
    generation_mw: float
    settlement_period: Optional[int] = None
    dataset: str = "FUELHH"


class ForecastRecord(BaseModel):
    """Normalized wind generation forecast record (from WINDFOR)."""
    start_time_utc: datetime
    publish_time_utc: datetime
    generation_mw: float
    dataset: str = "WINDFOR"


class MatchedPeriod(BaseModel):
    """
    A delivery period with the selected forecast and actual generation matched.

    The selected forecast is the version whose publishTime is latest but
    still at or before the configured decision cutoff on the previous day.
    """
    start_time_utc: datetime
    delivery_date: date
    settlement_period: Optional[int] = None
    decision_cutoff_utc: datetime

    # Forecast selected at decision time
    forecast_mw: Optional[float] = None
    forecast_publish_time_utc: Optional[datetime] = None
    forecast_selected: bool = False  # True if an eligible forecast exists

    # Actual generation
    actual_mw: Optional[float] = None
    actual_available: bool = False

    # Derived
    error_mw: Optional[float] = None          # forecast - actual
    abs_error_mw: Optional[float] = None
    pct_error: Optional[float] = None         # abs(error)/abs(actual)*100

    # Data quality flags
    missing_forecast: bool = False
    missing_actual: bool = False
    excluded_from_mape: bool = False  # True if actual == 0
    data_quality_note: Optional[str] = None

    def compute_errors(self) -> None:
        """Populate error fields from forecast and actual values."""
        if self.forecast_mw is not None and self.actual_mw is not None:
            self.error_mw = self.forecast_mw - self.actual_mw
            self.abs_error_mw = abs(self.error_mw)
            if self.actual_mw == 0:
                self.excluded_from_mape = True
                self.pct_error = None
            else:
                self.pct_error = abs(self.error_mw) / abs(self.actual_mw) * 100


class ForecastVersion(BaseModel):
    """A single forecast version for use in the publication history explorer."""
    publish_time_utc: datetime
    generation_mw: float
    is_selected_for_decision: bool = False
    is_post_cutoff: bool = False


class DataSourceMeta(BaseModel):
    """Metadata about a data fetch from Elexon."""
    dataset: str
    source_url: str
    fetched_at: datetime
    record_count: int
    excluded_count: int = 0
    error: Optional[str] = None
    note: Optional[str] = None
    is_fixture: bool = False
