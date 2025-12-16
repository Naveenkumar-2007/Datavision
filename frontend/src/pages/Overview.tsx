import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  ShoppingCart,
  Activity,
  Loader,
  AlertCircle,
  Lightbulb,
} from 'lucide-react';
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '@/services/api';
import { formatCurrency, getCurrencySymbol, getUserPreferredCurrency, convertCurrency } from '@/utils/currency';

interface CurrencyBreakdownItem {
  currency: string;
  amount: number;
  symbol: string;
  formatted: string;
  usd_equivalent: number;
  name: string;
}

interface CurrencyBreakdown {
  breakdown: CurrencyBreakdownItem[];
  total_usd_equivalent: number;
  total_usd_formatted: string;
  primary_currency: string;
  currencies_count: number;
}

interface BusinessInsight {
  type: 'success' | 'warning' | 'info';
  icon: string;
  title: string;
  message: string;
}

interface AnalyticsData {
  metrics: {
    totalRevenue: number;
    totalInvoices: number;
    uniqueCustomers: number;
    averageOrderValue: number;
    currency?: string;
  };
  timeSeries: Array<{ date: string; revenue: number; invoices: number }>;
  topProducts: Array<{ name: string; revenue: number; count: number }>;
  bottomProducts?: Array<{ name: string; revenue: number; count: number }>;
  allProducts?: Array<{ name: string; revenue: number; count: number }>;
  topCustomers: Array<{ name: string; revenue: number; orders: number }>;
  bottomCustomers?: Array<{ name: string; revenue: number; orders: number }>;
  allCustomers?: Array<{ name: string; revenue: number; orders: number }>;
  hasData: boolean;
  message?: string;
  currency?: string;
  currencyBreakdown?: CurrencyBreakdown;
}

const Overview: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [insights, setInsights] = useState<BusinessInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();

    // Listen for file updates from other pages
    const handleFilesUpdated = () => {
      loadData();
    };

    window.addEventListener('filesUpdated', handleFilesUpdated);

    return () => {
      window.removeEventListener('filesUpdated', handleFilesUpdated);
    };
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch analytics and insights in parallel
      const [analyticsResponse, insightsResponse] = await Promise.all([
        apiService.getAnalyticsOverview(),
        apiService.getInsights().catch(() => ({ data: { insights: [] } }))
      ]);

      setData(analyticsResponse.data);
      setInsights(insightsResponse.data?.insights || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader className="w-12 h-12 text-orange-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading real data from your uploaded files...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center glass-card p-8 max-w-md">
          <AlertCircle className="w-12 h-12 text-accent-red mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Error Loading Data</h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={loadData}
            className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data?.hasData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center glass-card p-8 max-w-md">
          <Activity className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No Data Available</h2>
          <p className="text-gray-400 mb-4">{data?.message || 'Upload files to see analytics'}</p>
          <a
            href="/data-hub"
            className="inline-block px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors"
          >
            Upload Files
          </a>
        </div>
      </div>
    );
  }

  // Get user's preferred currency from Settings
  const userPreferredCurrency = getUserPreferredCurrency();
  const userCurrencySymbol = getCurrencySymbol(userPreferredCurrency);

  // Determine display currency and values based on multi-currency or single currency
  // ALWAYS use user's preferred currency for display
  const hasMultipleCurrencies = data.currencyBreakdown && data.currencyBreakdown.currencies_count > 1;
  const displayCurrency = userPreferredCurrency; // Use user's preference
  const displaySymbol = userCurrencySymbol;

  // Get raw USD value and convert to user's preferred currency
  const rawUsdRevenue = hasMultipleCurrencies
    ? data.currencyBreakdown!.total_usd_equivalent
    : data.metrics.totalRevenue;
  const displayRevenue = userPreferredCurrency !== 'USD' && hasMultipleCurrencies
    ? convertCurrency(rawUsdRevenue, 'USD', userPreferredCurrency)
    : rawUsdRevenue;
  const displayAvgOrder = displayRevenue / (data.metrics.totalInvoices || 1);

  // Currency Icon for KPIs - uses display currency
  const DisplayCurrencyIcon = () => (
    <div className="w-5 h-5 flex items-center justify-center font-bold text-current">
      {displaySymbol}
    </div>
  );

  const kpis = [
    {
      label: 'Total Revenue',
      value: formatCurrency(displayRevenue, displayCurrency),
      change: '+12.5%',
      trend: 'up',
      icon: DisplayCurrencyIcon,
      color: 'text-accent-green',
    },
    {
      label: 'Active Customers',
      value: data.metrics.uniqueCustomers.toLocaleString('en-IN'),
      change: '+8.2%',
      trend: 'up',
      icon: Users,
      color: 'text-primary-400',
    },
    {
      label: 'Total Orders',
      value: data.metrics.totalInvoices.toLocaleString('en-IN'),
      change: '+5.7%',
      trend: 'up',
      icon: ShoppingCart,
      color: 'text-accent-orange',
    },
    {
      label: `Avg Order Value${displayCurrency !== 'USD' ? ` (${displayCurrency})` : ''}`,
      value: formatCurrency(displayAvgOrder, displayCurrency),
      change: '+3.2%',
      trend: 'up',
      icon: Activity,
      color: 'text-accent-orange',
    },
  ];

  // Format time series for charts
  const revenueData = data.timeSeries.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    revenue: item.revenue,
    orders: item.invoices,
  }));

  // Top products for pie chart
  const categoryData = data.topProducts.slice(0, 5).map((product, index) => ({
    name: product.name,
    value: product.revenue,
    color: ['#3B82F6', '#22C55E', '#F97316', '#F97316', '#EAB308'][index],
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-bold text-white mb-2">Business Overview</h1>
        <p className="text-gray-400">Real metrics from your uploaded files</p>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((kpi, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -5 }}
            className="glass-card p-6 hover:shadow-card-hover transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${i === 0
                  ? 'from-accent-green/20 to-accent-green/10'
                  : i === 1
                    ? 'from-primary-500/20 to-primary-400/10'
                    : i === 2
                      ? 'from-accent-orange/20 to-accent-orange/10'
                      : 'from-accent-orange/20 to-accent-orange/10'
                  } flex items-center justify-center`}
              >
                <kpi.icon className={`w-6 h-6 ${kpi.color}`} />
              </div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{kpi.value}</div>
            <div className="text-sm text-gray-400">{kpi.label}</div>
          </motion.div>
        ))}
      </div>

      {/* AI Business Insights */}
      {insights.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass-card p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500/20 to-primary-400/10 flex items-center justify-center">
              <Lightbulb className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">AI Business Insights</h2>
              <p className="text-sm text-gray-400">Automatically generated from your data</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {insights.map((insight, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
                className={`p-4 rounded-xl border ${insight.type === 'success'
                  ? 'bg-accent-green/10 border-accent-green/30'
                  : insight.type === 'warning'
                    ? 'bg-accent-orange/10 border-accent-orange/30'
                    : 'bg-primary-500/10 border-primary-500/30'
                  }`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{insight.icon}</span>
                  <div>
                    <h3 className={`font-semibold ${insight.type === 'success' ? 'text-accent-green'
                      : insight.type === 'warning' ? 'text-accent-orange'
                        : 'text-primary-400'
                      }`}>
                      {insight.title}
                    </h3>
                    <p className="text-sm text-gray-300 mt-1">{insight.message}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Multi-Currency Breakdown - Shows when multiple currencies exist */}
      {data.currencyBreakdown && data.currencyBreakdown.breakdown.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">💰 Revenue by Currency</h2>
            {data.currencyBreakdown.currencies_count > 1 && (
              <span className="text-sm text-gray-400 bg-surface-600/50 px-3 py-1 rounded-full">
                {data.currencyBreakdown.currencies_count} currencies detected
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            {data.currencyBreakdown.breakdown.map((item) => (
              <div
                key={item.currency}
                className="bg-surface-700/50 rounded-xl p-4 border border-surface-600/50"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl font-bold text-primary-400">{item.symbol}</span>
                  <span className="text-gray-400 text-sm">{item.name}</span>
                </div>
                <div className="text-2xl font-bold text-white">{item.formatted}</div>
                {item.currency !== userPreferredCurrency && (
                  <div className="text-sm text-gray-400 mt-1">
                    ≈ {formatCurrency(convertCurrency(item.usd_equivalent, 'USD', userPreferredCurrency), userPreferredCurrency)}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* User's Preferred Currency Equivalent Total */}
          {data.currencyBreakdown.currencies_count > 1 && (
            <div className="border-t border-surface-600/50 pt-4 mt-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Combined Total ({userPreferredCurrency} Equivalent)</span>
                <span className="text-2xl font-bold text-accent-green">
                  {/* Convert USD total to user's preferred currency */}
                  {formatCurrency(
                    convertCurrency(data.currencyBreakdown.total_usd_equivalent, 'USD', userPreferredCurrency),
                    userPreferredCurrency
                  )}
                </span>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">📈 Revenue Trend</h2>
            {revenueData.length > 0 && (
              <span className="text-sm text-gray-400 bg-surface-700/50 px-3 py-1 rounded-full">
                {revenueData.length} data points
              </span>
            )}
          </div>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={revenueData}>
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.4} />
                    <stop offset="50%" stopColor="#22C55E" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#3B82F6" />
                    <stop offset="50%" stopColor="#22C55E" />
                    <stop offset="100%" stopColor="#3B82F6" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" opacity={0.5} />
                <XAxis
                  dataKey="date"
                  stroke="#6B7280"
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  axisLine={{ stroke: '#374151' }}
                />
                <YAxis
                  stroke="#6B7280"
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  axisLine={{ stroke: '#374151' }}
                  tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}K` : value}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid #3B82F6',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
                    color: '#F9FAFB',
                    padding: '12px 16px',
                  }}
                  labelStyle={{ color: '#9CA3AF', fontWeight: 600, marginBottom: '4px' }}
                  formatter={(value: number) => [formatCurrency(value, displayCurrency), 'Revenue']}
                  cursor={{ stroke: '#3B82F6', strokeDasharray: '5 5' }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="url(#lineGradient)"
                  strokeWidth={3}
                  fill="url(#revenueGradient)"
                  dot={{ fill: '#3B82F6', r: 4, strokeWidth: 2, stroke: '#1e3a5f' }}
                  activeDot={{ r: 8, fill: '#22C55E', stroke: '#fff', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <Activity className="w-12 h-12 mb-3 opacity-50" />
              <p>No time series data available</p>
              <p className="text-sm">Upload files with date information</p>
            </div>
          )}
        </motion.div>

        {/* Top Products Distribution */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">🏆 Top Products</h2>
            {categoryData.length > 0 && (
              <span className="text-sm text-gray-400 bg-surface-700/50 px-3 py-1 rounded-full">
                {categoryData.length} products
              </span>
            )}
          </div>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <defs>
                  {/* Premium gradient for each slice */}
                  <linearGradient id="pieGradient0" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" />
                    <stop offset="100%" stopColor="#1D4ED8" />
                  </linearGradient>
                  <linearGradient id="pieGradient1" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#22C55E" />
                    <stop offset="100%" stopColor="#15803D" />
                  </linearGradient>
                  <linearGradient id="pieGradient2" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#F97316" />
                    <stop offset="100%" stopColor="#C2410C" />
                  </linearGradient>
                  <linearGradient id="pieGradient3" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#EAB308" />
                    <stop offset="100%" stopColor="#A16207" />
                  </linearGradient>
                  <linearGradient id="pieGradient4" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#8B5CF6" />
                    <stop offset="100%" stopColor="#6D28D9" />
                  </linearGradient>
                </defs>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={{ stroke: '#374151', strokeWidth: 1 }}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  innerRadius={60}
                  outerRadius={110}
                  paddingAngle={3}
                  dataKey="value"
                  animationDuration={1000}
                  animationEasing="ease-out"
                >
                  {categoryData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={`url(#pieGradient${index % 5})`}
                      stroke="rgba(255,255,255,0.1)"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid #3B82F6',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
                    padding: '12px 16px',
                  }}
                  itemStyle={{ color: '#F9FAFB' }}
                  labelStyle={{ color: '#9CA3AF', fontWeight: 600 }}
                  formatter={(value: number) => [formatCurrency(value, displayCurrency), 'Revenue']}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <ShoppingCart className="w-12 h-12 mb-3 opacity-50" />
              <p>No product data available</p>
              <p className="text-sm">Upload files with product information</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Top Products Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-card p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-4">Top Products (Real Data)</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 border-b border-dark-border">
                <th className="pb-3">Product</th>
                <th className="pb-3 text-right">Revenue</th>
                <th className="pb-3 text-right">Sales</th>
                <th className="pb-3 text-right">Source</th>
              </tr>
            </thead>
            <tbody>
              {data.topProducts.map((product: any, i) => (
                <tr key={i} className="border-b border-dark-border/50">
                  <td className="py-4 text-white">{product.name}</td>
                  <td className="py-4 text-right text-accent-green font-semibold">
                    {formatCurrency(product.revenue, displayCurrency)}
                  </td>
                  <td className="py-4 text-right text-gray-300">{product.count}</td>
                  <td className="py-4 text-right text-gray-700 dark:text-gray-300 text-sm font-medium">{product.source || 'Unknown'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Lowest-Performing Products Table */}
      {data.bottomProducts && data.bottomProducts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">
            <span className="text-accent-orange">Lowest-Performing</span> Products (Real Data)
          </h2>
          <p className="text-gray-400 text-sm mb-4">Products with the lowest revenue - consider promotion or discontinuation</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 border-b border-dark-border">
                  <th className="pb-3">Product</th>
                  <th className="pb-3 text-right">Revenue</th>
                  <th className="pb-3 text-right">Sales</th>
                  <th className="pb-3 text-right">Source</th>
                </tr>
              </thead>
              <tbody>
                {data.bottomProducts.map((product: any, i) => (
                  <tr key={i} className="border-b border-dark-border/50">
                    <td className="py-4 text-white flex items-center">
                      {i === 0 && <span className="text-accent-red mr-2">🔻</span>}
                      {product.name}
                      {i === 0 && <span className="ml-2 text-xs bg-accent-red/20 text-accent-red px-2 py-0.5 rounded">LOWEST</span>}
                    </td>
                    <td className="py-4 text-right text-accent-orange font-semibold">
                      {formatCurrency(product.revenue, displayCurrency)}
                    </td>
                    <td className="py-4 text-right text-gray-300">{product.count}</td>
                    <td className="py-4 text-right text-gray-700 dark:text-gray-300 text-sm font-medium">{product.source || 'Unknown'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Top Customers Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-4">Top Customers (Real Data)</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 border-b border-dark-border">
                <th className="pb-3">Customer</th>
                <th className="pb-3 text-right">Revenue</th>
                <th className="pb-3 text-right">Orders</th>
                <th className="pb-3 text-right">Source</th>
              </tr>
            </thead>
            <tbody>
              {data.topCustomers.map((customer: any, i) => (
                <tr key={i} className="border-b border-dark-border/50">
                  <td className="py-4 text-white">{customer.name}</td>
                  <td className="py-4 text-right text-accent-green font-semibold">
                    {formatCurrency(customer.revenue, displayCurrency)}
                  </td>
                  <td className="py-4 text-right text-gray-300">{customer.orders}</td>
                  <td className="py-4 text-right text-gray-700 dark:text-gray-300 text-sm font-medium">{customer.source || 'Unknown'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Lowest-Spending Customers Table */}
      {data.bottomCustomers && data.bottomCustomers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">
            <span className="text-accent-orange">Lowest-Spending</span> Customers (Real Data)
          </h2>
          <p className="text-gray-400 text-sm mb-4">Customers with the lowest revenue - potential for growth or churn risk</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 border-b border-dark-border">
                  <th className="pb-3">Customer</th>
                  <th className="pb-3 text-right">Revenue</th>
                  <th className="pb-3 text-right">Orders</th>
                  <th className="pb-3 text-right">Source</th>
                </tr>
              </thead>
              <tbody>
                {data.bottomCustomers.map((customer: any, i) => (
                  <tr key={i} className="border-b border-dark-border/50">
                    <td className="py-4 text-white flex items-center">
                      {i === 0 && <span className="text-accent-red mr-2">🔻</span>}
                      {customer.name}
                      {i === 0 && <span className="ml-2 text-xs bg-accent-red/20 text-accent-red px-2 py-0.5 rounded">LOWEST</span>}
                    </td>
                    <td className="py-4 text-right text-accent-orange font-semibold">
                      {formatCurrency(customer.revenue, displayCurrency)}
                    </td>
                    <td className="py-4 text-right text-gray-300">{customer.orders}</td>
                    <td className="py-4 text-right text-gray-700 dark:text-gray-300 text-sm font-medium">{customer.source || 'Unknown'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Overview;
