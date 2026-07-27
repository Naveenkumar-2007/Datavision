import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import SimulatorChart from './SimulatorChart';
import { BarChart2, Search, ArrowUpDown, Filter } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';

const VariableImportanceTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'importance' | 'correlation'>('importance');
  const [selectedFeature, setSelectedFeature] = useState<string>('');
  const [pdData, setPdData] = useState<any>(null);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiService.getFeatureImportance();
        setData(res.data);
        if (res.data?.features?.length > 0) {
          setSelectedFeature(res.data.features[0].feature);
        }
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetch();
  }, []);

  useEffect(() => {
    if (!selectedFeature) return;
    const fetchPD = async () => {
      try {
        const res = await apiService.getPartialDependence(selectedFeature);
        setPdData(res.data);
      } catch {}
    };
    fetchPD();
  }, [selectedFeature]);

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>;

  const features = (data?.features || [])
    .filter((f: any) => f.feature.toLowerCase().includes(search.toLowerCase()))
    .sort((a: any, b: any) => sortBy === 'importance' ? Math.abs(b.importance) - Math.abs(a.importance) : Math.abs(b.correlation) - Math.abs(a.correlation));

  // Horizontal bar chart data
  const barData = features.slice(0, 10).map((f: any) => ({
    feature: f.feature,
    value: Math.abs(f.shap_value),
    direction: f.direction,
  }));

  return (
    <div className="space-y-5">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1 relative min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: textMuted }} />
          <input
            type="text"
            placeholder="Search features..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl text-xs border outline-none focus:ring-2 focus:ring-indigo-500/30"
            style={{ background: cardBg, borderColor: cardBorder, color: textPrimary }}
          />
        </div>
        <button
          onClick={() => setSortBy(sortBy === 'importance' ? 'correlation' : 'importance')}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-medium hover:bg-white/5"
          style={{ borderColor: cardBorder, color: textMuted }}
        >
          <ArrowUpDown className="w-3.5 h-3.5" /> Sort: {sortBy === 'importance' ? 'Importance' : 'Correlation'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* SHAP Bar Chart */}
        <div className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
          <h3 className="text-sm font-bold mb-4 flex items-center gap-2" style={{ color: textPrimary }}>
            <BarChart2 className="w-4 h-4 text-indigo-400" /> Feature Importance (SHAP Values)
          </h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={barData} layout="vertical" margin={{ left: 80, right: 20, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'} horizontal={false} />
              <XAxis type="number" tick={{ fill: textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="feature" tick={{ fill: isDark ? '#cbd5e1' : '#475569', fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
              <Tooltip
                contentStyle={{ background: isDark ? '#1e1e2e' : '#fff', border: `1px solid ${cardBorder}`, borderRadius: 12, fontSize: 12 }}
                labelStyle={{ color: textPrimary, fontWeight: 600 }}
              />
              <Bar dataKey="value" radius={[0, 6, 6, 0]} cursor="pointer" onClick={(d: any) => setSelectedFeature(d.feature)}>
                {barData.map((entry: any, i: number) => (
                  <Cell key={i} fill={entry.direction === 'positive' ? '#6366f1' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Feature Table */}
        <div className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: textPrimary }}>Feature Ranking</h3>
          <div className="space-y-2 max-h-[360px] overflow-y-auto">
            {features.map((f: any, i: number) => (
              <motion.div
                key={f.feature}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => setSelectedFeature(f.feature)}
                className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                  selectedFeature === f.feature ? 'ring-1 ring-indigo-500/30' : ''
                }`}
                style={{
                  background: selectedFeature === f.feature
                    ? (isDark ? 'rgba(99,102,241,0.06)' : 'rgba(99,102,241,0.04)')
                    : 'transparent',
                }}
              >
                <span className="text-xs font-bold w-6 text-center" style={{ color: textMuted }}>#{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate" style={{ color: textPrimary }}>{f.feature}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-20">
                    <div className="h-1.5 rounded-full" style={{ background: isDark ? '#1e293b' : '#e2e8f0' }}>
                      <div className="h-full rounded-full" style={{
                        width: `${Math.min(100, f.importance * 250)}%`,
                        background: f.direction === 'positive' ? '#6366f1' : '#ef4444',
                      }} />
                    </div>
                  </div>
                  <span className="text-[10px] font-bold w-10 text-right" style={{ color: '#6366f1' }}>{f.importance.toFixed(3)}</span>
                  <span className={`text-[10px] font-bold w-10 text-right ${f.correlation >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {f.correlation >= 0 ? '+' : ''}{f.correlation.toFixed(2)}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Partial Dependence Plot */}
      {pdData?.points && (
        <div className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: textPrimary }}>
            Partial Dependence: {selectedFeature}
          </h3>
          <SimulatorChart
            data={pdData.points}
            height={250}
            xDataKey="x"
            lines={[{ dataKey: 'y', color: '#6366f1', name: 'Impact', type: 'monotone' }]}
          />
        </div>
      )}
    </div>
  );
};

export default VariableImportanceTab;
