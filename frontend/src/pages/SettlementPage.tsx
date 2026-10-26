import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Download, 
  Search, 
  ArrowUpDown, 
  CheckCircle2 
} from 'lucide-react';
import { SettlementResponse, SettlementPeriodRow } from '../types';
import { fetchSettlementPeriods, getSettlementCsvExportUrl, downloadSettlementCsvDirectly } from '../api/client';

interface SettlementPageProps {
  selectedDate: string;
  cutoffTime: string;
  useUtc: boolean;
}

export const SettlementPage: React.FC<SettlementPageProps> = ({
  selectedDate,
  cutoffTime,
  useUtc,
}) => {
  const [data, setData] = useState<SettlementResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Search states
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterMode, setFilterMode] = useState<'all' | 'peak' | 'high_error'>('all');
  const [sortField, setSortField] = useState<keyof SettlementPeriodRow>('settlement_period');
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchSettlementPeriods(selectedDate, cutoffTime, 1, 48)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load settlement periods');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedDate, cutoffTime]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
        <div className="w-12 h-12 border-4 border-teal-500/20 border-t-teal-500 rounded-full animate-spin" />
        <p className="text-slate-400 font-mono text-sm">Loading 48 settlement periods for {selectedDate}...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-rose-950/20 border border-rose-900/40 rounded-xl text-rose-300 text-sm">
        <p>Error loading settlement periods: {error}</p>
      </div>
    );
  }

  // Filter rows
  let filtered = data.rows.filter((row) => {
    // Search
    const term = searchTerm.toLowerCase();
    const spMatch = row.settlement_period?.toString().includes(term);
    const timeMatch = row.start_time_uk.toLowerCase().includes(term) || row.start_time_utc.toLowerCase().includes(term);
    if (term && !spMatch && !timeMatch) return false;

    // Filter Mode
    if (filterMode === 'peak') {
      const sp = row.settlement_period || 0;
      if (sp < 15 || sp > 38) return false;
    } else if (filterMode === 'high_error') {
      if (!row.abs_error_mw || row.abs_error_mw < 800) return false;
    }

    return true;
  });

  // Sort rows
  filtered.sort((a, b) => {
    const valA = a[sortField];
    const valB = b[sortField];
    if (valA === null || valA === undefined) return 1;
    if (valB === null || valB === undefined) return -1;
    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  const toggleSort = (field: keyof SettlementPeriodRow) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const exportUrl = getSettlementCsvExportUrl(selectedDate, cutoffTime);

  // Summary calculations
  const totalForecastGwh = (data.rows.reduce((acc, r) => acc + (r.forecast_mw || 0), 0) * 0.5) / 1000;
  const totalActualGwh = (data.rows.reduce((acc, r) => acc + (r.actual_mw || 0), 0) * 0.5) / 1000;
  const netErrorGwh = totalActualGwh - totalForecastGwh;

  return (
    <div className="space-y-6">
      {/* Table Header and Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center">
            <Table className="w-5 h-5 text-teal-400 mr-2" />
            Settlement Period Ledger ({selectedDate})
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Half-hourly outturn generation vs day-ahead gate forecasts. Total 48 settlement periods.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* CSV Export Button */}
          <button
            onClick={() => {
              if (data?.rows?.length) {
                downloadSettlementCsvDirectly(data.rows, selectedDate);
              } else {
                window.location.href = exportUrl;
              }
            }}
            title="Download full 48-period audit ledger as CSV"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-slate-950 font-semibold text-xs shadow-md shadow-teal-600/20 transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download CSV Export</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search SP (e.g. 24) or time..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500/50"
            />
          </div>

          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setFilterMode('all')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'all' ? 'bg-teal-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              All (48)
            </button>
            <button
              onClick={() => setFilterMode('peak')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'peak' ? 'bg-teal-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
              title="Peak periods SP 15 – 38 (07:00 – 19:00)"
            >
              Peak Only
            </button>
            <button
              onClick={() => setFilterMode('high_error')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'high_error' ? 'bg-teal-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
              title="Settlement periods where |error| > 800 MW"
            >
              High Error
            </button>
          </div>
        </div>

        {/* Quick summary badges */}
        <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
          <span>Forecast: <strong className="text-white">{totalForecastGwh.toFixed(1)} GWh</strong></span>
          <span>•</span>
          <span>Actual: <strong className="text-teal-400">{totalActualGwh.toFixed(1)} GWh</strong></span>
          <span>•</span>
          <span>
            Net Error:{' '}
            <strong className={netErrorGwh >= 0 ? 'text-cyan-400' : 'text-rose-400'}>
              {netErrorGwh >= 0 ? `+${netErrorGwh.toFixed(1)}` : netErrorGwh.toFixed(1)} GWh
            </strong>
          </span>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono select-none">
                <th 
                  onClick={() => toggleSort('settlement_period')}
                  className="py-3 px-3 cursor-pointer hover:text-teal-400 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>SP #</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-3">Time ({useUtc ? 'UTC' : 'UK Local'})</th>
                <th 
                  onClick={() => toggleSort('forecast_mw')}
                  className="py-3 px-3 text-right cursor-pointer hover:text-teal-400 transition-colors"
                >
                  <div className="flex items-center justify-end space-x-1">
                    <span>Forecast (MW)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th 
                  onClick={() => toggleSort('actual_mw')}
                  className="py-3 px-3 text-right cursor-pointer hover:text-teal-400 transition-colors"
                >
                  <div className="flex items-center justify-end space-x-1">
                    <span>Actual (MW)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th 
                  onClick={() => toggleSort('error_mw')}
                  className="py-3 px-3 text-right cursor-pointer hover:text-teal-400 transition-colors"
                >
                  <div className="flex items-center justify-end space-x-1">
                    <span>Error (Actual - F)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th 
                  onClick={() => toggleSort('abs_error_mw')}
                  className="py-3 px-3 text-right cursor-pointer hover:text-teal-400 transition-colors"
                >
                  <div className="flex items-center justify-end space-x-1">
                    <span>|Error| (MW)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-3 text-center">Period Type</th>
                <th className="py-3 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filtered.map((row) => {
                const sp = row.settlement_period || 0;
                const isPeak = sp >= 15 && sp <= 38;
                const isPositive = row.error_mw !== null && row.error_mw > 0;
                const isLargeError = row.abs_error_mw !== null && row.abs_error_mw > 1000;

                return (
                  <tr 
                    key={row.start_time_utc}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isLargeError ? 'bg-amber-950/10' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 font-bold text-teal-400">
                      SP {row.settlement_period}
                    </td>

                    <td className="py-2.5 px-3 text-slate-300">
                      {useUtc ? row.start_time_utc.slice(11, 16) : row.start_time_uk.slice(11, 16)}
                      <span className="text-[10px] text-slate-500 ml-1">
                        – {useUtc ? row.start_time_utc.slice(11, 16) : row.start_time_uk.slice(11, 16)} (+30m)
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-right font-semibold text-slate-200">
                      {row.forecast_mw !== null ? row.forecast_mw.toLocaleString() : '—'}
                    </td>

                    <td className="py-2.5 px-3 text-right font-semibold text-teal-300">
                      {row.actual_mw !== null ? row.actual_mw.toLocaleString() : '—'}
                    </td>

                    <td className="py-2.5 px-3 text-right font-bold">
                      {row.error_mw !== null ? (
                        <span className={isPositive ? 'text-rose-400' : 'text-cyan-400'}>
                          {isPositive ? `+${row.error_mw.toFixed(0)}` : row.error_mw.toFixed(0)}
                        </span>
                      ) : '—'}
                    </td>

                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {row.abs_error_mw !== null ? row.abs_error_mw.toFixed(0) : '—'}
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        isPeak 
                          ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30' 
                          : 'bg-slate-800 text-slate-400'
                      }`}>
                        {isPeak ? 'PEAK' : 'OFF-PEAK'}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <span className="flex items-center justify-center space-x-1 text-emerald-400 text-[11px]">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Matched</span>
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
