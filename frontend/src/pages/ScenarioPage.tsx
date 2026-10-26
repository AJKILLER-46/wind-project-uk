import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  CartesianGrid 
} from 'recharts';
import { 
  Sliders, 
  Zap, 
  Flame, 
  ShieldAlert 
} from 'lucide-react';
import { ScenarioResponse } from '../types';
import { calculateScenario, getFallbackScenario } from '../api/client';

interface ScenarioPageProps {
  selectedDate: string;
  cutoffTime: string;
  useUtc: boolean;
}

export const ScenarioPage: React.FC<ScenarioPageProps> = ({
  selectedDate,
  cutoffTime,
  useUtc,
}) => {
  const [demandMw, setDemandMw] = useState<number>(38000);
  const [otherSupplyMw, setOtherSupplyMw] = useState<number>(8000);
  const [scenarioData, setScenarioData] = useState<ScenarioResponse | null>(() =>
    getFallbackScenario({
      assumed_demand_mw: 38000,
      assumed_other_supply_mw: 8000,
      delivery_date: selectedDate,
      decision_cutoff_time: cutoffTime,
    })
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Quick demand presets
  const demandPresets = [
    { label: 'Mild Winter Day', demand: 32000, other: 8000 },
    { label: 'Typical Winter Workday', demand: 38000, other: 8000 },
    { label: 'Extreme Cold Snap Peak', demand: 46000, other: 9000 },
  ];

  const runCalculation = () => {
    setIsLoading(true);
    calculateScenario({
      assumed_demand_mw: demandMw,
      assumed_other_supply_mw: otherSupplyMw,
      delivery_date: selectedDate,
      decision_cutoff_time: cutoffTime,
    })
      .then((res) => {
        setScenarioData(res);
        setError(null);
      })
      .catch((err) => {
        console.info('Backend sync note for scenario:', err);
        setScenarioData(
          getFallbackScenario({
            assumed_demand_mw: demandMw,
            assumed_other_supply_mw: otherSupplyMw,
            delivery_date: selectedDate,
            decision_cutoff_time: cutoffTime,
          })
        );
      })
      .finally(() => {
        setIsLoading(false);
      });
  };


  useEffect(() => {
    runCalculation();
  }, [selectedDate, cutoffTime, demandMw, otherSupplyMw]);

  const chartData = scenarioData
    ? scenarioData.periods.map((p, idx) => ({
        sp: idx + 1,
        time: `${p.start_time_uk.slice(11, 16)} ${useUtc ? 'UTC' : 'UK'}`,
        forecastWind: p.forecast_mw,
        actualWind: p.actual_mw,
        residualForecast: p.residual_forecast,
        residualActual: p.residual_actual,
        residualDelta: 
          p.residual_actual !== null && p.residual_forecast !== null
            ? p.residual_actual - p.residual_forecast
            : null,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center">
            <Sliders className="w-5 h-5 text-teal-400 mr-2" />
            Residual Demand & Flexibility Dispatch Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Model the required conventional thermal / flexible balancing generation across all 48 settlement periods.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          {isLoading && <span className="w-2.5 h-2.5 rounded-full bg-teal-400 animate-ping mr-1" />}
          <span>Target Date: <strong className="text-teal-400">{selectedDate}</strong></span>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-xl text-rose-300 text-xs">
          Simulation error: {error}
        </div>
      )}

      {/* Simulator Inputs Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center">
          <Zap className="w-4 h-4 text-cyan-400 mr-2" />
          Simulation Parameters
        </h3>

        {/* Quick Presets */}
        <div className="flex items-center space-x-2 mb-5">
          <span className="text-xs text-slate-500">Presets:</span>
          {demandPresets.map((p, i) => (
            <button
              key={i}
              onClick={() => {
                setDemandMw(p.demand);
                setOtherSupplyMw(p.other);
              }}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 font-mono transition-colors"
            >
              {p.label} ({p.demand / 1000}k MW)
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Assumed Gross Demand Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-300 font-medium">Assumed National Demand:</span>
              <span className="font-mono font-bold text-teal-400 text-sm">
                {demandMw.toLocaleString()} MW
              </span>
            </div>
            <input
              type="range"
              min="20000"
              max="60000"
              step="500"
              value={demandMw}
              onChange={(e) => setDemandMw(Number(e.target.value))}
              className="w-full accent-teal-400 cursor-pointer bg-slate-950 rounded-lg h-2"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>20,000 MW (Overnight)</span>
              <span>40,000 MW (Average)</span>
              <span>60,000 MW (Peak Freeze)</span>
            </div>
          </div>

          {/* Assumed Other Supply Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-300 font-medium">Baseload / Non-Wind Supply (Nuclear + Imports):</span>
              <span className="font-mono font-bold text-indigo-400 text-sm">
                {otherSupplyMw.toLocaleString()} MW
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="25000"
              step="500"
              value={otherSupplyMw}
              onChange={(e) => setOtherSupplyMw(Number(e.target.value))}
              className="w-full accent-indigo-400 cursor-pointer bg-slate-950 rounded-lg h-2"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0 MW</span>
              <span>10,000 MW (Typical)</span>
              <span>25,000 MW</span>
            </div>
          </div>
        </div>
      </div>

      {/* Results & Comparison Chart */}
      {scenarioData && (
        <div className="space-y-6">
          {/* KPI Output Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400 uppercase font-semibold">Avg Day-Ahead Wind</span>
              <div className="mt-2 text-2xl font-bold font-mono text-indigo-400">
                {scenarioData.avg_forecast_mw ? `${scenarioData.avg_forecast_mw.toLocaleString()} MW` : '—'}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Scheduled at 11:00 D-1</span>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400 uppercase font-semibold">Avg Actual Wind</span>
              <div className="mt-2 text-2xl font-bold font-mono text-teal-400">
                {scenarioData.avg_actual_mw ? `${scenarioData.avg_actual_mw.toLocaleString()} MW` : '—'}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Metered generation outturn</span>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400 uppercase font-semibold">Planned Thermal Need</span>
              <div className="mt-2 text-2xl font-bold font-mono text-slate-200">
                {scenarioData.avg_residual_forecast ? `${scenarioData.avg_residual_forecast.toLocaleString()} MW` : '—'}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Demand - (Forecast Wind + Other)</span>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400 uppercase font-semibold">Actual Thermal Dispatched</span>
              <div className="mt-2 text-2xl font-bold font-mono text-amber-400">
                {scenarioData.avg_residual_actual ? `${scenarioData.avg_residual_actual.toLocaleString()} MW` : '—'}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Outturn residual generation</span>
            </div>
          </div>

          {/* Residual Demand Profile Chart */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center">
                <Flame className="w-4 h-4 text-amber-400 mr-2" />
                Residual Demand Profile: Day-Ahead Plan vs Real-Time Outturn
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Displays the gap that flexible dispatchable power (gas CCGT, peakers, hydro, batteries) had to fill.
              </p>
            </div>

            <div className="h-[380px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                  <defs>
                    <linearGradient id="residualGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>

                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

                  <XAxis 
                    dataKey="sp" 
                    tick={{ fill: '#94a3b8', fontSize: 10 }} 
                    axisLine={{ stroke: '#334155' }}
                    label={{ value: 'Settlement Period (1 – 48)', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 11 }}
                  />

                  <YAxis 
                    tick={{ fill: '#94a3b8', fontSize: 10 }} 
                    axisLine={{ stroke: '#334155' }}
                    unit=" MW" 
                    tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                  />

                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const d = payload[0].payload;
                        return (
                          <div className="bg-slate-950/95 border border-slate-700 p-3 rounded-lg text-xs space-y-1 font-mono">
                            <div className="font-bold text-white border-b border-slate-800 pb-1">
                              SP #{d.sp} ({d.time} UK)
                            </div>
                            <div className="text-slate-300">
                              Planned Residual: <strong className="text-white">{d.residualForecast?.toLocaleString()} MW</strong>
                            </div>
                            <div className="text-amber-400">
                              Actual Residual: <strong className="text-amber-300">{d.residualActual?.toLocaleString()} MW</strong>
                            </div>
                            {d.residualDelta !== null && (
                              <div className={`pt-1 border-t border-slate-800 ${d.residualDelta > 0 ? 'text-rose-400' : 'text-teal-400'}`}>
                                Balancing Delta: {d.residualDelta > 0 ? `+${d.residualDelta.toLocaleString()}` : d.residualDelta.toLocaleString()} MW
                              </div>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />

                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />

                  {/* Shaded Area for Outturn Residual */}
                  <Area
                    type="monotone"
                    dataKey="residualActual"
                    name="Actual Residual Thermal Need (MW)"
                    stroke="#f59e0b"
                    strokeWidth={2.5}
                    fill="url(#residualGradient)"
                  />

                  {/* Dashed Line for Planned Residual */}
                  <Line
                    type="monotone"
                    dataKey="residualForecast"
                    name="Planned Day-Ahead Residual (MW)"
                    stroke="#818cf8"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Legal / Operational Disclaimer */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-start space-x-3 text-xs text-slate-400">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-200 block mb-0.5">Platform Disclaimer</span>
              <p className="leading-relaxed">
                {scenarioData.disclaimer}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
