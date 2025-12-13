import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  ShoppingCart,
  Activity,
  Loader,
  AlertCircle,
} from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
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
      const response = await apiService.getAnalyticsOverview();
      setData(response.data);
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
      label: hasMultipleCurrencies ? 'Avg Order Value (USD)' : 'Avg Order Value',
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
                <div className="text-sm text-gray-400 mt-1">
                  ≈ ${item.usd_equivalent.toLocaleString()} USD
                </div>
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
          <h2 className="text-xl font-semibold text-white mb-4">Revenue Trend (Real Data)</h2>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="date" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10172A',
                    border: '1px solid #1F2937',
                    borderRadius: '12px',
                    color: '#F9FAFB',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  dot={{ fill: '#3B82F6', r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-20">No time series data available</p>
          )}
        </motion.div>

        {/* Top Products Distribution */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Top Products (Real Data)</h2>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: document.documentElement.classList.contains('light-theme') ? '#FFFFFF' : '#1F2937',
                    border: document.documentElement.classList.contains('light-theme') ? '1px solid #E5E7EB' : '1px solid #374151',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                  }}
                  itemStyle={{
                    color: document.documentElement.classList.contains('light-theme') ? '#111827' : '#F9FAFB',
                  }}
                  labelStyle={{
                    color: document.documentElement.classList.contains('light-theme') ? '#111827' : '#F9FAFB',
                    fontWeight: 'bold',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-20">No product data available</p>
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
              </tr>
            </thead>
            <tbody>
              {data.topProducts.map((product, i) => (
                <tr key={i} className="border-b border-dark-border/50">
                  <td className="py-4 text-white">{product.name}</td>
                  <td className="py-4 text-right text-accent-green font-semibold">
                    {formatCurrency(product.revenue, displayCurrency)}
                  </td>
                  <td className="py-4 text-right text-gray-300">{product.count}</td>
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
                </tr>
              </thead>
              <tbody>
                {data.bottomProducts.map((product, i) => (
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
              </tr>
            </thead>
            <tbody>
              {data.topCustomers.map((customer, i) => (
                <tr key={i} className="border-b border-dark-border/50">
                  <td className="py-4 text-white">{customer.name}</td>
                  <td className="py-4 text-right text-accent-green font-semibold">
                    {formatCurrency(customer.revenue, displayCurrency)}
                  </td>
                  <td className="py-4 text-right text-gray-300">{customer.orders}</td>
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
                </tr>
              </thead>
              <tbody>
                {data.bottomCustomers.map((customer, i) => (
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
