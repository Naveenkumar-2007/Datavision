import React from 'react';
import { motion } from 'framer-motion';
import { Play, GitCompare, Bookmark, Copy, Trash2 } from 'lucide-react';
import { useUserStore } from '@/store/userStore';

interface ScenarioCardProps {
  id: string;
  name: string;
  title: string;
  goal: string;
  tags?: string[];
  badge?: string | null;
  badgeColor?: string;
  metrics?: {
    revenue_change?: number;
    profit_change?: number;
    risk?: string;
  };
  confidence?: number;
  estimatedRoi?: string;
  runtimeMs?: number;
  onRun?: (id: string) => void;
  onCompare?: (id: string) => void;
  onSave?: (id: string) => void;
  onClone?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const ScenarioCard: React.FC<ScenarioCardProps> = ({
  id, name, title, goal, tags = [], badge, badgeColor = 'emerald',
  metrics = {}, confidence, estimatedRoi, runtimeMs,
  onRun, onCompare, onSave, onClone, onDelete,
}) => {
  const { isDark } = useUserStore();

  const riskColors: Record<string, string> = {
    Low: 'text-emerald-500 bg-emerald-500/10',
    Medium: 'text-amber-500 bg-amber-500/10',
    High: 'text-red-500 bg-red-500/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border p-5 flex flex-col gap-3 group hover:border-indigo-500/30 transition-all duration-300"
      style={{
        background: isDark ? 'rgba(255,255,255,0.03)' : '#ffffff',
        borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
        boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>{name}</p>
          <h4 className="text-sm font-bold mt-0.5" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>{title}</h4>
        </div>
        {badge && (
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full bg-${badgeColor}-500/15 text-${badgeColor}-500`}
            style={{
              background: badgeColor === 'emerald' ? 'rgba(16,185,129,0.12)' : 'rgba(99,102,241,0.12)',
              color: badgeColor === 'emerald' ? '#10b981' : '#6366f1',
            }}
          >
            {badge}
          </span>
        )}
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag, i) => (
          <span
            key={i}
            className="text-[10px] font-medium px-2 py-0.5 rounded-full"
            style={{
              background: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
              color: isDark ? '#94a3b8' : '#64748b',
            }}
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Description */}
      <p className="text-xs leading-relaxed" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
        {goal}
      </p>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3 pt-2 border-t" style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
        {metrics.revenue_change !== undefined && (
          <div>
            <p className="text-[10px]" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>Revenue</p>
            <p className={`text-xs font-bold ${metrics.revenue_change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
              ↑ {Math.abs(metrics.revenue_change)}%
            </p>
          </div>
        )}
        {metrics.profit_change !== undefined && (
          <div>
            <p className="text-[10px]" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>Profit</p>
            <p className={`text-xs font-bold ${metrics.profit_change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
              ↑ {Math.abs(metrics.profit_change)}%
            </p>
          </div>
        )}
        {metrics.risk && (
          <div>
            <p className="text-[10px]" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>Risk</p>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${riskColors[metrics.risk] || ''}`}>
              {metrics.risk}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={() => onRun?.(id)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm shadow-indigo-600/20"
        >
          <Play className="w-3 h-3" /> Run Scenario
        </button>
        <button
          onClick={() => onCompare?.(id)}
          className="p-2 rounded-xl border transition-all hover:border-indigo-500/30"
          style={{
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            color: isDark ? '#94a3b8' : '#64748b',
          }}
          title="Compare"
        >
          <GitCompare className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => onSave?.(id)}
          className="p-2 rounded-xl border transition-all hover:border-indigo-500/30"
          style={{
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            color: isDark ? '#94a3b8' : '#64748b',
          }}
          title="Save"
        >
          <Bookmark className="w-3.5 h-3.5" />
        </button>
      </div>
    </motion.div>
  );
};

export default ScenarioCard;
