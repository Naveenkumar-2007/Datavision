/**
 * Reports Page - Business Intelligence Reports
 * Supports dark/light theme matching Landing page design
 */

import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FileText,
  Download,
  TrendingUp,
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
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  BarChart as BarChartComponent,
  Bar,
} from 'recharts';
import { apiService } from '@/services/api';
import { formatCurrency, getCurrencySymbol, getUserPreferredCurrency } from '@/utils/currency';
import { exportToPDF } from '@/utils/pdfExport';

interface ThemeContext {
  isDark: boolean;
  bgColor: string;
  cardBg: string;
  textPrimary: string;
  textMuted: string;
  borderColor: string;
}

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
  const theme = useOutletContext<ThemeContext>() || {
    isDark: true,
    bgColor: '#0a0a0b',
    cardBg: '#141414',
    textPrimary: '#F8FAFC',
    textMuted: '#9CA3AF',
    borderColor: '#262626',
  };

  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [generating, setGenerating] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('metrics');
  const [analytics, setAnalytics] = useState<any>(null);
  // Removed dashboardStats - no longer needed

  const CHART_COLORS = ['#14B8A6', '#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899'];
  const userPreferredCurrency = getUserPreferredCurrency();
  const currency = userPreferredCurrency;
  const currencySymbol = getCurrencySymbol(currency);
  const hasMultipleCurrencies = analytics?.currencyBreakdown?.currencies_count > 1;

  // Commented out as these are no longer needed with dynamic metrics
  // const rawRevenue = hasMultipleCurrencies
  //   ? analytics?.currencyBreakdown?.total_usd_equivalent || analytics?.metrics?.totalRevenue
  //   : analytics?.metrics?.totalRevenue || 0;
  // const displayRevenue = hasMultipleCurrencies && currency !== 'USD'
  //   ? convertCurrency(rawRevenue, 'USD', currency)
  //   : rawRevenue;

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      // Use unified analytics for consistency with Overview and Dashboards
      const analyticsResponse = await apiService.getUnifiedAnalytics();
      setAnalytics(analyticsResponse.data);
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
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const content = `${report.title}\nGenerated: ${new Date(report.generatedAt).toLocaleString()}\n\n${report.sections.map(s => `${s.title}\n${'='.repeat(s.title.length)}\n${s.content}`).join('\n\n')}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${report.reportType}_report.txt`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handleExportPDF = async () => {
    if (!report) return;
    setExportingPDF(true);
    try {
      await exportToPDF('report-content', { filename: `${report.reportType}_report`, orientation: 'portrait', margin: 15 });
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
      setExportingPDF(false);
    }
  };

  const reportTypes = [
    { value: 'metrics', label: 'Metrics Analysis', description: 'Analyze numeric data', icon: TrendingUp },
    { value: 'breakdown', label: 'Data Breakdown', description: 'Category distributions', icon: PieChartIcon },
    { value: 'summary', label: 'Data Summary', description: 'Complete overview', icon: BarChart3 },
    { value: 'executive', label: 'Executive Summary', description: 'High-level insights', icon: FileText },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold" style={{ color: theme.textPrimary }}>Data Reports</h1>
        <p className="text-sm" style={{ color: theme.textMuted }}>Automatic reports generated from your uploaded data</p>
      </motion.div>

      {/* Key Metrics - Dynamic from Unified Analytics */}
      {analytics?.hasData && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {hasMultipleCurrencies && (
            <div className="p-4 rounded-2xl border" style={{ backgroundColor: theme.cardBg, borderColor: '#14B8A6' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">💰</span>
                  <div>
                    <div className="font-semibold" style={{ color: theme.textPrimary }}>
                      {analytics.currencyBreakdown?.currencies_count} Currencies Detected
                    </div>
                    <div className="text-sm" style={{ color: theme.textMuted }}>
                      Auto-converted to {currencySymbol} ({currency})
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Use KPIs from unified analytics (same as Overview/Dashboards) */}
            {(() => {
              // Get KPIs from unified analytics - same source as Overview/Dashboards
              const kpis = analytics.overviewLayout?.kpis || analytics.dashboardLayout?.kpis || [];

              if (kpis.length > 0) {
                return kpis.slice(0, 4).map((kpi: any, i: number) => {
                  const kpiColor = kpi.color || CHART_COLORS[i % CHART_COLORS.length];
                  const hasDelta = kpi.delta !== null && kpi.delta !== undefined;
                  const isPositive = hasDelta && kpi.delta > 0;
                  const hasSparkline = kpi.sparkline && kpi.sparkline.length > 2;

                  // Generate sparkline path
                  const getSparkPath = () => {
                    if (!hasSparkline) return '';
                    const data = kpi.sparkline;
                    const max = Math.max(...data);
                    const min = Math.min(...data);
                    const range = max - min || 1;
                    const step = 50 / (data.length - 1);
                    return data.map((v: number, idx: number) =>
                      `${idx === 0 ? 'M' : 'L'}${idx * step},${18 - ((v - min) / range) * 14}`
                    ).join(' ');
                  };

                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.08 }}
                      className="p-4 rounded-2xl border relative overflow-hidden"
                      style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                    >
                      {/* Gradient accent */}
                      <div
                        className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20 pointer-events-none"
                        style={{ background: `radial-gradient(circle, ${kpiColor} 0%, transparent 70%)` }}
                      />

                      <div className="relative z-10 flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 rounded-full" style={{ background: kpiColor }} />
                            <span className="text-[10px] uppercase font-bold tracking-wider" style={{ color: kpiColor }}>
                              {kpi.title}
                            </span>
                          </div>
                          <div className="text-2xl font-black" style={{ color: theme.textPrimary }}>
                            {kpi.format === 'currency' && <span className="text-lg opacity-60">$</span>}
                            {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
                          </div>
                          {hasDelta ? (
                            <div className="flex items-center gap-1.5 mt-2">
                              <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${isPositive ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingUp className="w-3 h-3 rotate-180" />}
                                {isPositive ? '+' : ''}{kpi.delta.toFixed(1)}%
                              </div>
                            </div>
                          ) : (
                            <div className="text-[10px] mt-2" style={{ color: theme.textMuted }}>Current value</div>
                          )}
                        </div>

                        {/* Mini sparkline */}
                        {hasSparkline && (
                          <svg className="w-12 h-6" viewBox="0 0 50 18">
                            <defs>
                              <linearGradient id={`rpt-grad-${i}`} x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor={isPositive ? '#22C55E' : '#EF4444'} stopOpacity="0.3" />
                                <stop offset="100%" stopColor={isPositive ? '#22C55E' : '#EF4444'} stopOpacity="0" />
                              </linearGradient>
                            </defs>
                            <path d={`${getSparkPath()} L50,18 L0,18 Z`} fill={`url(#rpt-grad-${i})`} />
                            <path d={getSparkPath()} fill="none" stroke={isPositive ? '#22C55E' : '#EF4444'} strokeWidth="1.5" strokeLinecap="round" />
                          </svg>
                        )}
                      </div>
                    </motion.div>
                  );
                });
              }

              // Fallback if no KPIs from unified analytics
              const dataShape = analytics.dataShape || {};
              return (
                <>
                  <div className="p-4 rounded-2xl border" style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}>
                    <div className="flex items-center gap-3">
                      <FileText className="w-8 h-8" style={{ color: '#22C55E' }} />
                      <div>
                        <div className="text-xl font-bold" style={{ color: theme.textPrimary }}>{(dataShape.rows || 0).toLocaleString()}</div>
                        <div className="text-sm" style={{ color: theme.textMuted }}>Total Records</div>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 rounded-2xl border" style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}>
                    <div className="flex items-center gap-3">
                      <BarChart3 className="w-8 h-8" style={{ color: '#14B8A6' }} />
                      <div>
                        <div className="text-xl font-bold" style={{ color: theme.textPrimary }}>{dataShape.columns || 0}</div>
                        <div className="text-sm" style={{ color: theme.textMuted }}>Data Columns</div>
                      </div>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </motion.div>
      )}

      {/* Generate Report */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="p-6 rounded-2xl border"
        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
      >
        <h2 className="text-lg font-semibold mb-6" style={{ color: theme.textPrimary }}>Generate New Report</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {reportTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setSelectedType(type.value)}
              className={`p-4 rounded-xl transition-all text-left border ${selectedType === type.value ? 'border-teal-500 bg-teal-500/10' : 'hover:border-teal-500/50'}`}
              style={{ backgroundColor: selectedType === type.value ? 'rgba(20, 184, 166, 0.1)' : theme.cardBg, borderColor: selectedType === type.value ? '#14B8A6' : theme.borderColor }}
            >
              <type.icon className={`w-6 h-6 mb-2`} style={{ color: selectedType === type.value ? '#14B8A6' : theme.textMuted }} />
              <div className="font-semibold" style={{ color: theme.textPrimary }}>{type.label}</div>
              <div className="text-sm" style={{ color: theme.textMuted }}>{type.description}</div>
            </button>
          ))}
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full px-6 py-4 bg-teal-500 hover:bg-teal-600 disabled:bg-gray-600 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          {generating ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Generating Report...</span>
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              <span>Generate {reportTypes.find(t => t.value === selectedType)?.label}</span>
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 rounded-xl border bg-red-500/10 border-red-500/30">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <div>
                <div className="text-red-400 font-semibold">Error</div>
                <div className="text-sm" style={{ color: theme.textMuted }}>{error}</div>
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Generated Report */}
      {report && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 rounded-2xl border"
          style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
                <h2 className="text-xl font-semibold" style={{ color: theme.textPrimary }}>{report.title}</h2>
              </div>
              <div className="text-sm" style={{ color: theme.textMuted }}>
                Generated: {new Date(report.generatedAt).toLocaleString()} | Source: {report.dataSource}
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={handleExportPDF} disabled={exportingPDF} className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 font-medium hover:bg-emerald-500/20 transition-colors flex items-center gap-2">
                {exportingPDF ? <Loader className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                <span>{exportingPDF ? 'Exporting...' : 'Export PDF'}</span>
              </button>
              <button onClick={handleDownload} className="px-4 py-2 bg-teal-500/10 border border-teal-500/30 rounded-xl text-teal-400 font-medium hover:bg-teal-500/20 transition-colors flex items-center gap-2">
                <Download className="w-4 h-4" />
                <span>Download TXT</span>
              </button>
            </div>
          </div>

          <div id="report-content" className="p-6 rounded-xl border" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)', borderColor: theme.borderColor }}>
            <div className="mb-6 pb-4 border-b-2" style={{ borderColor: '#14B8A6' }}>
              <h1 className="text-xl font-bold" style={{ color: theme.textPrimary }}>{report.title}</h1>
              <p className="text-sm mt-1" style={{ color: theme.textMuted }}>Generated: {new Date(report.generatedAt).toLocaleString()} | Source: {report.dataSource}</p>
            </div>

            {report.error ? (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                <div className="text-red-400 font-semibold">{report.error}</div>
              </div>
            ) : (
              <div className="space-y-6">
                {report.sections.map((section: any, i: number) => {
                  // Check if section has chart data
                  const hasChartData = Array.isArray(section.data) && section.data.length > 0 && section.chartType;

                  return (
                    <div key={i} className="border-l-4 pl-4" style={{ borderColor: CHART_COLORS[i % CHART_COLORS.length] }}>
                      <h3 className="text-lg font-semibold mb-2" style={{ color: theme.textPrimary }}>{section.title}</h3>

                      {/* Text content */}
                      <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed mb-4" style={{ color: theme.textMuted }}>{section.content}</pre>

                      {/* Chart visualization if available */}
                      {hasChartData && (
                        <div className="mt-4 p-4 rounded-xl border" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)', borderColor: theme.borderColor }}>
                          <ResponsiveContainer width="100%" height={200}>
                            {section.chartType === 'pie' ? (
                              <PieChart>
                                <Pie
                                  data={section.data}
                                  dataKey="value"
                                  nameKey="name"
                                  cx="50%"
                                  cy="50%"
                                  innerRadius={40}
                                  outerRadius={70}
                                  paddingAngle={3}
                                >
                                  {section.data.map((item: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={item.color || CHART_COLORS[index % CHART_COLORS.length]} />
                                  ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                <Legend />
                              </PieChart>
                            ) : section.chartType === 'line' ? (
                              <AreaChart data={section.data}>
                                <defs>
                                  <linearGradient id={`gradient-${i}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#14B8A6" stopOpacity={0} />
                                  </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} vertical={false} />
                                <XAxis dataKey="period" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                <Area type="monotone" dataKey="value" stroke="#14B8A6" strokeWidth={2} fill={`url(#gradient-${i})`} />
                              </AreaChart>
                            ) : section.chartType === 'bar' ? (
                              /* Actual BAR chart for breakdown/executive reports */
                              <BarChartComponent data={section.data} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} horizontal={true} vertical={false} />
                                <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} width={80} />
                                <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                  {section.data.map((item: any, index: number) => (
                                    <Cell key={`bar-${index}`} fill={item.color || CHART_COLORS[index % CHART_COLORS.length]} />
                                  ))}
                                </Bar>
                              </BarChartComponent>
                            ) : (
                              /* Fallback to PIE chart */
                              <PieChart>
                                <Pie
                                  data={section.data.slice(0, 8)}
                                  dataKey="value"
                                  nameKey="name"
                                  cx="50%"
                                  cy="50%"
                                  innerRadius={40}
                                  outerRadius={70}
                                  paddingAngle={3}
                                >
                                  {section.data.slice(0, 8).map((item: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={item.color || CHART_COLORS[index % CHART_COLORS.length]} />
                                  ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                <Legend />
                              </PieChart>
                            )}
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {!report && !generating && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-12 rounded-2xl text-center border" style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}>
          <FileText className="w-16 h-16 mx-auto mb-4" style={{ color: theme.textMuted }} />
          <h3 className="text-xl font-semibold mb-2" style={{ color: theme.textPrimary }}>No Report Generated Yet</h3>
          <p className="mb-4" style={{ color: theme.textMuted }}>Select a report type above and click generate.</p>
          {!analytics?.hasData && (
            <a href="/data-hub" className="inline-block px-6 py-2 bg-teal-500 hover:bg-teal-600 text-white rounded-full transition-colors">
              Upload Files First
            </a>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Reports;
