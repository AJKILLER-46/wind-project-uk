import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend, 
  Cell 
} from 'recharts';
import { 
  TrendingUp, 
  BarChart3, 
  Clock, 
  Layers, 
  AlertTriangle 
} from 'lucide-react';
import { AccuracyResponse } from '../types';
import { fetchAccuracy } from '../api/client';

interface AnalyticsPageProps {
  cutoffTime: string;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ cutoffTime }) => {
  const [data, setData] = useState<AccuracyResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchAccuracy('2026-01-01', '2026-01-31', cutoffTime)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load analytics data');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [cutoffTime]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
        <div className="w-12 h-12 border-4 border-teal-500/20 border-t-teal-500 rounded-full animate-spin" />
        <p className="text-slate-400 font-mono text-sm">Computing accuracy analytics across January 2026 reporting period...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-rose-950/20 border border-rose-900/40 rounded-xl text-rose-300 text-sm">
        <div className="flex items-center space-x-2 font-semibold mb-2">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <span>Error loading accuracy metrics</span>
        </div>
        <p>{error || 'No data available'}</p>
      </div>
    );
  }

  // Daily accuracy trend chart data
  const dailyChartData = data.daily_accuracy.map((d) => ({
    date: d.date.slice(5), // MM-DD
    fullDate: d.date,
    mae: d.mae,
    rmse: d.rmse,
    mape: d.mape,
    bias: d.bias,
    matched: d.n_matched,
  }));

  // Error distribution histogram data
  const errorHistogramData = data.error_bins.map((b) => ({
    label: b.bin_label,
    count: b.count,
    min: b.bin_min,
    max: b.bin_max,
  }));

  return (
    <div className="space-y-6">
      {/* Title & Scope header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center">
            <TrendingUp className="w-5 h-5 text-teal-400 mr-2" />
            January 2026 Multi-Day Accuracy & Bias Distribution
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Statistical validation across all 31 days (1,488 half-hour settlement periods) with {cutoffTime} D-1 decision gate.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          <span>Evaluated: <strong className="text-teal-400">{data.coverage.matched_periods}</strong> SPs</span>
          <span>•</span>
          <span>Coverage: <strong className="text-emerald-400">{data.coverage.coverage_pct}%</strong></span>
        </div>
      </div>

      {/* Grid: Daily MAE Trend & Error Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily MAE / RMSE Chart */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center">
              <BarChart3 className="w-4 h-4 text-teal-400 mr-2" />
              Daily Mean Absolute Error (MAE) Trend
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Daily error fluctuations across January 2026 (spikes indicate weather front timing errors)
            </p>
          </div>

          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyChartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: '#94a3b8', fontSize: 10 }} 
                  axisLine={{ stroke: '#334155' }}
                />
                <YAxis 
                  tick={{ fill: '#94a3b8', fontSize: 10 }} 
                  axisLine={{ stroke: '#334155' }}
                  unit=" MW" 
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-950/95 border border-slate-700 p-3 rounded-lg text-xs space-y-1 font-mono">
                          <div className="font-bold text-white border-b border-slate-800 pb-1">{d.fullDate}</div>
                          <div className="text-teal-400">MAE: {d.mae ? `${d.mae.toFixed(1)} MW` : 'N/A'}</div>
                          <div className="text-indigo-400">RMSE: {d.rmse ? `${d.rmse.toFixed(1)} MW` : 'N/A'}</div>
                          <div className="text-cyan-400">MAPE: {d.mape ? `${d.mape.toFixed(1)}%` : 'N/A'}</div>
                          <div className={d.bias && d.bias > 0 ? 'text-rose-400' : 'text-slate-300'}>
                            Bias: {d.bias ? `${d.bias > 0 ? '+' : ''}${d.bias.toFixed(1)} MW` : 'N/A'}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                <Line
                  type="monotone"
                  dataKey="mae"
                  name="Daily MAE (MW)"
                  stroke="#14b8a6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#14b8a6' }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="rmse"
                  name="Daily RMSE (MW)"
                  stroke="#6366f1"
                  strokeWidth={1.5}
                  strokeDasharray="3 3"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Error Distribution Histogram */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center">
              <Layers className="w-4 h-4 text-cyan-400 mr-2" />
              Forecast Error Distribution (Forecast − Actual)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Histogram of error occurrences across all settlement periods (positive = over-forecast, negative = under-forecast)
            </p>
          </div>

          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={errorHistogramData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="label" 
                  tick={{ fill: '#94a3b8', fontSize: 9 }} 
                  axisLine={{ stroke: '#334155' }}
                  interval={0}
                  angle={-25}
                  textAnchor="end"
                />
                <YAxis 
                  tick={{ fill: '#94a3b8', fontSize: 10 }} 
                  axisLine={{ stroke: '#334155' }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-950/95 border border-slate-700 p-2.5 rounded-lg text-xs font-mono">
                          <div className="text-white font-bold">{d.label}</div>
                          <div className="text-teal-400 mt-1">Settlement Periods: {d.count}</div>
                          <div className="text-slate-400 text-[10px]">
                            {((d.count / (data.coverage.matched_periods || 1)) * 100).toFixed(1)}% of all observations
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" name="Settlement Periods">
                  {errorHistogramData.map((entry, index) => {
                    const isPositive = entry.min >= 0;
                    return (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={isPositive ? '#06b6d4' : '#f59e0b'} 
                        opacity={0.8}
                      />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Procurement Insights Panel */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center">
          <Clock className="w-4 h-4 text-teal-400 mr-2" />
          Procurement & Balancing Strategy Recommendations
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <span className="font-semibold text-teal-400 block mb-1">Morning Ramp Volatility (06:00 – 09:00)</span>
            <p className="text-slate-400 leading-relaxed">
              Wind forecasts tend to under-predict the steep morning acceleration by ~12-18%. Keep short-term battery storage (BESS) or fast-start hydro on standby for frequency response.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <span className="font-semibold text-cyan-400 block mb-1">Evening Peak Deficit Risk (16:30 – 19:00)</span>
            <p className="text-slate-400 leading-relaxed">
              Highest financial exposure occurs when high demand coincides with over-estimated wind. Procurement desk should secure flexible CCGT capacity on day-ahead auction.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <span className="font-semibold text-amber-400 block mb-1">Storm Cut-Off Events</span>
            <p className="text-slate-400 leading-relaxed">
              During high-wind storm events (e.g., Jan 21), watch for high-speed wind turbine cutouts (&gt;25 m/s). This triggers sudden drop-offs not always captured in day-ahead NWP models.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
