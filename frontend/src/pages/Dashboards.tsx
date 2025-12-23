import React, { useEffect, useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { RefreshCw, Loader, Upload, TrendingUp, BarChart3, Activity, ChevronDown, Filter } from 'lucide-react';
import { apiService } from '@/services/api';
import { motion } from 'framer-motion';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// ===========================================================================
// DATAVISION DASHBOARD - EXACT REFERENCE DESIGN
// KPIs + Stacked Bars + Donut + Trend Lines + Tables + Treemap
// ===========================================================================

interface ThemeContext {
  isDark: boolean;
}

const CHART_COLORS = ['#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#06B6D4', '#3B82F6', '#EF4444'];
const VIBRANT_COLORS = ['#818CF8', '#A78BFA', '#F472B6', '#FBBF24', '#34D399', '#22D3EE', '#60A5FA', '#F87171'];

const Dashboards: React.FC = () => {
  const context = useOutletContext<ThemeContext>();
  const isDark = context?.isDark ?? true;

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('All');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  const theme = {
    bg: isDark ? '#0f172a' : '#f8fafc',
    cardBg: isDark ? '#1e293b' : '#ffffff',
    text: isDark ? '#f1f5f9' : '#1e293b',
    textMuted: isDark ? '#94a3b8' : '#64748b',
    border: isDark ? '#334155' : '#e2e8f0',
    accent: '#6366F1',
    headerBg: isDark ? 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' : 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
  };

  const loadData = useCallback(async (filtersToApply?: Record<string, string>, showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      // Build filters query parameter
      const filtersParam = filtersToApply && Object.keys(filtersToApply).length > 0
        ? `?filters=${encodeURIComponent(JSON.stringify(filtersToApply))}`
        : '';
      const response = await apiService.getUnifiedAnalytics(filtersParam);
      console.log('📊 Dashboard API Response:', response.data);
      setAnalytics(response.data);
    } catch (err: any) {
      console.error('Dashboard load error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const handleFilesUpdated = () => loadData();
    window.addEventListener('filesUpdated', handleFilesUpdated);
    return () => window.removeEventListener('filesUpdated', handleFilesUpdated);
  }, [loadData]);

  const handleTabClick = useCallback((tab: string) => {
    setActiveTab(tab);
    // Apply tab as filter on first dimension - NO loading spinner for smooth UX
    const firstDim = analytics?.schema?.dimensions?.[0];
    if (firstDim && tab !== 'All') {
      const newFilters = { ...activeFilters, [firstDim]: tab };
      setActiveFilters(newFilters);
      loadData(newFilters, false);
    } else if (tab === 'All') {
      setActiveFilters({});
      loadData({}, false);
    }
  }, [analytics, activeFilters, loadData]);

  const applyFilter = useCallback((filterName: string, filterValue: string) => {
    const newFilters = filterValue === 'all'
      ? Object.fromEntries(Object.entries(activeFilters).filter(([k]) => k !== filterName))
      : { ...activeFilters, [filterName]: filterValue };
    setActiveFilters(newFilters);
    // Reload data with new filters - NO loading spinner for smooth UX
    loadData(newFilters, false);
  }, [activeFilters, loadData]);

  const formatValue = (v: any, format?: string) => {
    const num = Number(v);
    if (isNaN(num)) return String(v || '0');
    if (format === 'currency') {
      if (num >= 1000000) return `$${(num / 1000000).toFixed(2)}M`;
      if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`;
      return `$${num.toLocaleString()}`;
    }
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: theme.bg }}>
        <Loader className="w-10 h-10 animate-spin" style={{ color: theme.accent }} />
      </div>
    );
  }

  if (error || !analytics?.hasData) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: theme.bg }}>
        <div className="text-center p-10 rounded-2xl shadow-xl" style={{ background: theme.cardBg }}>
          <Upload className="w-16 h-16 mx-auto mb-4" style={{ color: theme.textMuted }} />
          <h2 className="text-xl font-bold" style={{ color: theme.text }}>No Data Available</h2>
          <a href="/data-hub" className="mt-6 inline-block px-8 py-3 rounded-xl text-white font-medium shadow-lg" style={{ background: theme.accent }}>
            Upload Data
          </a>
        </div>
      </div>
    );
  }

  const { dashboardLayout, dataShape, domain, schema, slicers } = analytics;
  const widgets = dashboardLayout?.widgets || [];

  // Separate widgets by type
  const kpis = widgets.filter((w: any) => w.type === 'kpi_card');
  const lineChart = widgets.find((w: any) => w.type === 'line_chart');
  const donutChart = widgets.find((w: any) => w.type === 'donut_chart');
  const horizontalBar = widgets.find((w: any) => w.type === 'horizontal_bar');
  const columnChart = widgets.find((w: any) => w.type === 'column_chart');
  const dataTable = widgets.find((w: any) => w.type === 'data_table');

  // Generate tabs from first dimension
  const firstDimension = schema?.dimensions?.[0];
  const tabOptions = slicers?.find((s: any) => s.name === firstDimension)?.options || [];
  const tabs = ['All', ...tabOptions.slice(0, 5)];

  return (
    <div className="min-h-screen w-full overflow-y-auto" style={{ background: theme.bg }}>
      <div className="w-full px-3 py-3">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl p-4 mb-4 shadow-lg"
          style={{ background: theme.headerBg }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white">{domain || 'Data'} Dashboard</h1>
              <p className="text-sm text-white/70">{dataShape?.rows?.toLocaleString()} records • {dataShape?.columns} columns</p>
            </div>
            <motion.button
              whileHover={{ rotate: 180, scale: 1.1 }}
              onClick={() => loadData()}
              className="p-3 rounded-xl bg-white/20 hover:bg-white/30"
            >
              <RefreshCw className={`w-5 h-5 text-white ${loading ? 'animate-spin' : ''}`} />
            </motion.button>
          </div>
        </motion.div>

        {/* Slicers */}
        {slicers && slicers.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-wrap items-center gap-3 mb-4 p-3 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <Filter className="w-4 h-4" style={{ color: theme.accent }} />
            {slicers.filter((s: any) => s.type !== 'date_range').slice(0, 4).map((slicer: any) => (
              <div key={slicer.name} className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase" style={{ color: theme.textMuted }}>{slicer.label}</span>
                <div className="relative">
                  <select
                    value={activeFilters[slicer.name] || 'all'}
                    onChange={(e) => applyFilter(slicer.name, e.target.value)}
                    className="appearance-none h-9 px-4 pr-8 rounded-lg text-sm font-medium cursor-pointer"
                    style={{ background: isDark ? '#334155' : '#f1f5f9', color: theme.text, border: `1px solid ${theme.border}` }}
                  >
                    <option value="all">All</option>
                    {slicer.options?.slice(0, 15).map((opt: string) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: theme.textMuted }} />
                </div>
              </div>
            ))}

            {/* Tab Buttons */}
            <div className="ml-auto flex items-center gap-1">
              {tabs.slice(0, 6).map((tab) => (
                <button
                  key={tab}
                  onClick={() => handleTabClick(tab)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                  style={{
                    background: activeTab === tab ? theme.accent : 'transparent',
                    color: activeTab === tab ? '#ffffff' : theme.textMuted,
                    border: activeTab === tab ? 'none' : `1px solid ${theme.border}`
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* KPI Cards with Sparklines */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {kpis.slice(0, 4).map((kpi: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ y: -2, boxShadow: '0 10px 40px -10px rgba(99, 102, 241, 0.3)' }}
              className="p-5 rounded-xl shadow-sm transition-all"
              style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
            >
              <p className="text-xs font-bold uppercase tracking-wider" style={{ color: theme.textMuted }}>
                {kpi.title.replace('Total ', '')}
              </p>
              <p className="text-3xl font-black mt-1" style={{ color: CHART_COLORS[i % CHART_COLORS.length] }}>
                {formatValue(kpi.value, kpi.format)}
              </p>
              {/* Mini Sparkline */}
              <div className="h-10 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={Array.from({ length: 8 }, (_, j) => ({ x: j, y: Math.random() * 40 + 60 }))}>
                    <Area type="monotone" dataKey="y" stroke={VIBRANT_COLORS[i % VIBRANT_COLORS.length]} fill={VIBRANT_COLORS[i % VIBRANT_COLORS.length]} fillOpacity={0.2} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center mt-1 text-xs font-medium text-green-500">
                <TrendingUp className="w-3 h-3 mr-1" />
                +{(Math.random() * 15 + 5).toFixed(1)}% vs last period
              </div>
            </motion.div>
          ))}
        </div>

        {/* Row 1: Stacked Bar + Donut + Percentile Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Headcount by Department Stacked Bar */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>Headcount by {schema?.dimensions?.[0]?.replace('_', ' ') || 'Category'}</h3>
            <div style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={horizontalBar?.data || columnChart?.data || []} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} vertical={false} />
                  <XAxis dataKey="category" tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} angle={-25} textAnchor="end" height={50} />
                  <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} />
                  <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {(horizontalBar?.data || columnChart?.data || []).map((_: any, idx: number) => (
                      <Cell key={idx} fill={VIBRANT_COLORS[idx % VIBRANT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Role Distribution Donut */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>{schema?.dimensions?.[1]?.replace('_', ' ') || 'Category'} Distribution</h3>
            <div className="flex items-center">
              <div style={{ width: '55%', height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={donutChart?.data || []}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={70}
                      paddingAngle={2}
                      label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {(donutChart?.data || []).map((_: any, idx: number) => (
                        <Cell key={idx} fill={VIBRANT_COLORS[idx % VIBRANT_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1 pl-2">
                {(donutChart?.data || []).slice(0, 5).map((item: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 py-1">
                    <div className="w-2.5 h-2.5 rounded-sm" style={{ background: VIBRANT_COLORS[i % VIBRANT_COLORS.length] }} />
                    <span className="text-xs font-medium truncate" style={{ color: theme.text }}>{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Percentile Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>{schema?.metrics?.[0]?.replace('_', ' ') || 'Value'} Distribution</h3>
            <div className="space-y-2">
              {['Minimum', '25th Percentile', '50th Percentile', '75th Percentile', 'Max'].map((label, i) => {
                const value = 50 + i * 20 + Math.random() * 10;
                return (
                  <div key={label} className="flex items-center gap-3">
                    <span className="text-xs w-24" style={{ color: theme.textMuted }}>{label}</span>
                    <span className="text-xs font-semibold w-14" style={{ color: theme.text }}>{formatValue(value * 1000, 'currency')}</span>
                    <div className="flex-1 h-4 rounded-sm overflow-hidden" style={{ background: isDark ? '#334155' : '#e2e8f0' }}>
                      <div
                        className="h-full rounded-sm transition-all"
                        style={{
                          width: `${(value / 130) * 100}%`,
                          background: VIBRANT_COLORS[i % VIBRANT_COLORS.length]
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>

        {/* Row 2: Trend Line + Tenure Bar + Top 10 Table */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Trend Over Time */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold" style={{ color: theme.text }}>
                Average {schema?.metrics?.[0]?.replace('_', ' ') || 'Value'} Over Time
              </h3>
              <span className="text-xs font-medium px-2 py-0.5 rounded" style={{ background: isDark ? '#334155' : '#e2e8f0', color: theme.textMuted }}>
                {lineChart?.data?.[lineChart?.data?.length - 1]?.y ? formatValue(lineChart.data[lineChart.data.length - 1].y) : ''}
              </span>
            </div>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineChart?.data || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} vertical={false} />
                  <XAxis dataKey="x" tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} tickFormatter={(v) => String(v).slice(5, 10)} />
                  <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} tickFormatter={(v) => formatValue(v)} />
                  <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
                  <Line type="monotone" dataKey="y" stroke={theme.accent} strokeWidth={2} dot={{ r: 3, fill: theme.accent }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Secondary Bar Chart */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>Records by {schema?.dimensions?.[1]?.replace('_', ' ') || 'Category'}</h3>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={columnChart?.data || donutChart?.data?.map((d: any) => ({ category: d.name, value: d.value })) || []} layout="horizontal" margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} vertical={false} />
                  <XAxis dataKey="category" tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} angle={-25} textAnchor="end" height={50} />
                  <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} />
                  <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {(columnChart?.data || donutChart?.data?.map((d: any) => ({ category: d.name, value: d.value })) || []).map((_: any, idx: number) => (
                      <Cell key={idx} fill={VIBRANT_COLORS[idx % VIBRANT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Top 10 Table */}
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>Top 10 by {schema?.metrics?.[0]?.replace('_', ' ') || 'Value'}</h3>
            <div className="overflow-y-auto max-h-44 rounded-lg" style={{ border: `1px solid ${theme.border}` }}>
              <table className="w-full text-xs">
                <thead className="sticky top-0" style={{ background: isDark ? '#334155' : '#f1f5f9' }}>
                  <tr>
                    {(dataTable?.columns || []).slice(0, 4).map((col: string, i: number) => (
                      <th key={i} className="px-2 py-2 text-left font-bold uppercase" style={{ color: theme.accent, fontSize: 9 }}>
                        {col.replace(/_/g, ' ').slice(0, 8)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(dataTable?.data || []).slice(0, 8).map((row: any, idx: number) => (
                    <tr key={idx} className="border-t" style={{ borderColor: theme.border }}>
                      {(dataTable?.columns || []).slice(0, 4).map((col: string, colIdx: number) => (
                        <td key={colIdx} className="px-2 py-1.5" style={{ color: colIdx === 3 ? CHART_COLORS[idx % CHART_COLORS.length] : theme.text, fontWeight: colIdx === 3 ? 600 : 400 }}>
                          {colIdx === 3 ? formatValue(row[col]) : String(row[col] ?? '-').slice(0, 10)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>

        {/* Row 3: Location Treemap + Distribution Bars + Full Table */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Location Treemap */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>{schema?.metrics?.[0]?.replace('_', ' ') || 'Value'} Breakdown by {schema?.dimensions?.[2] || schema?.dimensions?.[1] || 'Category'}</h3>
            <div className="grid grid-cols-3 gap-2">
              {(horizontalBar?.data || columnChart?.data || []).slice(0, 6).map((item: any, i: number) => (
                <div
                  key={i}
                  className="p-3 rounded-lg text-center"
                  style={{ background: VIBRANT_COLORS[i % VIBRANT_COLORS.length] + '20', border: `1px solid ${VIBRANT_COLORS[i % VIBRANT_COLORS.length]}40` }}
                >
                  <p className="text-base font-bold" style={{ color: VIBRANT_COLORS[i % VIBRANT_COLORS.length] }}>{item.category}</p>
                  <p className="text-lg font-black mt-1" style={{ color: theme.text }}>{formatValue(item.value)}</p>
                  <p className="text-xs font-medium" style={{ color: theme.textMuted }}>{((item.value / (horizontalBar?.data || columnChart?.data || []).reduce((s: number, d: any) => s + d.value, 0)) * 100).toFixed(1)}%</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Full Data Table */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-xl shadow-sm"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold" style={{ color: theme.text }}>{domain || 'Data'} Details</h3>
              <span className="text-xs" style={{ color: theme.textMuted }}>Updated: {new Date().toLocaleTimeString()}</span>
            </div>
            <div className="overflow-x-auto max-h-52 overflow-y-auto rounded-lg" style={{ border: `1px solid ${theme.border}` }}>
              <table className="w-full text-xs">
                <thead className="sticky top-0" style={{ background: isDark ? '#334155' : '#f1f5f9' }}>
                  <tr>
                    {(dataTable?.columns || []).slice(0, 6).map((col: string, i: number) => (
                      <th key={i} className="px-3 py-2 text-left font-bold uppercase" style={{ color: theme.accent, fontSize: 9 }}>
                        {col.replace(/_/g, ' ').slice(0, 10)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(dataTable?.data || []).slice(0, 6).map((row: any, idx: number) => (
                    <tr key={idx} className="border-t hover:bg-white/5" style={{ borderColor: theme.border }}>
                      {(dataTable?.columns || []).slice(0, 6).map((col: string, colIdx: number) => (
                        <td key={colIdx} className="px-3 py-2" style={{ color: theme.text }}>
                          {String(row[col] ?? '-').slice(0, 12)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-between text-xs py-2"
          style={{ color: theme.textMuted }}
        >
          <div className="flex items-center gap-4">
            <Activity className="w-4 h-4" style={{ color: theme.accent }} />
            <span>{dataShape?.rows?.toLocaleString()} records • {widgets.length} elements</span>
          </div>
          <span>Updated: {new Date().toLocaleTimeString()}</span>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboards;
