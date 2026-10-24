export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
  upstream_fuelhh: string;
  upstream_windfor: string;
  data_note: string;
  cache_info: {
    hits?: number;
    misses?: number;
    size?: number;
    [key: string]: any;
  };
}

export interface MetricCard {
  name: string;
  value: number | null;
  unit: string;
  n_observations: number;
  definition: string;
  interpretation: string;
  excluded_count: number;
  excluded_reason: string | null;
}

export interface CoverageSummary {
  total_expected_periods: number;
  matched_periods: number;
  coverage_pct: number;
  missing_forecast_count: number;
  missing_actual_count: number;
  over_forecast_count: number;
  under_forecast_count: number;
}

export interface OverviewResponse {
  reporting_period_start: string;
  reporting_period_end: string;
  selected_delivery_date: string;
  decision_cutoff_time: string;
  data_note: string;
  is_fixture_data: boolean;
  fetched_at: string;
  avg_forecast_mw: number | null;
  avg_actual_mw: number | null;
  metrics: MetricCard[];
  coverage: CoverageSummary;
  source_meta: Array<{
    dataset: string;
    source_url: string;
    fetched_at: string;
    record_count: number;
    excluded_count: number;
    is_fixture: boolean;
    note?: string;
  }>;
}

export interface HalfHourPoint {
  start_time_utc: string;
  start_time_uk: string;
  settlement_period: number | null;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  forecast_publish_time_utc: string | null;
  missing_forecast: boolean;
  missing_actual: boolean;
}

export interface ForecastResponse {
  delivery_date: string;
  decision_cutoff_utc: string;
  decision_cutoff_time: string;
  data_note: string;
  is_fixture_data: boolean;
  periods: HalfHourPoint[];
  period_count: number;
}

export interface ForecastVersionItem {
  publish_time_utc: string;
  publish_time_uk: string;
  generation_mw: number;
  is_selected_for_decision: boolean;
  is_post_cutoff: boolean;
  error_mw: number | null;
  abs_error_mw: number | null;
}

export interface ForecastVersionsResponse {
  delivery_date: string;
  start_time_utc: string;
  start_time_uk: string;
  decision_cutoff_utc: string;
  decision_cutoff_time: string;
  actual_mw: number | null;
  versions: ForecastVersionItem[];
  selected_version: ForecastVersionItem | null;
  total_versions: number;
  post_cutoff_versions: number;
  data_note: string;
  is_fixture_data: boolean;
}

export interface ErrorBin {
  bin_label: string;
  bin_min: number;
  bin_max: number;
  count: number;
}

export interface DailyAccuracy {
  date: string;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  mape: number | null;
  n_matched: number;
  n_mape_excluded: number;
}

export interface AccuracyResponse {
  period_start: string;
  period_end: string;
  decision_cutoff_time: string;
  data_note: string;
  is_fixture_data: boolean;
  metrics: MetricCard[];
  coverage: CoverageSummary;
  error_bins: ErrorBin[];
  daily_accuracy: DailyAccuracy[];
}

export interface SettlementPeriodRow {
  delivery_date: string;
  start_time_utc: string;
  start_time_uk: string;
  settlement_period: number | null;
  decision_cutoff_utc: string;
  forecast_publish_time_utc: string | null;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  abs_error_mw: number | null;
  status: 'matched' | 'missing_forecast' | 'missing_actual' | 'no_eligible_forecast' | string;
}

export interface SettlementResponse {
  total: number;
  page: number;
  page_size: number;
  data_note: string;
  is_fixture_data: boolean;
  rows: SettlementPeriodRow[];
}

export interface ScenarioInput {
  assumed_demand_mw: number;
  assumed_other_supply_mw?: number;
  delivery_date: string;
  decision_cutoff_time?: string;
}

export interface ScenarioPeriod {
  start_time_uk: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  residual_forecast: number | null;
  residual_actual: number | null;
}

export interface ScenarioResponse {
  assumed_demand_mw: number;
  assumed_other_supply_mw: number;
  delivery_date: string;
  decision_cutoff_time: string;
  avg_forecast_mw: number | null;
  avg_actual_mw: number | null;
  avg_residual_forecast: number | null;
  avg_residual_actual: number | null;
  periods: ScenarioPeriod[];
  disclaimer: string;
  data_note: string;
  is_fixture_data: boolean;
}
