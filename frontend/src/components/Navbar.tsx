import React from 'react';
import { 
  Wind, 
  Calendar, 
  Clock, 
  Activity, 
  Sliders, 
  Table, 
  TrendingUp, 
  Database,
  Globe,
  Layers
} from 'lucide-react';
import { HealthResponse } from '../types';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  selectedDate: string;
  setSelectedDate: (d: string) => void;
  cutoffTime: string;
  setCutoffTime: (t: string) => void;
  useUtc: boolean;
  setUseUtc: (u: boolean) => void;
  health?: HealthResponse | null;
  isFixtureData?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  selectedDate,
  setSelectedDate,
  cutoffTime,
  setCutoffTime,
  useUtc,
  setUseUtc,
  health,
  isFixtureData,
}) => {
  const quickDates = [
    { label: 'Jan 10 (Calm)', date: '2026-01-10', badge: 'Low Wind' },
    { label: 'Jan 15 (Typical)', date: '2026-01-15', badge: 'Normal' },
    { label: 'Jan 21 (Storm Isha)', date: '2026-01-21', badge: 'High Wind' },
    { label: 'Jan 28 (Volatile)', date: '2026-01-28', badge: 'Ramp Event' },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40">
      {/* Top Banner / Status */}
      <div className="bg-slate-950/80 border-b border-slate-800/60 px-4 py-1.5 text-xs flex flex-wrap items-center justify-between text-slate-400 gap-2">
        <div className="flex items-center space-x-3">
          <span className="flex items-center text-teal-400 font-semibold tracking-wide">
            <span className="w-2 h-2 rounded-full bg-teal-400 mr-2 animate-ping" />
            UK NATIONAL GRID / ELEXON BMRS INTELLIGENCE
          </span>
          <span className="text-slate-600">|</span>
          <span className="flex items-center">
            <Database className="w-3.5 h-3.5 mr-1 text-slate-500" />
            Mode: {isFixtureData ? (
              <span className="text-amber-400 font-medium ml-1">Synthetic Jan 2026 Baseline Fixtures</span>
            ) : (
              <span className="text-emerald-400 font-medium ml-1">Live Elexon BMRS API</span>
            )}
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => setUseUtc(!useUtc)}
            className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Toggle between UTC and UK Local Time (GMT/BST)"
          >
            <Globe className="w-3 h-3 text-teal-400" />
            <span>Time: <strong className="text-teal-300">{useUtc ? 'UTC' : 'UK Local (GMT)'}</strong></span>
          </button>

          <span className="text-slate-500">
            Backend: {health ? (
              <span className="text-emerald-400 font-mono">v{health.version} [Online]</span>
            ) : (
              <span className="text-amber-400 font-mono">Connecting...</span>
            )}
          </span>
        </div>
      </div>

      {/* Main Nav */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Wind className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white">WindLens</span>
                <span className="text-xs font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  UK
                </span>
              </div>
              <p className="text-xs text-slate-400">Day-Ahead Wind Forecast & Procurement Platform</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex space-x-1">
            <button
              onClick={() => setCurrentTab('overview')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'overview'
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-4 h-4 mr-1.5" />
              Executive Overview
            </button>

            <button
              onClick={() => setCurrentTab('explorer')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'explorer'
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Layers className="w-4 h-4 mr-1.5" />
              Forecast Explorer
            </button>

            <button
              onClick={() => setCurrentTab('analytics')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'analytics'
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <TrendingUp className="w-4 h-4 mr-1.5" />
              Accuracy Analysis
            </button>

            <button
              onClick={() => setCurrentTab('settlement')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'settlement'
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Table className="w-4 h-4 mr-1.5" />
              Settlement Ledger
            </button>

            <button
              onClick={() => setCurrentTab('scenario')}
              className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'scenario'
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Sliders className="w-4 h-4 mr-1.5" />
              Scenario Simulator
            </button>
          </nav>

          {/* Controls: Date Picker & Decision Cutoff */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5">
              <Calendar className="w-4 h-4 text-teal-400 mr-2" />
              <input
                type="date"
                min="2026-01-01"
                max="2026-01-31"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent text-sm text-slate-100 focus:outline-none font-mono cursor-pointer"
              />
            </div>

            <div className="flex items-center bg-slate-800/80 border border-slate-700/80 rounded-lg px-2.5 py-1.5" title="Day-Ahead Gate Cutoff Time (UK Local)">
              <Clock className="w-4 h-4 text-cyan-400 mr-1.5" />
              <span className="text-xs text-slate-400 mr-1">Gate:</span>
              <select
                value={cutoffTime}
                onChange={(e) => setCutoffTime(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none font-mono cursor-pointer"
              >
                <option value="11:00" className="bg-slate-900 text-slate-100">11:00 D-1 (Standard)</option>
                <option value="12:00" className="bg-slate-900 text-slate-100">12:00 D-1 (EPEX DA)</option>
                <option value="16:00" className="bg-slate-900 text-slate-100">16:00 D-1 (Afternoon)</option>
                <option value="23:00" className="bg-slate-900 text-slate-100">23:00 D-1 (Late Night)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Quick Date Presets */}
        <div className="py-2 border-t border-slate-800/50 flex flex-wrap items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 md:pb-0">
            <span className="text-slate-500 mr-1">Key Scenarios:</span>
            {quickDates.map((item) => (
              <button
                key={item.date}
                onClick={() => setSelectedDate(item.date)}
                className={`px-2.5 py-1 rounded-md transition-all font-mono text-xs flex items-center space-x-1.5 ${
                  selectedDate === item.date
                    ? 'bg-teal-500 text-slate-950 font-semibold shadow-md shadow-teal-500/20'
                    : 'bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/50'
                }`}
              >
                <span>{item.label}</span>
                <span className={`text-[10px] px-1 py-0.2 rounded ${
                  selectedDate === item.date ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-700/60 text-slate-300'
                }`}>
                  {item.badge}
                </span>
              </button>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 hidden lg:block">
            Delivery Date Range: <span className="font-mono text-teal-400">2026-01-01</span> to <span className="font-mono text-teal-400">2026-01-31</span> (Winter Peak Study)
          </div>
        </div>
      </div>
    </header>
  );
};
