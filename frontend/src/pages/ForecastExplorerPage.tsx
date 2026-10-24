import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  ReferenceLine, 
  CartesianGrid,
  Scatter
} from 'recharts';
import { 
  Layers, 
  Clock, 
  CheckCircle2, 
  Info, 
  Zap, 
  TrendingUp,
  History
} from 'lucide-react';
import { ForecastVersionsResponse, ForecastResponse } from '../types';
import { fetchForecastVersions, fetchForecast } from '../api/client';

interface ForecastExplorerPageProps {
  selectedDate: string;
  setSelectedDate: (d: string) => void;
  cutoffTime: string;
  useUtc: boolean;
}

export const ForecastExplorerPage: React.FC<ForecastExplorerPageProps> = ({
  selectedDate,
  cutoffTime,
  useUtc,
}) => {
  const [selectedSp, setSelectedSp] = useState<number>(24); // Default to midday SP 24 (11:30 - 12:00)
  const [forecastOverview, setForecastOverview] = useState<ForecastResponse | null>(null);
  const [versionsData, setVersionsData] = useState<ForecastVersionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load day's periods first
  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchForecast(selectedDate, cutoffTime)
      .then((res) => {
        if (isMounted) {
          setForecastOverview(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load day forecast');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedDate, cutoffTime]);

  // Load version history whenever selected date, cutoff, or selected settlement period changes
  useEffect(() => {
    if (!forecastOverview) return;
    const period = forecastOverview.periods.find((p) => p.settlement_period === selectedSp);
    if (!period) return;

    let isMounted = true;
    setIsLoading(true);
    fetchForecastVersions(selectedDate, period.start_time_utc, cutoffTime)
      .then((res) => {
        if (isMounted) {
          setVersionsData(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load forecast versions');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedDate, cutoffTime, selectedSp, forecastOverview]);

  const currentPeriod = forecastOverview?.periods.find((p) => p.settlement_period === selectedSp);

  // Prepare chart data for forecast revisions over publication time
  const chartData = versionsData?.versions.map((v, idx) => {
    const pubTimeLabel = useUtc ? v.publish_time_utc.slice(5, 16).replace('T', ' ') : v.publish_time_uk.slice(5, 16);
    return {
      index: idx + 1,
      pubTime: pubTimeLabel,
      pubTimeFull: useUtc ? v.publish_time_utc : v.publish_time_uk,
      generation: v.generation_mw,
      isSelected: v.is_selected_for_decision,
      isPostCutoff: v.is_post_cutoff,
      error: v.error_mw,
      selectedGen: v.is_selected_for_decision ? v.generation_mw : null,
      preCutoffGen: !v.is_post_cutoff ? v.generation_mw : null,
      postCutoffGen: v.is_post_cutoff ? v.generation_mw : null,
    };
  }) || [];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center">
            <History className="w-5 h-5 text-teal-400 mr-2" />
            Forecast Publication & Revision History Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit how Elexon WINDFOR forecasts evolved leading up to the delivery window and verify point-in-time selection.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          {isLoading && <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping mr-1" />}
          <span>Gate Closure: <strong className="text-indigo-400">{cutoffTime} D-1</strong></span>
          <span>•</span>
          <span>Target Delivery: <strong className="text-teal-400">{selectedDate}</strong></span>
        </div>
      </div>

      {/* Control Bar: Settlement Period Selector & Date Picker */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Settlement Period Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-xs font-semibold text-slate-300">
              Settlement Period:
            </label>
            <select
              value={selectedSp}
              onChange={(e) => setSelectedSp(Number(e.target.value))}
              className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-teal-500"
            >
              {forecastOverview?.periods.map((p) => (
                <option key={p.settlement_period} value={p.settlement_period || 1}>
                  SP #{p.settlement_period} ({useUtc ? p.start_time_utc.slice(11, 16) + ' UTC' : p.start_time_uk.slice(11, 16) + ' UK'})
                </option>
              )) || Array.from({ length: 48 }, (_, i) => (
                <option key={i + 1} value={i + 1}>SP #{i + 1}</option>
              ))}
            </select>
          </div>

          {/* Quick jump to peak periods */}
          <div className="flex items-center space-x-1 text-xs">
            <span className="text-slate-500 text-[11px]">Quick Jump:</span>
            {[
              { label: 'SP 1 (Overnight)', sp: 1 },
              { label: 'SP 16 (Morning Peak)', sp: 16 },
              { label: 'SP 24 (Midday)', sp: 24 },
              { label: 'SP 36 (Evening Peak)', sp: 36 },
              { label: 'SP 48 (Night Close)', sp: 48 },
            ].map((btn) => (
              <button
                key={btn.sp}
                onClick={() => setSelectedSp(btn.sp)}
                className={`px-2 py-0.5 rounded transition-colors text-[11px] ${
                  selectedSp === btn.sp
                    ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40 font-semibold'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-400'
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Selected Period Snapshot */}
        {currentPeriod && (
          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="text-slate-400">
              Target Start: <span className="text-white font-semibold">{useUtc ? currentPeriod.start_time_utc.slice(0, 16) : currentPeriod.start_time_uk}</span>
            </div>
            <div className="text-slate-400">
              Actual Outturn: <span className="text-teal-400 font-bold">{currentPeriod.actual_mw !== null ? `${currentPeriod.actual_mw.toLocaleString()} MW` : 'N/A'}</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-xl text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* KPI Cards for the Selected Period */}
      {versionsData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Selected Forecast */}
          <div className="bg-slate-900/80 border border-teal-500/30 rounded-xl p-4 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 transform translate-x-2 -translate-y-2 w-16 h-16 bg-teal-500/10 rounded-full blur-xl pointer-events-none" />
            <div className="flex items-center justify-between text-xs text-teal-400 font-semibold uppercase">
              <span>Decision Forecast</span>
              <CheckCircle2 className="w-4 h-4 text-teal-400" />
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-white">
              {versionsData.selected_version ? `${versionsData.selected_version.generation_mw.toLocaleString()} MW` : 'None eligible'}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              Published: {versionsData.selected_version?.publish_time_uk || 'N/A'}
            </div>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] bg-teal-500/20 text-teal-300 border border-teal-500/40">
              Selected at {cutoffTime} D-1 Gate
            </span>
          </div>

          {/* Card 2: Actual Metered Generation */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
              <span>Actual Generation (FUELHH)</span>
              <Zap className="w-4 h-4 text-teal-400" />
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-teal-400">
              {versionsData.actual_mw !== null ? `${versionsData.actual_mw.toLocaleString()} MW` : 'Unavailable'}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              National outturn metered generation
            </div>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
              Settlement Verification Baseline
            </span>
          </div>

          {/* Card 3: Decision Error */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
              <span>Decision Error (F − A)</span>
              <TrendingUp className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="mt-2 text-2xl font-bold font-mono">
              {versionsData.selected_version?.error_mw !== null && versionsData.selected_version?.error_mw !== undefined ? (
                <span className={versionsData.selected_version.error_mw > 0 ? 'text-amber-400' : 'text-rose-400'}>
                  {versionsData.selected_version.error_mw > 0 ? `+${versionsData.selected_version.error_mw.toFixed(0)}` : versionsData.selected_version.error_mw.toFixed(0)} MW
                </span>
              ) : '—'}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              {versionsData.selected_version?.error_mw && versionsData.selected_version.error_mw > 0
                ? 'Over-forecast (Reserve power was trimmed)'
                : 'Under-forecast (Peakers/batteries called)'}
            </div>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Unsigned |Error|: {versionsData.selected_version?.abs_error_mw?.toFixed(0) || '0'} MW
            </span>
          </div>

          {/* Card 4: Publication Versions Count */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
              <span>Forecast Version Count</span>
              <Layers className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-cyan-400">
              {versionsData.total_versions} runs
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              {versionsData.post_cutoff_versions} version(s) published post-cutoff
            </div>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              Full Historical Revision Trail
            </span>
          </div>
        </div>
      )}

      {/* Revision Evolution Chart */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center">
              <Layers className="w-5 h-5 text-teal-400 mr-2" />
              Forecast Publication Timeline vs Actual Outturn
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Tracks each WINDFOR model run published for SP #{selectedSp}. Note the transition from Day-Ahead Gate to subsequent intraday updates.
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            <span className="flex items-center text-teal-300">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-400 mr-1.5" />
              ★ Day-Ahead Selected Version
            </span>
            <span className="flex items-center text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500 mr-1.5" />
              Later Updates (Hindsight)
            </span>
          </div>
        </div>

        <div className="h-[360px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 15, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              
              <XAxis 
                dataKey="pubTime" 
                tick={{ fill: '#94a3b8', fontSize: 10 }} 
                axisLine={{ stroke: '#334155' }}
                label={{ value: 'Publication Timestamp', position: 'insideBottom', offset: -15, fill: '#64748b', fontSize: 11 }}
              />
              
              <YAxis 
                tick={{ fill: '#94a3b8', fontSize: 11 }} 
                axisLine={{ stroke: '#334155' }}
                unit=" MW"
                domain={['auto', 'auto']}
                tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
              />

              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="bg-slate-950/95 border border-slate-700 p-3.5 rounded-xl shadow-2xl text-xs space-y-1.5 font-mono min-w-[230px]">
                        <div className="font-bold text-white border-b border-slate-800 pb-1 flex justify-between">
                          <span>Run #{d.index}</span>
                          <span className={d.isSelected ? 'text-teal-400 font-bold' : d.isPostCutoff ? 'text-slate-400' : 'text-indigo-300'}>
                            {d.isSelected ? '★ SELECTED AT CUTOFF' : d.isPostCutoff ? 'Post-Cutoff Update' : 'Pre-Cutoff Run'}
                          </span>
                        </div>
                        <div className="text-slate-300">
                          Published: <strong className="text-white">{d.pubTimeFull}</strong>
                        </div>
                        <div className="text-indigo-300">
                          Forecast Wind: <strong className="text-white">{d.generation.toLocaleString()} MW</strong>
                        </div>
                        {versionsData?.actual_mw !== null && (
                          <div className="text-teal-400">
                            Actual Outturn: <strong className="text-white">{versionsData?.actual_mw?.toLocaleString()} MW</strong>
                          </div>
                        )}
                        {d.error !== null && (
                          <div className={`pt-1 border-t border-slate-800 ${d.error > 0 ? 'text-amber-400' : 'text-rose-400'}`}>
                            Error (F − A): {d.error > 0 ? `+${d.error.toFixed(0)}` : d.error.toFixed(0)} MW
                          </div>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />

              <Legend verticalAlign="top" align="right" wrapperStyle={{ paddingBottom: 15, fontSize: 11 }} />

              {/* Reference line for Actual Generation */}
              {versionsData && versionsData.actual_mw !== null && (
                <ReferenceLine 
                  y={versionsData.actual_mw} 
                  stroke="#14b8a6" 
                  strokeWidth={2}
                  strokeDasharray="4 4" 
                  label={{ 
                    value: `Actual Outturn: ${versionsData.actual_mw.toLocaleString()} MW`, 
                    fill: '#14b8a6', 
                    fontSize: 11,
                    position: 'top' 
                  }} 
                />
              )}

              {/* Pre-cutoff forecast evolution line */}
              <Line
                type="monotone"
                dataKey="preCutoffGen"
                name="Eligible Pre-Cutoff Runs"
                stroke="#818cf8"
                strokeWidth={2}
                dot={{ r: 4, fill: '#818cf8' }}
              />

              {/* Post-cutoff forecast evolution line */}
              <Line
                type="monotone"
                dataKey="postCutoffGen"
                name="Post-Cutoff Updates (Hindsight)"
                stroke="#64748b"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                dot={{ r: 3, fill: '#64748b' }}
              />

              {/* Highlighting the Selected Decision Forecast */}
              <Scatter
                dataKey="selectedGen"
                name="Day-Ahead Decision Version"
                fill="#2dd4bf"
                shape="star"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Publication History Table */}
      {versionsData && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center">
                <Clock className="w-4 h-4 text-teal-400 mr-2" />
                Chronological Publication Audit Log
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Every forecast record submitted to Elexon BMRS for this specific delivery period.
              </p>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              Total {versionsData.total_versions} Versions
            </span>
          </div>

          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="py-2.5 px-3">Run #</th>
                  <th className="py-2.5 px-3">Publish Time ({useUtc ? 'UTC' : 'UK Local'})</th>
                  <th className="py-2.5 px-3">Forecast MW</th>
                  <th className="py-2.5 px-3">Revision Delta</th>
                  <th className="py-2.5 px-3">Error (F − A)</th>
                  <th className="py-2.5 px-3">Classification & Decision Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {versionsData.versions.map((v, i) => {
                  const prevGen = i > 0 ? versionsData.versions[i - 1].generation_mw : null;
                  const delta = prevGen !== null ? v.generation_mw - prevGen : null;

                  return (
                    <tr
                      key={i}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        v.is_selected_for_decision
                          ? 'bg-teal-950/40 border-l-4 border-teal-400 font-bold'
                          : v.is_post_cutoff
                          ? 'opacity-70'
                          : ''
                      }`}
                    >
                      <td className="py-2.5 px-3 text-slate-400">
                        #{i + 1}
                      </td>
                      <td className="py-2.5 px-3 text-slate-200">
                        {useUtc ? v.publish_time_utc : v.publish_time_uk}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-white">
                        {v.generation_mw.toLocaleString()} MW
                      </td>
                      <td className="py-2.5 px-3">
                        {delta !== null ? (
                          <span className={delta > 0 ? 'text-emerald-400' : delta < 0 ? 'text-amber-400' : 'text-slate-400'}>
                            {delta > 0 ? `+${delta.toFixed(0)}` : delta.toFixed(0)} MW
                          </span>
                        ) : (
                          <span className="text-slate-500">Initial Run</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        {v.error_mw !== null ? (
                          <span className={v.error_mw > 0 ? 'text-amber-400' : 'text-rose-400'}>
                            {v.error_mw > 0 ? `+${v.error_mw.toFixed(0)}` : v.error_mw.toFixed(0)} MW
                          </span>
                        ) : '—'}
                      </td>
                      <td className="py-2.5 px-3">
                        {v.is_selected_for_decision ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-teal-500/20 text-teal-300 border border-teal-500/40 font-bold">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            SELECTED AT CUTOFF
                          </span>
                        ) : v.is_post_cutoff ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700">
                            Post-Cutoff (Hindsight Only)
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[10px]">
                            Superseded Prior Run
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Point-in-Time Integrity Educational Box */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-start space-x-3 text-xs text-slate-400">
        <Info className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200 block mb-0.5">
            Trading Rule: Preventing Lookahead Bias in Renewable Procurement
          </span>
          <p className="leading-relaxed">
            In Great Britain's wholesale electricity market, day-ahead power auctions clear before gate closure (typically 11:00 D-1 for EPEX SPOT and Nord Pool). 
            WindLens UK enforces strict point-in-time forecast selection: any forecast published after 11:00 D-1 is displayed strictly for retrospective analysis and is never used to simulate or evaluate historical day-ahead trading decisions.
          </p>
        </div>
      </div>
    </div>
  );
};
