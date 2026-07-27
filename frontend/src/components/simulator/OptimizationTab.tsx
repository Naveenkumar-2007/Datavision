import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import { Sliders, CheckCircle2, Zap, Target } from 'lucide-react';

const OptimizationTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [objective, setObjective] = useState('maximize_prediction');
  const [objectiveType, setObjectiveType] = useState('maximize');
  const [maxIterations, setMaxIterations] = useState(100);
  const [optimizing, setOptimizing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await apiService.runOptimization({
        objective,
        objective_type: objectiveType,
        max_iterations: maxIterations,
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setOptimizing(false);
    }
  };

  const targetName = result?.target_name || 'Target Metric';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      {/* Left Config */}
      <div className="lg:col-span-5 space-y-4">
        <div className="rounded-2xl border p-5 space-y-4" style={{ background: cardBg, borderColor: cardBorder }}>
          <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
            <Sliders className="w-4 h-4 text-indigo-400" /> Optimization Engine Configuration
          </h3>

          <div>
            <label className="text-xs font-semibold mb-1.5 block" style={{ color: textMuted }}>Optimization Goal</label>
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full px-3 py-2 rounded-xl text-xs border outline-none cursor-pointer"
              style={{ background: cardBg, borderColor: cardBorder, color: textPrimary }}
            >
              <option value="maximize_prediction">Maximize Target Value</option>
              <option value="minimize_prediction">Minimize Target Value</option>
              <option value="optimize_roi">Maximize Efficiency (ROI)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold mb-1.5 block" style={{ color: textMuted }}>Objective Direction</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setObjectiveType('maximize')}
                className={`py-2 rounded-xl text-xs font-semibold transition-all border ${
                  objectiveType === 'maximize' ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/30' : ''
                }`}
                style={objectiveType !== 'maximize' ? { borderColor: cardBorder, color: textMuted } : undefined}
              >
                Maximize ↑
              </button>
              <button
                onClick={() => setObjectiveType('minimize')}
                className={`py-2 rounded-xl text-xs font-semibold transition-all border ${
                  objectiveType === 'minimize' ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/30' : ''
                }`}
                style={objectiveType !== 'minimize' ? { borderColor: cardBorder, color: textMuted } : undefined}
              >
                Minimize ↓
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold mb-1.5 block" style={{ color: textMuted }}>Iterations: {maxIterations}</label>
            <input
              type="range"
              min={10}
              max={500}
              step={10}
              value={maxIterations}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>

          <button
            onClick={handleOptimize}
            disabled={optimizing}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition-all"
          >
            {optimizing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Optimizing Variables...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" /> Run AI Optimization
              </>
            )}
          </button>
        </div>
      </div>

      {/* Right Results */}
      <div className="lg:col-span-7">
        {result ? (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border p-6 space-y-5" style={{ background: cardBg, borderColor: cardBorder }}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Optimal Solution ({targetName})
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                {result.improvement_pct >= 0 ? '+' : ''}{result.improvement_pct?.toFixed(1)}% Improvement
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4 p-4 rounded-xl" style={{ background: isDark ? 'rgba(99,102,241,0.05)' : 'rgba(99,102,241,0.03)' }}>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Optimal Target</p>
                <p className="text-lg font-bold text-indigo-500">
                  {result.formatted_best_prediction || result.best_prediction?.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Baseline Target</p>
                <p className="text-lg font-bold" style={{ color: textMuted }}>
                  {result.formatted_baseline_prediction || result.baseline_prediction?.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-[10px]" style={{ color: textMuted }}>Iterations Evaluated</p>
                <p className="text-lg font-bold" style={{ color: textPrimary }}>{result.iterations}</p>
              </div>
            </div>

            {/* Optimal Variable Values */}
            <div>
              <h4 className="text-xs font-bold mb-3" style={{ color: textPrimary }}>Optimal Variable Inputs</h4>
              <div className="space-y-2">
                {Object.entries(result.best_values || {}).map(([key, val]: [string, any]) => (
                  <div key={key} className="flex items-center justify-between p-3 rounded-xl border" style={{ borderColor: cardBorder }}>
                    <span className="text-xs font-medium" style={{ color: textPrimary }}>{key}</span>
                    <span className="text-xs font-bold text-indigo-500">{typeof val === 'number' ? val.toLocaleString() : String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="rounded-2xl border p-12 flex flex-col items-center justify-center gap-3 h-full" style={{ background: cardBg, borderColor: cardBorder }}>
            <Target className="w-10 h-10" style={{ color: textMuted }} />
            <p className="text-sm font-semibold" style={{ color: textPrimary }}>Run Optimization</p>
            <p className="text-xs text-center max-w-xs" style={{ color: textMuted }}>
              Select an objective goal and click Run AI Optimization to discover the highest-performing variable combinations for your dataset.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OptimizationTab;
