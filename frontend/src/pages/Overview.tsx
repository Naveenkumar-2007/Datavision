import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { RefreshCw, Loader, Upload, TrendingUp, TrendingDown, ChevronRight, Lightbulb, Globe, Clock, BarChart3, GraduationCap, Users, ShoppingCart, Heart, Factory, Store, Briefcase, Trophy, Activity, Database, Layers, Target, Hash, CheckCircle, AlertCircle, Zap } from 'lucide-react';
import { apiService } from '@/services/api';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, LineChart, Line } from 'recharts';

// ===========================================================================
// POWER BI OVERVIEW PAGE v6.0 - RICH FEATURES
// Shows: KPIs, Donut, Funnel, Gauge, Progress Bars, Metric Cards, Data Quality
// ALL charts are DYNAMIC based on data support!
// ===========================================================================

interface ThemeContext { isDark: boolean; }

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

const COLORS = ['#3B82F6', '#22C55E', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4', '#EF4444', '#14B8A6'];

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
// DYNAMIC CHART RENDERER FOR OVERVIEW
// ============================================
const OverviewChart: React.FC<{ chart: any; index: number; theme: any; isDark: boolean }> = ({ chart, index, theme, isDark }) => {
  const colors = COLORS;

  switch (chart.type) {
    case 'donut':
      const donutData = chart.data?.data || [];
      if (!donutData.length) return null;
      const total = donutData.reduce((a: number, b: any) => a + (b.value || 0), 0);
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-1" style={{ color: theme.text }}>{chart.title}</h3>
          <p className="text-[10px] mb-3" style={{ color: theme.textMuted }}>Category distribution</p>
          <div className="h-48 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={donutData} cx="40%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={2} dataKey="value">
                  {donutData.map((entry: any, idx: number) => <Cell key={idx} fill={entry.color || colors[idx % 8]} stroke="none" />)}
                </Pie>
                <Legend layout="vertical" align="right" verticalAlign="middle" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 10 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute left-[28%] top-1/2 -translate-y-1/2 text-center">
              <p className="text-xl font-black" style={{ color: colors[0] }}>{Math.round((donutData[0]?.value / total) * 100)}%</p>
              <p className="text-[9px]" style={{ color: theme.textMuted }}>{donutData[0]?.name?.substring(0, 10)}</p>
            </div>
          </div>
        </motion.div>
      );

    case 'funnel':
      const funnelData = chart.data || [];
      if (!funnelData.length) return null;
      const maxFunnel = funnelData[0]?.value || 1;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-2">
            {funnelData.map((item: any, i: number) => (
              <div key={i} className="relative">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium" style={{ color: theme.text }}>{item.name}</span>
                  <span className="text-xs font-bold" style={{ color: item.color }}>{fmt(item.value)}</span>
                </div>
                <div className="h-6 rounded-md overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0', width: `${70 + (30 * (funnelData.length - i) / funnelData.length)}%`, margin: '0 auto' }}>
                  <div className="h-full rounded-md transition-all" style={{ width: `${(item.value / maxFunnel) * 100}%`, background: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'gauge':
      const gaugeData = chart.data || {};
      const percent = gaugeData.percent || 0;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="relative h-32 flex items-center justify-center">
            <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke={isDark ? '#334155' : '#E2E8F0'} strokeWidth="12" />
              <circle cx="60" cy="60" r="50" fill="none" stroke={colors[0]} strokeWidth="12" strokeLinecap="round"
                strokeDasharray={`${percent * 3.14} 314`} className="transition-all duration-700" />
            </svg>
            <div className="absolute text-center">
              <p className="text-2xl font-black" style={{ color: theme.text }}>{fmt(gaugeData.value)}</p>
              <p className="text-[9px]" style={{ color: theme.textMuted }}>{percent.toFixed(0)}%</p>
            </div>
          </div>
          <div className="flex justify-between text-[9px] mt-2" style={{ color: theme.textMuted }}>
            <span>Min: {fmt(gaugeData.min)}</span>
            <span>Target: {fmt(gaugeData.target)}</span>
            <span>Max: {fmt(gaugeData.max)}</span>
          </div>
        </motion.div>
      );

    case 'top_performers':
      const topData = chart.data || [];
      if (!topData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-1" style={{ color: theme.text }}>{chart.title}</h3>
          <p className="text-[10px] mb-3" style={{ color: theme.textMuted }}>By {chart.metricName || 'Value'}</p>
          <div className="space-y-2">
            {topData.slice(0, 5).map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ background: colors[i % 8] }}>{i + 1}</div>
                  <span className="text-xs" style={{ color: theme.text }}>{item.name?.substring(0, 18) || item.category?.substring(0, 18)}</span>
                </div>
                <span className="text-xs font-bold" style={{ color: colors[i % 8] }}>{fmt(item.value)}</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'progress_bars':
      const progData = chart.data || [];
      if (!progData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-3">
            {progData.slice(0, 5).map((item: any, i: number) => (
              <div key={i}>
                <div className="flex justify-between mb-1">
                  <span className="text-xs" style={{ color: theme.text }}>{item.name?.substring(0, 15)}</span>
                  <span className="text-xs font-bold" style={{ color: item.color }}>{fmt(item.value)}</span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  <div className="h-full rounded-full transition-all" style={{ width: `${item.percent}%`, background: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'metric_cards':
      const metricData = chart.data || [];
      if (!metricData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {metricData.map((item: any, i: number) => (
              <div key={i} className="p-3 rounded-lg text-center" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <p className="text-lg font-black" style={{ color: item.color }}>{fmt(item.value)}</p>
                <p className="text-[9px] font-medium" style={{ color: theme.textMuted }}>{item.name}</p>
                <div className="flex items-center justify-center gap-1 mt-1">
                  {item.change > 0 ? <TrendingUp className="w-3 h-3 text-green-500" /> : <TrendingDown className="w-3 h-3 text-red-500" />}
                  <span className={`text-[9px] ${item.change > 0 ? 'text-green-500' : 'text-red-500'}`}>{item.change > 0 ? '+' : ''}{item.change}%</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'data_quality':
      const qualityData = chart.data || [];
      if (!qualityData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-2">
            {qualityData.slice(0, 5).map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {item.completeness >= 90 ? <CheckCircle className="w-4 h-4 text-green-500" /> : <AlertCircle className="w-4 h-4 text-amber-500" />}
                  <span className="text-xs" style={{ color: theme.text }}>{item.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: isDark ? '#0F172A' : '#F1F5F9', color: theme.textMuted }}>{item.type}</span>
                  <span className="text-xs font-bold" style={{ color: item.completeness >= 90 ? '#22C55E' : '#F59E0B' }}>{item.completeness}%</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'sparkline':
      const sparkData = chart.data || [];
      if (!sparkData.length) return null;
      const chartData = sparkData.map((v: number, i: number) => ({ x: i, y: v }));
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold" style={{ color: theme.text }}>{chart.title}</h3>
            <div className="flex items-center gap-1">
              <Zap className="w-4 h-4" style={{ color: chart.change > 0 ? '#22C55E' : '#EF4444' }} />
              <span className={`text-xs font-bold ${chart.change > 0 ? 'text-green-500' : 'text-red-500'}`}>{chart.trend} {Math.abs(chart.change)}%</span>
            </div>
          </div>
          <div className="h-16">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <Line type="monotone" dataKey="y" stroke={chart.change > 0 ? '#22C55E' : '#EF4444'} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      );

    case 'treemap':
      const treemapItems = chart.data || [];
      if (!treemapItems.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="grid grid-cols-3 gap-1">
            {treemapItems.slice(0, 9).map((item: any, i: number) => (
              <div key={i} className="rounded-lg p-2 flex flex-col items-center justify-center text-center transition-transform hover:scale-105"
                style={{ background: item.color || colors[i % 8], minHeight: `${Math.max(40, item.area || 50)}px` }}>
                <span className="text-white text-[9px] font-bold">{item.name}</span>
                <span className="text-white/80 text-[8px]">{item.percentage}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'comparison':
      const compData = chart.data || {};
      const topItems = compData.top || [];
      const bottomItems = compData.bottom || [];
      if (!topItems.length && !bottomItems.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="text-[9px] font-bold uppercase text-green-500">Top Performers</p>
              {topItems.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 rounded" style={{ background: isDark ? '#064E3B' : '#D1FAE5' }}>
                  <span className="text-xs font-medium" style={{ color: theme.text }}>{item.name}</span>
                  <span className="text-xs font-bold text-green-600">{fmt(item.value)}</span>
                </div>
              ))}
            </div>
            <div className="border-t pt-2" style={{ borderColor: theme.cardBorder }}>
              <p className="text-[9px] font-bold uppercase text-red-500 mb-1">Bottom Performers</p>
              {bottomItems.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 rounded" style={{ background: isDark ? '#7F1D1D' : '#FEE2E2' }}>
                  <span className="text-xs font-medium" style={{ color: theme.text }}>{item.name}</span>
                  <span className="text-xs font-bold text-red-600">{fmt(item.value)}</span>
                </div>
              ))}
            </div>
            {compData.gap > 0 && (
              <div className="text-center pt-2">
                <span className="text-[9px]" style={{ color: theme.textMuted }}>Performance Gap: </span>
                <span className="text-xs font-bold" style={{ color: '#3B82F6' }}>{fmt(compData.gap)}</span>
              </div>
            )}
          </div>
        </motion.div>
      );

    case 'waterfall':
      const wfData = chart.data || [];
      if (!wfData.length) return null;
      const wfMax = Math.max(...wfData.map((d: any) => d.end || d.value || 0));
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-2">
            {wfData.map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] w-20 truncate" style={{ color: theme.text }}>{item.name}</span>
                <div className="flex-1 h-5 rounded overflow-hidden relative" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  <div className="absolute h-full rounded transition-all" style={{
                    left: item.isTotal ? 0 : `${(item.start / wfMax) * 100}%`,
                    width: `${((item.isTotal ? item.end : item.value) / wfMax) * 100}%`,
                    background: item.color || (item.isTotal ? '#3B82F6' : colors[i % 8])
                  }} />
                </div>
                <span className="text-[10px] font-bold w-12 text-right" style={{ color: item.color }}>{fmt(item.value)}</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'heatmap':
      const heatData = chart.data || [];
      if (!heatData.length) return null;
      const rows = [...new Set(heatData.map((d: any) => d.row))] as string[];
      const cols = [...new Set(heatData.map((d: any) => d.col))] as string[];
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="overflow-auto">
            <div className="grid gap-1" style={{ gridTemplateColumns: `80px repeat(${cols.length}, 1fr)` }}>
              <div></div>
              {cols.slice(0, 5).map((col, i) => (
                <div key={i} className="text-[9px] text-center font-medium truncate" style={{ color: theme.textMuted }}>{col}</div>
              ))}
              {rows.slice(0, 5).map((row, ri) => (
                <React.Fragment key={ri}>
                  <div className="text-[9px] font-medium truncate flex items-center" style={{ color: theme.text }}>{row}</div>
                  {cols.slice(0, 5).map((col, ci) => {
                    const cell = heatData.find((d: any) => d.row === row && d.col === col);
                    return (
                      <div key={ci} className="h-8 rounded flex items-center justify-center text-[9px] font-bold"
                        style={{ background: cell?.color || '#E2E8F0', color: cell?.intensity > 4 ? 'white' : '#1E293B' }}>
                        {cell ? fmt(cell.value) : '-'}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        </motion.div>
      );

    case 'sparklines_grid':
      const sparkGridData = chart.data || [];
      if (!sparkGridData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {sparkGridData.slice(0, 6).map((item: any, i: number) => {
              const points = item.points || [];
              const max = Math.max(...points);
              const min = Math.min(...points);
              const range = max - min || 1;
              return (
                <div key={i} className="p-2 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-medium truncate" style={{ color: theme.text }}>{item.name}</span>
                    <span className={`text-[9px] font-bold ${item.isUp ? 'text-green-500' : 'text-red-500'}`}>
                      {item.isUp ? '↑' : '↓'}{Math.abs(item.change)}%
                    </span>
                  </div>
                  <svg className="w-full h-8" viewBox={`0 0 ${points.length * 10} 30`}>
                    <polyline fill="none" stroke={item.color || colors[i % 8]} strokeWidth="2"
                      points={points.map((p: number, j: number) => `${j * 10},${30 - ((p - min) / range) * 28}`).join(' ')} />
                  </svg>
                </div>
              );
            })}
          </div>
        </motion.div>
      );

    case 'ring_progress':
      const ringData = chart.data || [];
      if (!ringData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {ringData.slice(0, 4).map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <div className="relative w-12 h-12">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="16" fill="none" stroke={isDark ? '#334155' : '#E2E8F0'} strokeWidth="4" />
                    <circle cx="20" cy="20" r="16" fill="none" stroke={item.color} strokeWidth="4" strokeLinecap="round"
                      strokeDasharray={`${item.percentage} 100`} />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold" style={{ color: item.color }}>{item.percentage}%</span>
                </div>
                <div>
                  <p className="text-[10px] font-medium truncate" style={{ color: theme.text }}>{item.name}</p>
                  <p className="text-[9px]" style={{ color: theme.textMuted }}>{fmt(item.value)}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'top_n_table':
      const tableItems = chart.data || [];
      if (!tableItems.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-2">
            {tableItems.slice(0, 8).map((item: any, i: number) => (
              <div key={i} className="flex items-center gap-2 p-2 rounded" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-bold" style={{ background: item.color }}>
                  {item.rank}
                </div>
                <span className="flex-1 text-[11px] font-medium truncate" style={{ color: theme.text }}>{item.name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded font-bold" style={{ background: item.gradeColor + '20', color: item.gradeColor }}>
                  {item.grade}
                </span>
                <span className="text-[10px] font-bold" style={{ color: item.color }}>{item.percentage}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'distribution':
      const distData = chart.data || [];
      if (!distData.length) return null;
      const distMax = Math.max(...distData.map((d: any) => d.count || 0));
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="flex items-end gap-1 h-24">
            {distData.map((item: any, i: number) => (
              <div key={i} className="flex-1 flex flex-col items-center">
                <div className="w-full rounded-t transition-all hover:opacity-80" style={{
                  height: `${(item.count / distMax) * 100}%`,
                  minHeight: '4px',
                  background: item.color || colors[i % 8]
                }} />
                <span className="text-[8px] mt-1 text-center" style={{ color: theme.textMuted }}>{item.range}</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'bubble':
      const bubbleData = chart.data || [];
      if (!bubbleData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="flex flex-wrap gap-2 justify-center">
            {bubbleData.slice(0, 8).map((item: any, i: number) => (
              <div key={i} className="rounded-full flex items-center justify-center text-white text-[9px] font-bold transition-transform hover:scale-110 cursor-pointer"
                style={{ width: `${item.size}px`, height: `${item.size}px`, background: item.color || colors[i % 8] }}>
                {item.name?.substring(0, 4)}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-[9px]" style={{ color: theme.textMuted }}>
            <span>{chart.xLabel}</span>
            <span>{chart.yLabel}</span>
          </div>
        </motion.div>
      );

    // =====================================================
    // NEW ADVANCED CHART TYPES
    // =====================================================

    case 'box_plot':
      const boxData = chart.data || [];
      if (!boxData.length) return null;
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-1" style={{ color: theme.text }}>{chart.title}</h3>
          <p className="text-[10px] mb-3" style={{ color: theme.textMuted }}>{chart.xLabel} distribution</p>
          <div className="space-y-2">
            {boxData.map((box: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] w-16 truncate" style={{ color: theme.text }}>{box.category}</span>
                <div className="flex-1 relative h-6" style={{ background: isDark ? '#334155' : '#E2E8F0' }}>
                  {/* Min-Max range bar */}
                  <div className="absolute h-full" style={{
                    left: `${((box.min - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity)) / (boxData.reduce((max: number, b: any) => Math.max(max, b.max), -Infinity) - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity))) * 100}%`,
                    width: `${((box.max - box.min) / (boxData.reduce((max: number, b: any) => Math.max(max, b.max), -Infinity) - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity))) * 100}%`,
                    background: `${box.color}20`,
                    borderLeft: `2px solid ${box.color}`,
                    borderRight: `2px solid ${box.color}`
                  }} />
                  {/* IQR box */}
                  <div className="absolute h-full" style={{
                    left: `${((box.q1 - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity)) / (boxData.reduce((max: number, b: any) => Math.max(max, b.max), -Infinity) - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity))) * 100}%`,
                    width: `${((box.q3 - box.q1) / (boxData.reduce((max: number, b: any) => Math.max(max, b.max), -Infinity) - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity))) * 100}%`,
                    background: box.color
                  }} />
                  {/* Median line */}
                  <div className="absolute w-0.5 h-full bg-white" style={{
                    left: `${((box.median - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity)) / (boxData.reduce((max: number, b: any) => Math.max(max, b.max), -Infinity) - boxData.reduce((min: number, b: any) => Math.min(min, b.min), Infinity))) * 100}%`
                  }} />
                </div>
                <span className="text-[9px] font-bold w-12 text-right" style={{ color: box.color }}>{fmt(box.median)}</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'sankey':
      const sankeyFlows = chart.data || [];
      if (!sankeyFlows.length) return null;
      // Simple sankey visualization (source → target with width based on value)
      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="space-y-1.5">
            {sankeyFlows.slice(0, 10).map((flow: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[9px] w-20 truncate" style={{ color: theme.text }}>{flow.source}</span>
                <div className="flex-1 h-4 rounded-full" style={{ background: flow.color || colors[i % 8], width: `${Math.min(100, (flow.value / Math.max(...sankeyFlows.map((f: any) => f.value))) * 100)}%` }} />
                <span className="text-[9px] w-20 truncate text-right" style={{ color: theme.text }}>{flow.target}</span>
                <span className="text-[9px] font-bold w-10 text-right" style={{ color: flow.color }}>{fmt(flow.value)}</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'calendar_heatmap':
      const calendarData = chart.data || [];
      if (!calendarData.length) return null;
      // Group by month for compact view
      const monthlyData = calendarData.reduce((acc: any, day: any) => {
        const month = day.date.substring(0, 7); // YYYY-MM
        if (!acc[month]) acc[month] = [];
        acc[month].push(day);
        return acc;
      }, {});

      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
          <div className="grid grid-cols-7 gap-1">
            {calendarData.slice(0, 49).map((day: any, i: number) => (
              <div key={i}
                className="w-full h-6 rounded-sm flex items-center justify-center transition-transform hover:scale-110 cursor-pointer"
                style={{ background: day.color || colors[day.intensity % 8] }}
                title={`${day.date}: ${fmt(day.value)}`}>
                <span className="text-[7px] font-bold text-white">{new Date(day.date).getDate()}</span>
              </div>
            ))}
          </div>
        </motion.div>
      );

    case 'correlation_matrix':
      const corrData = chart.data || [];
      const metrics = chart.metrics || [];
      if (!corrData.length || !metrics.length) return null;

      return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
          <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>{chart.title}</h3>
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
        </motion.div>
      );

    default:
      return null;
  }
};

// ============================================
// KPI CARD
// ============================================
const KpiCard: React.FC<{ kpi: any; index: number; theme: any }> = ({ kpi, index, theme }) => {
  const delta = kpi.delta ?? kpi.change;
  const isPositive = delta > 0;
  const kpiColor = kpi.color || COLORS[index % 8];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className="rounded-xl p-5 border" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
      <p className="text-[10px] uppercase font-bold tracking-widest mb-2" style={{ color: kpiColor }}>{kpi.title}</p>
      <p className="text-4xl font-black tracking-tight mb-2" style={{ color: theme.text }}>{fmt(kpi.value)}</p>
      <div className="flex items-center gap-1.5">
        {isPositive ? <TrendingUp className="w-4 h-4 text-green-500" /> : <TrendingDown className="w-4 h-4 text-red-500" />}
        <span className={`text-xs font-semibold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>{isPositive ? '+' : ''}{delta?.toFixed(1)}%</span>
        <span className="text-[10px] ml-1" style={{ color: theme.textMuted }}>vs last period</span>
      </div>
    </motion.div>
  );
};

// ============================================
// MAIN OVERVIEW COMPONENT
// ============================================
const Overview: React.FC = () => {
  const context = useOutletContext<ThemeContext>();
  const isDark = context?.isDark ?? false;

  const theme = useMemo(() => ({
    bg: isDark ? '#0F172A' : 'linear-gradient(180deg, #E8F4FD 0%, #F0F7FF 100%)',
    cardBg: isDark ? '#1E293B' : '#FFFFFF',
    cardBorder: isDark ? '#334155' : '#E2E8F0',
    text: isDark ? '#F8FAFC' : '#1E293B',
    textSecondary: isDark ? '#CBD5E1' : '#475569',
    textMuted: isDark ? '#94A3B8' : '#64748B',
    shadow: isDark ? '0 4px 6px -1px rgba(0,0,0,0.3)' : '0 2px 8px rgba(0,0,0,0.08)',
    headerBg: isDark ? '#1E293B' : '#FFFFFF',
  }), [isDark]);

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      const cacheBuster = isRefresh ? `?_t=${Date.now()}` : '';
      const response = await apiService.getUnifiedAnalytics(cacheBuster);
      setAnalytics(response.data);
      if (isRefresh) setRefreshKey(prev => prev + 1);
    } catch (err) {
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const handleUpdate = () => loadData(true);
    window.addEventListener('filesUpdated', handleUpdate);
    return () => window.removeEventListener('filesUpdated', handleUpdate);
  }, [loadData]);

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: theme.bg }}>
        <div className="text-center">
          <Loader className="w-10 h-10 animate-spin mx-auto mb-4" style={{ color: '#3B82F6' }} />
          <p style={{ color: theme.textMuted }}>Analyzing your data...</p>
        </div>
      </div>
    );
  }

  if (!analytics?.hasData) {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-8" style={{ background: theme.bg }}>
        <div className="rounded-2xl p-12 text-center max-w-md" style={{ background: theme.cardBg, border: `1px solid ${theme.cardBorder}`, boxShadow: theme.shadow }}>
          <Upload className="w-16 h-16 mx-auto mb-6" style={{ color: theme.textMuted }} />
          <h2 className="text-2xl font-bold mb-3" style={{ color: theme.text }}>No Data Yet</h2>
          <p className="text-sm mb-8" style={{ color: theme.textMuted }}>Upload CSV or Excel files in Data Hub to generate analytics.</p>
          <Link to="/datahub" className="inline-block px-8 py-3 rounded-lg text-white font-semibold" style={{ background: '#3B82F6' }}>Go to Data Hub</Link>
        </div>
      </div>
    );
  }

  const { overviewLayout, dataShape, domain, palette } = analytics;
  const { kpis = [], charts = [], columnBreakdown = [], aiInsight, quickStats } = overviewLayout || {};
  const accentColor = palette?.accent || '#3B82F6';
  const validKpis = kpis.filter((k: any) => k.value !== null && k.value !== undefined);

  // Split charts into rows dynamically
  const row1Charts = charts.slice(0, 2);
  const row2Charts = charts.slice(2, 5);
  const row3Charts = charts.slice(5);

  return (
    <div className="min-h-screen" style={{ background: theme.bg }} key={refreshKey}>

      {/* HEADER BAR */}
      <div className="border-b" style={{ background: theme.headerBg, borderColor: theme.cardBorder }}>
        <div className="w-full px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: accentColor + '20', color: accentColor }}>
                {getDomainIcon(domain)}
              </div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold" style={{ color: theme.text }}>{domain || 'Business'} Analytics</h1>
                <span style={{ color: theme.textMuted }}>|</span>
                <span className="text-base" style={{ color: theme.textSecondary }}>Overview</span>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm" style={{ color: theme.textMuted }}>
                <Clock className="w-4 h-4" />
                <span>All Data</span>
                <span className="mx-1">|</span>
                <span className="font-semibold" style={{ color: theme.text }}>{fmt(dataShape?.rows)} Records</span>
              </div>
              <button onClick={() => loadData(true)} disabled={refreshing} className="p-2 rounded-lg border hover:bg-opacity-80 transition-all" style={{ borderColor: theme.cardBorder }}>
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} style={{ color: theme.textMuted }} />
              </button>
              <Link to="/dashboards" className="flex items-center gap-2 px-4 py-2 rounded-lg text-white font-semibold text-sm transition-all hover:opacity-90" style={{ background: accentColor }}>
                <BarChart3 className="w-4 h-4" />
                Dashboards
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="w-full px-6 py-6 space-y-6">

        {/* KPI Cards */}
        {validKpis.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {validKpis.slice(0, 4).map((kpi: any, i: number) => (
              <KpiCard key={i} kpi={kpi} index={i} theme={theme} />
            ))}
          </div>
        )}

        {/* Row 1: First 2 charts */}
        {row1Charts.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {row1Charts.map((chart: any, i: number) => (
              <OverviewChart key={`r1-${i}`} chart={chart} index={i} theme={theme} isDark={isDark} />
            ))}
          </div>
        )}

        {/* Row 2: Next 3 charts */}
        {row2Charts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {row2Charts.map((chart: any, i: number) => (
              <OverviewChart key={`r2-${i}`} chart={chart} index={i + 2} theme={theme} isDark={isDark} />
            ))}
          </div>
        )}

        {/* Row 3: Remaining charts + Quick Stats + AI Insight */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {row3Charts.map((chart: any, i: number) => (
            <OverviewChart key={`r3-${i}`} chart={chart} index={i + 5} theme={theme} isDark={isDark} />
          ))}

          {/* Quick Stats */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="rounded-xl border p-5" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
            <h3 className="text-sm font-bold mb-4" style={{ color: theme.text }}>Data Summary</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <Database className="w-5 h-5 mx-auto mb-1" style={{ color: COLORS[0] }} />
                <p className="text-xl font-black" style={{ color: theme.text }}>{fmt(quickStats?.records || 0)}</p>
                <p className="text-[9px] uppercase font-semibold" style={{ color: theme.textMuted }}>Records</p>
              </div>
              <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <Layers className="w-5 h-5 mx-auto mb-1" style={{ color: COLORS[1] }} />
                <p className="text-xl font-black" style={{ color: theme.text }}>{quickStats?.columns || 0}</p>
                <p className="text-[9px] uppercase font-semibold" style={{ color: theme.textMuted }}>Columns</p>
              </div>
              <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <Target className="w-5 h-5 mx-auto mb-1" style={{ color: COLORS[2] }} />
                <p className="text-xl font-black" style={{ color: theme.text }}>{quickStats?.metrics || 0}</p>
                <p className="text-[9px] uppercase font-semibold" style={{ color: theme.textMuted }}>Metrics</p>
              </div>
              <div className="text-center p-3 rounded-lg" style={{ background: isDark ? '#0F172A' : '#F8FAFC' }}>
                <Hash className="w-5 h-5 mx-auto mb-1" style={{ color: COLORS[3] }} />
                <p className="text-xl font-black" style={{ color: theme.text }}>{quickStats?.dimensions || 0}</p>
                <p className="text-[9px] uppercase font-semibold" style={{ color: theme.textMuted }}>Dimensions</p>
              </div>
            </div>
          </motion.div>

          {/* AI Insight */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="rounded-xl border p-5 flex flex-col" style={{ background: theme.cardBg, borderColor: theme.cardBorder, boxShadow: theme.shadow }}>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5" style={{ color: '#F59E0B' }} />
              <h3 className="text-sm font-bold" style={{ color: theme.text }}>AI Insight</h3>
            </div>
            <p className="text-sm flex-1" style={{ color: theme.textSecondary }}>{aiInsight || 'Upload data to get insights.'}</p>
            <Link to="/dashboards" className="mt-4 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all hover:opacity-90" style={{ background: accentColor, color: 'white' }}>
              <BarChart3 className="w-4 h-4" />
              View Full Dashboard
              <ChevronRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </div>

      </div>
    </div>
  );
};

export default Overview;
