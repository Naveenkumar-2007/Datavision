import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import { useLiveStore } from '@/store/liveStore';
import apiService from '@/services/api';
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
  Zap, History, FileText, Rocket, RefreshCcw, Database,
  AlertTriangle, Upload
} from 'lucide-react';

const tabs = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'builder', label: 'Scenario Builder', icon: Sliders },
  { id: 'forecast', label: 'Forecast', icon: TrendingUp },
  { id: 'ai-insights', label: 'AI Insights', icon: Lightbulb },
  { id: 'importance', label: 'Variable Importance', icon: BarChart2 },
  { id: 'ai-suggested', label: 'AI Suggested', icon: Brain },
  { id: 'comparison', label: 'Comparison', icon: GitCompare },
  { id: 'optimization', label: 'Optimization', icon: Zap },
  { id: 'history', label: 'History', icon: History },
  { id: 'reports', label: 'Reports', icon: FileText },
];

const ScenarioSimulator: React.FC = () => {
  const navigate = useNavigate();
  const { isDark } = useUserStore();
  const { clearSimulatorCache } = useLiveStore();
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshKey, setRefreshKey] = useState(0);
  const [hasData, setHasData] = useState<boolean | null>(null); // null = loading
  const [simRunning, setSimRunning] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDesc, setSaveDesc] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';
  const borderSubtle = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';

  const handleManualRefresh = () => {
    clearSimulatorCache();
    setRefreshKey(prev => prev + 1);
    checkDataAvailability();
  };

  // Check if user has data to simulate
  const checkDataAvailability = async () => {
    try {
      const res = await apiService.getSimulatorVariables();
      setHasData(res.data && Array.isArray(res.data) && res.data.length > 0);
    } catch {
      setHasData(false);
    }
  };

  useEffect(() => {
    checkDataAvailability();
  }, []);

  // Auto refresh when returning to this page if a new model was trained
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'last_trained_timestamp' || e.key === 'hasMLResults') {
        clearSimulatorCache();
        setRefreshKey(prev => prev + 1);
        checkDataAvailability();
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  // Run actual simulation
  const handleRunSimulation = async () => {
    setSimRunning(true);
    try {
      const varsRes = await apiService.getSimulatorVariables();
      if (varsRes.data && varsRes.data.length > 0) {
        const values: Record<string, any> = {};
        varsRes.data.forEach((v: any) => { values[v.name || v.display_name] = v.current_value; });
        const runRes = await apiService.runSimulation(values);
        setSimResult(runRes.data);
        setActiveTab('builder');
      }
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimRunning(false);
    }
  };

  // Save current scenario
  const handleSaveScenario = async () => {
    if (!saveName.trim()) return;
    setSaving(true);
    try {
      const varsRes = await apiService.getSimulatorVariables();
      const values: Record<string, any> = {};
      if (varsRes.data) {
        varsRes.data.forEach((v: any) => { values[v.name || v.display_name] = v.current_value; });
      }
      await apiService.saveScenario({
        name: saveName,
        description: saveDesc,
        variables: values,
        prediction: simResult?.prediction,
        confidence: simResult?.confidence,
        metrics: simResult?.metrics,
      });
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveModalOpen(false);
        setSaveSuccess(false);
        setSaveName('');
        setSaveDesc('');
      }, 1500);
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  };

  // No data state
  if (hasData === false) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md"
        >
          <div className={`p-4 rounded-2xl inline-flex mb-4 ${isDark ? 'bg-amber-500/10' : 'bg-amber-50'}`}>
            <Database className={`w-10 h-10 ${isDark ? 'text-amber-400' : 'text-amber-500'}`} />
          </div>
          <h2 className="text-xl font-bold mb-2" style={{ color: textPrimary }}>No Dataset Available</h2>
          <p className="text-sm mb-6" style={{ color: textMuted }}>
            The Scenario Simulator requires a dataset with a trained model to work. 
            Upload data in the Data Hub and train a model in AutoML first.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => navigate('/datahub')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/20 hover:opacity-95 transition-all"
            >
              <Upload className="w-3.5 h-3.5" /> Upload Dataset
            </button>
            <button
              onClick={() => navigate('/ml-predictions')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all"
              style={{ borderColor: borderSubtle, color: textMuted }}
            >
              <Rocket className="w-3.5 h-3.5" /> Train Model
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Loading state
  if (hasData === null) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="flex items-center gap-3">
          <RefreshCcw className="w-5 h-5 text-indigo-500 animate-spin" />
          <span className="text-sm" style={{ color: textMuted }}>Loading simulator data...</span>
        </div>
      </div>
    );
  }

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
          <button
            onClick={() => navigate('/ml-predictions')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-sm shadow-emerald-500/20 hover:opacity-95 transition-all"
            title="Train a new AutoML model or select another dataset"
          >
            <Rocket className="w-3.5 h-3.5" /> Train New Model
          </button>

          <button
            onClick={handleManualRefresh}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border hover:bg-white/5 transition-all"
            style={{ borderColor: borderSubtle, color: textMuted }}
            title="Reload active model metadata and clear cache"
          >
            <RefreshCcw className="w-3.5 h-3.5" /> Reload Data
          </button>

          <button
            onClick={() => setSaveModalOpen(true)}
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
            onClick={handleRunSimulation}
            disabled={simRunning}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all ${
              simRunning ? 'bg-indigo-400 cursor-wait' : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {simRunning ? (
              <RefreshCcw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-white" />
            )}
            {simRunning ? 'Running...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {/* Tab Navigation Bar */}
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

      {/* Save Scenario Modal */}
      <AnimatePresence>
        {saveModalOpen && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setSaveModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className={`w-full max-w-md p-6 rounded-2xl border shadow-2xl ${
                isDark ? 'bg-[#12131a] border-white/10' : 'bg-white border-slate-200'
              }`}
            >
              {saveSuccess ? (
                <div className="text-center py-6">
                  <div className="p-3 rounded-full bg-emerald-500/10 inline-flex mb-3">
                    <svg className="w-8 h-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold" style={{ color: textPrimary }}>Scenario Saved!</h3>
                </div>
              ) : (
                <>
                  <h3 className="text-lg font-bold mb-4" style={{ color: textPrimary }}>Save Current Scenario</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-semibold block mb-1" style={{ color: textMuted }}>Scenario Name *</label>
                      <input
                        value={saveName}
                        onChange={e => setSaveName(e.target.value)}
                        placeholder="e.g., Best-case Revenue Q3"
                        className={`w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-indigo-500 transition-all ${
                          isDark ? 'bg-white/5 border-white/10 text-white placeholder:text-slate-600' : 'bg-slate-50 border-slate-200 text-slate-900'
                        }`}
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold block mb-1" style={{ color: textMuted }}>Description (optional)</label>
                      <textarea
                        value={saveDesc}
                        onChange={e => setSaveDesc(e.target.value)}
                        rows={2}
                        placeholder="What does this scenario represent?"
                        className={`w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-indigo-500 transition-all resize-none ${
                          isDark ? 'bg-white/5 border-white/10 text-white placeholder:text-slate-600' : 'bg-slate-50 border-slate-200 text-slate-900'
                        }`}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-5">
                    <button
                      onClick={() => setSaveModalOpen(false)}
                      className="flex-1 px-4 py-2 rounded-xl text-xs font-semibold border transition-all"
                      style={{ borderColor: borderSubtle, color: textMuted }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveScenario}
                      disabled={!saveName.trim() || saving}
                      className={`flex-1 px-4 py-2 rounded-xl text-xs font-semibold text-white transition-all ${
                        !saveName.trim() || saving ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
                      }`}
                    >
                      {saving ? 'Saving...' : 'Save Scenario'}
                    </button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ScenarioSimulator;
