import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  ShoppingCart,
  RefreshCw,
  ChevronRight,
  Calendar,
  BarChart3,
  Activity,
  Package,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Area, CartesianGrid,
  ComposedChart, Line
} from 'recharts';
import { apiService } from '@/services/api';
import { formatCurrency, getCurrencySymbol, getUserPreferredCurrency, formatCompactCurrency, Currency } from '@/utils/currency';

// Website Theme Colors (from tailwind.config.js)
const THEME = {
  primary: '#F97316',      // Orange
  primaryLight: '#FB923C',
  primaryDark: '#EA580C',
  green: '#22C55E',
  red: '#EF4444',
  amber: '#F59E0B',
  yellow: '#FBBF24',
  // Card backgrounds for dark mode
  cardBg: '#1E293B',
  surfaceBg: '#0F172A',
};

// Vibrant chart colors that are visible in dark mode
const CHART_COLORS = [
  '#F97316',  // Orange (primary)
  '#22C55E',  // Green
  '#3B82F6',  // Blue
  '#F59E0B',  // Amber
  '#EF4444',  // Red
  '#8B5CF6',  // Purple
  '#06B6D4',  // Cyan
  '#EC4899',  // Pink
];

// KPI Card Component - Uses glass-card for theme support
// ENTERPRISE: Added tooltip definitions for audit-readiness
const KPICard: React.FC<{
  title: string;
  value: string;
  change?: number;
  icon: React.ReactNode;
  color: string;
  tooltip?: string;  // Enterprise: Definition for this metric
}> = ({ title, value, change, icon, color, tooltip }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -4, boxShadow: `0 20px 40px ${color}30` }}
    className="glass-card p-5 hover:border-primary-500/30 transition-all relative group"
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-1">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">{title}</p>
          {tooltip && (
            <div className="relative">
              <span className="text-gray-500 hover:text-primary-400 cursor-help text-xs" title={tooltip}>ⓘ</span>
              {/* Tooltip popup on hover */}
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-50 w-48 p-2 bg-surface-800 border border-surface-600 rounded-lg shadow-xl text-xs text-gray-300">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <p className="text-2xl font-bold text-white">{value}</p>
        {change !== undefined ? (
          <div className={`flex items-center mt-2 text-sm ${change >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
            {change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
            <span className="font-semibold">{Math.abs(change).toFixed(1)}%</span>
            <span className="text-gray-500 ml-1 text-xs">vs last</span>
          </div>
        ) : (
          <div className="mt-2 text-xs text-gray-500">No historical baseline</div>
        )}
      </div>
      <div
        className="p-3 rounded-xl"
        style={{ backgroundColor: `${color}20`, border: `1px solid ${color}40` }}
      >
        {icon}
      </div>
    </div>
  </motion.div>
);

// Data Table - Uses CSS variables for theme support
const DataTable: React.FC<{
  title: string;
  icon: React.ReactNode;
  data: any[];
  columns: { key: string; label: string; format?: (v: any, row?: any) => any; align?: string }[];
  currency: Currency;
}> = ({ title, icon, data, columns, currency: _currency }) => (
  <div className="glass-card overflow-hidden">
    <div className="px-5 py-4 border-b border-dark-border flex items-center gap-3">
      {icon}
      <h3 className="text-base font-semibold text-white">{title}</h3>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider ${col.align === 'right' ? 'text-right' : 'text-left'}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 6).map((row, i) => (
            <motion.tr
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              {columns.map((col, j) => (
                <td
                  key={col.key}
                  className={`px-5 py-4 text-sm ${col.align === 'right' ? 'text-right' : 'text-left'} ${j === 0 ? 'font-medium text-white' : 'text-gray-300'}`}
                >
                  {col.format ? col.format(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

interface DashboardData {
  hasData: boolean;
  currency: string;
  summary: {
    totalRevenue: number;
    totalOrders: number;
    uniqueCustomers: number;
    uniqueProducts: number;
    avgOrderValue: number;
  };
  abcAnalysis: {
    products: any[];
    customers: any[];
    summary: any;
  };
  customerSegments: any[];
  segmentSummary: any[];
  growthMetrics: any;
  revenueTimeline: { month: string; revenue: number; customers: number }[];
  categoryBreakdown?: { category: string; revenue: number; count: number }[];
  categoryColumn?: string | null;
  topInsights: any[];
}

const Dashboards: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState('30d');

  // Get user's SELECTED currency from Settings
  const currency = getUserPreferredCurrency();
  const currencySymbol = getCurrencySymbol(currency);

  useEffect(() => {
    loadData();
    const handleFilesUpdated = () => loadData();
    window.addEventListener('filesUpdated', handleFilesUpdated);
    return () => window.removeEventListener('filesUpdated', handleFilesUpdated);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getDashboardStats();
      setData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-14 h-14 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !data?.hasData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center bg-surface-800 p-10 rounded-2xl border border-surface-700 max-w-md">
          <BarChart3 className="w-16 h-16 text-primary-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">No Data Available</h2>
          <p className="text-gray-400 mb-6">Upload your data to see insights</p>
          <a
            href="/data-hub"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-amber text-white rounded-xl font-medium hover:shadow-glow transition-all"
          >
            Upload Data
            <ChevronRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    );
  }

  // Prepare donut chart data for products
  const productPieData = data.abcAnalysis.products.slice(0, 6).map((p, i) => ({
    name: p.name.length > 20 ? p.name.substring(0, 20) + '...' : p.name,
    value: p.revenue,
    percentage: p.percentage,
    fill: CHART_COLORS[i % CHART_COLORS.length],
  }));

  // Prepare horizontal bar data for customers
  const customerBarData = data.abcAnalysis.customers.slice(0, 6).map((c, i) => ({
    name: c.name.length > 15 ? c.name.substring(0, 15) + '...' : c.name,
    revenue: c.revenue,
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  // Segment pie data
  const segmentPieData = data.segmentSummary.map((seg, i) => ({
    name: seg.segment,
    value: seg.count,
    fill: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <div className="space-y-6 p-2">
      {/* Top Bar - Filter & Refresh */}
      <div className="flex items-center justify-end gap-3">
        <div className="flex items-center gap-2 glass-card px-4 py-2 rounded-xl">
          <Calendar className="w-4 h-4 text-primary-400" />
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="bg-transparent text-sm text-gray-300 focus:outline-none"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="all">All time</option>
          </select>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white rounded-xl text-sm font-medium transition-all hover:shadow-glow"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* KPI Cards - ENTERPRISE: Added metric definitions for audit-readiness */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          title="Total Revenue"
          value={formatCompactCurrency(data.summary.totalRevenue, currency)}
          change={data.growthMetrics?.revenueGrowth}
          icon={<DollarSign className="w-6 h-6 text-primary-400" />}
          color={THEME.primary}
          tooltip="Sum of Annual Contract Value across all active customer contracts from uploaded data."
        />
        <KPICard
          title="Customers"
          value={data.summary.uniqueCustomers.toLocaleString()}
          change={data.growthMetrics?.customerGrowth}
          icon={<Users className="w-6 h-6 text-accent-green" />}
          color={THEME.green}
          tooltip="Unique customer entities present in uploaded data."
        />
        <KPICard
          title="Orders"
          value={data.summary.totalOrders.toLocaleString()}
          change={data.growthMetrics?.orderGrowth}
          icon={<ShoppingCart className="w-6 h-6 text-accent-amber" />}
          color={THEME.amber}
          tooltip="Active contracts (1 contract per customer in this dataset)."
        />
        <KPICard
          title="Avg Order"
          value={formatCompactCurrency(data.summary.avgOrderValue, currency)}
          change={data.growthMetrics?.avgOrderGrowth}
          icon={<Activity className="w-6 h-6 text-blue-400" />}
          color="#3B82F6"
          tooltip="Total Revenue ÷ Total Orders."
        />
      </div>

      {/* Revenue Trend + Customer Segments */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Trend - ENTERPRISE: Shows message if no time-series data */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-2 glass-card p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary-500/20">
                <TrendingUp className="w-5 h-5 text-primary-500" />
              </div>
              <h3 className="text-base font-semibold text-white">Revenue Trend</h3>
            </div>
            <span className="text-xl font-bold text-primary-400">
              {formatCompactCurrency(data.summary.totalRevenue, currency)}
            </span>
          </div>
          {/* ENTERPRISE: Check if time-series data exists */}
          {data.revenueTimeline && data.revenueTimeline.length > 1 ? (
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={data.revenueTimeline}>
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={THEME.primary} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={THEME.primary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <YAxis
                  yAxisId="left" axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 11 }}
                  tickFormatter={(v) => formatCompactCurrency(v, currency).replace(currencySymbol, '')}
                />
                <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}
                  labelStyle={{ color: '#E5E7EB', fontWeight: 600 }}
                  itemStyle={{ color: '#FFFFFF' }}
                  formatter={(value: number, name: string) => [
                    name === 'revenue' ? formatCurrency(value, currency) : value,
                    name === 'revenue' ? 'Revenue' : 'Customers'
                  ]}
                />
                <Area yAxisId="left" type="monotone" dataKey="revenue" fill="url(#revenueGradient)" stroke={THEME.primary} strokeWidth={3} />
                <Line yAxisId="right" type="monotone" dataKey="customers" stroke={THEME.green} strokeWidth={2} dot={{ fill: THEME.green, strokeWidth: 0 }} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : data.categoryBreakdown && data.categoryBreakdown.length > 0 ? (
            /* 🎨 PREMIUM: Category Breakdown - Enterprise Visualization */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-300">
                    Revenue by {data.categoryColumn || 'Category'}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">Alternative analysis (no time data)</p>
                </div>
                <div className="text-xl font-bold text-primary-400">
                  {data.categoryBreakdown.length} {data.categoryBreakdown.length === 1 ? 'Category' : 'Categories'}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.categoryBreakdown} margin={{ top: 20, right: 10, left: 10, bottom: 40 }}>
                  <defs>
                    {/* Premium Gradient Definitions */}
                    {CHART_COLORS.map((color, idx) => (
                      <linearGradient key={`gradient-${idx}`} id={`barGradient${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity={0.95} />
                        <stop offset="100%" stopColor={color} stopOpacity={0.6} />
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                  <XAxis
                    dataKey="category"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    height={70}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 11 }}
                    tickFormatter={(v) => formatCompactCurrency(v, currency).replace(currencySymbol, '')}
                  />
                  <Tooltip
                    cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                    contentStyle={{
                      backgroundColor: '#1E293B',
                      border: '1px solid #475569',
                      borderRadius: '16px',
                      boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
                      padding: '12px 16px'
                    }}
                    labelStyle={{ color: '#E5E7EB', fontWeight: 700, marginBottom: '8px' }}
                    itemStyle={{ color: '#FFFFFF', fontSize: '14px', fontWeight: 600 }}
                    formatter={(value: number, _name: string, props: any) => [
                      formatCurrency(value, currency),
                      `Revenue (${props.payload.count} items)`
                    ]}
                  />
                  <Bar dataKey="revenue" radius={[8, 8, 0, 0]} maxBarSize={60}>
                    {data.categoryBreakdown.map((_entry: any, index: number) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={`url(#barGradient${index % CHART_COLORS.length})`}
                        stroke={CHART_COLORS[index % CHART_COLORS.length]}
                        strokeWidth={2}
                        style={{
                          filter: `drop-shadow(0 8px 16px ${CHART_COLORS[index % CHART_COLORS.length]}40)`,
                        }}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <TrendingUp className="w-12 h-12 text-gray-600 mb-4" />
              <p className="text-gray-400 font-medium mb-2">Time-series trend unavailable</p>
              <p className="text-gray-500 text-sm max-w-xs">
                Upload data with date fields (e.g., Order Date, Transaction Date) to enable revenue trends.
              </p>
            </div>
          )}
        </motion.div>

        {/* Customer Segments */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5"
        >
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-lg bg-accent-green/20">
              <Users className="w-5 h-5 text-accent-green" />
            </div>
            <h3 className="text-base font-semibold text-white">Customer Segments</h3>
          </div>
          {/* ENTERPRISE: Explain how segments are derived */}
          <p className="text-xs text-gray-500 mb-4 ml-11">Segments derived using revenue distribution rules (ABC Analysis).</p>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={segmentPieData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={75}
                paddingAngle={3}
                dataKey="value"
                stroke="none"
              >
                {segmentPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}
                labelStyle={{ color: '#E5E7EB', fontWeight: 600 }}
                itemStyle={{ color: '#FFFFFF' }}
                formatter={(value: number) => [`${value} customers`]}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {segmentPieData.map((seg) => (
              <div key={seg.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: seg.fill }}></div>
                  <span className="text-gray-400">{seg.name}</span>
                </div>
                <span className="font-medium text-white">{seg.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <DataTable
            title="Top Customers - Who's Buying?"
            icon={<Users className="w-5 h-5 text-primary-400" />}
            data={data.abcAnalysis.customers}
            currency={currency}
            columns={[
              { key: 'name', label: 'Customer' },
              { key: 'revenue', label: 'Revenue', align: 'right', format: (v) => formatCurrency(v, currency) },
              { key: 'percentage', label: '%', align: 'right', format: (v) => `${v}%` },
              {
                key: 'grade', label: '', align: 'right', format: (v) => (
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${v === 'A' ? 'bg-accent-green/20 text-accent-green' :
                    v === 'B' ? 'bg-accent-amber/20 text-accent-amber' :
                      'bg-accent-red/20 text-accent-red'
                    }`}>{v}</span>
                )
              }
            ]}
          />
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <DataTable
            title="Trending Products - What's Selling?"
            icon={<Package className="w-5 h-5 text-accent-amber" />}
            data={data.abcAnalysis.products}
            currency={currency}
            columns={[
              { key: 'name', label: 'Product' },
              { key: 'revenue', label: 'Revenue', align: 'right', format: (v) => formatCurrency(v, currency) },
              { key: 'percentage', label: '%', align: 'right', format: (v) => `${v}%` },
              {
                key: 'rank', label: '#', align: 'right', format: (v) => (
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${v <= 3 ? 'bg-primary-500/20 text-primary-400' : 'bg-gray-700 text-gray-400'
                    }`}>#{v}</span>
                )
              }
            ]}
          />
        </motion.div>
      </div>

      {/* Charts Row - Product Donut + Customer Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Product Distribution - Donut with Labels */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-primary-500/20">
              <Package className="w-5 h-5 text-primary-400" />
            </div>
            <h3 className="text-base font-semibold text-white">Product Distribution</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={productPieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
                label={({ percentage, cx, cy, midAngle, innerRadius, outerRadius }) => {
                  const RADIAN = Math.PI / 180;
                  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                  const x = cx + radius * Math.cos(-midAngle * RADIAN);
                  const y = cy + radius * Math.sin(-midAngle * RADIAN);
                  if (percentage < 8) return null;
                  return (
                    <text
                      x={x}
                      y={y}
                      fill="#FFFFFF"
                      textAnchor="middle"
                      dominantBaseline="central"
                      fontSize={11}
                      fontWeight={600}
                      style={{ textShadow: '0 1px 3px rgba(0,0,0,0.5)' }}
                    >
                      {percentage.toFixed(0)}%
                    </text>
                  );
                }}
                labelLine={false}
              >
                {productPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}
                labelStyle={{ color: '#E5E7EB', fontWeight: 600 }}
                itemStyle={{ color: '#FFFFFF' }}
                formatter={(value: number, _name: string, props: any) => [
                  formatCurrency(value, currency),
                  props.payload.name
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Legend below chart */}
          <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-dark-border">
            {productPieData.slice(0, 6).map((p) => (
              <div key={p.name} className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: p.fill }}></div>
                <span className="text-gray-300 truncate">{p.name}</span>
                <span className="text-gray-500 ml-auto">{p.percentage}%</span>
              </div>
            ))}
          </div>
        </motion.div>


        {/* Customer Revenue - Horizontal Bars */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-accent-green/20">
              <Users className="w-5 h-5 text-accent-green" />
            </div>
            <h3 className="text-base font-semibold text-white">Top Customer Revenue</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={customerBarData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
              <XAxis
                type="number"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#6B7280', fontSize: 10 }}
                tickFormatter={(v) => formatCompactCurrency(v, currency).replace(currencySymbol, '')}
              />
              <YAxis
                type="category"
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#374151', fontSize: 11 }}
                width={90}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}
                labelStyle={{ color: '#E5E7EB', fontWeight: 600 }}
                itemStyle={{ color: '#FFFFFF' }}
                formatter={(value: number) => [formatCurrency(value, currency), 'Revenue']}
              />
              <Bar dataKey="revenue" radius={[0, 8, 8, 0]}>
                {customerBarData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* ENTERPRISE: Data Coverage Badge - Increases trust and audit readiness */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-6 p-4 glass-card border border-surface-700 rounded-xl"
      >
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <span className="font-medium text-gray-300">Data Coverage:</span>
            </span>
            <span>{data.summary.uniqueCustomers.toLocaleString()} customers</span>
            <span className="text-gray-600">•</span>
            <span>{data.summary.uniqueProducts.toLocaleString()} products</span>
            <span className="text-gray-600">•</span>
            <span>Snapshot dataset</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Source: Uploaded files</span>
            <span className="px-2 py-0.5 bg-primary-500/20 text-primary-400 rounded text-xs font-medium">
              Enterprise
            </span>
          </div>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          Derived from statistical analysis of uploaded data. No external data used.
        </p>
      </motion.div>
    </div>
  );
};

export default Dashboards;
