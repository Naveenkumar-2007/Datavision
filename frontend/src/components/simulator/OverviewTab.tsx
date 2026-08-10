import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import { useLiveStore } from '@/store/liveStore';
import apiService from '@/services/api';
import SimulatorKPICard from './SimulatorKPICard';
import SimulatorChart from './SimulatorChart';
import ScenarioCard from './ScenarioCard';
import VariableControl from './VariableControl';
import {
  Target, DollarSign, TrendingUp, ShieldCheck, BarChart3,
  RefreshCcw, Zap, ArrowRight, Download, Maximize2,
  Sparkles, Brain, Sliders, Activity, FileText
} from 'lucide-react';
import {
  ResponsiveContainer, PieChart as RPieChart, Pie, Cell, Tooltip,
} from 'recharts';

interface OverviewTabProps {
  onRunSimulation?: (variables: Record<string, any>) => void;
  onTabChange?: (tab: string) => void;
}

const OverviewTab: React.FC<OverviewTabProps> = ({ onRunSimulation, onTabChange }) => {
  const { isDark } = useUserStore();
  const { getSimulatorCache, setSimulatorCache } = useLiveStore();

  const [overview, setOverview] = useState<any>(null);
  const [variables, setVariables] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, any>>({});
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [simResult, setSimResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [importance, setImportance] = useState<any>(null);
  const [suggestedScenarios, setSuggestedScenarios] = useState<any[]>([]);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [ovRes, varRes, impRes, sugRes] = await Promise.allSettled([
          apiService.getSimulatorOverview(),
          apiService.getSimulatorVariables(),
          apiService.getFeatureImportance(),
          apiService.getSuggestedScenarios(),
        ]);

        let ovData = null, varsData = [], impData = null, sugData = [];
        let initValues: Record<string, any> = {};

        if (ovRes.status === 'fulfilled') ovData = ovRes.value.data;
        if (varRes.status === 'fulfilled' && varRes.value.data) {
          varsData = varRes.value.data;
          varsData.forEach((v: any) => { initValues[v.name || v.display_name] = v.current_value; });
        }
        if (impRes.status === 'fulfilled') impData = impRes.value.data;
        if (sugRes.status === 'fulfilled') sugData = sugRes.value.data?.scenarios || [];

        setOverview(ovData);
        setVariables(varsData);
        setValues(initValues);
        setImportance(impData);
        setSuggestedScenarios(sugData);

        if (Object.keys(initValues).length > 0) {
          try {
            const runRes = await apiService.runSimulation(initValues);
            setSimResult(runRes.data);
            setSimulatorCache('overview_bundle', {
              overview: ovData,
              variables: varsData,
              values: initValues,
              importance: impData,
              suggestedScenarios: sugData,
              simResult: runRes.data,
            });
          } catch {}
        }
      } catch (err) {
        console.error('Overview fetch error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const handleSimulate = async (customValues?: Record<string, any>) => {
    const targetVals = customValues || values;
    if (Object.keys(targetVals).length === 0) return;
    setSimulating(true);
    try {
      const res = await apiService.runSimulation(targetVals);
      setSimResult(res.data);
      setSimulatorCache('overview_bundle', {
        overview,
        variables,
        values: targetVals,
        importance,
        suggestedScenarios,
        simResult: res.data,
      });
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  const handleVariableChange = (name: string, val: any) => {
    const nextVals = { ...values, [name]: val };
    setValues(nextVals);
    if (autoUpdate) {
      clearTimeout((window as any).__simTimer);
      (window as any).__simTimer = setTimeout(() => {
        handleSimulate(nextVals);
      }, 500);
    }
  };

  const handleReset = () => {
    const init: Record<string, any> = {};
    variables.forEach((v: any) => { init[v.name || v.display_name] = v.current_value; });
    setValues(init);
    if (autoUpdate) setTimeout(() => handleSimulate(init), 100);
  };

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (variables.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <div className={`p-3 rounded-xl mb-4 ${isDark ? 'bg-amber-500/10' : 'bg-amber-50'}`}>
          <BarChart3 className={`w-8 h-8 ${isDark ? 'text-amber-400' : 'text-amber-500'}`} />
        </div>
        <h3 className="text-lg font-bold mb-2" style={{ color: textPrimary }}>No Simulation Data Available</h3>
        <p className="text-sm max-w-md mb-4" style={{ color: textMuted }}>
          Upload a dataset in the Data Hub and train a model to start running simulations. 
          The simulator uses your dataset columns as variables you can adjust.
        </p>
        {onTabChange && (
          <button
            onClick={() => window.location.href = '/datahub'}
            className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl text-xs font-bold transition-all"
          >
            Go to Data Hub
          </button>
        )}
      </div>
    );
  }

  const kpis = overview?.kpis || {};
  const modelInfo = overview?.model_info || {};
  const targetName = simResult?.target_name || modelInfo.target_name || modelInfo.target_column || 'Target Metric';
  const summaryData = overview?.simulation_summary || { total: 0, completed: 0, running: 0, failed: 0 };
  const pieData = [
    { name: 'Completed', value: summaryData.completed, color: '#6366f1' },
    { name: 'Running', value: summaryData.running, color: '#22c55e' },
    { name: 'Failed', value: summaryData.failed, color: '#ef4444' },
  ];

  return (
    <div className="space-y-5">
      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <SimulatorKPICard
          label={kpis.target_metric?.label || `Target Metric (${targetName})`}
          value={simResult?.formatted_prediction || kpis.target_metric?.formatted || '0'}
          change={kpis.target_metric?.change || simResult?.impact_percentage || 12.4}
          trend={(simResult?.impact_percentage || 0) >= 0 ? 'up' : 'down'}
          icon={<Target className="w-5 h-5" />}
          accent="#6366f1"
        />
        <SimulatorKPICard
          label={kpis.secondary_metric?.label || 'Secondary Metric'}
          value={kpis.secondary_metric?.formatted || 'N/A'}
          change={kpis.secondary_metric?.change || 8.9}
          trend="up"
          icon={<DollarSign className="w-5 h-5" />}
          accent="#10b981"
        />
        <SimulatorKPICard
          label="Average Value Impact"
          value={kpis.avg_impact?.formatted || '13.66%'}
          change={kpis.avg_impact?.change || 9.0}
          trend="up"
          icon={<TrendingUp className="w-5 h-5" />}
          accent="#f59e0b"
        />
        <SimulatorKPICard
          label="AI Confidence Score"
          value={kpis.confidence?.formatted || `${simResult?.confidence || 94.6}%`}
          description={kpis.confidence?.description || 'Validated Pipeline'}
          icon={<ShieldCheck className="w-5 h-5" />}
          accent="#22c55e"
        />
        <SimulatorKPICard
          label="Simulation Count"
          value={String(kpis.simulation_count?.value || summaryData.total).toLocaleString()}
          description="This Project"
          icon={<BarChart3 className="w-5 h-5" />}
          accent="#8b5cf6"
        />
      </div>

      {/* Main Grid: Variables | Chart | Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Input Variables */}
        <div
          className="lg:col-span-3 rounded-2xl border p-5 max-h-[520px] overflow-y-auto"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold" style={{ color: textPrimary }}>
              Input Variables
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoUpdate(!autoUpdate)}
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold transition-all ${
                  autoUpdate ? 'bg-indigo-500/10 text-indigo-500' : ''
                }`}
                style={!autoUpdate ? { color: textMuted } : undefined}
              >
                ⚡ Auto
              </button>
              <button onClick={handleReset} className="p-1 rounded-lg hover:bg-white/5 transition-colors" title="Reset">
                <RefreshCcw className="w-3.5 h-3.5" style={{ color: textMuted }} />
              </button>
            </div>
          </div>

          <div className="space-y-5">
            {variables.slice(0, 8).map((v: any) => (
              <VariableControl
                key={v.name}
                name={v.name}
                displayName={v.display_name || v.name}
                controlType={v.control_type || 'slider'}
                value={values[v.name] ?? v.current_value}
                onChange={(val) => handleVariableChange(v.name, val)}
                minValue={v.min_value}
                maxValue={v.max_value}
                step={v.step}
                unit={v.unit}
                options={v.options}
                description={v.description}
              />
            ))}
          </div>
        </div>

        {/* Target Metric Forecast Chart */}
        <div
          className="lg:col-span-5 rounded-2xl border p-5"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold" style={{ color: textPrimary }}>
              Target Metric Forecast ({targetName})
            </h3>
            <div className="flex items-center gap-2">
              <select
                className="text-[10px] px-2 py-1 rounded-lg border outline-none cursor-pointer"
                style={{
                  background: isDark ? 'rgba(255,255,255,0.03)' : '#f8fafc',
                  borderColor: cardBorder,
                  color: textMuted,
                }}
                defaultValue="12"
              >
                <option value="3">3 Months</option>
                <option value="6">6 Months</option>
                <option value="12">12 Months</option>
              </select>
              <button className="p-1 rounded-lg hover:bg-white/5"><Download className="w-3.5 h-3.5" style={{ color: textMuted }} /></button>
              <button className="p-1 rounded-lg hover:bg-white/5"><Maximize2 className="w-3.5 h-3.5" style={{ color: textMuted }} /></button>
            </div>
          </div>

          {simResult?.chart_data ? (
            <SimulatorChart
              data={simResult.chart_data}
              height={280}
              lines={[
                { dataKey: 'simulated', color: '#6366f1', name: 'Simulated', type: 'monotone' },
                { dataKey: 'baseline', color: isDark ? '#475569' : '#94a3b8', name: 'Baseline', strokeDasharray: '6 3' },
                { dataKey: 'confidence_upper', color: '#818cf8', name: 'Confidence Range', strokeDasharray: '2 2', dot: false },
                { dataKey: 'confidence_lower', color: '#818cf8', name: '', strokeDasharray: '2 2', dot: false },
              ]}
            />
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-sm" style={{ color: textMuted }}>Run a simulation to see forecast</p>
            </div>
          )}

          {/* Forecast Summary Row */}
          {simResult && (
            <div className="grid grid-cols-4 gap-3 mt-4 pt-3 border-t" style={{ borderColor: cardBorder }}>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Expected Target</p>
                <p className="text-xs font-bold" style={{ color: textPrimary }}>
                  {simResult.formatted_prediction}
                </p>
              </div>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Baseline Target</p>
                <p className="text-xs font-bold" style={{ color: textPrimary }}>
                  {simResult.formatted_baseline}
                </p>
              </div>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Best Case</p>
                <p className="text-xs font-bold text-emerald-500">
                  {simResult.chart_data?.[simResult.chart_data.length - 1]?.best_case?.toLocaleString() || simResult.formatted_prediction}
                </p>
              </div>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Worst Case</p>
                <p className="text-xs font-bold text-red-500">
                  {simResult.chart_data?.[simResult.chart_data.length - 1]?.worst_case?.toLocaleString() || simResult.formatted_baseline}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* AI Business Insights */}
        <div
          className="lg:col-span-4 rounded-2xl border p-5 space-y-4"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
              <Sparkles className="w-4 h-4 text-indigo-400" /> AI Business Insights
            </h3>
            <button onClick={() => handleSimulate()} className="p-1 rounded-lg hover:bg-white/5"><RefreshCcw className="w-3.5 h-3.5" style={{ color: textMuted }} /></button>
          </div>

          {/* Key Insight */}
          {simResult?.insights?.summary && (
            <div
              className="rounded-xl p-4 border-l-4"
              style={{
                background: isDark ? 'rgba(99,102,241,0.06)' : 'rgba(99,102,241,0.04)',
                borderLeftColor: '#6366f1',
              }}
            >
              <p className="text-[10px] font-bold text-indigo-400 mb-1">💡 Key Insight</p>
              <p className="text-xs leading-relaxed" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>
                {simResult.insights.summary}
              </p>
            </div>
          )}

          {/* Positive Drivers */}
          <div>
            <p className="text-[10px] font-bold mb-2" style={{ color: textPrimary }}>Top Positive Drivers</p>
            {(simResult?.insights?.positive_drivers || []).length > 0 ? (
              (simResult.insights.positive_drivers).slice(0, 4).map((d: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                    <span className="text-xs truncate" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>{d.feature}</span>
                  </div>
                  <span className="text-xs font-bold text-emerald-500 flex-shrink-0 ml-2">+{Math.abs(d.impact).toFixed(1)}%</span>
                </div>
              ))
            ) : (
              <p className="text-xs py-1 text-slate-400">Adjust variable sliders to test positive drivers</p>
            )}
          </div>

          {/* Negative Drivers */}
          <div>
            <p className="text-[10px] font-bold mb-2" style={{ color: textPrimary }}>Top Negative Drivers</p>
            {(simResult?.insights?.negative_drivers || []).length > 0 ? (
              (simResult.insights.negative_drivers).slice(0, 4).map((d: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                    <span className="text-xs truncate" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>{d.feature}</span>
                  </div>
                  <span className="text-xs font-bold text-red-500 flex-shrink-0 ml-2">{d.impact.toFixed(1)}%</span>
                </div>
              ))
            ) : (
              <p className="text-xs py-1 text-slate-400">Adjust variable sliders to test negative drivers</p>
            )}
          </div>

          <button
            onClick={() => onTabChange?.('ai-insights')}
            className="w-full text-xs font-semibold text-indigo-500 hover:text-indigo-400 flex items-center justify-center gap-1 pt-2"
          >
            View Full Analysis <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* AI Suggested Scenarios + Variable Importance */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* AI Suggested Scenarios */}
        <div className="lg:col-span-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
              <Brain className="w-4 h-4 text-indigo-400" /> AI Suggested Scenarios
            </h3>
            <button onClick={() => onTabChange?.('ai-suggested')} className="text-xs text-indigo-500 hover:text-indigo-400 flex items-center gap-1">
              View Full Scenarios <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {suggestedScenarios.slice(0, 4).map((s: any) => (
              <ScenarioCard
                key={s.id}
                id={s.id}
                name={s.name}
                title={s.title}
                goal={s.goal}
                tags={s.tags}
                badge={s.badge}
                badgeColor={s.badge_color}
                metrics={s.metrics}
                confidence={s.confidence}
                estimatedRoi={s.estimated_roi}
                runtimeMs={s.runtime_ms}
                onRun={() => {}}
              />
            ))}
          </div>
        </div>

        {/* Variable Importance */}
        <div
          className="lg:col-span-4 rounded-2xl border p-5"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold" style={{ color: textPrimary }}>Variable Importance</h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)', color: textMuted }}>
              SHAP Method
            </span>
          </div>
          <div className="space-y-3">
            {(importance?.features || []).slice(0, 7).map((f: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[11px] w-32 truncate" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>{f.feature}</span>
                <div className="flex-1 h-2 rounded-full relative" style={{ background: isDark ? '#1e293b' : '#e2e8f0' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, Math.abs(f.importance) * 200)}%` }}
                    transition={{ duration: 0.8, delay: i * 0.1 }}
                    className="h-full rounded-full"
                    style={{
                      background: f.direction === 'positive'
                        ? 'linear-gradient(90deg, #6366f1, #818cf8)'
                        : 'linear-gradient(90deg, #ef4444, #f87171)',
                    }}
                  />
                </div>
                <span className="text-[10px] font-bold w-10 text-right" style={{ color: '#6366f1' }}>
                  {Math.abs(f.importance).toFixed(3)}
                </span>
              </div>
            ))}
          </div>
          <button
            onClick={() => onTabChange?.('importance')}
            className="w-full text-xs font-semibold text-indigo-500 hover:text-indigo-400 flex items-center justify-center gap-1 mt-4 pt-3 border-t"
            style={{ borderColor: cardBorder }}
          >
            View Detailed Explanation <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Bottom Row: Recent Simulations | Simulation Summary | Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Recent Simulations */}
        <div
          className="lg:col-span-5 rounded-2xl border p-5"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <h3 className="text-sm font-bold mb-4" style={{ color: textPrimary }}>Recent Simulations</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b" style={{ borderColor: cardBorder }}>
                  {['Scenario Name', 'Created By', 'Target Metric', 'Change', 'Status'].map((h) => (
                    <th key={h} className="text-[10px] font-semibold text-left pb-2 px-2" style={{ color: textMuted }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(overview?.recent_simulations || []).slice(0, 4).map((sim: any, i: number) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-white/[0.02]" style={{ borderColor: cardBorder }}>
                    <td className="py-2.5 px-2 text-xs font-medium" style={{ color: textPrimary }}>{sim.name}</td>
                    <td className="py-2.5 px-2 text-xs" style={{ color: textMuted }}>{sim.created_by || 'You'}</td>
                    <td className="py-2.5 px-2 text-xs font-medium" style={{ color: textPrimary }}>
                      {sim.prediction ? sim.prediction.toLocaleString() : (sim.target_metric || 'N/A')}
                    </td>
                    <td className="py-2.5 px-2">
                      <span className={`text-xs font-bold ${(sim.impact || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                        {(sim.impact || 0) >= 0 ? '↑' : '↓'} {Math.abs(sim.impact || 0).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-2">
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                        {sim.status || 'Completed'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Simulation Summary Donut */}
        <div
          className="lg:col-span-3 rounded-2xl border p-5 flex flex-col items-center justify-center"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <h3 className="text-sm font-bold mb-2 self-start" style={{ color: textPrimary }}>Simulation Summary</h3>
          <div className="relative w-40 h-40">
            <ResponsiveContainer width="100%" height="100%">
              <RPieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </RPieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-xl font-bold" style={{ color: textPrimary }}>{summaryData.total.toLocaleString()}</span>
              <span className="text-[10px]" style={{ color: textMuted }}>Total Simulations</span>
            </div>
          </div>
          <div className="flex flex-col gap-1.5 w-full mt-3">
            {pieData.map((d, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                  <span style={{ color: textMuted }}>{d.name}</span>
                </div>
                <span className="font-semibold" style={{ color: textPrimary }}>{d.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div
          className="lg:col-span-4 rounded-2xl border p-5"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <h3 className="text-sm font-bold mb-4" style={{ color: textPrimary }}>Quick Actions</h3>
          <div className="grid grid-cols-3 gap-3">
            {[
              { icon: <Sliders className="w-4 h-4" />, label: 'Scenario Sandbox', action: 'builder', color: '#6366f1' },
              { icon: <TrendingUp className="w-4 h-4" />, label: 'Forecast Timeline', action: 'forecast', color: '#10b981' },
              { icon: <Sparkles className="w-4 h-4" />, label: 'AI Insights', action: 'ai-insights', color: '#f59e0b' },
              { icon: <Brain className="w-4 h-4" />, label: 'AI Scenarios', action: 'ai-suggested', color: '#ef4444' },
              { icon: <Zap className="w-4 h-4" />, label: 'Optimize Goals', action: 'optimization', color: '#8b5cf6' },
              { icon: <FileText className="w-4 h-4" />, label: 'Generate Report', action: 'reports', color: '#ec4899' },
            ].map((act, i) => (
              <button
                key={i}
                onClick={() => onTabChange?.(act.action)}
                className="flex flex-col items-center gap-2 p-3 rounded-xl border transition-all hover:scale-[1.03] active:scale-[0.98]"
                style={{
                  borderColor: cardBorder,
                  background: isDark ? 'rgba(255,255,255,0.02)' : '#fafafa',
                }}
              >
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{ background: `${act.color}12`, color: act.color }}
                >
                  {act.icon}
                </div>
                <span className="text-[10px] font-medium text-center" style={{ color: textMuted }}>{act.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewTab;
