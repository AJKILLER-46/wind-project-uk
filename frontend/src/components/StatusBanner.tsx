import { AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';
import { OverviewResponse } from '../types';

interface StatusBannerProps {
  overview?: OverviewResponse | null;
  isLoading: boolean;
  onRefresh?: () => void;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  overview,
  isLoading,
  onRefresh,
}) => {
  if (!overview) return null;

  const isFixture = overview.is_fixture_data;

  return (
    <div className={`border-b ${isFixture ? 'bg-amber-950/20 border-amber-900/40 text-amber-200' : 'bg-emerald-950/20 border-emerald-900/40 text-emerald-200'} px-4 py-2 text-xs transition-colors`}>
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div className="flex items-start md:items-center space-x-2">
          {isFixture ? (
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5 md:mt-0" />
          ) : (
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5 md:mt-0" />
          )}
          <div>
            <span className="font-semibold uppercase tracking-wider mr-2">
              {isFixture ? 'Notice: Synthetic Historical Baseline' : 'Live Elexon BMRS Verified'}
            </span>
            <span className="text-slate-300">
              {isFixture 
                ? 'Showing calibrated deterministic January 2026 fixture data (WINDFOR & FUELHH) designed for procurement model validation.'
                : 'Showing active telemetry streamed from Elexon BMRS Open API endpoints.'}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4 shrink-0 text-slate-400">
          <div className="flex items-center space-x-1" title="Delivery Date & Decision Cutoff">
            <span className="text-slate-500">Cutoff:</span>
            <span className="font-mono text-slate-200">{overview.decision_cutoff_time} D-1</span>
          </div>

          <div className="flex items-center space-x-1" title="Coverage across 48 Settlement Periods">
            <span className="text-slate-500">Coverage:</span>
            <span className="font-mono text-teal-400 font-semibold">{overview.coverage.coverage_pct}%</span>
            <span className="text-slate-500">({overview.coverage.matched_periods}/{overview.coverage.total_expected_periods} SPs)</span>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              title="Refresh data from server"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin text-teal-400' : ''}`} />
              <span>Sync</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
