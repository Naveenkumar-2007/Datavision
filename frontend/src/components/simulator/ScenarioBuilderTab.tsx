import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import VariableControl from './VariableControl';
import {
  Play, RefreshCcw, Save, Upload, Copy, Undo2, Redo2,
  Search, Sliders, ChevronDown, ChevronRight, Zap
} from 'lucide-react';

const ScenarioBuilderTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [variables, setVariables] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, any>>({});
  const [history, setHistory] = useState<Record<string, any>[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [search, setSearch] = useState('');
  const [lockedVars, setLockedVars] = useState<Set<string>>(new Set());
  const [pinnedVars, setPinnedVars] = useState<Set<string>>(new Set());
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [scenarioName, setScenarioName] = useState('');
  const [showSaveModal, setShowSaveModal] = useState(false);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  useEffect(() => {
    const fetchVars = async () => {
      try {
        const res = await apiService.getSimulatorVariables();
        if (res.data) {
          setVariables(res.data);
          const init: Record<string, any> = {};
          res.data.forEach((v: any) => { init[v.name] = v.current_value; });
          setValues(init);
          setHistory([init]);
          setHistoryIndex(0);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchVars();
  }, []);

  const handleChange = useCallback((name: string, val: any) => {
    if (lockedVars.has(name)) return;
    setValues(prev => {
      const next = { ...prev, [name]: val };
      setHistory(h => [...h.slice(0, historyIndex + 1), next]);
      setHistoryIndex(i => i + 1);
      return next;
    });
  }, [lockedVars, historyIndex]);

  const handleUndo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(i => i - 1);
      setValues(history[historyIndex - 1]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(i => i + 1);
      setValues(history[historyIndex + 1]);
    }
  };

  const handleReset = () => {
    const init: Record<string, any> = {};
    variables.forEach((v: any) => { init[v.name] = v.current_value; });
    setValues(init);
    setHistory(h => [...h, init]);
    setHistoryIndex(h => h + 1);
  };

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      const res = await apiService.runSimulation(values, scenarioName || undefined);
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  const handleSave = async () => {
    try {
      await apiService.saveScenario({
        name: scenarioName || `Scenario ${new Date().toLocaleTimeString()}`,
        variables: values,
        prediction: result?.prediction,
        confidence: result?.confidence,
        metrics: result?.secondary_metrics,
      });
      setShowSaveModal(false);
      setScenarioName('');
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (!autoUpdate || Object.keys(values).length === 0) return;
    const timer = setTimeout(handleSimulate, 600);
    return () => clearTimeout(timer);
  }, [values, autoUpdate]);

  const groups: Record<string, any[]> = {};
  const filteredVars = variables.filter(v =>
    v.display_name?.toLowerCase().includes(search.toLowerCase()) ||
    v.name?.toLowerCase().includes(search.toLowerCase())
  );
  const pinned = filteredVars.filter(v => pinnedVars.has(v.name));
  const unpinned = filteredVars.filter(v => !pinnedVars.has(v.name));
  unpinned.forEach(v => {
    const g = v.group || 'General';
    if (!groups[g]) groups[g] = [];
    groups[g].push(v);
  });

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>;
  }

  if (variables.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <Sliders className={`w-10 h-10 mb-3 ${isDark ? 'text-slate-600' : 'text-slate-300'}`} />
        <h3 className="text-base font-bold mb-1" style={{ color: textPrimary }}>No Variables to Configure</h3>
        <p className="text-xs max-w-md" style={{ color: textMuted }}>
          Variables are automatically generated from your dataset columns. Upload data in the Data Hub first.
        </p>
      </div>
    );
  }

  const targetName = result?.target_name || 'Target Metric';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      {/* Left: Controls */}
      <div className="lg:col-span-5 space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: textMuted }} />
            <input
              type="text"
              placeholder="Search variables..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl text-xs border outline-none focus:ring-2 focus:ring-indigo-500/30"
              style={{ background: cardBg, borderColor: cardBorder, color: textPrimary }}
            />
          </div>
          <button onClick={handleUndo} disabled={historyIndex <= 0} className="p-2 rounded-xl border disabled:opacity-30 hover:bg-white/5" style={{ borderColor: cardBorder }} title="Undo">
            <Undo2 className="w-4 h-4" style={{ color: textMuted }} />
          </button>
          <button onClick={handleRedo} disabled={historyIndex >= history.length - 1} className="p-2 rounded-xl border disabled:opacity-30 hover:bg-white/5" style={{ borderColor: cardBorder }} title="Redo">
            <Redo2 className="w-4 h-4" style={{ color: textMuted }} />
          </button>
          <button onClick={handleReset} className="p-2 rounded-xl border hover:bg-white/5" style={{ borderColor: cardBorder }} title="Reset">
            <RefreshCcw className="w-4 h-4" style={{ color: textMuted }} />
          </button>
        </div>

        {/* Variable controls */}
        <div className="rounded-2xl border p-5 space-y-4 max-h-[600px] overflow-y-auto" style={{ background: cardBg, borderColor: cardBorder }}>
          {pinned.length > 0 && (
            <div className="space-y-4 pb-3 border-b" style={{ borderColor: cardBorder }}>
              <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">📌 Pinned Variables</p>
              {pinned.map(v => (
                <VariableControl
                  key={v.name}
                  name={v.name}
                  displayName={v.display_name || v.name}
                  controlType={v.control_type}
                  value={values[v.name] ?? v.current_value}
                  onChange={(val) => handleChange(v.name, val)}
                  minValue={v.min_value}
                  maxValue={v.max_value}
                  step={v.step}
                  unit={v.unit}
                  options={v.options}
                  locked={lockedVars.has(v.name)}
                  pinned={true}
                  description={v.description}
                  onLock={() => setLockedVars(prev => { const n = new Set(prev); n.has(v.name) ? n.delete(v.name) : n.add(v.name); return n; })}
                  onPin={() => setPinnedVars(prev => { const n = new Set(prev); n.delete(v.name); return n; })}
                />
              ))}
            </div>
          )}

          {Object.entries(groups).map(([group, vars]) => (
            <div key={group} className="space-y-3">
              <button
                onClick={() => setCollapsedGroups(prev => { const n = new Set(prev); n.has(group) ? n.delete(group) : n.add(group); return n; })}
                className="flex items-center gap-2 w-full text-left"
              >
                {collapsedGroups.has(group) ? <ChevronRight className="w-3.5 h-3.5" style={{ color: textMuted }} /> : <ChevronDown className="w-3.5 h-3.5" style={{ color: textMuted }} />}
                <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: textMuted }}>{group}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)', color: textMuted }}>{vars.length}</span>
              </button>
              {!collapsedGroups.has(group) && (
                <div className="space-y-4 pl-2">
                  {vars.map(v => (
                    <VariableControl
                      key={v.name}
                      name={v.name}
                      displayName={v.display_name || v.name}
                      controlType={v.control_type}
                      value={values[v.name] ?? v.current_value}
                      onChange={(val) => handleChange(v.name, val)}
                      minValue={v.min_value}
                      maxValue={v.max_value}
                      step={v.step}
                      unit={v.unit}
                      options={v.options}
                      locked={lockedVars.has(v.name)}
                      pinned={pinnedVars.has(v.name)}
                      description={v.description}
                      onLock={() => setLockedVars(prev => { const n = new Set(prev); n.has(v.name) ? n.delete(v.name) : n.add(v.name); return n; })}
                      onPin={() => setPinnedVars(prev => { const n = new Set(prev); pinnedVars.has(v.name) ? n.delete(v.name) : n.add(v.name); return n; })}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setShowSaveModal(true)} className="flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-medium hover:bg-white/5 transition-all" style={{ borderColor: cardBorder, color: textMuted }}>
            <Save className="w-3.5 h-3.5" /> Save
          </button>
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-medium hover:bg-white/5 transition-all" style={{ borderColor: cardBorder, color: textMuted }}>
            <Upload className="w-3.5 h-3.5" /> Import
          </button>
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-medium hover:bg-white/5 transition-all" style={{ borderColor: cardBorder, color: textMuted }}>
            <Copy className="w-3.5 h-3.5" /> Clone
          </button>
          <div className="flex-1" />
          <button
            onClick={() => setAutoUpdate(!autoUpdate)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${autoUpdate ? 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/30' : 'border'}`}
            style={!autoUpdate ? { borderColor: cardBorder, color: textMuted } : undefined}
          >
            <Zap className="w-3.5 h-3.5" /> Auto Update
          </button>
          <button
            onClick={handleSimulate}
            disabled={simulating}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 disabled:opacity-60 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-white" /> {simulating ? 'Running...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {/* Right: Results */}
      <div className="lg:col-span-7 space-y-4">
        {/* Live Prediction */}
        <div className="rounded-2xl border p-6" style={{ background: cardBg, borderColor: cardBorder }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold" style={{ color: textPrimary }}>
              Live Prediction ({targetName})
            </h3>
            {result && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-bold">● Live</span>}
          </div>

          {result ? (
            <div className="space-y-5">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-[10px]" style={{ color: textMuted }}>Prediction</p>
                  <p className="text-xl font-bold text-indigo-500">
                    {result.formatted_prediction || result.prediction?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-[10px]" style={{ color: textMuted }}>Baseline</p>
                  <p className="text-xl font-bold" style={{ color: textMuted }}>
                    {result.formatted_baseline || result.baseline_prediction?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-[10px]" style={{ color: textMuted }}>Impact</p>
                  <p className={`text-xl font-bold ${result.impact_percentage >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {result.impact_percentage >= 0 ? '+' : ''}{result.impact_percentage?.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-[10px]" style={{ color: textMuted }}>Confidence</p>
                  <p className="text-xl font-bold text-emerald-500">{result.confidence?.toFixed(1)}%</p>
                </div>
              </div>

              {/* Feature contributions */}
              {result.feature_contributions?.length > 0 && (
                <div>
                  <p className="text-[10px] font-bold mb-2" style={{ color: textMuted }}>Feature Impact Shift</p>
                  <div className="space-y-2">
                    {result.feature_contributions.slice(0, 6).map((fc: any, i: number) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-[11px] w-32 truncate" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>{fc.feature}</span>
                        <div className="flex-1 h-1.5 rounded-full relative" style={{ background: isDark ? '#1e293b' : '#e2e8f0' }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(100, Math.abs(fc.contribution) * 3)}%` }}
                            className="h-full rounded-full"
                            style={{ background: fc.contribution >= 0 ? '#22c55e' : '#ef4444' }}
                          />
                        </div>
                        <span className={`text-[10px] font-bold w-12 text-right ${fc.contribution >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                          {fc.contribution >= 0 ? '+' : ''}{fc.contribution.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-[10px]" style={{ color: textMuted }}>
                Computed in {result.duration_ms}ms • {new Date().toLocaleTimeString()}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 gap-3">
              <Sliders className="w-8 h-8" style={{ color: textMuted }} />
              <p className="text-sm" style={{ color: textMuted }}>Adjust variables and run a simulation</p>
            </div>
          )}
        </div>

        {/* Secondary Metrics */}
        {result?.secondary_metrics && Object.keys(result.secondary_metrics).length > 0 && (
          <div className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
            <h3 className="text-sm font-bold mb-3" style={{ color: textPrimary }}>Secondary Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(result.secondary_metrics).map(([key, val]: [string, any]) => (
                <div key={key} className="p-3 rounded-xl border" style={{ borderColor: cardBorder }}>
                  <p className="text-[10px]" style={{ color: textMuted }}>{key}</p>
                  <p className="text-sm font-bold" style={{ color: textPrimary }}>
                    {val.formatted_simulated || val.simulated?.toLocaleString()}
                  </p>
                  <p className={`text-[10px] font-bold mt-1 ${val.impact >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {val.impact >= 0 ? '↑' : '↓'} {Math.abs(val.impact).toFixed(1)}% vs baseline
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowSaveModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative z-10 w-full max-w-md rounded-2xl border p-6 shadow-2xl"
            style={{ background: isDark ? '#1e1e2e' : '#ffffff', borderColor: cardBorder }}
          >
            <h3 className="text-base font-bold mb-4" style={{ color: textPrimary }}>Save Scenario</h3>
            <input
              type="text"
              placeholder="Scenario name..."
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-indigo-500/30 mb-4"
              style={{ background: cardBg, borderColor: cardBorder, color: textPrimary }}
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowSaveModal(false)} className="px-4 py-2 rounded-xl text-sm border" style={{ borderColor: cardBorder, color: textMuted }}>Cancel</button>
              <button onClick={handleSave} className="px-4 py-2 rounded-xl text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-medium">Save</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default ScenarioBuilderTab;
