import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import { History, Search, RefreshCcw, RotateCcw, ArrowRight } from 'lucide-react';

const HistoryTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [simulations, setSimulations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await apiService.getSimulationHistory(page, 20, search);
      setSimulations(res.data?.simulations || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, search]);

  return (
    <div className="space-y-5">
      {/* Search & Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex-1 relative min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: textMuted }} />
          <input
            type="text"
            placeholder="Search simulation history..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl text-xs border outline-none focus:ring-2 focus:ring-indigo-500/30"
            style={{ background: cardBg, borderColor: cardBorder, color: textPrimary }}
          />
        </div>
        <button onClick={fetchHistory} className="flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-medium hover:bg-white/5" style={{ borderColor: cardBorder, color: textMuted }}>
          <RefreshCcw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* History Table */}
      <div className="rounded-2xl border p-5 overflow-x-auto" style={{ background: cardBg, borderColor: cardBorder }}>
        <table className="w-full text-left">
          <thead>
            <tr className="border-b" style={{ borderColor: cardBorder }}>
              {['Simulation Name', 'Model', 'Target Metric', 'Impact', 'Confidence', 'Status', 'Date', 'Action'].map((h) => (
                <th key={h} className="py-2.5 px-3 text-xs font-semibold" style={{ color: textMuted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {simulations.map((sim: any, i: number) => (
              <tr key={i} className="border-b last:border-0 hover:bg-white/[0.02]" style={{ borderColor: cardBorder }}>
                <td className="py-3 px-3 text-xs font-semibold" style={{ color: textPrimary }}>{sim.name}</td>
                <td className="py-3 px-3 text-xs" style={{ color: textMuted }}>{sim.model_name || 'AutoML'}</td>
                <td className="py-3 px-3 text-xs font-bold" style={{ color: textPrimary }}>
                  {typeof sim.prediction === 'number' ? sim.prediction.toLocaleString(undefined, { maximumFractionDigits: 2 }) : 'N/A'}
                </td>
                <td className="py-3 px-3">
                  <span className={`text-xs font-bold ${(sim.impact_percentage || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {(sim.impact_percentage || 0) >= 0 ? '+' : ''}{(sim.impact_percentage || 0).toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-3 text-xs font-bold text-indigo-500">
                  {(sim.confidence || 90).toFixed(1)}%
                </td>
                <td className="py-3 px-3">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                    {sim.status || 'Completed'}
                  </span>
                </td>
                <td className="py-3 px-3 text-xs" style={{ color: textMuted }}>
                  {sim.created_at ? new Date(sim.created_at).toLocaleDateString() : 'Just now'}
                </td>
                <td className="py-3 px-3">
                  <button className="flex items-center gap-1 text-xs font-semibold text-indigo-500 hover:text-indigo-400">
                    <RotateCcw className="w-3 h-3" /> Restore
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {simulations.length === 0 && !loading && (
          <div className="text-center py-12">
            <History className="w-10 h-10 mx-auto mb-2 opacity-40" style={{ color: textMuted }} />
            <p className="text-xs" style={{ color: textMuted }}>No past simulation records found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryTab;
