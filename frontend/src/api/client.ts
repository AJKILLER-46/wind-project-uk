import {
  HealthResponse,
  OverviewResponse,
  ForecastResponse,
  ForecastVersionsResponse,
  AccuracyResponse,
  SettlementResponse,
  SettlementPeriodRow,
  ScenarioInput,
  ScenarioResponse,
} from '../types';
import {
  getFallbackHealth,
  getFallbackOverview,
  getFallbackForecast,
  getFallbackForecastVersions,
  getFallbackAccuracy,
  getFallbackSettlementPeriods,
  getFallbackScenario,
  generateSettlementCsv,
} from './fallback';

// Support VITE_API_URL if configured, otherwise use relative /api
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || '/api';

/**
 * Fast fetch wrapper with automatic timeout (default 2500ms).
 * Prevents UI freezes or long hangs when backend is cold or unreachable.
 */
async function safeFetch(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 2500
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return res;
  } finally {
    clearTimeout(id);
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const err = await res.json();
        errorDetail = err.detail || JSON.stringify(err);
      } else {
        errorDetail = await res.text();
      }
    } catch {
      errorDetail = `${res.status} ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await safeFetch(`${BASE_URL}/health`);
    return await handleResponse<HealthResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Backend unreachable, using client engine fallback for health.', err);
    return getFallbackHealth();
  }
}

export async function fetchOverview(
  deliveryDate?: string,
  cutoffTime: string = '11:00'
): Promise<OverviewResponse> {
  const date = deliveryDate || '2026-01-15';
  try {
    const params = new URLSearchParams();
    if (deliveryDate) params.append('delivery_date', deliveryDate);
    params.append('cutoff_time', cutoffTime);

    const res = await safeFetch(`${BASE_URL}/overview?${params.toString()}`);
    return await handleResponse<OverviewResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Using client engine fallback for overview:', date, err);
    return getFallbackOverview(date, cutoffTime);
  }
}

export async function fetchForecast(
  deliveryDate?: string,
  cutoffTime: string = '11:00'
): Promise<ForecastResponse> {
  const date = deliveryDate || '2026-01-15';
  try {
    const params = new URLSearchParams();
    if (deliveryDate) params.append('delivery_date', deliveryDate);
    params.append('cutoff_time', cutoffTime);

    const res = await safeFetch(`${BASE_URL}/forecast?${params.toString()}`);
    return await handleResponse<ForecastResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Using client engine fallback for forecast:', date, err);
    return getFallbackForecast(date, cutoffTime);
  }
}

export async function fetchForecastVersions(
  deliveryDate: string,
  startTimeUtc: string,
  cutoffTime: string = '11:00'
): Promise<ForecastVersionsResponse> {
  try {
    const params = new URLSearchParams({
      delivery_date: deliveryDate,
      start_time_utc: startTimeUtc,
      cutoff_time: cutoffTime,
    });

    const res = await safeFetch(`${BASE_URL}/forecast/versions?${params.toString()}`);
    return await handleResponse<ForecastVersionsResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Using client engine fallback for versions:', deliveryDate, err);
    return getFallbackForecastVersions(deliveryDate, startTimeUtc, cutoffTime);
  }
}

export async function fetchAccuracy(
  startDate?: string,
  endDate?: string,
  cutoffTime: string = '11:00'
): Promise<AccuracyResponse> {
  const sDate = startDate || '2026-01-01';
  const eDate = endDate || '2026-01-31';
  try {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('cutoff_time', cutoffTime);

    const res = await safeFetch(`${BASE_URL}/analytics/accuracy?${params.toString()}`);
    return await handleResponse<AccuracyResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Using client engine fallback for accuracy metrics:', err);
    return getFallbackAccuracy(sDate, eDate, cutoffTime);
  }
}

export async function fetchSettlementPeriods(
  deliveryDate?: string,
  cutoffTime: string = '11:00',
  page: number = 1,
  pageSize: number = 48
): Promise<SettlementResponse> {
  const date = deliveryDate || '2026-01-15';
  try {
    const params = new URLSearchParams();
    if (deliveryDate) params.append('delivery_date', deliveryDate);
    params.append('cutoff_time', cutoffTime);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());

    const res = await safeFetch(`${BASE_URL}/settlement?${params.toString()}`);
    return await handleResponse<SettlementResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Using client engine fallback for settlement ledger:', date, err);
    return getFallbackSettlementPeriods(date, cutoffTime, page, pageSize);
  }
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

export function downloadSettlementCsvDirectly(
  rows: SettlementPeriodRow[],
  deliveryDate: string = '2026-01-15'
): void {
  const csvContent = generateSettlementCsv(rows);
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `windlens_settlement_${deliveryDate}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function calculateScenario(
  payload: ScenarioInput
): Promise<ScenarioResponse> {
  try {
    const res = await safeFetch(`${BASE_URL}/scenarios/residual-demand`, {
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
    return await handleResponse<ScenarioResponse>(res);
  } catch (err) {
    console.info('[WindLens UK] Using client engine fallback for scenario calculation:', err);
    return getFallbackScenario(payload);
  }
}

// Re-export fallback methods for direct instant frontend rendering
export {
  getFallbackHealth,
  getFallbackOverview,
  getFallbackForecast,
  getFallbackForecastVersions,
  getFallbackAccuracy,
  getFallbackSettlementPeriods,
  getFallbackScenario,
  generateSettlementCsv,
};

