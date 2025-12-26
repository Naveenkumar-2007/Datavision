import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { RefreshCw, Loader, Filter, ChevronDown, X, TrendingUp, TrendingDown, User, LayoutGrid, GraduationCap, Users, ShoppingCart, Heart, Factory, Store, Briefcase, Globe, Search, Check, Trophy, Activity, Upload } from 'lucide-react';
import { apiService } from '@/services/api';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ScatterChart, Scatter, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// ===========================================================================
// POWER BI ENTERPRISE DASHBOARD v4.0 - FULLY DYNAMIC
// No hardcoded chart slots! Renders ALL charts from backend dynamically.
// ===========================================================================

interface ThemeContext { isDark: boolean; }

const COLOR_PALETTES = [
  ['#3B82F6', '#22C55E', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4'],
  ['#6366F1', '#10B981', '#F97316', '#E11D48', '#A855F7', '#14B8A6'],
  ['#2563EB', '#16A34A', '#CA8A04', '#DB2777', '#7C3AED', '#0891B2'],
  ['#0EA5E9', '#84CC16', '#EAB308', '#F43F5E', '#9333EA', '#0D9488'],
  ['#3730A3', '#059669', '#D97706', '#BE123C', '#6D28D9', '#0E7490'],
];

const getDomainIcon = (domain: string) => {
  const icons: Record<string, React.ReactNode> = {
    Education: <GraduationCap className="w-5 h-5" />,
    HR: <Users className="w-5 h-5" />,
    Sales: <ShoppingCart className="w-5 h-5" />,
    Healthcare: <Heart className="w-5 h-5" />,
    Finance: <Briefcase className="w-5 h-5" />,
    Manufacturing: <Factory className="w-5 h-5" />,
    Retail: <Store className="w-5 h-5" />,
    Sports: <Trophy className="w-5 h-5" />,
    Analytics: <Activity className="w-5 h-5" />,
  };
  return icons[domain] || <Globe className="w-5 h-5" />;
};

const fmt = (v: any): string => {
  if (v === null || v === undefined) return '-';
  if (typeof v !== 'number' || isNaN(v)) return String(v);
  if (v >= 1e12) return `${(v / 1e12).toFixed(1)}T`;
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  if (!Number.isInteger(v) && v < 100) return v.toFixed(2);
  return v.toLocaleString();
};

// ============================================
// SEARCHABLE FILTER DROPDOWN
// ============================================
interface FilterDropdownProps {
  label: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
  theme: any;
}

const FilterDropdown: React.FC<FilterDropdownProps> = ({ label, options, value, onChange, theme }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredOptions = useMemo(() => {
    if (!search) return options.slice(0, 15);
    return options.filter(opt => opt.toLowerCase().includes(search.toLowerCase())).slice(0, 20);
  }, [options, search]);

  const displayValue = value === 'all' ? 'All' : value;

  return (
    <div ref={dropdownRef} className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm transition-all hover:border-blue-400" style={{ background: theme.inputBg, borderColor: theme.border, color: theme.text }}>
        <span className="text-xs font-medium uppercase opacity-60">{label}</span>
        <span className="font-semibold">{displayValue?.substring(0, 10)}</span>
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="absolute z-50 mt-2 w-56 rounded-xl border shadow-xl overflow-hidden" style={{ background: theme.cardBg, borderColor: theme.border }}>
          <div className="p-2 border-b" style={{ borderColor: theme.border }}>
            <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg" style={{ background: theme.inputBg }}>
              <Search className="w-3.5 h-3.5" style={{ color: theme.textMuted }} />
              <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full bg-transparent text-xs outline-none" style={{ color: theme.text }} />
            </div>
          </div>
          <div className="max-h-48 overflow-y-auto p-1">
            <button onClick={() => { onChange('all'); setIsOpen(false); setSearch(''); }} className={`w-full text-left px-3 py-2 text-xs rounded-lg transition-colors ${value === 'all' ? 'bg-blue-500/20 text-blue-400' : ''}`} style={{ color: theme.text }}>All</button>
            {filteredOptions.map((opt) => (
              <button key={opt} onClick={() => { onChange(opt); setIsOpen(false); setSearch(''); }} className={`w-full text-left px-3 py-2 text-xs rounded-lg transition-colors ${value === opt ? 'bg-blue-500/20 text-blue-400' : ''}`} style={{ color: theme.text }}>{opt}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================
// DYNAMIC WIDGET COMPONENT - Renders ANY chart type
// ============================================
interface DynamicWidgetProps {
  widget: any;
  theme: any;
  colors: string[];
  index: number;
  isDark: boolean;
}

const DynamicWidget: React.FC<DynamicWidgetProps> = ({ widget, theme, colors, index, isDark }) => {
  const getColors = (idx: number) => COLOR_PALETTES[(idx + index) % COLOR_PALETTES.length];

  const renderContent = () => {
    switch (widget.type) {
      case 'area':
        const areaData = widget.data?.series?.[0]?.data || [];
        if (!areaData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={areaData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id={`grad-${index}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[0]} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={colors[0]} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.gridStroke} vertical={false} />
              <XAxis dataKey="x" tick={{ fontSize: 9, fill: theme.textMuted }} stroke="transparent" />
              <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke="transparent" />
              <Tooltip contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
              <Area type="monotone" dataKey="y" stroke={colors[0]} fill={`url(#grad-${index})`} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar_vertical':
        const barData = widget.data?.data || [];
        if (!barData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.gridStroke} vertical={false} />
              <XAxis dataKey="category" tick={{ fontSize: 9, fill: theme.textMuted }} stroke="transparent" />
              <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke="transparent" />
              <Tooltip contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {barData.map((_: any, idx: number) => <Cell key={idx} fill={getColors(0)[idx % 6]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      case 'bar_horizontal':
        const hBarData = widget.data?.data || [];
        if (!hBarData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hBarData} layout="vertical" margin={{ left: 0, right: 30, top: 0, bottom: 0 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="category" width={80} tick={{ fontSize: 10, fill: theme.text }} stroke="transparent" />
              <Tooltip contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20} label={{ position: 'right', fontSize: 10, fill: theme.text, fontWeight: 600, formatter: fmt }}>
                {hBarData.map((_: any, idx: number) => <Cell key={idx} fill={getColors(1)[idx % 6]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      case 'donut':
        const pieData = widget.data?.data || [];
        if (!pieData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={35} outerRadius={60} paddingAngle={2} dataKey="value" label={({ percent }) => `${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((_: any, idx: number) => <Cell key={idx} fill={getColors(2)[idx % 6]} stroke="none" />)}
              </Pie>
              <Legend layout="vertical" align="right" verticalAlign="middle" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'radar':
        const radarData = widget.data?.data || widget.data || [];
        if (!radarData.length || radarData.length < 3) return <p className="text-sm" style={{ color: theme.textMuted }}>Needs 3+ categories</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke={theme.gridStroke} />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9, fill: theme.textMuted }} />
              <PolarRadiusAxis tick={{ fontSize: 8, fill: theme.textMuted }} />
              <Radar name="Value" dataKey="value" stroke={widget.color || colors[0]} fill={widget.color || colors[0]} fillOpacity={0.5} />
            </RadarChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        const scatterData = widget.data?.data || [];
        if (!scatterData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>Needs 2+ metrics</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.gridStroke} />
              <XAxis dataKey="x" type="number" tick={{ fontSize: 9, fill: theme.textMuted }} />
              <YAxis dataKey="y" type="number" tick={{ fontSize: 9, fill: theme.textMuted }} />
              <Tooltip contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
              <Scatter data={scatterData} fill={colors[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'line':
        const lineData = widget.data?.series?.[0]?.data || [];
        if (!lineData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No time data</p>;
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lineData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.gridStroke} vertical={false} />
              <XAxis dataKey="x" tick={{ fontSize: 9, fill: theme.textMuted }} stroke="transparent" />
              <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke="transparent" />
              <Tooltip contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
              <Line type="monotone" dataKey="y" stroke={colors[0]} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'stats_card':
        if (!widget.data || widget.data.avg === undefined) return <p className="text-sm" style={{ color: theme.textMuted }}>No numeric data</p>;
        return (
          <div className="space-y-2.5 h-full flex flex-col justify-center">
            {['min', '25th', 'median', '75th', 'max'].map((key, i) => {
              const val = widget.data[key];
              if (val === undefined) return null;
              const labels: Record<string, string> = { min: 'Min', '25th': '25th %', median: 'Median', '75th': '75th %', max: 'Max' };
              return (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-[10px] w-14 truncate" style={{ color: theme.textMuted }}>{labels[key]}</span>
                  <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                    <div className="h-full rounded-full" style={{ width: `${Math.min((val / widget.data.max) * 100, 100) * 0.7}%`, background: getColors(3)[i % 6] }} />
                  </div>
                  <span className="text-[10px] font-semibold w-12 text-right" style={{ color: theme.text }}>{fmt(val)}</span>
                </div>
              );
            })}
            <div className="text-center mt-2">
              <span className="text-lg font-bold" style={{ color: colors[0] }}>{fmt(widget.data.avg)}</span>
              <span className="text-[10px] ml-1" style={{ color: theme.textMuted }}>Avg</span>
            </div>
          </div>
        );

      case 'top5_list':
        const listData = widget.data || [];
        if (!listData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="space-y-2.5">
            {listData.slice(0, 5).map((item: any, j: number) => (
              <div key={j} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: getColors(4)[j % 6] }}>
                    <User className="w-3.5 h-3.5 text-white" />
                  </div>
                  <span className="text-xs" style={{ color: theme.text }}>{item.name?.substring(0, 15)}</span>
                </div>
                <span className="text-xs font-bold" style={{ color: theme.text }}>{fmt(item.value)}</span>
              </div>
            ))}
          </div>
        );

      case 'summary':
        return (
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
              <p className="text-2xl font-bold" style={{ color: colors[0] }}>{fmt(widget.data?.records || 0)}</p>
              <p className="text-[10px]" style={{ color: theme.textMuted }}>Records</p>
            </div>
            <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
              <p className="text-2xl font-bold" style={{ color: colors[1] }}>{widget.data?.columns || 0}</p>
              <p className="text-[10px]" style={{ color: theme.textMuted }}>Columns</p>
            </div>
            <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
              <p className="text-2xl font-bold" style={{ color: colors[2] }}>{widget.data?.metrics || 0}</p>
              <p className="text-[10px]" style={{ color: theme.textMuted }}>Metrics</p>
            </div>
            <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
              <p className="text-2xl font-bold" style={{ color: colors[3] }}>{widget.data?.dimensions || 0}</p>
              <p className="text-[10px]" style={{ color: theme.textMuted }}>Dimensions</p>
            </div>
          </div>
        );

      case 'data_table':
        if (!widget.data?.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="overflow-x-auto max-h-40">
            <table className="w-full text-[10px]">
              <thead style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <tr>
                  {widget.columns?.slice(0, 4).map((col: string, j: number) => (
                    <th key={j} className="text-left px-3 py-1.5 font-bold uppercase" style={{ color: getColors(4)[j % 6] }}>{col.replace(/_/g, ' ').substring(0, 12)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {widget.data?.slice(0, 5).map((row: any, j: number) => (
                  <tr key={j} className="border-b last:border-0" style={{ borderColor: theme.border }}>
                    {widget.columns?.slice(0, 4).map((col: string, k: number) => (
                      <td key={k} className="px-3 py-1.5" style={{ color: theme.text }}>{String(row[col] ?? '-').substring(0, 15)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'waterfall':
        const wfData = widget.data || [];
        if (!wfData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="space-y-2">
            {wfData.slice(0, 6).map((item: any, j: number) => (
              <div key={j}>
                <div className="flex justify-between mb-1">
                  <span className="text-[10px]" style={{ color: theme.textMuted }}>{item.name?.substring(0, 12)}</span>
                  <span className="text-[10px] font-bold" style={{ color: item.color }}>{fmt(item.value)}</span>
                </div>
                <div className="h-5 rounded-md flex overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  <div className="h-full rounded-md transition-all" style={{ width: `${(item.value / (wfData[0]?.value || 1)) * 100}%`, background: item.color }} />
                </div>
              </div>
            ))}
            <div className="text-center pt-2 border-t" style={{ borderColor: theme.border }}>
              <span className="text-sm font-bold" style={{ color: colors[0] }}>Total: {fmt(wfData[wfData.length - 1]?.total || 0)}</span>
            </div>
          </div>
        );

      case 'treemap':
        const treeData = widget.data || [];
        if (!treeData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        const totalTree = treeData.reduce((a: number, b: any) => a + (b.value || 0), 0);
        return (
          <div className="grid grid-cols-3 gap-1.5 h-full">
            {treeData.slice(0, 9).map((item: any, j: number) => (
              <div key={j} className="rounded-lg p-2 flex flex-col justify-center items-center" style={{ background: item.color, minHeight: `${Math.max(30, (item.value / totalTree) * 150)}px` }}>
                <span className="text-[10px] text-white font-bold text-center">{item.name?.substring(0, 8)}</span>
                <span className="text-[9px] text-white/80">{item.percent}%</span>
              </div>
            ))}
          </div>
        );

      case 'stacked_bar':
        const stackData = widget.data || [];
        const stackKeys = widget.keys || [];
        if (!stackData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="space-y-2">
            {stackData.slice(0, 5).map((item: any, j: number) => (
              <div key={j}>
                <div className="flex justify-between mb-1">
                  <span className="text-[10px]" style={{ color: theme.text }}>{item.name}</span>
                </div>
                <div className="h-5 rounded-md flex overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  {stackKeys.map((key: string, k: number) => (
                    <div key={k} className="h-full" style={{ width: `${(item[key] || 0) * 20}%`, background: getColors(k)[k % 6] }} />
                  ))}
                </div>
              </div>
            ))}
            <div className="flex flex-wrap gap-2 mt-2">
              {stackKeys.slice(0, 4).map((key: string, k: number) => (
                <div key={k} className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{ background: getColors(k)[k % 6] }} />
                  <span className="text-[9px]" style={{ color: theme.textMuted }}>{key}</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'bullet':
        const bulletData = widget.data || {};
        const ranges = bulletData.ranges || [0, 0, 0];
        const bulletMax = ranges[2] || 100;
        return (
          <div className="flex flex-col justify-center h-full">
            <div className="relative h-8 rounded-md overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
              {/* Range bars */}
              <div className="absolute h-full" style={{ width: '100%', background: '#86EFAC' }} />
              <div className="absolute h-full" style={{ width: `${(ranges[1] / bulletMax) * 100}%`, background: '#FDE047' }} />
              <div className="absolute h-full" style={{ width: `${(ranges[0] / bulletMax) * 100}%`, background: '#FCA5A5' }} />
              {/* Value bar */}
              <div className="absolute h-3 top-2.5 rounded" style={{ width: `${(bulletData.value / bulletMax) * 100}%`, background: colors[0] }} />
              {/* Target line */}
              <div className="absolute w-1 h-full top-0" style={{ left: `${(bulletData.target / bulletMax) * 100}%`, background: '#0F172A' }} />
            </div>
            <div className="flex justify-between mt-2">
              <span className="text-[10px]" style={{ color: theme.textMuted }}>Value: <b style={{ color: theme.text }}>{fmt(bulletData.value)}</b></span>
              <span className="text-[10px]" style={{ color: theme.textMuted }}>Target: <b style={{ color: colors[0] }}>{fmt(bulletData.target)}</b></span>
            </div>
          </div>
        );

      case 'treemap':
        const treemapItems = widget.data || [];
        if (!treemapItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-1 h-full">
            {treemapItems.slice(0, 9).map((item: any, i: number) => (
              <div key={i} className="rounded-lg p-2 flex flex-col items-center justify-center text-center transition-transform hover:scale-105"
                style={{ background: item.color || getColors(0)[i % 6], minHeight: `${Math.max(40, item.area || 50)}px` }}>
                <span className="text-white text-[10px] font-bold">{item.name}</span>
                <span className="text-white/80 text-[9px]">{item.percentage}%</span>
              </div>
            ))}
          </div>
        );

      case 'comparison':
        const compData = widget.data || {};
        const topPerformers = compData.top || [];
        const bottomPerformers = compData.bottom || [];
        return (
          <div className="space-y-2 h-full flex flex-col justify-center">
            <div className="space-y-1">
              <p className="text-[9px] font-bold uppercase text-green-500">Top Performers</p>
              {topPerformers.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 rounded" style={{ background: isDark ? '#064E3B' : '#D1FAE5' }}>
                  <span className="text-xs font-medium" style={{ color: theme.text }}>{item.name}</span>
                  <span className="text-xs font-bold text-green-600">{fmt(item.value)}</span>
                </div>
              ))}
            </div>
            <div className="border-t pt-2" style={{ borderColor: theme.border }}>
              <p className="text-[9px] font-bold uppercase text-red-500 mb-1">Bottom Performers</p>
              {bottomPerformers.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 rounded" style={{ background: isDark ? '#7F1D1D' : '#FEE2E2' }}>
                  <span className="text-xs font-medium" style={{ color: theme.text }}>{item.name}</span>
                  <span className="text-xs font-bold text-red-600">{fmt(item.value)}</span>
                </div>
              ))}
            </div>
            {compData.gap > 0 && (
              <div className="text-center pt-1">
                <span className="text-[9px]" style={{ color: theme.textMuted }}>Gap: </span>
                <span className="text-xs font-bold" style={{ color: '#3B82F6' }}>{fmt(compData.gap)}</span>
              </div>
            )}
          </div>
        );

      case 'kpi_grid':
        const kpiCards = widget.data || [];
        return (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 h-full">
            {kpiCards.map((kpi: any, i: number) => (
              <div key={i} className="rounded-lg p-4 flex flex-col justify-center" style={{ background: isDark ? '#0F172A' : '#F8FAFC', border: `1px solid ${theme.border}` }}>
                <p className="text-[9px] uppercase font-bold mb-1" style={{ color: kpi.color }}>{kpi.title}</p>
                <p className="text-xl font-black mb-1" style={{ color: theme.text }}>{kpi.formatted || fmt(kpi.value)}</p>
                <div className="flex items-center gap-1">
                  {kpi.change >= 0 ?
                    <TrendingUp className="w-3 h-3 text-green-500" /> :
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  }
                  <span className={`text-[9px] font-bold ${kpi.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {kpi.change >= 0 ? '+' : ''}{kpi.change}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        );

      case 'horizontal_bar':
        const hBarItems = widget.data || [];
        if (!hBarItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        const hBarMax = Math.max(...hBarItems.map((d: any) => d.value || 0));
        return (
          <div className="space-y-2 h-full flex flex-col justify-center">
            {hBarItems.slice(0, 6).map((item: any, i: number) => (
              <div key={i}>
                <div className="flex justify-between mb-1">
                  <span className="text-xs font-medium" style={{ color: theme.text }}>{item.name}</span>
                  <span className="text-xs font-bold" style={{ color: item.color || getColors(0)[i % 6] }}>{fmt(item.value)}</span>
                </div>
                <div className="h-4 rounded-full overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  <div className="h-full rounded-full transition-all" style={{
                    width: `${(item.value / hBarMax) * 100}%`,
                    background: item.color || getColors(0)[i % 6]
                  }} />
                </div>
              </div>
            ))}
          </div>
        );

      case 'waterfall':
        const wfItems = widget.data || [];
        if (!wfItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        const wfMax = Math.max(...wfItems.map((d: any) => d.end || d.value || 0));
        return (
          <div className="space-y-2 h-full flex flex-col justify-center">
            {wfItems.map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] w-16 truncate" style={{ color: theme.text }}>{item.name}</span>
                <div className="flex-1 h-4 rounded overflow-hidden relative" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  <div className="absolute h-full rounded" style={{
                    left: item.isTotal ? 0 : `${(item.start / wfMax) * 100}%`,
                    width: `${((item.isTotal ? item.end : item.value) / wfMax) * 100}%`,
                    background: item.color || getColors(0)[i % 6]
                  }} />
                </div>
                <span className="text-[10px] font-bold w-10 text-right" style={{ color: item.color }}>{fmt(item.value)}</span>
              </div>
            ))}
          </div>
        );

      case 'sparklines_grid':
        const sparkItems = widget.data || [];
        if (!sparkItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="grid grid-cols-2 gap-2 h-full">
            {sparkItems.slice(0, 6).map((item: any, i: number) => {
              const pts = item.points || [];
              const max = Math.max(...pts);
              const min = Math.min(...pts);
              const rng = max - min || 1;
              return (
                <div key={i} className="p-2 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[9px] font-medium truncate" style={{ color: theme.text }}>{item.name}</span>
                    <span className={`text-[8px] font-bold ${item.isUp ? 'text-green-500' : 'text-red-500'}`}>
                      {item.isUp ? '↑' : '↓'}{Math.abs(item.change)}%
                    </span>
                  </div>
                  <svg className="w-full h-6" viewBox={`0 0 ${pts.length * 10} 25`}>
                    <polyline fill="none" stroke={item.color || getColors(0)[i % 6]} strokeWidth="2"
                      points={pts.map((p: number, j: number) => `${j * 10},${23 - ((p - min) / rng) * 20}`).join(' ')} />
                  </svg>
                </div>
              );
            })}
          </div>
        );

      case 'ring_progress':
        const ringItems = widget.data || [];
        if (!ringItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="grid grid-cols-2 gap-3 h-full">
            {ringItems.slice(0, 4).map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <div className="relative w-10 h-10">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="15" fill="none" stroke={isDark ? '#334155' : '#E2E8F0'} strokeWidth="3" />
                    <circle cx="20" cy="20" r="15" fill="none" stroke={item.color} strokeWidth="3" strokeLinecap="round"
                      strokeDasharray={`${item.percentage} 100`} />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[8px] font-bold" style={{ color: item.color }}>{item.percentage}%</span>
                </div>
                <div>
                  <p className="text-[9px] font-medium truncate" style={{ color: theme.text }}>{item.name}</p>
                  <p className="text-[8px]" style={{ color: theme.textMuted }}>{fmt(item.value)}</p>
                </div>
              </div>
            ))}
          </div>
        );

      case 'top_n_table':
        const tableRows = widget.data || [];
        if (!tableRows.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="space-y-1 h-full overflow-auto">
            {tableRows.slice(0, 8).map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-2 p-1.5 rounded" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[9px] font-bold" style={{ background: item.color }}>
                  {item.rank}
                </div>
                <span className="flex-1 text-[10px] font-medium truncate" style={{ color: theme.text }}>{item.name}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold" style={{ background: item.gradeColor + '20', color: item.gradeColor }}>
                  {item.grade}
                </span>
                <span className="text-[9px] font-bold" style={{ color: item.color }}>{item.percentage}%</span>
              </div>
            ))}
          </div>
        );

      case 'distribution':
        const distItems = widget.data || [];
        if (!distItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        const distMax = Math.max(...distItems.map((d: any) => d.count || 0));
        return (
          <div className="flex items-end gap-1 h-full">
            {distItems.map((item: any, i: number) => (
              <div key={i} className="flex-1 flex flex-col items-center h-full justify-end">
                <div className="w-full rounded-t transition-all hover:opacity-80" style={{
                  height: `${(item.count / distMax) * 100}%`,
                  minHeight: '4px',
                  background: item.color || getColors(0)[i % 6]
                }} />
                <span className="text-[7px] mt-1 text-center" style={{ color: theme.textMuted }}>{item.range}</span>
              </div>
            ))}
          </div>
        );

      case 'bubble':
        const bubbleItems = widget.data || [];
        if (!bubbleItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        return (
          <div className="flex flex-wrap gap-2 justify-center items-center h-full">
            {bubbleItems.slice(0, 8).map((item: any, i: number) => (
              <div key={i} className="rounded-full flex items-center justify-center text-white text-[8px] font-bold transition-transform hover:scale-110 cursor-pointer"
                style={{ width: `${item.size}px`, height: `${item.size}px`, background: item.color || getColors(0)[i % 6] }}>
                {item.name?.substring(0, 4)}
              </div>
            ))}
          </div>
        );

      case 'heatmap':
        const heatItems = widget.data || [];
        if (!heatItems.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No data</p>;
        const heatRows = [...new Set(heatItems.map((d: any) => d.row))] as string[];
        const heatCols = [...new Set(heatItems.map((d: any) => d.col))] as string[];
        return (
          <div className="overflow-auto h-full">
            <div className="grid gap-1" style={{ gridTemplateColumns: `60px repeat(${Math.min(heatCols.length, 4)}, 1fr)` }}>
              <div></div>
              {heatCols.slice(0, 4).map((col, i) => (
                <div key={i} className="text-[8px] text-center font-medium truncate" style={{ color: theme.textMuted }}>{col}</div>
              ))}
              {heatRows.slice(0, 4).map((row, ri) => (
                <React.Fragment key={ri}>
                  <div className="text-[8px] font-medium truncate flex items-center" style={{ color: theme.text }}>{row}</div>
                  {heatCols.slice(0, 4).map((col, ci) => {
                    const cell = heatItems.find((d: any) => d.row === row && d.col === col);
                    return (
                      <div key={ci} className="h-6 rounded flex items-center justify-center text-[8px] font-bold"
                        style={{ background: cell?.color || '#E2E8F0', color: cell?.intensity > 4 ? 'white' : '#1E293B' }}>
                        {cell ? fmt(cell.value) : '-'}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        );

      // =====================================================
      // NEW ADVANCED CHART TYPES
      // =====================================================

      case 'box_plot':
        const boxData = widget.data || [];
        if (!boxData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No distribution data</p>;
        const boxMin = Math.min(...boxData.map((b: any) => b.min));
        const boxMax = Math.max(...boxData.map((b: any) => b.max));
        const boxRange = boxMax - boxMin || 1;
        return (
          <div className="space-y-2 h-full flex flex-col justify-center">
            {boxData.map((box: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] w-16 truncate" style={{ color: theme.text }}>{box.category}</span>
                <div className="flex-1 relative h-6" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  {/* Min-Max range */}
                  <div className="absolute h-full" style={{
                    left: `${((box.min - boxMin) / boxRange) * 100}%`,
                    width: `${((box.max - box.min) / boxRange) * 100}%`,
                    background: `${box.color}20`,
                    borderLeft: `2px solid ${box.color}`,
                    borderRight: `2px solid ${box.color}`
                  }} />
                  {/* IQR (Q1-Q3) */}
                  <div className="absolute h-full" style={{
                    left: `${((box.q1 - boxMin) / boxRange) * 100}%`,
                    width: `${((box.q3 - box.q1) / boxRange) * 100}%`,
                    background: box.color
                  }} />
                  {/* Median line */}
                  <div className="absolute w-0.5 h-full bg-white" style={{
                    left: `${((box.median - boxMin) / boxRange) * 100}%`
                  }} />
                </div>
                <span className="text-[9px] font-bold w-12 text-right" style={{ color: box.color }}>{fmt(box.median)}</span>
              </div>
            ))}
          </div>
        );

      case 'sankey':
        const sankeyFlows = widget.data || [];
        if (!sankeyFlows.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No flow data</p>;
        const sankeyMax = Math.max(...sankeyFlows.map((f: any) => f.value));
        return (
          <div className="space-y-1.5 h-full overflow-auto">
            {sankeyFlows.slice(0, 12).map((flow: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[9px] w-20 truncate" style={{ color: theme.text }}>{flow.source}</span>
                <div className="flex-1 h-4 rounded-full transition-all hover:opacity-80"
                  style={{ background: flow.color || getColors(0)[i % 6], width: `${Math.min(100, (flow.value / sankeyMax) * 100)}%` }} />
                <span className="text-[9px] w-20 truncate text-right" style={{ color: theme.text }}>{flow.target}</span>
                <span className="text-[9px] font-bold w-10 text-right" style={{ color: flow.color }}>{fmt(flow.value)}</span>
              </div>
            ))}
          </div>
        );

      case 'calendar_heatmap':
        const calendarData = widget.data || [];
        if (!calendarData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No temporal data</p>;
        return (
          <div className="grid grid-cols-7 gap-1 h-full">
            {calendarData.slice(0, 49).map((day: any, i: number) => (
              <div key={i}
                className="w-full aspect-square rounded-sm flex items-center justify-center transition-transform hover:scale-110 cursor-pointer"
                style={{ background: day.color || getColors(0)[day.intensity % 6] }}
                title={`${day.date}: ${fmt(day.value)}`}>
                <span className="text-[7px] font-bold text-white">{new Date(day.date).getDate()}</span>
              </div>
            ))}
          </div>
        );

      case 'correlation_matrix':
        const corrData = widget.data || [];
        const metrics = widget.metrics || [];
        if (!corrData.length) return <p className="text-sm" style={{ color: theme.textMuted }}>No correlation data</p>;
        return (
          <div className="overflow-auto h-full">
            <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${metrics.length}, minmax(0, 1fr))` }}>
              {corrData.map((cell: any, i: number) => (
                <div key={i}
                  className="aspect-square rounded flex items-center justify-center transition-transform hover:scale-105 cursor-pointer"
                  style={{ background: cell.color }}
                  title={`${cell.x} vs ${cell.y}: ${cell.value.toFixed(2)}`}>
                  <span className="text-[8px] font-bold" style={{ color: Math.abs(cell.value) > 0.5 ? 'white' : theme.text }}>
                    {cell.value.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-[9px]" style={{ color: theme.textMuted }}>
              <span>-1 (negative)</span>
              <span>+1 (positive)</span>
            </div>
          </div>
        );

      default:
        return <p className="text-sm" style={{ color: theme.textMuted }}>Unknown chart type: {widget.type}</p>;
    }
  };

  // Determine height based on chart type
  const getHeight = () => {
    if (widget.type === 'top5_list' || widget.type === 'summary') return 'h-auto min-h-[150px]';
    if (widget.type === 'data_table') return 'h-auto min-h-[120px]';
    if (widget.type === 'stats_card') return 'h-48';
    return 'h-48';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl border p-4"
      style={{ background: theme.cardBg, borderColor: theme.border, boxShadow: theme.shadow }}
    >
      <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>{widget.title}</h3>
      <div className={getHeight()}>
        {renderContent()}
      </div>
    </motion.div>
  );
};

// ============================================
// KPI CARD WITH MINI CHART
// ============================================
const KpiCard: React.FC<{ kpi: any; index: number; theme: any; isDark: boolean }> = ({ kpi, index, theme, isDark }) => {
  const delta = kpi.delta ?? kpi.change;
  const isPositive = delta > 0;
  const kpiColor = kpi.color || COLOR_PALETTES[0][index % 6];
  const circumference = 2 * Math.PI * 28;
  const strokeDashoffset = circumference * (1 - Math.min(kpi.value, 100) / 100);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl p-4 border" style={{ background: theme.cardBg, borderColor: theme.border, boxShadow: theme.shadow }}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className="text-[10px] uppercase font-bold tracking-wide mb-1" style={{ color: kpiColor }}>{kpi.title}</p>
          <p className="text-3xl font-black tracking-tight" style={{ color: theme.text }}>{fmt(kpi.value)}</p>
          <div className="flex items-center gap-1 mt-1">
            {isPositive ? <TrendingUp className="w-3 h-3 text-green-500" /> : <TrendingDown className="w-3 h-3 text-red-500" />}
            <span className={`text-[10px] font-medium ${isPositive ? 'text-green-500' : 'text-red-500'}`}>{isPositive ? '+' : ''}{delta?.toFixed(1)}% vs last period</span>
          </div>
        </div>
        <div className="relative w-14 h-14">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="none" stroke={isDark ? '#334155' : '#E2E8F0'} strokeWidth="5" />
            <circle cx="32" cy="32" r="28" fill="none" stroke={kpiColor} strokeWidth="5" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} className="transition-all duration-700" />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[10px] font-bold" style={{ color: theme.text }}>{fmt(kpi.value)}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ============================================
// MAIN DASHBOARD COMPONENT
// ============================================
const Dashboards: React.FC = () => {
  const context = useOutletContext<ThemeContext>();
  const isDark = context?.isDark ?? true;

  const theme = useMemo(() => ({
    bg: isDark ? 'linear-gradient(180deg, #0F172A 0%, #1E293B 100%)' : 'linear-gradient(180deg, #F8FAFC 0%, #EEF2FF 100%)',
    cardBg: isDark ? '#1E293B' : '#FFFFFF',
    border: isDark ? '#334155' : '#E2E8F0',
    text: isDark ? '#F8FAFC' : '#1E293B',
    textMuted: isDark ? '#94A3B8' : '#64748B',
    filterBg: isDark ? '#1E293B' : '#FFFFFF',
    inputBg: isDark ? '#0F172A' : '#F8FAFC',
    gridStroke: isDark ? '#334155' : '#E5E7EB',
    shadow: isDark ? '0 4px 6px -1px rgba(0,0,0,0.3)' : '0 2px 8px rgba(0,0,0,0.08)',
  }), [isDark]);

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [pendingFilters, setPendingFilters] = useState<Record<string, string>>({});

  const loadData = useCallback(async (filtersToApply?: Record<string, string>, isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      let query = '';
      const validFilters = filtersToApply ? Object.fromEntries(
        Object.entries(filtersToApply).filter(([_, v]) => v && v !== 'all')
      ) : {};

      if (Object.keys(validFilters).length > 0) {
        query = `?filters=${encodeURIComponent(JSON.stringify(validFilters))}`;
      }
      if (isRefresh) {
        query += (query ? '&' : '?') + `_t=${Date.now()}`;
      }

      const response = await apiService.getUnifiedAnalytics(query);
      setData(response.data);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const handleUpdate = () => loadData(activeFilters, true);
    window.addEventListener('filesUpdated', handleUpdate);
    return () => window.removeEventListener('filesUpdated', handleUpdate);
  }, [loadData]);

  // Extract data
  const domain = data?.domain || 'Analytics';
  const dataShape = data?.dataShape || { rows: 0, columns: 0 };
  const kpis = useMemo(() => data?.dashboardLayout?.kpis || data?.overviewLayout?.kpis || [], [data]);
  const slicers = useMemo(() => data?.slicers || [], [data]);

  // ALL widgets from backend - FULLY DYNAMIC!
  const allWidgets = useMemo(() => data?.dashboardLayout?.widgets || [], [data]);
  const validSlicers = useMemo(() => slicers.filter((s: any) => s.options?.length > 0), [slicers]);

  const activeFilterCount = Object.values(activeFilters).filter(v => v && v !== 'all').length;
  const pendingFilterCount = Object.values(pendingFilters).filter(v => v && v !== 'all').length;

  const handleFilterChange = useCallback((name: string, value: string) => {
    setPendingFilters(prev => {
      const newFilters = { ...prev };
      if (value === 'all') delete newFilters[name];
      else newFilters[name] = value;
      return newFilters;
    });
  }, []);

  const applyFilters = useCallback(() => {
    setActiveFilters(pendingFilters);
    loadData(pendingFilters, true);
  }, [pendingFilters, loadData]);

  const clearAllFilters = useCallback(() => {
    setActiveFilters({});
    setPendingFilters({});
    loadData({}, true);
  }, [loadData]);

  const colors = COLOR_PALETTES[0];

  // Loading State
  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: theme.bg }}>
        <Loader className="w-8 h-8 animate-spin" style={{ color: '#3B82F6' }} />
      </div>
    );
  }

  // Empty State
  if (!data?.hasData) {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-8" style={{ background: theme.bg }}>
        <div className="rounded-2xl p-12 text-center max-w-md" style={{ background: theme.cardBg, border: `1px solid ${theme.border}`, boxShadow: theme.shadow }}>
          <Upload className="w-16 h-16 mx-auto mb-6" style={{ color: theme.textMuted }} />
          <h2 className="text-2xl font-bold mb-3" style={{ color: theme.text }}>No Data Yet</h2>
          <p className="text-sm mb-8" style={{ color: theme.textMuted }}>Upload CSV or Excel files in Data Hub to generate analytics.</p>
          <Link to="/datahub" className="inline-block px-8 py-3 rounded-lg text-white font-semibold" style={{ background: '#3B82F6' }}>Go to Data Hub</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: theme.bg }}>
      {/* HEADER */}
      <div className="sticky top-0 z-40 border-b backdrop-blur-xl" style={{ background: isDark ? 'rgba(15,23,42,0.95)' : 'rgba(255,255,255,0.95)', borderColor: theme.border }}>
        <div className="w-full px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg" style={{ background: `${colors[0]}20`, color: colors[0] }}>
              {getDomainIcon(domain)}
            </div>
            <div>
              <h1 className="text-lg font-bold" style={{ color: theme.text }}>{domain} Dashboard</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium" style={{ color: theme.text }}>{fmt(dataShape.rows)} Records</span>
            <span className="text-sm" style={{ color: theme.textMuted }}>All Data</span>
            <button onClick={() => loadData(activeFilters, true)} className="p-2 rounded-lg hover:bg-white/10 transition-colors" disabled={refreshing}>
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} style={{ color: theme.textMuted }} />
            </button>
            <Link to="/overview" className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-500 text-white flex items-center gap-2 hover:bg-blue-600 transition-colors">
              <LayoutGrid className="w-4 h-4" />
              Overview
            </Link>
          </div>
        </div>
      </div>

      {/* FILTER BAR */}
      {validSlicers.length > 0 && (
        <div className="sticky top-14 z-30 border-b" style={{ background: theme.filterBg, borderColor: theme.border }}>
          <div className="w-full px-6 py-3">
            <div className="flex items-center gap-4 flex-wrap">
              <Filter className="w-4 h-4" style={{ color: theme.textMuted }} />
              {validSlicers.slice(0, 4).map((slicer: any) => (
                <FilterDropdown
                  key={slicer.name}
                  label={slicer.label}
                  options={slicer.options}
                  value={pendingFilters[slicer.name] || 'all'}
                  onChange={(val) => handleFilterChange(slicer.name, val)}
                  theme={theme}
                />
              ))}
              <button
                onClick={applyFilters}
                disabled={pendingFilterCount === 0}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${pendingFilterCount > 0 ? 'bg-blue-500 hover:bg-blue-600 text-white' : 'bg-gray-500/30 text-gray-400 cursor-not-allowed'}`}
              >
                <Check className="w-4 h-4" />
                Apply Filters
              </button>
              {activeFilterCount > 0 && (
                <button onClick={clearAllFilters} className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10 transition-all">
                  <X className="w-4 h-4" />
                  Clear All
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="w-full p-4 space-y-4">

        {/* KPI CARDS */}
        {kpis.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {kpis.slice(0, 4).map((kpi: any, i: number) => (
              <KpiCard key={i} kpi={kpi} index={i} theme={theme} isDark={isDark} />
            ))}
          </div>
        )}

        {/* DYNAMIC WIDGETS GRID - Renders ALL widgets from backend! */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {allWidgets.map((widget: any, i: number) => (
            <DynamicWidget
              key={`${widget.type}-${i}`}
              widget={widget}
              theme={theme}
              colors={colors}
              index={i}
              isDark={isDark}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-[10px] pt-2" style={{ color: theme.textMuted }}>
          <span>📊 {fmt(dataShape.rows)} records • {activeFilterCount > 0 ? `${activeFilterCount} filter(s) applied` : 'No filters'}</span>
          <div className="flex items-center gap-1">
            <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Updated: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboards;
