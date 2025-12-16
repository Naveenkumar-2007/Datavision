import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Download,
  TrendingUp,
  Users,
  ShoppingCart,
  Loader,
  AlertCircle,
  CheckCircle,
  FileDown,
  BarChart3,
  PieChart as PieChartIcon,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { apiService } from '@/services/api';
import { formatCurrency, getCurrencySymbol, getUserPreferredCurrency, convertCurrency, formatCompactCurrency } from '@/utils/currency';
import { exportToPDF } from '@/utils/pdfExport';

interface ReportSection {
  title: string;
  content: string;
}

interface GeneratedReport {
  title: string;
  reportType: string;
  generatedAt: string;
  dataSource: string;
  sections: ReportSection[];
  error?: string;
}

const Reports: React.FC = () => {
  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [generating, setGenerating] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('revenue');
  const [analytics, setAnalytics] = useState<any>(null);
  const [dashboardStats, setDashboardStats] = useState<any>(null);

  // Chart colors for enterprise-grade visualization
  const CHART_COLORS = ['#F97316', '#22C55E', '#3B82F6', '#EAB308', '#8B5CF6', '#EC4899'];

  // Use user's preferred currency from Settings
  const userPreferredCurrency = getUserPreferredCurrency();
  const currency = userPreferredCurrency;
  const currencySymbol = getCurrencySymbol(currency);

  // Check if there are multiple currencies in the data
  const hasMultipleCurrencies = analytics?.currencyBreakdown?.currencies_count > 1;

  // Get display values - convert to user's preferred currency
  const rawRevenue = hasMultipleCurrencies
    ? analytics?.currencyBreakdown?.total_usd_equivalent || analytics?.metrics?.totalRevenue
    : analytics?.metrics?.totalRevenue || 0;
  const displayRevenue = hasMultipleCurrencies && currency !== 'USD'
    ? convertCurrency(rawRevenue, 'USD', currency)
    : rawRevenue;
  const displayAvgOrder = displayRevenue / (analytics?.metrics?.totalInvoices || 1);

  // Currency Icon Component
  const CurrencyIcon = () => (
    <div className="w-8 h-8 flex items-center justify-center font-bold text-current">
      {currencySymbol}
    </div>
  );

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [analyticsResponse, statsResponse] = await Promise.all([
        apiService.getAnalyticsOverview(),
        apiService.getDashboardStats()
      ]);
      setAnalytics(analyticsResponse.data);
      setDashboardStats(statsResponse.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const response = await apiService.generateReport(selectedType);
      setReport(response.data);
    } catch (err: any) {
      console.error('Generate report failed:', err);
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;

    const content = `
${report.title}
Generated: ${new Date(report.generatedAt).toLocaleString()}
Data Source: ${report.dataSource}

${report.sections.map(section => `
${section.title}
${'='.repeat(section.title.length)}
${section.content}
`).join('\n')}
    `.trim();

    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${report.reportType}_report_${Date.now()}.txt`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handleExportPDF = async () => {
    if (!report) return;
    setExportingPDF(true);
    try {
      await exportToPDF('report-content', {
        filename: `${report.reportType}_report`,
        orientation: 'portrait',
        margin: 15,
      });
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
      setExportingPDF(false);
    }
  };

  const reportTypes = [
    {
      value: 'revenue',
      label: 'Revenue Report',
      description: 'Revenue analysis from uploaded files',
      icon: CurrencyIcon
    },
    {
      value: 'customer',
      label: 'Customer Report',
      description: 'Customer insights from uploaded files',
      icon: Users
    },
    {
      value: 'product',
      label: 'Product Report',
      description: 'Product performance from uploaded files',
      icon: ShoppingCart
    },
    {
      value: 'executive',
      label: 'Executive Summary',
      description: 'High-level overview from uploaded files',
      icon: TrendingUp
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4 mb-2"
      >
        <img src="/logo.png" alt="Logo" className="w-12 h-12 rounded-xl shadow-lg shadow-orange-500/20" />
        <div>
          <h1 className="text-4xl font-bold text-white">Business Reports</h1>
          <p className="text-gray-400">Real reports generated from your uploaded files</p>
        </div>
      </motion.div>

      {/* Key Metrics Summary - REAL DATA */}
      {analytics?.hasData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Currency Info Banner */}
          {hasMultipleCurrencies && (
            <div className="glass-card p-4 border border-orange-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">💰</span>
                  <div>
                    <div className="text-white font-semibold">
                      {analytics.currencyBreakdown?.currencies_count} Currencies Detected
                    </div>
                    <div className="text-sm text-gray-400">
                      Data auto-converted to {currencySymbol} ({currency})
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">Original currencies:</div>
                  <div className="flex flex-wrap gap-1 justify-end mt-1">
                    {analytics.currencyBreakdown?.breakdown?.map((item: any, i: number) => (
                      <span key={i} className="px-2 py-1 bg-dark-card rounded text-xs text-gray-300">
                        {item.symbol} {item.currency}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              {
                label: 'Total Revenue',
                value: formatCurrency(displayRevenue || 0, currency),
                icon: CurrencyIcon,
                color: 'text-accent-green'
              },
              {
                label: 'Customers',
                value: analytics.metrics.uniqueCustomers.toLocaleString(),
                icon: Users,
                color: 'text-orange-400'
              },
              {
                label: 'Orders',
                value: analytics.metrics.totalInvoices.toLocaleString(),
                icon: ShoppingCart,
                color: 'text-accent-orange'
              },
              {
                label: 'Avg Order',
                value: formatCurrency(displayAvgOrder || 0, currency),
                icon: TrendingUp,
                color: 'text-accent-orange'
              },
            ].map((metric, i) => (
              <div key={i} className="glass-card p-4">
                <div className="flex items-center space-x-3">
                  <metric.icon className={`w-8 h-8 ${metric.color}`} />
                  <div>
                    <div className="text-2xl font-bold text-white">{metric.value}</div>
                    <div className="text-sm text-gray-400">{metric.label}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Generate Report Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-8"
      >
        <h2 className="text-2xl font-semibold text-white mb-6">Generate New Report</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {reportTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setSelectedType(type.value)}
              className={`p-4 rounded-xl transition-all text-left ${selectedType === type.value
                ? 'bg-orange-500/20 border-2 border-orange-500'
                : 'glass-card hover:border-orange-500/50'
                }`}
            >
              <type.icon className={`w-6 h-6 mb-2 ${selectedType === type.value ? 'text-orange-400' : 'text-gray-400'}`} />
              <div className="font-semibold mb-1">
                {type.label}
              </div>
              <div className="text-sm">{type.description}</div>
            </button>
          ))}
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full px-6 py-4 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 text-white font-semibold rounded-xl transition-colors flex items-center justify-center space-x-2"
        >
          {generating ? (
            <>
              <Loader className="w-5 h-5 animate-spin text-orange-500" />
              <span>Generating Report from Real Data...</span>
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              <span>Generate {reportTypes.find(t => t.value === selectedType)?.label}</span>
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-accent-red/10 border border-accent-red/20 rounded-xl flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-accent-red font-semibold">Error</div>
              <div className="text-gray-300 text-sm">{error}</div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Generated Report Display */}
      {report && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-6 h-6 text-accent-green" />
                <h2 className="text-2xl font-semibold text-white">{report.title}</h2>
              </div>
              <div className="text-sm text-gray-400">
                Generated: {new Date(report.generatedAt).toLocaleString()} |
                Source: {report.dataSource}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleExportPDF}
                disabled={exportingPDF}
                className="px-4 py-2 bg-accent-green/10 border border-accent-green/20 rounded-xl text-accent-green font-medium hover:bg-accent-green/20 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {exportingPDF ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <FileDown className="w-4 h-4" />
                )}
                <span>{exportingPDF ? 'Exporting...' : 'Export PDF'}</span>
              </button>
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-orange-500/10 border border-orange-500/20 rounded-xl text-orange-400 font-medium hover:bg-orange-500/20 transition-colors flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download TXT</span>
              </button>
            </div>
          </div>

          {/* PDF Export Wrapper - Dark Mode Compatible */}
          <div id="report-content" className="glass-card p-6 rounded-xl">
            {/* Report Header for PDF */}
            <div className="mb-6 pb-4 border-b-2 border-orange-500">
              <h1 className="text-2xl font-bold text-white">{report.title}</h1>
              <p className="text-sm text-gray-400 mt-1">
                Generated: {new Date(report.generatedAt).toLocaleString()} | Source: {report.dataSource}
              </p>
            </div>

            {report.error ? (
              <div className="p-4 bg-accent-red/10 border border-accent-red/20 rounded-xl">
                <div className="text-accent-red font-semibold">{report.error}</div>
                <div className="text-gray-400 text-sm mt-2">Please upload files to generate reports with real data.</div>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Text Sections */}
                {report.sections.map((section, i) => (
                  <div key={i} className="border-l-4 border-orange-500 pl-4">
                    <h3 className="text-lg font-semibold text-white mb-2">{section.title}</h3>
                    <pre className="text-gray-300 whitespace-pre-wrap font-mono text-sm leading-relaxed">
                      {section.content}
                    </pre>
                  </div>
                ))}

                {/* Enterprise Charts Section */}
                {dashboardStats?.hasData && (
                  <div className="mt-8 pt-8 border-t border-orange-500/30">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                      <BarChart3 className="w-6 h-6 text-orange-400" />
                      Visual Analytics
                    </h3>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Revenue Trend Chart */}
                      {dashboardStats.revenueTimeline?.length > 0 && (
                        <div className="glass-card p-6">
                          <h4 className="text-lg font-semibold text-white mb-4">Revenue Trend</h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <AreaChart data={dashboardStats.revenueTimeline}>
                              <defs>
                                <linearGradient id="reportRevenueGradient" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#F97316" stopOpacity={0.4} />
                                  <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                              <XAxis
                                dataKey="month"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                              />
                              <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                                tickFormatter={(v) => formatCompactCurrency(v, currency)}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#1E293B',
                                  border: '1px solid #475569',
                                  borderRadius: '12px',
                                }}
                                formatter={(value: number) => [formatCurrency(value, currency), 'Revenue']}
                              />
                              <Area
                                type="monotone"
                                dataKey="revenue"
                                stroke="#F97316"
                                strokeWidth={3}
                                fill="url(#reportRevenueGradient)"
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {/* Customer Segments Pie Chart - Uses segmentSummary for proper categories */}
                      {dashboardStats.segmentSummary?.length > 0 && (
                        <div className="glass-card p-6">
                          <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <PieChartIcon className="w-5 h-5 text-green-400" />
                            Customer Segments
                          </h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                              <Pie
                                data={dashboardStats.segmentSummary}
                                dataKey="revenue"
                                nameKey="segment"
                                cx="50%"
                                cy="50%"
                                innerRadius={50}
                                outerRadius={80}
                                paddingAngle={3}
                              >
                                {dashboardStats.segmentSummary.map((_: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#1E293B',
                                  border: '1px solid #475569',
                                  borderRadius: '12px',
                                }}
                                formatter={(value: number, name: string) => [
                                  `${formatCurrency(value, currency)} (${dashboardStats.segmentSummary.find((s: any) => s.segment === name)?.count || 0} customers)`,
                                  name
                                ]}
                              />
                              <Legend
                                verticalAlign="bottom"
                                height={36}
                                formatter={(value) => <span className="text-gray-300 text-sm">{value}</span>}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {/* Top Products Bar Chart */}
                      {dashboardStats.abcAnalysis?.products?.length > 0 && (
                        <div className="glass-card p-6 lg:col-span-2">
                          <h4 className="text-lg font-semibold text-white mb-4">Top Products by Revenue</h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={dashboardStats.abcAnalysis.products.slice(0, 8)} layout="vertical">
                              <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                              <XAxis
                                type="number"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                                tickFormatter={(v) => formatCompactCurrency(v, currency)}
                              />
                              <YAxis
                                type="category"
                                dataKey="name"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                                width={120}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#1E293B',
                                  border: '1px solid #475569',
                                  borderRadius: '12px',
                                }}
                                formatter={(value: number) => [formatCurrency(value, currency), 'Revenue']}
                              />
                              <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                                {dashboardStats.abcAnalysis.products.slice(0, 8).map((_: any, index: number) => (
                                  <Cell key={`bar-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {!report && !generating && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <FileText className="w-16 h-16 text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Report Generated Yet</h3>
          <p className="text-gray-400 mb-4">
            Select a report type above and click generate to create a report from your uploaded files.
          </p>
          {!analytics?.hasData && (
            <a
              href="/data-hub"
              className="inline-block px-6 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl transition-colors"
            >
              Upload Files First
            </a>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Reports;
