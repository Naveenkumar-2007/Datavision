import React from 'react';
import { useUserStore } from '@/store/userStore';
import { Lock, Pin, Info } from 'lucide-react';

interface VariableControlProps {
  name: string;
  displayName: string;
  controlType: string;
  value: any;
  onChange: (value: any) => void;
  minValue?: number;
  maxValue?: number;
  step?: number;
  unit?: string;
  options?: string[];
  locked?: boolean;
  pinned?: boolean;
  description?: string;
  onLock?: () => void;
  onPin?: () => void;
}

const VariableControl: React.FC<VariableControlProps> = ({
  name, displayName, controlType, value, onChange,
  minValue = 0, maxValue = 100, step = 1, unit = '',
  options = [], locked = false, pinned = false, description,
  onLock, onPin,
}) => {
  const { isDark } = useUserStore();

  const formatValue = (v: any) => {
    if (typeof v !== 'number') return String(v);
    if (unit === '₹') {
      if (v >= 10000000) return `₹${(v / 10000000).toFixed(2)} Cr`;
      if (v >= 100000) return `₹${(v / 100000).toFixed(1)} L`;
      return `₹${v.toLocaleString()}`;
    }
    if (unit === '%') return `${v.toLocaleString()}%`;
    return v.toLocaleString();
  };

  // Calculate slider fill percentage
  const fillPct = controlType === 'slider' && typeof value === 'number'
    ? ((value - (minValue || 0)) / ((maxValue || 100) - (minValue || 0))) * 100
    : 0;

  return (
    <div className={`space-y-2 ${locked ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Label row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <label
            className="text-xs font-medium truncate"
            style={{ color: isDark ? '#e2e8f0' : '#334155' }}
            title={displayName}
          >
            {displayName}
          </label>
          {description && (
            <div className="group relative">
              <Info className="w-3 h-3 flex-shrink-0" style={{ color: isDark ? '#475569' : '#94a3b8' }} />
              <div className="absolute z-50 bottom-full left-0 mb-1 hidden group-hover:block">
                <div className="px-2 py-1 rounded-lg text-[10px] whitespace-nowrap shadow-lg border"
                  style={{
                    background: isDark ? '#1e293b' : '#fff',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    color: isDark ? '#cbd5e1' : '#475569',
                  }}
                >
                  {description}
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-1">
          {onPin && (
            <button onClick={onPin} className="p-0.5 rounded hover:bg-white/5 transition-colors" title="Pin">
              <Pin className={`w-3 h-3 ${pinned ? 'text-indigo-400' : ''}`} style={{ color: pinned ? undefined : (isDark ? '#475569' : '#94a3b8') }} />
            </button>
          )}
          {onLock && (
            <button onClick={onLock} className="p-0.5 rounded hover:bg-white/5 transition-colors" title="Lock">
              <Lock className={`w-3 h-3 ${locked ? 'text-amber-400' : ''}`} style={{ color: locked ? undefined : (isDark ? '#475569' : '#94a3b8') }} />
            </button>
          )}
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-md ml-1"
            style={{
              background: isDark ? 'rgba(99,102,241,0.1)' : 'rgba(99,102,241,0.08)',
              color: '#6366f1',
            }}
          >
            {formatValue(value)}
          </span>
        </div>
      </div>

      {/* Control */}
      {controlType === 'slider' && (
        <div className="space-y-1">
          <div className="relative w-full h-1.5">
            <div
              className="absolute inset-0 rounded-full"
              style={{ background: isDark ? '#1e293b' : '#e2e8f0' }}
            />
            <div
              className="absolute top-0 left-0 h-full rounded-full transition-all duration-75"
              style={{
                width: `${fillPct}%`,
                background: 'linear-gradient(90deg, #6366f1, #818cf8)',
              }}
            />
            <input
              type="range"
              min={minValue}
              max={maxValue}
              step={step}
              value={value}
              onChange={(e) => onChange(parseFloat(e.target.value))}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              style={{ margin: 0 }}
            />
            <div
              className="absolute top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full border-2 shadow-md transition-all duration-75 pointer-events-none"
              style={{
                left: `calc(${fillPct}% - 7px)`,
                borderColor: '#6366f1',
                background: isDark ? '#0f172a' : '#ffffff',
                boxShadow: '0 0 6px rgba(99,102,241,0.4)',
              }}
            />
          </div>
          <div className="flex justify-between text-[10px]" style={{ color: isDark ? '#475569' : '#94a3b8' }}>
            <span>{formatValue(minValue)}</span>
            <span>{formatValue(maxValue)}</span>
          </div>
        </div>
      )}

      {controlType === 'number' && (
        <input
          type="number"
          value={value}
          min={minValue}
          max={maxValue}
          step={step}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="w-full px-3 py-2 rounded-xl text-sm border outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
          style={{
            background: isDark ? 'rgba(255,255,255,0.03)' : '#f8fafc',
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            color: isDark ? '#f8fafc' : '#0f172a',
          }}
        />
      )}

      {controlType === 'dropdown' && (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 rounded-xl text-sm border outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all cursor-pointer"
          style={{
            background: isDark ? 'rgba(255,255,255,0.03)' : '#f8fafc',
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            color: isDark ? '#f8fafc' : '#0f172a',
          }}
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )}

      {controlType === 'categorical' && (
        <div className="flex flex-wrap gap-1.5">
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => onChange(opt)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all border ${
                value === opt
                  ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-500'
                  : ''
              }`}
              style={value !== opt ? {
                borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
                color: isDark ? '#94a3b8' : '#64748b',
              } : undefined}
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      {controlType === 'boolean' && (
        <button
          onClick={() => onChange(!value)}
          className={`relative w-11 h-6 rounded-full transition-all duration-200 ${
            value ? 'bg-indigo-500' : isDark ? 'bg-gray-700' : 'bg-gray-300'
          }`}
        >
          <div
            className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-md transition-transform duration-200 ${
              value ? 'translate-x-[22px]' : 'translate-x-0.5'
            }`}
          />
        </button>
      )}
    </div>
  );
};

export default VariableControl;
