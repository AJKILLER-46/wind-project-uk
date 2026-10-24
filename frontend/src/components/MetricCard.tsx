import React, { useState } from 'react';
import { HelpCircle, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { MetricCard as MetricCardType } from '../types';

interface MetricCardProps {
  metric: MetricCardType;
  accentColor?: 'teal' | 'cyan' | 'amber' | 'rose' | 'indigo';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  metric,
  accentColor = 'teal',
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const getAccentBorder = () => {
    switch (accentColor) {
      case 'amber':
        return 'border-amber-500/30 hover:border-amber-500/60';
      case 'rose':
        return 'border-rose-500/30 hover:border-rose-500/60';
      case 'cyan':
        return 'border-cyan-500/30 hover:border-cyan-500/60';
      case 'indigo':
        return 'border-indigo-500/30 hover:border-indigo-500/60';
      default:
        return 'border-teal-500/30 hover:border-teal-500/60';
    }
  };

  const getAccentBadge = () => {
    switch (accentColor) {
      case 'amber':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'rose':
        return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
      case 'cyan':
        return 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
      case 'indigo':
        return 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
      default:
        return 'bg-teal-500/15 text-teal-300 border-teal-500/30';
    }
  };

  // Determine trend / direction icon for Bias
  const renderTrend = () => {
    if (metric.name === 'BIAS' && metric.value !== null) {
      if (metric.value > 0) {
        return (
          <span className="flex items-center text-rose-400 text-xs font-medium" title="Underforecasting: actual > forecast (shortage risk)">
            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
            Underforecast (+{metric.value} MW)
          </span>
        );
      } else if (metric.value < 0) {
        return (
          <span className="flex items-center text-cyan-400 text-xs font-medium" title="Overforecasting: forecast > actual (curtailment/surplus risk)">
            <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
            Overforecast ({metric.value} MW)
          </span>
        );
      }
      return (
        <span className="flex items-center text-slate-400 text-xs font-medium">
          <Minus className="w-3.5 h-3.5 mr-0.5" /> Neutral
        </span>
      );
    }
    return null;
  };

  return (
    <div className={`relative bg-slate-900/80 backdrop-blur-sm border rounded-xl p-4 transition-all duration-200 shadow-md ${getAccentBorder()} group`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-1.5">
          <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
            {metric.name}
          </span>
          <button
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            onClick={() => setShowTooltip(!showTooltip)}
            className="text-slate-500 hover:text-teal-400 focus:outline-none transition-colors"
            aria-label={`Definition of ${metric.name}`}
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
        </div>

        <span className={`text-[11px] font-mono px-2 py-0.5 rounded border ${getAccentBadge()}`}>
          {metric.unit}
        </span>
      </div>

      {/* Main value display */}
      <div className="mt-3 flex items-baseline space-x-2">
        <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
          {metric.value !== null && metric.value !== undefined
            ? metric.value.toLocaleString(undefined, { maximumFractionDigits: 1 })
            : '—'}
        </span>
        <span className="text-sm font-medium text-slate-400">{metric.unit}</span>
      </div>

      {/* Subtitle / Observations / Trend */}
      <div className="mt-2 flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-800/80">
        <span>{metric.n_observations} SPs evaluated</span>
        {renderTrend()}
        {metric.excluded_count > 0 && (
          <span className="text-amber-400/90" title={metric.excluded_reason || 'Excluded periods'}>
            ({metric.excluded_count} excl.)
          </span>
        )}
      </div>

      {/* Interactive Definition Tooltip */}
      {showTooltip && (
        <div className="absolute left-0 right-0 -bottom-2 transform translate-y-full z-50 p-3 bg-slate-950 border border-slate-700 rounded-lg shadow-2xl text-xs text-slate-200 pointer-events-none">
          <p className="font-semibold text-teal-300 mb-1">{metric.definition}</p>
          <p className="text-slate-400">{metric.interpretation}</p>
        </div>
      )}
    </div>
  );
};
