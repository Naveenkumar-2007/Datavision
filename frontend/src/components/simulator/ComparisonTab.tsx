import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import SimulatorChart from './SimulatorChart';
import { GitCompare, Download, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const ComparisonTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const savedRes = await apiService.listScenarios();
        const saved = savedRes.data || [];
        setScenarios(saved);

        const compRes = await apiService.compareScenarios(
          saved.length > 0 ? saved.map((s: any) => s.id) : []
        );
        setComparison(compRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>;

  const comps = comparison?.comparisons || [];
  const chartData = comps.map((c: any) => ({
    name: c.name,
    prediction: c.prediction || 0,
    impact: c.impact || c.impact_percentage || 0,
    confidence: c.confidence || 90,
  }));

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
          <GitCompare className="w-4 h-4 text-indigo-400" /> Scenario Comparison & Trade-off Analysis
        </h3>
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs hover:bg-white/5" style={{ borderColor: cardBorder, color: textMuted }}>
          <Download className="w-3.5 h-3.5" /> Export Comparison
        </button>
      </div>

      {/* Comparison Table */}
      <div className="rounded-2xl border p-5 overflow-x-auto" style={{ background: cardBg, borderColor: cardBorder }}>
        <table className="w-full text-left">
          <thead>
            <tr className="border-b" style={{ borderColor: cardBorder }}>
              <th className="py-2.5 px-3 text-xs font-semibold" style={{ color: textMuted }}>Metric / Scenario</th>
              {comps.map((c: any, i: number) => (
                <th key={i} className="py-2.5 px-3 text-xs font-bold" style={{ color: textPrimary }}>
                  {c.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b" style={{ borderColor: cardBorder }}>
              <td className="py-3 px-3 text-xs font-semibold" style={{ color: textMuted }}>Target Prediction</td>
              {comps.map((c: any, i: number) => (
                <td key={i} className="py-3 px-3 text-sm font-bold" style={{ color: '#6366f1' }}>
                  {c.formatted_prediction || c.prediction?.toLocaleString()}
                </td>
              ))}
            </tr>
            <tr className="border-b" style={{ borderColor: cardBorder }}>
              <td className="py-3 px-3 text-xs font-semibold" style={{ color: textMuted }}>Impact vs Baseline</td>
              {comps.map((c: any, i: number) => {
                const imp = c.impact || c.impact_percentage || 0;
                return (
                  <td key={i} className="py-3 px-3">
                    <span className={`text-xs font-bold flex items-center gap-1 ${imp >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                      {imp >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                      {imp >= 0 ? '+' : ''}{imp.toFixed(1)}%
                    </span>
                  </td>
                );
              })}
            </tr>
            <tr className="border-b" style={{ borderColor: cardBorder }}>
              <td className="py-3 px-3 text-xs font-semibold" style={{ color: textMuted }}>AI Confidence Score</td>
              {comps.map((c: any, i: number) => (
                <td key={i} className="py-3 px-3 text-xs font-bold text-emerald-500">
                  {(c.confidence || 90).toFixed(1)}%
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Grouped Comparison Chart */}
      <div className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
        <h3 className="text-sm font-bold mb-4" style={{ color: textPrimary }}>Target Metric Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'} vertical={false} />
            <XAxis dataKey="name" tick={{ fill: textMuted, fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: textMuted, fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: isDark ? '#1e1e2e' : '#fff', border: `1px solid ${cardBorder}`, borderRadius: 12 }} />
            <Bar dataKey="prediction" name="Target Prediction" fill="#6366f1" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ComparisonTab;
