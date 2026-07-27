import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import SimulatorChart from './SimulatorChart';
import { Download, Maximize2, Calendar } from 'lucide-react';

const ForecastTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [periods, setPeriods] = useState(12);
  const [interval, setInterval] = useState('monthly');
  const [variables, setVariables] = useState<Record<string, any>>({});
  const [modelInfo, setModelInfo] = useState<any>(null);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  useEffect(() => {
    const fetchVars = async () => {
      try {
        const [varRes, ovRes] = await Promise.all([
          apiService.getSimulatorVariables(),
          apiService.getSimulatorOverview(),
        ]);
        if (ovRes.data?.model_info) setModelInfo(ovRes.data.model_info);
        if (varRes.data) {
          const init: Record<string, any> = {};
          varRes.data.forEach((v: any) => { init[v.name] = v.current_value; });
          setVariables(init);
        }
      } catch {}
    };
    fetchVars();
  }, []);

  useEffect(() => {
    if (Object.keys(variables).length === 0) return;
    const fetchForecast = async () => {
      setLoading(true);
      try {
        const res = await apiService.getSimulatorForecast(variables, periods, interval);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchForecast();
  }, [variables, periods, interval]);

  const targetUnit = modelInfo?.target_unit || '';
  const targetName = modelInfo?.target_name || modelInfo?.target_column?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) || 'Target';

  const formatValue = (val: any) => {
    if (typeof val !== 'number' || isNaN(val)) return '0';
    if (targetUnit === '%') return `${val.toFixed(1)}%`;
    if (targetUnit === '₹') {
      if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
      if (val >= 100000) return `₹${(val / 100000).toFixed(1)} L`;
      return `₹${val.toLocaleString()}`;
    }
    return val >= 1000000 ? `${(val / 1000000).toFixed(1)}M` : val.toLocaleString();
  };

  return (
    <div className="space-y-5">
      {/* Controls bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" style={{ color: textMuted }} />
          {['3', '6', '12', '24'].map(p => (
            <button
              key={p}
              onClick={() => setPeriods(Number(p))}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                periods === Number(p) ? 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/30' : 'border'
              }`}
              style={periods !== Number(p) ? { borderColor: cardBorder, color: textMuted } : undefined}
            >
              {p}M
            </button>
          ))}
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs border cursor-pointer outline-none"
            style={{ background: cardBg, borderColor: cardBorder, color: textMuted }}
          >
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 rounded-xl border hover:bg-white/5" style={{ borderColor: cardBorder }}>
            <Download className="w-4 h-4" style={{ color: textMuted }} />
          </button>
          <button className="p-2 rounded-xl border hover:bg-white/5" style={{ borderColor: cardBorder }}>
            <Maximize2 className="w-4 h-4" style={{ color: textMuted }} />
          </button>
        </div>
      </div>

      {/* Main Chart */}
      <div className="rounded-2xl border p-6" style={{ background: cardBg, borderColor: cardBorder }}>
        <h3 className="text-sm font-bold mb-4" style={{ color: textPrimary }}>
          Prediction Timeline ({targetName})
        </h3>
        {loading ? (
          <div className="flex items-center justify-center h-80">
            <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : data?.chart_data ? (
          <SimulatorChart
            data={data.chart_data}
            height={380}
            lines={[
              { dataKey: 'simulated', color: '#6366f1', name: 'Scenario', type: 'monotone' },
              { dataKey: 'baseline', color: isDark ? '#475569' : '#94a3b8', name: 'Baseline', strokeDasharray: '6 3' },
              { dataKey: 'confidence_upper', color: '#a5b4fc', name: 'Confidence Upper', strokeDasharray: '2 2', dot: false },
              { dataKey: 'confidence_lower', color: '#a5b4fc', name: 'Confidence Lower', strokeDasharray: '2 2', dot: false },
              { dataKey: 'best_case', color: '#22c55e', name: 'Best Case', strokeDasharray: '4 4', dot: false },
              { dataKey: 'worst_case', color: '#ef4444', name: 'Worst Case', strokeDasharray: '4 4', dot: false },
            ]}
            formatY={(v) => formatValue(v)}
          />
        ) : (
          <div className="flex items-center justify-center h-80">
            <p className="text-sm" style={{ color: textMuted }}>No forecast data available</p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      {data?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: `Expected ${targetName}`, value: data.summary.expected, color: '#6366f1' },
            { label: '95% Range', value: data.summary.confidence_range, color: '#818cf8' },
            { label: 'Best Case', value: data.summary.best_case, color: '#22c55e' },
            { label: 'Worst Case', value: data.summary.worst_case, color: '#ef4444' },
            { label: 'Baseline', value: data.summary.baseline, color: isDark ? '#475569' : '#94a3b8' },
          ].map((item, i) => (
            <div key={i} className="rounded-xl border p-4" style={{ background: cardBg, borderColor: cardBorder }}>
              <p className="text-[10px] mb-1" style={{ color: textMuted }}>{item.label}</p>
              <p className="text-sm font-bold" style={{ color: item.color }}>{item.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ForecastTab;
