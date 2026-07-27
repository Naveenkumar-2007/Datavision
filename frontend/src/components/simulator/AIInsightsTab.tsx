import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import {
  Sparkles, TrendingUp, TrendingDown, AlertTriangle, Target,
  Lightbulb, Shield, ArrowRight, RefreshCcw, Zap
} from 'lucide-react';

const AIInsightsTab: React.FC = () => {
  const { isDark } = useUserStore();
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [variables, setVariables] = useState<Record<string, any>>({});

  const cardBg = isDark ? 'rgba(255,255,255,0.03)' : '#ffffff';
  const cardBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textMuted = isDark ? '#94a3b8' : '#64748b';

  useEffect(() => {
    const fetch = async () => {
      try {
        const varRes = await apiService.getSimulatorVariables();
        if (varRes.data) {
          const init: Record<string, any> = {};
          varRes.data.forEach((v: any) => { init[v.name] = v.current_value; });
          setVariables(init);
          const res = await apiService.getSimulatorInsights(init);
          setInsights(res.data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await apiService.getSimulatorInsights(variables);
      setInsights(res.data);
    } catch {} finally { setLoading(false); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>;
  }

  const riskColor = insights?.risk_level === 'Low' ? '#22c55e' : insights?.risk_level === 'Medium' ? '#f59e0b' : '#ef4444';

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: textPrimary }}>
          <Sparkles className="w-4 h-4 text-indigo-400" /> AI-Powered Business Insights
        </h3>
        <button onClick={handleRefresh} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs hover:bg-white/5" style={{ borderColor: cardBorder, color: textMuted }}>
          <RefreshCcw className="w-3.5 h-3.5" /> Regenerate
        </button>
      </div>

      {/* Business Summary */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border p-6 border-l-4" style={{ background: cardBg, borderColor: cardBorder, borderLeftColor: '#6366f1' }}>
        <h4 className="text-sm font-bold mb-2 flex items-center gap-2" style={{ color: textPrimary }}>
          <Lightbulb className="w-4 h-4 text-amber-400" /> Business Summary
        </h4>
        <p className="text-sm leading-relaxed" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>
          {insights?.summary || 'No insights available. Run a simulation to generate AI insights.'}
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Positive Drivers */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
          <h4 className="text-sm font-bold mb-4 flex items-center gap-2" style={{ color: textPrimary }}>
            <TrendingUp className="w-4 h-4 text-emerald-500" /> Positive Drivers
          </h4>
          <div className="space-y-3">
            {(insights?.positive_drivers || []).map((d: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl" style={{ background: isDark ? 'rgba(34,197,94,0.05)' : 'rgba(34,197,94,0.04)' }}>
                <span className="text-xs font-medium" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>{d.feature}</span>
                <span className="text-xs font-bold text-emerald-500">+{Math.abs(d.impact).toFixed(1)}%</span>
              </div>
            ))}
            {(!insights?.positive_drivers || insights.positive_drivers.length === 0) && (
              <p className="text-xs text-center py-4" style={{ color: textMuted }}>No positive drivers detected</p>
            )}
          </div>
        </motion.div>

        {/* Negative Drivers */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
          <h4 className="text-sm font-bold mb-4 flex items-center gap-2" style={{ color: textPrimary }}>
            <TrendingDown className="w-4 h-4 text-red-500" /> Negative Drivers
          </h4>
          <div className="space-y-3">
            {(insights?.negative_drivers || []).map((d: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl" style={{ background: isDark ? 'rgba(239,68,68,0.05)' : 'rgba(239,68,68,0.04)' }}>
                <span className="text-xs font-medium" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>{d.feature}</span>
                <span className="text-xs font-bold text-red-500">{d.impact.toFixed(1)}%</span>
              </div>
            ))}
            {(!insights?.negative_drivers || insights.negative_drivers.length === 0) && (
              <p className="text-xs text-center py-4" style={{ color: textMuted }}>No negative drivers detected</p>
            )}
          </div>
        </motion.div>

        {/* Risk & Opportunity */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="rounded-2xl border p-5 space-y-4" style={{ background: cardBg, borderColor: cardBorder }}>
          {/* Risk */}
          <div>
            <h4 className="text-sm font-bold mb-3 flex items-center gap-2" style={{ color: textPrimary }}>
              <Shield className="w-4 h-4" style={{ color: riskColor }} /> Risk Assessment
            </h4>
            <div className="flex items-center gap-3">
              <div className="w-16 h-16 rounded-full border-4 flex items-center justify-center" style={{ borderColor: riskColor }}>
                <span className="text-lg font-bold" style={{ color: riskColor }}>{insights?.risk_score || 0}</span>
              </div>
              <div>
                <p className="text-sm font-bold" style={{ color: riskColor }}>{insights?.risk_level || 'Unknown'} Risk</p>
                <p className="text-[10px]" style={{ color: textMuted }}>Based on variable sensitivity</p>
              </div>
            </div>
          </div>

          {/* Opportunity */}
          <div>
            <h4 className="text-sm font-bold mb-2 flex items-center gap-2" style={{ color: textPrimary }}>
              <Target className="w-4 h-4 text-indigo-500" /> Opportunity Score
            </h4>
            <div className="w-full h-3 rounded-full relative" style={{ background: isDark ? '#1e293b' : '#e2e8f0' }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${insights?.opportunity_score || 0}%` }}
                transition={{ duration: 1 }}
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg, #6366f1, #a855f7)' }}
              />
            </div>
            <p className="text-xs font-bold mt-1" style={{ color: '#6366f1' }}>{(insights?.opportunity_score || 0).toFixed(0)}%</p>
          </div>
        </motion.div>
      </div>

      {/* Recommendations */}
      <div className="rounded-2xl border p-5" style={{ background: cardBg, borderColor: cardBorder }}>
        <h4 className="text-sm font-bold mb-4 flex items-center gap-2" style={{ color: textPrimary }}>
          <Zap className="w-4 h-4 text-amber-400" /> Recommendations
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(insights?.recommendations || []).map((rec: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="p-4 rounded-xl border flex gap-3"
              style={{ borderColor: cardBorder }}
            >
              <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center ${
                rec.priority === 'high' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'
              }`}>
                {rec.type === 'opportunity' ? <TrendingUp className="w-4 h-4" /> :
                 rec.type === 'risk' ? <AlertTriangle className="w-4 h-4" /> :
                 <ArrowRight className="w-4 h-4" />}
              </div>
              <div>
                <p className="text-xs font-bold mb-1" style={{ color: textPrimary }}>{rec.title}</p>
                <p className="text-[11px] leading-relaxed" style={{ color: textMuted }}>{rec.description}</p>
                <span className={`text-[9px] font-bold uppercase mt-2 inline-block px-1.5 py-0.5 rounded ${
                  rec.priority === 'high' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'
                }`}>
                  {rec.priority} priority
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AIInsightsTab;
