import React, { useEffect, useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { RefreshCw, Loader, Upload, ChevronDown, Filter } from 'lucide-react';
import { apiService } from '@/services/api';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
  PieChart, Pie
} from 'recharts';

// ===========================================================================
// DATAVISION OVERVIEW - EXACT SECOND REFERENCE IMAGE
// KPIs + Salary by Department + Role Breakdown (Donut + Bars) + Table + Location
// ===========================================================================

interface ThemeContext {
  isDark: boolean;
}

const CHART_COLORS = ['#818CF8', '#F472B6', '#FBBF24', '#34D399', '#22D3EE', '#A78BFA', '#FB923C', '#4ADE80'];

const Overview: React.FC = () => {
  const context = useOutletContext<ThemeContext>();
  const isDark = context?.isDark ?? true;

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  const theme = {
    bg: isDark ? '#0f172a' : '#f8fafc',
    cardBg: isDark ? '#1e293b' : '#ffffff',
    text: isDark ? '#f1f5f9' : '#1e293b',
    textMuted: isDark ? '#94a3b8' : '#64748b',
    border: isDark ? '#334155' : '#e2e8f0',
    accent: '#6366F1',
    headerBg: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
  };

  const loadData = useCallback(async (filtersToApply?: Record<string, string>, showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      // Build filters query parameter
      const filtersParam = filtersToApply && Object.keys(filtersToApply).length > 0
        ? `?filters=${encodeURIComponent(JSON.stringify(filtersToApply))}`
        : '';
      const response = await apiService.getUnifiedAnalytics(filtersParam);
      console.log('📊 Overview API:', response.data);
      setAnalytics(response.data);
    } catch (err: any) {
      console.error('Overview error:', err);
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

  const applyFilter = (filterName: string, filterValue: string) => {
    const newFilters = filterValue === 'all'
      ? Object.fromEntries(Object.entries(activeFilters).filter(([k]) => k !== filterName))
      : { ...activeFilters, [filterName]: filterValue };
    setActiveFilters(newFilters);
    // Reload data with new filters - NO loading spinner for smooth UX
    loadData(newFilters, false);
  };

  const formatValue = (v: any, format?: string) => {
    const num = Number(v);
    if (isNaN(num)) return String(v || '0');
    if (format === 'currency') {
      if (num >= 1000000) return `$${(num / 1000000).toFixed(2)}M`;
      if (num >= 1000) return `$${(num / 1000).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
      return `$${num.toLocaleString()}`;
    }
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${Math.round(num / 1000)}K`;
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
          <p className="text-sm mt-2 mb-6" style={{ color: theme.textMuted }}>Upload your data to start analyzing</p>
          <a href="/data-hub" className="px-8 py-3 rounded-xl text-white font-medium" style={{ background: theme.accent }}>Upload Data</a>
        </div>
      </div>
    );
  }

  const { overviewLayout, dashboardLayout, slicers, dataShape, domain, schema } = analytics;
  const kpis = overviewLayout?.kpis || [];
  const charts = overviewLayout?.charts || [];
  const dashWidgets = dashboardLayout?.widgets || [];

  // Extract specific chart data
  const columnChart = charts.find((c: any) => c.type === 'column_chart');
  const stackedBar = charts.find((c: any) => c.type === 'stacked_bar');
  const donutData = dashWidgets.find((w: any) => w.type === 'donut_chart');
  const dataTable = dashWidgets.find((w: any) => w.type === 'data_table');
  const horizontalBar = dashWidgets.find((w: any) => w.type === 'horizontal_bar');

  // Generate horizontal bar data for Role Breakdown from stackedBar keys
  const roleBreakdownData = stackedBar?.keys?.map((key: string, i: number) => {
    const total = stackedBar.data?.reduce((sum: number, d: any) => sum + (d[key] || 0), 0) || 0;
    return { name: key, value: total };
  }) || donutData?.data || [];

  return (
    <div className="min-h-screen w-full overflow-y-auto" style={{ background: theme.bg }}>
      <div className="w-full px-3 py-3">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-4 mb-4"
          style={{ background: theme.headerBg }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white">{domain || 'HR'} Overview</h1>
              <p className="text-sm text-white/70 flex items-center gap-2">
                {dataShape?.rows?.toLocaleString()} records • {dataShape?.columns} columns
                <RefreshCw className="w-3 h-3" />
              </p>
            </div>
            <motion.button
              whileHover={{ rotate: 180 }}
              onClick={() => loadData()}
              className="p-2.5 rounded-lg bg-white/20 hover:bg-white/30"
            >
              <RefreshCw className={`w-5 h-5 text-white ${loading ? 'animate-spin' : ''}`} />
            </motion.button>
          </div>
        </motion.div>

        {/* Slicers Row */}
        {slicers && slicers.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-wrap items-center gap-3 mb-4 p-3 rounded-lg"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <Filter className="w-4 h-4" style={{ color: theme.accent }} />
            {slicers.filter((s: any) => s.type !== 'date_range').slice(0, 3).map((slicer: any, idx: number) => (
              <div key={slicer.name} className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase" style={{ color: theme.textMuted }}>{slicer.label}</span>
                <div className="relative">
                  <select
                    value={activeFilters[slicer.name] || 'all'}
                    onChange={(e) => applyFilter(slicer.name, e.target.value)}
                    className="h-8 px-3 pr-7 rounded-md text-sm font-medium"
                    style={{ background: isDark ? '#334155' : '#f1f5f9', color: theme.text, border: `1px solid ${theme.border}` }}
                  >
                    <option value="all">All</option>
                    {slicer.options?.slice(0, 15).map((opt: string) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: theme.textMuted }} />
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* KPI Cards Row */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          {kpis.slice(0, 4).map((kpi: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="p-4 rounded-lg"
              style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
            >
              <p className="text-xs font-bold uppercase tracking-wide" style={{ color: theme.textMuted }}>{kpi.title}</p>
              <p className="text-3xl font-black mt-1" style={{ color: theme.text }}>
                {formatValue(kpi.value, kpi.format)}
              </p>
              {i === 3 && (
                <div className="flex gap-1 mt-1">
                  {CHART_COLORS.slice(0, 6).map((c, j) => (
                    <div key={j} className="w-3 h-3 rounded-full" style={{ background: c }} />
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Row 1: Salary by Department + Employee Breakdown by Role */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Salary by Department - Column Chart */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-4 rounded-lg"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>
              {columnChart?.title || `Total ${schema?.metrics?.[0]?.replace('_', ' ') || 'Value'} by ${schema?.dimensions?.[0]?.replace('_', ' ') || 'Category'}`}
            </h3>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={columnChart?.data || []} margin={{ top: 10, right: 10, left: 0, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} vertical={false} />
                  <XAxis dataKey="category" tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} angle={-30} textAnchor="end" height={50} />
                  <YAxis tick={{ fontSize: 9, fill: theme.textMuted }} stroke={theme.border} tickFormatter={(v) => formatValue(v)} />
                  <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {(columnChart?.data || []).map((_: any, idx: number) => <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Employee Breakdown by Role - Donut + Horizontal Bars */}
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-4 rounded-lg"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <h3 className="text-sm font-bold mb-3" style={{ color: theme.text }}>
              {schema?.dimensions?.[1]?.replace('_', ' ') || 'Category'} Breakdown
            </h3>
            <div className="flex items-start gap-4">
              {/* Donut Chart */}
              <div style={{ width: '40%', height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={roleBreakdownData}
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
                      {roleBreakdownData.map((_: any, idx: number) => <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Horizontal Bar Breakdown */}
              <div className="flex-1">
                {roleBreakdownData.slice(0, 5).map((item: any, i: number) => {
                  const maxVal = Math.max(...roleBreakdownData.map((d: any) => d.value));
                  const pct = maxVal > 0 ? (item.value / maxVal) * 100 : 0;
                  return (
                    <div key={i} className="flex items-center gap-2 mb-2">
                      <span className="text-xs w-16 truncate" style={{ color: theme.textMuted }}>{item.name}</span>
                      <div className="flex-1 h-5 rounded overflow-hidden" style={{ background: isDark ? '#334155' : '#e2e8f0' }}>
                        <div className="h-full rounded transition-all" style={{ width: `${pct}%`, background: CHART_COLORS[i % CHART_COLORS.length] }} />
                      </div>
                    </div>
                  );
                })}
                {/* Legend */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {roleBreakdownData.slice(0, 5).map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-1">
                      <div className="w-2.5 h-2.5 rounded-sm" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                      <span className="text-[10px]" style={{ color: theme.textMuted }}>{item.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Row 2: Top Departments Table + Employees by Location */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Top Departments by Salary - Table */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-lg"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold" style={{ color: theme.text }}>
                Top {schema?.dimensions?.[0]?.replace('_', ' ') || 'Records'} by {schema?.metrics?.[0]?.replace('_', ' ') || 'Value'}
              </h3>
              <span className="text-xs px-2 py-0.5 rounded" style={{ background: isDark ? '#334155' : '#e2e8f0', color: theme.textMuted }}>all</span>
            </div>
            <div className="overflow-x-auto rounded-lg" style={{ border: `1px solid ${theme.border}` }}>
              <table className="w-full text-xs">
                <thead style={{ background: isDark ? '#334155' : '#f1f5f9' }}>
                  <tr>
                    <th className="px-3 py-2 text-left font-bold uppercase" style={{ color: theme.accent }}>{schema?.dimensions?.[0]?.toUpperCase() || 'CATEGORY'}</th>
                    <th className="px-3 py-2 text-left font-bold uppercase" style={{ color: theme.accent }}>TYPE</th>
                    <th className="px-3 py-2 text-right font-bold uppercase" style={{ color: theme.accent }}>TOTAL {schema?.metrics?.[0]?.toUpperCase() || 'VALUE'}</th>
                  </tr>
                </thead>
                <tbody>
                  {(columnChart?.data || []).slice(0, 6).map((row: any, idx: number) => (
                    <tr key={idx} className="border-t" style={{ borderColor: theme.border }}>
                      <td className="px-3 py-2.5 font-medium" style={{ color: theme.text }}>{row.category}</td>
                      <td className="px-3 py-2.5" style={{ color: theme.textMuted }}>{schema?.dimensions?.[0]}</td>
                      <td className="px-3 py-2.5 text-right font-bold" style={{ color: CHART_COLORS[idx % CHART_COLORS.length] }}>
                        {formatValue(row.value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Employees by Location - Column Chart + Details Table */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-lg"
            style={{ background: theme.cardBg, border: `1px solid ${theme.border}` }}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold" style={{ color: theme.text }}>
                {schema?.dimensions?.[2] || schema?.dimensions?.[1] ? `Records by ${(schema?.dimensions?.[2] || schema?.dimensions?.[1])?.replace('_', ' ')}` : 'Distribution'}
              </h3>
              <select className="text-xs px-2 py-1 rounded" style={{ background: isDark ? '#334155' : '#e2e8f0', color: theme.text, border: `1px solid ${theme.border}` }}>
                <option>Total</option>
              </select>
            </div>
            <div style={{ height: 140 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={(horizontalBar?.data || columnChart?.data || []).slice(0, 6)} margin={{ top: 5, right: 10, left: 0, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} vertical={false} />
                  <XAxis dataKey="category" tick={{ fontSize: 8, fill: theme.textMuted }} stroke={theme.border} angle={-20} textAnchor="end" height={35} />
                  <YAxis tick={{ fontSize: 8, fill: theme.textMuted }} stroke={theme.border} tickFormatter={(v) => formatValue(v)} />
                  <Tooltip formatter={(v: any) => formatValue(v)} contentStyle={{ background: theme.cardBg, border: `1px solid ${theme.border}`, borderRadius: 8, fontSize: 10 }} />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                    {(horizontalBar?.data || columnChart?.data || []).slice(0, 6).map((_: any, idx: number) => <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Employee Details Table */}
            <div className="mt-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold" style={{ color: theme.text }}>{domain || 'Data'} Details</h4>
                <span className="text-[10px]" style={{ color: theme.textMuted }}>Updated: {new Date().toLocaleTimeString()}</span>
              </div>
              <div className="overflow-x-auto max-h-32 overflow-y-auto rounded" style={{ border: `1px solid ${theme.border}` }}>
                <table className="w-full text-[10px]">
                  <thead className="sticky top-0" style={{ background: isDark ? '#334155' : '#f1f5f9' }}>
                    <tr>
                      {(dataTable?.columns || []).slice(0, 5).map((col: string, i: number) => (
                        <th key={i} className="px-2 py-1.5 text-left font-bold uppercase" style={{ color: theme.accent }}>{col.replace(/_/g, ' ').slice(0, 8)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(dataTable?.data || []).slice(0, 5).map((row: any, idx: number) => (
                      <tr key={idx} className="border-t" style={{ borderColor: theme.border }}>
                        {(dataTable?.columns || []).slice(0, 5).map((col: string, colIdx: number) => (
                          <td key={colIdx} className="px-2 py-1" style={{ color: colIdx === 4 ? CHART_COLORS[idx % CHART_COLORS.length] : theme.text, fontWeight: colIdx === 4 ? 600 : 400 }}>
                            {colIdx === 4 ? formatValue(row[col], 'currency') : String(row[col] ?? '-').slice(0, 10)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
          <span>{dataShape?.rows?.toLocaleString()} records • {schema?.dimensions?.length || 0} dimensions</span>
          <span>Updated: {new Date().toLocaleTimeString()}</span>
        </motion.div>
      </div>
    </div>
  );
};

export default Overview;
