import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Area, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  ReferenceLine, 
  CartesianGrid 
} from 'recharts';
import { 
  Layers, 
  Zap, 
  Clock 
} from 'lucide-react';
import { OverviewResponse, ForecastResponse, ForecastVersionsResponse, HalfHourPoint } from '../types';
import { MetricCard } from '../components/MetricCard';
import { fetchForecastVersions } from '../api/client';

interface OverviewPageProps {
  overview: OverviewResponse | null;
  forecastData: ForecastResponse | null;
  selectedDate: string;
  useUtc: boolean;
  isLoading: boolean;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  overview,
  forecastData,
  selectedDate,
  useUtc,
  isLoading,
}) => {
  const [showErrorBars, setShowErrorBars] = useState<boolean>(true);
  const [selectedPeriod, setSelectedPeriod] = useState<HalfHourPoint | null>(null);
  const [versionsData, setVersionsData] = useState<ForecastVersionsResponse | null>(null);
  const [loadingVersions, setLoadingVersions] = useState<boolean>(false);

  // Handle clicking a chart point or list item to drill into forecast versions
  const handleSelectPeriod = async (point: HalfHourPoint) => {
    setSelectedPeriod(point);
    setLoadingVersions(true);
    try {
      const data = await fetchForecastVersions(selectedDate, point.start_time_utc, overview?.decision_cutoff_time || '11:00');
      setVersionsData(data);
    } catch (err) {
      console.error('Failed to load forecast versions', err);
      setVersionsData(null);
    } finally {
      setLoadingVersions(false);
    }
  };

  if (isLoading || !overview || !forecastData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
        <div className="w-12 h-12 border-4 border-teal-500/20 border-t-teal-500 rounded-full animate-spin" />
        <p className="text-slate-400 font-mono text-sm">Loading Day-Ahead Forecast & Actuals for {selectedDate}...</p>
      </div>
    );
  }

  // Prepare chart data using official error convention: error_mw = forecast_mw - actual_mw
  const chartData = forecastData.periods.map((p) => {
    const error = p.error_mw !== undefined && p.error_mw !== null
      ? p.error_mw
      : (p.forecast_mw !== null && p.actual_mw !== null ? p.forecast_mw - p.actual_mw : null);
    return {
      sp: p.settlement_period,
      time: useUtc ? p.start_time_utc.slice(11, 16) : p.start_time_uk.slice(11, 16),
      timeUk: p.start_time_uk,
      timeUtc: p.start_time_utc,
      actual: p.actual_mw,
      forecast: p.forecast_mw,
      error: error,
      rawPoint: p,
    };
  });

  // Calculate underforecast and overforecast count
  const underforecastCount = overview.coverage.under_forecast_count;
  const overforecastCount = overview.coverage.over_forecast_count;

  return (
    <div className="space-y-6">
      {/* Executive KPI Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center">
            <Zap className="w-5 h-5 text-teal-400 mr-2" />
            Day-Ahead Forecast Performance Metrics
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Cutoff: {overview.decision_cutoff_time} D-1 | Evaluation Date: {overview.selected_delivery_date}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {overview.metrics.map((m, idx) => {
            let accent: 'teal' | 'cyan' | 'amber' | 'rose' | 'indigo' = 'teal';
            if (m.name.includes('MAE')) accent = 'teal';
            else if (m.name.includes('MAPE')) accent = 'cyan';
            else if (m.name.includes('RMSE')) accent = 'indigo';
            else if (m.name.includes('BIAS')) accent = m.value && m.value > 0 ? 'rose' : 'cyan';
            else if (m.name.includes('UNDER')) accent = 'rose';
            else if (m.name.includes('OVER')) accent = 'amber';

            return <MetricCard key={idx} metric={m} accentColor={accent} />;
          })}
        </div>
      </div>

      {/* Main Chart Section */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center">
              Day-Ahead Wind Forecast vs Metered Generation
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparison across 48 UK Half-Hour Settlement Periods (WINDFOR 11:00 D-1 Cutoff vs FUELHH Outturn)
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer bg-slate-800/80 px-2.5 py-1.5 rounded-lg border border-slate-700/60">
              <input
                type="checkbox"
                checked={showErrorBars}
                onChange={(e) => setShowErrorBars(e.target.checked)}
                className="rounded border-slate-700 text-teal-500 focus:ring-teal-400/20 bg-slate-950"
              />
              <span>Show Forecast Error Bars (MW)</span>
            </label>
          </div>
        </div>

        {/* Recharts Chart */}
        <div className="h-[420px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
              onClick={(e) => {
                if (e && e.activePayload && e.activePayload.length > 0) {
                  const raw = e.activePayload[0].payload.rawPoint;
                  if (raw) handleSelectPeriod(raw);
                }
              }}
            >
              <defs>
                <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

              <XAxis
                dataKey="sp"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
                tickLine={false}
                label={{ 
                  value: 'Settlement Period (1 – 48)', 
                  position: 'insideBottom', 
                  offset: -15, 
                  fill: '#64748b', 
                  fontSize: 11 
                }}
              />

              <YAxis
                yAxisId="generation"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: '#334155' }}
                tickLine={false}
                unit=" MW"
                tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
              />

              {showErrorBars && (
                <YAxis
                  yAxisId="error"
                  orientation="right"
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={false}
                  unit=" MW"
                  domain={['auto', 'auto']}
                />
              )}

              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    const error = data.error;
                    const isOver = error !== null && error > 0;
                    const isUnder = error !== null && error < 0;
                    return (
                      <div className="bg-slate-950/95 border border-slate-700/80 p-3.5 rounded-xl shadow-2xl text-xs space-y-1.5 min-w-[220px]">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 font-mono">
                          <span className="font-bold text-teal-400">SP #{data.sp}</span>
                          <span className="text-slate-400">{data.time} {useUtc ? 'UTC' : 'UK'}</span>
                        </div>

                        <div className="flex items-center justify-between text-slate-300">
                          <span className="flex items-center">
                            <span className="w-2 h-2 rounded-full bg-teal-400 mr-2" />
                            Actual Generation:
                          </span>
                          <span className="font-mono font-semibold text-white">
                            {data.actual !== null ? `${data.actual.toLocaleString()} MW` : 'N/A'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-slate-300">
                          <span className="flex items-center">
                            <span className="w-2 h-2 rounded-full bg-indigo-400 mr-2" />
                            Day-Ahead Forecast:
                          </span>
                          <span className="font-mono font-semibold text-white">
                            {data.forecast !== null ? `${data.forecast.toLocaleString()} MW` : 'N/A'}
                          </span>
                        </div>

                        {error !== null && (
                          <div className={`flex items-center justify-between pt-1 border-t border-slate-800/80 font-semibold ${
                            isOver ? 'text-amber-400' : isUnder ? 'text-rose-400' : 'text-slate-300'
                          }`}>
                            <span>Forecast Error (F − A):</span>
                            <span className="font-mono">
                              {error > 0 ? `+${error.toLocaleString()}` : error.toLocaleString()} MW
                              <span className="text-[10px] ml-1 font-normal text-slate-400">
                                ({isOver ? 'Over-forecast' : isUnder ? 'Under-forecast' : 'Exact'})
                              </span>
                            </span>
                          </div>
                        )}

                        <div className="text-[10px] text-slate-500 pt-1 italic text-center">
                          Click to inspect forecast revisions
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />

              <Legend 
                verticalAlign="top" 
                align="right" 
                wrapperStyle={{ paddingBottom: 15, fontSize: 12 }} 
              />

              <ReferenceLine y={0} yAxisId={showErrorBars ? "error" : "generation"} stroke="#475569" strokeDasharray="2 2" />

              {/* Area for actual generation */}
              <Area
                yAxisId="generation"
                type="monotone"
                dataKey="actual"
                name="Actual Wind (FUELHH)"
                stroke="#14b8a6"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#actualGradient)"
              />

              {/* Dashed line for day-ahead forecast */}
              <Line
                yAxisId="generation"
                type="monotone"
                dataKey="forecast"
                name="Day-Ahead Forecast (11:00 D-1)"
                stroke="#818cf8"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={{ r: 2, fill: '#818cf8' }}
                activeDot={{ r: 5, fill: '#6366f1' }}
              />

              {/* Error bars */}
              {showErrorBars && (
                <Bar
                  yAxisId="error"
                  dataKey="error"
                  name="Error (Forecast − Actual) MW"
                  fill="#06b6d4"
                  opacity={0.4}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Imbalance & Risk Insights */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 pt-4 border-t border-slate-800/80">
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80">
            <span className="text-xs text-slate-400 uppercase font-semibold">Underforecast Periods</span>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-rose-400">{underforecastCount}</span>
              <span className="text-xs text-slate-500">of 48 SPs</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Generation exceeded forecast. Less reserve needed, but potential cashout pricing implications.
            </p>
          </div>

          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80">
            <span className="text-xs text-slate-400 uppercase font-semibold">Overforecast Periods</span>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-cyan-400">{overforecastCount}</span>
              <span className="text-xs text-slate-500">of 48 SPs</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Wind fell short of day-ahead schedule. Flexible peaking units (CCGT/OCGT) needed to balance.
            </p>
          </div>

          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80">
            <span className="text-xs text-slate-400 uppercase font-semibold">Total Day Generation</span>
            <div className="mt-1 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-teal-400">
                {overview.avg_actual_mw ? `${((overview.avg_actual_mw * 24) / 1000).toFixed(1)}` : '—'}
              </span>
              <span className="text-xs text-slate-500">GWh estimated</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Average capacity factor ~{overview.avg_actual_mw ? `${((overview.avg_actual_mw / 28500) * 100).toFixed(0)}%` : '—'} of UK installed fleet (~28.5 GW).
            </p>
          </div>
        </div>
      </div>

      {/* Forecast Version Revision Inspector */}
      {selectedPeriod && (
        <div className="bg-slate-900/90 border border-teal-500/30 rounded-2xl p-5 shadow-2xl transition-all animate-fadeIn">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center">
                <Layers className="w-5 h-5 text-teal-400 mr-2" />
                Forecast Revision History for Settlement Period #{selectedPeriod.settlement_period}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Period Target: {selectedPeriod.start_time_uk} UK | Actual Generation: <strong className="text-white">{selectedPeriod.actual_mw} MW</strong>
              </p>
            </div>

            <button
              onClick={() => setSelectedPeriod(null)}
              className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              Close
            </button>
          </div>

          {loadingVersions ? (
            <div className="py-8 flex justify-center items-center space-x-2 text-slate-400 text-xs font-mono">
              <div className="w-4 h-4 border-2 border-teal-400 border-t-transparent rounded-full animate-spin" />
              <span>Fetching Elexon WINDFOR version log...</span>
            </div>
          ) : versionsData ? (
            <div className="mt-4 space-y-3">
              <div className="text-xs text-slate-300">
                Found <strong className="text-teal-400">{versionsData.total_versions}</strong> published WINDFOR forecasts.
                The platform selected the version published at{' '}
                <strong className="text-indigo-300">{versionsData.selected_version?.publish_time_uk || '11:00 D-1'}</strong>{' '}
                as the procurement decision baseline.
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-2 px-3">Publish Time (UK)</th>
                      <th className="py-2 px-3">Forecast MW</th>
                      <th className="py-2 px-3">Error (Actual - F)</th>
                      <th className="py-2 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {versionsData.versions.map((v, i) => (
                      <tr 
                        key={i} 
                        className={`hover:bg-slate-800/40 transition-colors ${
                          v.is_selected_for_decision ? 'bg-teal-950/40 border-l-2 border-teal-400 font-bold' : ''
                        }`}
                      >
                        <td className="py-2 px-3 flex items-center space-x-2">
                          <Clock className="w-3 h-3 text-slate-500" />
                          <span>{v.publish_time_uk}</span>
                        </td>
                        <td className="py-2 px-3 text-white font-semibold">
                          {v.generation_mw.toLocaleString()} MW
                        </td>
                        <td className="py-2 px-3">
                          {v.error_mw !== null ? (
                            <span className={v.error_mw > 0 ? 'text-rose-400' : 'text-cyan-400'}>
                              {v.error_mw > 0 ? `+${v.error_mw.toFixed(0)}` : v.error_mw.toFixed(0)} MW
                            </span>
                          ) : '—'}
                        </td>
                        <td className="py-2 px-3">
                          {v.is_selected_for_decision ? (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-teal-500/20 text-teal-300 border border-teal-500/40 uppercase">
                              Day-Ahead Selected
                            </span>
                          ) : v.is_post_cutoff ? (
                            <span className="text-slate-500 text-[10px]">
                              Post-Cutoff Update
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[10px]">
                              Earlier Version
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="py-4 text-xs text-slate-400">No version history available for this settlement period.</div>
          )}
        </div>
      )}
    </div>
  );
};
