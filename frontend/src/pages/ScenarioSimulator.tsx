import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import { useLiveStore } from '@/store/liveStore';
import OverviewTab from '@/components/simulator/OverviewTab';
import ScenarioBuilderTab from '@/components/simulator/ScenarioBuilderTab';
import ForecastTab from '@/components/simulator/ForecastTab';
import AIInsightsTab from '@/components/simulator/AIInsightsTab';
import VariableImportanceTab from '@/components/simulator/VariableImportanceTab';
import AISuggestedScenariosTab from '@/components/simulator/AISuggestedScenariosTab';
import ComparisonTab from '@/components/simulator/ComparisonTab';
import OptimizationTab from '@/components/simulator/OptimizationTab';
import HistoryTab from '@/components/simulator/HistoryTab';
import ReportsTab from '@/components/simulator/ReportsTab';
import {
  Sliders, Play, Save, Share2, Sparkles, LayoutDashboard,
  TrendingUp, Lightbulb, BarChart2, Brain, GitCompare,
  Zap, History, FileText, Rocket, RefreshCcw
} from 'lucide-react';

const tabs = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'builder', label: 'Scenario Builder', icon: Sliders },
  { id: 'forecast', label: 'Forecast', icon: TrendingUp },
  { id: 'ai-insights', label: 'AI Insights', icon: Lightbulb },
  { id: 'importance', label: 'Variable Importance', icon: BarChart2 },
  { id: 'ai-suggested', label: 'AI Suggested Scenarios', icon: Brain },
  { id: 'comparison', label: 'Comparison', icon: GitCompare },
  { id: 'optimization', label: 'Optimization', icon: Zap },
  { id: 'history', label: 'Simulation History', icon: History },
  { id: 'reports', label: 'Reports', icon: FileText },
];

const ScenarioSimulator: React.FC = () => {
  const navigate = useNavigate();
  const { isDark } = useUserStore();
  const { clearSimulatorCache } = useLiveStore();
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshKey, setRefreshKey] = useState(0);

  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';
  const borderSubtle = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';

  const handleManualRefresh = () => {
    clearSimulatorCache();
    setRefreshKey(prev => prev + 1);
  };

  // Auto refresh when returning to this page if a new model was trained
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'last_trained_timestamp' || e.key === 'hasMLResults') {
        clearSimulatorCache();
        setRefreshKey(prev => prev + 1);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  return (
    <div className="space-y-5 pb-10">
      {/* Top Bar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight" style={{ color: textPrimary }}>
              Scenario Simulator
            </h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 flex items-center gap-1 border border-indigo-500/20">
              <Sparkles className="w-3 h-3 text-indigo-400" /> Enterprise v3.0
            </span>
          </div>
          <p className="text-xs mt-0.5" style={{ color: textMuted }}>
            Real-time ML scenario simulation, multi-variable forecasting, AI insights, and trade-off optimization.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Train New Model */}
          <button
            onClick={() => navigate('/ml-predictions')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-sm shadow-emerald-500/20 hover:opacity-95 transition-all"
            title="Train a new AutoML model or select another dataset"
          >
            <Rocket className="w-3.5 h-3.5" /> Train New Model
          </button>

          {/* Refresh / Reload active model */}
          <button
            onClick={handleManualRefresh}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border hover:bg-white/5 transition-all"
            style={{ borderColor: borderSubtle, color: textMuted }}
            title="Reload active model metadata and clear cache"
          >
            <RefreshCcw className="w-3.5 h-3.5" /> Reload Data
          </button>

          <button
            onClick={() => setActiveTab('builder')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border hover:bg-white/5 transition-all"
            style={{ borderColor: borderSubtle, color: textMuted }}
          >
            <Save className="w-3.5 h-3.5" /> Save Scenario
          </button>

          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({ title: 'DataVision Scenario Simulator', url: window.location.href });
              } else {
                navigator.clipboard.writeText(window.location.href);
                alert('Link copied to clipboard!');
              }
            }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border hover:bg-white/5 transition-all"
            style={{ borderColor: borderSubtle, color: textMuted }}
          >
            <Share2 className="w-3.5 h-3.5" /> Share
          </button>

          <button
            onClick={() => setActiveTab('builder')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-white" /> Run Simulation
          </button>
        </div>
      </div>

      {/* 10-Tab Navigation Bar */}
      <div
        className="flex items-center gap-1 overflow-x-auto p-1.5 rounded-2xl border"
        style={{
          background: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
          borderColor: borderSubtle,
        }}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all relative ${
                active ? 'text-indigo-500 shadow-sm' : ''
              }`}
              style={{
                color: active ? '#6366f1' : textMuted,
                background: active ? (isDark ? 'rgba(99,102,241,0.12)' : '#ffffff') : 'transparent',
              }}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {active && (
                <motion.div
                  layoutId="activeTabGlow"
                  className="absolute inset-0 rounded-xl border border-indigo-500/30"
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content Display */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${activeTab}-${refreshKey}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'overview' && <OverviewTab onTabChange={setActiveTab} />}
          {activeTab === 'builder' && <ScenarioBuilderTab />}
          {activeTab === 'forecast' && <ForecastTab />}
          {activeTab === 'ai-insights' && <AIInsightsTab />}
          {activeTab === 'importance' && <VariableImportanceTab />}
          {activeTab === 'ai-suggested' && <AISuggestedScenariosTab />}
          {activeTab === 'comparison' && <ComparisonTab />}
          {activeTab === 'optimization' && <OptimizationTab />}
          {activeTab === 'history' && <HistoryTab />}
          {activeTab === 'reports' && <ReportsTab />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default ScenarioSimulator;
