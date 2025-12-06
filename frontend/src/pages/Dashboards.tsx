import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  Users,
  ShoppingBag,
  Download,
  Loader,
  AlertCircle,
} from 'lucide-react';
import { formatCurrency, getCurrencySymbol, detectCurrency } from '@/utils/currency';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { apiService } from '@/services/api';

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
  topCustomers: Array<{ name: string; revenue: number; orders: number }>;
  hasData: boolean;
  currency?: string;
}

const Dashboards: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState('30d');

  // Auto-detect currency from data
  const currency = data ? detectCurrency(data) : 'INR';
  const currencySymbol = getCurrencySymbol(currency);
  
  // Currency Icon Component
  const CurrencyIcon = () => (
    <div className="w-8 h-8 flex items-center justify-center font-bold text-current">
      {currencySymbol}
    </div>
  );

  useEffect(() => {
    loadData();
    
    // Listen for file updates from other pages
    const handleFilesUpdated = () => {
      console.log('Files updated, refreshing dashboards...');
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
      console.error('Failed to load analytics:', err);
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader className="w-12 h-12 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading real-time analytics from your files...</p>
        </div>
      </div>
    );
  }

  if (error || !data?.hasData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center glass-card p-8 max-w-md">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No Data Available</h2>
          <p className="text-gray-400 mb-4">Upload files to see live dashboards</p>
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

  const revenueData = data.timeSeries.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    revenue: item.revenue,
    invoices: item.invoices,
  }));

  const productData = data.topProducts.slice(0, 5).map(p => ({
    product: p.name,
    sales: p.count,
    revenue: p.revenue,
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Live Dashboards</h1>
          <p className="text-gray-400">Real-time analytics from your uploaded files</p>
        </div>
        <div className="flex space-x-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 bg-dark-card border border-dark-border rounded-xl text-gray-200 focus:outline-none focus:border-primary-500"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <button 
            onClick={() => window.print()}
            className="px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-xl text-primary-400 font-medium hover:bg-primary-500/20 transition-colors flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </motion.div>

      {/* KPI Cards - REAL DATA */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          {
            label: 'Total Revenue',
            value: formatCurrency(data.metrics.totalRevenue, currency),
            icon: CurrencyIcon,
            color: 'from-accent-green/20 to-accent-green/10',
            iconColor: 'text-accent-green',
          },
          {
            label: 'Active Customers',
            value: data.metrics.uniqueCustomers.toLocaleString(),
            icon: Users,
            color: 'from-primary-500/20 to-primary-400/10',
            iconColor: 'text-primary-400',
          },
          {
            label: 'Orders',
            value: data.metrics.totalInvoices.toLocaleString(),
            icon: ShoppingBag,
            color: 'from-accent-purple/20 to-accent-purple/10',
            iconColor: 'text-accent-purple',
          },
          {
            label: 'Avg Order Value',
            value: formatCurrency(data.metrics.averageOrderValue, currency),
            icon: TrendingUp,
            color: 'from-accent-orange/20 to-accent-orange/10',
            iconColor: 'text-accent-orange',
          },
        ].map((kpi, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -5 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${kpi.color} flex items-center justify-center`}>
                <kpi.icon className={`w-6 h-6 ${kpi.iconColor}`} />
              </div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{kpi.value}</div>
            <div className="text-sm text-gray-400">{kpi.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid - REAL DATA */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Revenue Trend (Real Data)</h2>
          </div>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="date" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: document.documentElement.classList.contains('light-theme') ? '#FFFFFF' : '#10172A',
                    border: document.documentElement.classList.contains('light-theme') ? '1px solid #E5E7EB' : '1px solid #1F2937',
                    borderRadius: '12px',
                    color: document.documentElement.classList.contains('light-theme') ? '#111827' : '#F9FAFB',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  name="Revenue"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-20">No time series data</p>
          )}
        </motion.div>

        {/* Product Performance */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Product Performance (Real Data)</h2>
          </div>
          {productData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={productData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="product" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: document.documentElement.classList.contains('light-theme') ? '#FFFFFF' : '#10172A',
                    border: document.documentElement.classList.contains('light-theme') ? '1px solid #E5E7EB' : '1px solid #1F2937',
                    borderRadius: '12px',
                    color: document.documentElement.classList.contains('light-theme') ? '#111827' : '#F9FAFB',
                  }}
                />
                <Legend />
                <Bar dataKey="revenue" fill="#3B82F6" name="Revenue" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-20">No product data</p>
          )}
        </motion.div>
      </div>

      {/* Top Customers Table - REAL DATA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
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
              {data.topCustomers.slice(0, 10).map((customer, i) => (
                <tr key={i} className="border-b border-dark-border/50">
                  <td className="py-4 text-white">{customer.name}</td>
                  <td className="py-4 text-right text-accent-green font-semibold">
                    {formatCurrency(customer.revenue, currency)}
                  </td>
                  <td className="py-4 text-right text-gray-300">{customer.orders}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboards;
