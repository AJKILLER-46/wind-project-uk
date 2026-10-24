import {
  HealthResponse,
  OverviewResponse,
  ForecastResponse,
  ForecastVersionsResponse,
  AccuracyResponse,
  SettlementResponse,
  ScenarioInput,
  ScenarioResponse,
} from '../types';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'API request failed';
    try {
      const err = await res.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch {
      errorDetail = `${res.status} ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`);
  return handleResponse<HealthResponse>(res);
}

export async function fetchOverview(
  deliveryDate?: string,
  cutoffTime: string = '11:00'
): Promise<OverviewResponse> {
  const params = new URLSearchParams();
  if (deliveryDate) params.append('delivery_date', deliveryDate);
  params.append('cutoff_time', cutoffTime);

  const res = await fetch(`${BASE_URL}/overview?${params.toString()}`);
  return handleResponse<OverviewResponse>(res);
}

export async function fetchForecast(
  deliveryDate?: string,
  cutoffTime: string = '11:00'
): Promise<ForecastResponse> {
  const params = new URLSearchParams();
  if (deliveryDate) params.append('delivery_date', deliveryDate);
  params.append('cutoff_time', cutoffTime);

  const res = await fetch(`${BASE_URL}/forecast?${params.toString()}`);
  return handleResponse<ForecastResponse>(res);
}

export async function fetchForecastVersions(
  deliveryDate: string,
  startTimeUtc: string,
  cutoffTime: string = '11:00'
): Promise<ForecastVersionsResponse> {
  const params = new URLSearchParams({
    delivery_date: deliveryDate,
    start_time_utc: startTimeUtc,
    cutoff_time: cutoffTime,
  });

  const res = await fetch(`${BASE_URL}/forecast/versions?${params.toString()}`);
  return handleResponse<ForecastVersionsResponse>(res);
}

export async function fetchAccuracy(
  startDate?: string,
  endDate?: string,
  cutoffTime: string = '11:00'
): Promise<AccuracyResponse> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  params.append('cutoff_time', cutoffTime);

  const res = await fetch(`${BASE_URL}/analytics/accuracy?${params.toString()}`);
  return handleResponse<AccuracyResponse>(res);
}

export async function fetchSettlementPeriods(
  deliveryDate?: string,
  cutoffTime: string = '11:00',
  page: number = 1,
  pageSize: number = 48
): Promise<SettlementResponse> {
  const params = new URLSearchParams();
  if (deliveryDate) params.append('delivery_date', deliveryDate);
  params.append('cutoff_time', cutoffTime);
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());

  const res = await fetch(`${BASE_URL}/settlement?${params.toString()}`);
  return handleResponse<SettlementResponse>(res);
}

export function getSettlementCsvExportUrl(
  deliveryDate?: string,
  cutoffTime: string = '11:00'
): string {
  const params = new URLSearchParams();
  if (deliveryDate) params.append('delivery_date', deliveryDate);
  params.append('cutoff_time', cutoffTime);
  return `${BASE_URL}/settlement/export?${params.toString()}`;
}

export async function calculateScenario(
  payload: ScenarioInput
): Promise<ScenarioResponse> {
  const res = await fetch(`${BASE_URL}/scenarios/residual-demand`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      assumed_demand_mw: payload.assumed_demand_mw,
      assumed_other_supply_mw: payload.assumed_other_supply_mw || 0,
      delivery_date: payload.delivery_date,
      decision_cutoff_time: payload.decision_cutoff_time || '11:00',
    }),
  });
  return handleResponse<ScenarioResponse>(res);
}
