import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useUserStore } from '@/store/userStore';

interface SimulatorKPICardProps {
  label: string;
  value: string;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  description?: string;
  icon?: React.ReactNode;
  accent?: string;
}

const SimulatorKPICard: React.FC<SimulatorKPICardProps> = ({
  label,
  value,
  change,
  trend = 'stable',
  description,
  icon,
  accent = '#6366f1',
}) => {
  const { isDark } = useUserStore();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="relative overflow-hidden rounded-2xl border p-5"
      style={{
        background: isDark ? 'rgba(255,255,255,0.03)' : '#ffffff',
        borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
        boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      {/* Accent glow */}
      <div
        className="absolute top-0 right-0 w-20 h-20 rounded-full blur-3xl opacity-10"
        style={{ background: accent }}
      />

      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p
            className="text-xs font-medium truncate mb-1.5"
            style={{ color: isDark ? '#94a3b8' : '#64748b' }}
          >
            {label}
          </p>
          <p
            className="text-2xl font-bold tracking-tight"
            style={{ color: isDark ? '#f8fafc' : '#0f172a' }}
          >
            {value}
          </p>
          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              <span
                className={`flex items-center gap-0.5 text-xs font-semibold ${
                  trend === 'up'
                    ? 'text-emerald-500'
                    : trend === 'down'
                    ? 'text-red-500'
                    : isDark
                    ? 'text-gray-400'
                    : 'text-gray-500'
                }`}
              >
                {trend === 'up' && <TrendingUp className="w-3.5 h-3.5" />}
                {trend === 'down' && <TrendingDown className="w-3.5 h-3.5" />}
                {trend === 'stable' && <Minus className="w-3.5 h-3.5" />}
                {change > 0 ? '+' : ''}{change}%
              </span>
              <span
                className="text-xs"
                style={{ color: isDark ? '#64748b' : '#94a3b8' }}
              >
                vs Baseline
              </span>
            </div>
          )}
          {description && (
            <p
              className="text-xs mt-1"
              style={{ color: isDark ? '#64748b' : '#94a3b8' }}
            >
              {description}
            </p>
          )}
        </div>
        {icon && (
          <div
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
            style={{
              background: `${accent}15`,
              color: accent,
            }}
          >
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default SimulatorKPICard;
