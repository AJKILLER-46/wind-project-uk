"""
Pydantic response schemas for WindLens UK API endpoints.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime
    upstream_fuelhh: str
    upstream_windfor: str
    data_note: str
    cache_info: Dict[str, Any]


class MetricCard(BaseModel):
    name: str
    value: Optional[float]
    unit: str
    n_observations: int
    definition: str
    interpretation: str
    excluded_count: int = 0
    excluded_reason: Optional[str] = None


class CoverageSummary(BaseModel):
    total_expected_periods: int
    matched_periods: int
    coverage_pct: float
    missing_forecast_count: int
    missing_actual_count: int
    over_forecast_count: int
    under_forecast_count: int


class OverviewResponse(BaseModel):
    reporting_period_start: date
    reporting_period_end: date
    selected_delivery_date: date
    decision_cutoff_time: str
    data_note: str
    is_fixture_data: bool
    fetched_at: datetime
    avg_forecast_mw: Optional[float]
    avg_actual_mw: Optional[float]
    metrics: List[MetricCard]
    coverage: CoverageSummary
    source_meta: List[Dict[str, Any]]


class HalfHourPoint(BaseModel):
    start_time_utc: datetime
    start_time_uk: str  # formatted UK local time
    settlement_period: Optional[int]
    forecast_mw: Optional[float]
    actual_mw: Optional[float]
    error_mw: Optional[float]
    forecast_publish_time_utc: Optional[datetime]
    missing_forecast: bool
    missing_actual: bool


class ForecastResponse(BaseModel):
    delivery_date: date
    decision_cutoff_utc: datetime
    decision_cutoff_time: str
    data_note: str
    is_fixture_data: bool
    periods: List[HalfHourPoint]
    period_count: int


class ForecastVersionItem(BaseModel):
    publish_time_utc: datetime
    publish_time_uk: str
    generation_mw: float
    is_selected_for_decision: bool
    is_post_cutoff: bool
    error_mw: Optional[float]
    abs_error_mw: Optional[float]


class ForecastVersionsResponse(BaseModel):
    delivery_date: date
    start_time_utc: datetime
    start_time_uk: str
    decision_cutoff_utc: datetime
    decision_cutoff_time: str
    actual_mw: Optional[float]
    versions: List[ForecastVersionItem]
    selected_version: Optional[ForecastVersionItem]
    total_versions: int
    post_cutoff_versions: int
    data_note: str
    is_fixture_data: bool


class ErrorBin(BaseModel):
    bin_label: str
    bin_min: float
    bin_max: float
    count: int


class DailyAccuracy(BaseModel):
    date: date
    mae: Optional[float]
    rmse: Optional[float]
    bias: Optional[float]
    mape: Optional[float]
    n_matched: int
    n_mape_excluded: int


class AccuracyResponse(BaseModel):
    period_start: date
    period_end: date
    decision_cutoff_time: str
    data_note: str
    is_fixture_data: bool
    metrics: List[MetricCard]
    coverage: CoverageSummary
    error_bins: List[ErrorBin]
    daily_accuracy: List[DailyAccuracy]


class SettlementPeriodRow(BaseModel):
    delivery_date: date
    start_time_utc: datetime
    start_time_uk: str
    settlement_period: Optional[int]
    decision_cutoff_utc: datetime
    forecast_publish_time_utc: Optional[datetime]
    forecast_mw: Optional[float]
    actual_mw: Optional[float]
    error_mw: Optional[float]
    abs_error_mw: Optional[float]
    status: str  # matched | missing_forecast | missing_actual | no_eligible_forecast


class SettlementResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data_note: str
    is_fixture_data: bool
    rows: List[SettlementPeriodRow]


class ScenarioInput(BaseModel):
    assumed_demand_mw: float = Field(..., ge=0, le=80000)
    assumed_other_supply_mw: float = Field(0.0, ge=0, le=80000)
    delivery_date: date
    decision_cutoff_time: str = "11:00"


class ScenarioPeriod(BaseModel):
    start_time_uk: str
    forecast_mw: Optional[float]
    actual_mw: Optional[float]
    residual_forecast: Optional[float]
    residual_actual: Optional[float]


class ScenarioResponse(BaseModel):
    assumed_demand_mw: float
    assumed_other_supply_mw: float
    delivery_date: date
    decision_cutoff_time: str
    avg_forecast_mw: Optional[float]
    avg_actual_mw: Optional[float]
    avg_residual_forecast: Optional[float]
    avg_residual_actual: Optional[float]
    periods: List[ScenarioPeriod]
    disclaimer: str
    data_note: str
    is_fixture_data: bool
