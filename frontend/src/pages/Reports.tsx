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
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Funnel,
  FunnelChart,
  LabelList,
  ScatterChart,
  Scatter,
} from 'recharts';
import { apiService } from '@/services/api';
import { getCurrencySymbol, getUserPreferredCurrency } from '@/utils/currency';
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
  data?: any[];
  chartType?: string;
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
  const [hasMLModel, setHasMLModel] = useState(false);
  const [mlModelInfo, setMlModelInfo] = useState<any>(null);

  const CHART_COLORS = ['#14B8A6', '#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899'];
  const userPreferredCurrency = getUserPreferredCurrency();
  const currency = userPreferredCurrency;
  const currencySymbol = getCurrencySymbol(currency);
  const hasMultipleCurrencies = analytics?.currencyBreakdown?.currencies_count > 1;

  useEffect(() => {
    loadAnalytics();
    checkMLModel();
  }, []);

  // Listen for file updates from DataHub - refresh analytics when files change
  useEffect(() => {
    const handleFilesUpdated = () => {
      console.log('📁 Files updated - refreshing reports analytics...');
      loadAnalytics();
      checkMLModel();
    };

    window.addEventListener('filesUpdated', handleFilesUpdated);
    return () => window.removeEventListener('filesUpdated', handleFilesUpdated);
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

  const checkMLModel = async () => {
    try {
      const userId = localStorage.getItem('userId') || 'default';
      const response = await fetch(`/api/v2/autonomous/models/${userId}`);
      const data = await response.json();
      if (data.success && data.has_models) {
        setHasMLModel(true);
        setMlModelInfo(data.active_model);
      }
    } catch (err) {
      console.log('No ML model found');
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
    { value: 'metrics', label: 'Metrics Analysis', description: 'Analyze numeric data with trends', icon: TrendingUp, color: '#14B8A6' },
    { value: 'breakdown', label: 'Data Breakdown', description: 'Category distributions & segments', icon: PieChartIcon, color: '#8B5CF6' },
    { value: 'summary', label: 'Data Summary', description: 'Complete overview of all data', icon: BarChart3, color: '#3B82F6' },
    { value: 'executive', label: 'Executive Summary', description: 'High-level insights for leaders', icon: FileText, color: '#22C55E' },
    {
      value: 'predictive',
      label: '🔮 Predictive Report',
      description: hasMLModel
        ? `Uses ${mlModelInfo?.model_name || 'trained model'} for predictions`
        : 'ML forecasts & predictions (train a model first)',
      icon: TrendingUp,
      color: '#F59E0B',
      badge: hasMLModel ? 'AutoML' : 'AI'
    },
    {
      value: 'anomaly',
      label: '⚠️ Anomaly Report',
      description: hasMLModel
        ? `Detect anomalies in ${mlModelInfo?.target_column || 'target'} data`
        : 'Outliers & unusual patterns detection',
      icon: AlertCircle,
      color: '#EF4444',
      badge: hasMLModel ? 'AutoML' : 'AI'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold" style={{ color: theme.textPrimary }}>Data Reports</h1>
        <p className="text-sm" style={{ color: theme.textMuted }}>Automatic reports generated from your uploaded data</p>
      </motion.div>

      {/* ML Model Status Banner */}
      {hasMLModel && mlModelInfo && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl border bg-gradient-to-r from-amber-500/10 to-teal-500/10"
          style={{ borderColor: '#F59E0B' }}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">🤖</span>
            <div className="flex-1">
              <div className="font-semibold" style={{ color: theme.textPrimary }}>
                AutoML Model Ready: {mlModelInfo.model_name}
              </div>
              <div className="text-sm" style={{ color: theme.textMuted }}>
                {mlModelInfo.task_type?.toUpperCase()} • Target: {mlModelInfo.target_column} •
                Score: {(() => {
                  const m = mlModelInfo.metrics || {};
                  const score = m.accuracy || m.f1_score || m.f1 || m.precision || m.r2 || m.r2_score || 0;
                  return (score * 100).toFixed(1);
                })()}%
              </div>
            </div>
            <div className="px-3 py-1 bg-teal-500/20 text-teal-400 text-xs font-bold rounded-full">
              v{mlModelInfo.version}
            </div>
          </div>
        </motion.div>
      )}

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

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {reportTypes.map((type, idx) => (
            <motion.button
              key={type.value}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => setSelectedType(type.value)}
              className={`p-5 rounded-xl transition-all text-left border relative overflow-hidden group ${selectedType === type.value
                ? 'ring-2 ring-offset-2 ring-offset-transparent'
                : 'hover:scale-[1.02]'
                }`}
              style={{
                backgroundColor: selectedType === type.value ? `${type.color}15` : theme.cardBg,
                borderColor: selectedType === type.value ? type.color : theme.borderColor,
                // @ts-ignore
                '--tw-ring-color': type.color
              }}
            >
              {/* Gradient accent */}
              <div
                className="absolute top-0 right-0 w-20 h-20 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity"
                style={{ background: `radial-gradient(circle, ${type.color} 0%, transparent 70%)` }}
              />

              {/* AI Badge */}
              {type.badge && (
                <div
                  className="absolute top-3 right-3 px-2 py-0.5 rounded-full text-[10px] font-bold"
                  style={{ backgroundColor: `${type.color}20`, color: type.color }}
                >
                  {type.badge}
                </div>
              )}

              <div className="relative z-10">
                <type.icon
                  className="w-8 h-8 mb-3"
                  style={{ color: selectedType === type.value ? type.color : theme.textMuted }}
                />
                <div className="font-semibold text-base mb-1" style={{ color: theme.textPrimary }}>
                  {type.label}
                </div>
                <div className="text-sm" style={{ color: theme.textMuted }}>
                  {type.description}
                </div>
              </div>

              {/* Selection indicator */}
              {selectedType === type.value && (
                <div
                  className="absolute bottom-0 left-0 right-0 h-1 rounded-b-xl"
                  style={{ backgroundColor: type.color }}
                />
              )}
            </motion.button>
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

            {/* AI Key Findings Section - Fully Autonomous */}
            {report.sections && report.sections.length > 0 && (() => {
              // Extract insights dynamically from report sections
              const firstSection = report.sections[0];
              const topInsight = firstSection?.content?.split('\n').filter((l: string) => l.trim())[0] || 'Data analysis complete';

              // Find action/recommendation section
              const actionSection = report.sections.find((s: any) =>
                s.title?.toLowerCase().includes('recommend') ||
                s.title?.toLowerCase().includes('action') ||
                s.title?.toLowerCase().includes('next')
              );
              const actionText = actionSection?.content?.split('\n').filter((l: string) => l.trim())[0]?.replace(/^\d+\.\s*/, '')?.replace(/^\*\s*/, '') ||
                (report.sections[1]?.content?.split('\n')[0] || 'Review data for opportunities');

              // Calculate confidence based on data richness
              const dataPoints = report.sections.reduce((acc: number, s: any) => {
                if (s.data && Array.isArray(s.data)) return acc + s.data.length;
                if (s.data && typeof s.data === 'object') return acc + Object.keys(s.data).length;
                return acc + 1;
              }, 0);
              const confidence = dataPoints > 20 ? 'Very High' : dataPoints > 10 ? 'High' : dataPoints > 5 ? 'Medium' : 'Standard';

              return (
                <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-teal-500/10 to-indigo-500/10 border border-teal-500/30">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">🤖</span>
                    <h3 className="font-semibold" style={{ color: theme.textPrimary }}>AI Key Findings</h3>
                    <span className="px-2 py-0.5 bg-teal-500/20 text-teal-400 text-[10px] font-bold rounded-full">AUTO-GENERATED</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-green-400">📈</span>
                        <span className="text-xs font-bold text-green-400">TOP INSIGHT</span>
                      </div>
                      <p className="text-sm" style={{ color: theme.textMuted }}>
                        {topInsight.slice(0, 100)}{topInsight.length > 100 ? '...' : ''}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-amber-400">⚡</span>
                        <span className="text-xs font-bold text-amber-400">ACTION ITEM</span>
                      </div>
                      <p className="text-sm" style={{ color: theme.textMuted }}>
                        {actionText.slice(0, 100)}{actionText.length > 100 ? '...' : ''}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-blue-400">🎯</span>
                        <span className="text-xs font-bold text-blue-400">CONFIDENCE</span>
                      </div>
                      <p className="text-sm" style={{ color: theme.textMuted }}>
                        {confidence} confidence • {report.sections.length} sections • {dataPoints} data points
                      </p>
                    </div>
                  </div>
                </div>
              );
            })()}

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
                          <ResponsiveContainer width="100%" height={250}>
                            {(() => {
                              // AUTONOMOUS CHART SELECTOR - decides best chart based on data
                              const chartType = section.chartType || 'bar';
                              const data = section.data || [];
                              const dataCount = data.length;

                              // Autonomous chart selection based on data characteristics
                              const getAutonomousChartType = () => {
                                if (chartType) return chartType; // Use backend suggestion if available

                                // Analyze data to choose best chart
                                const hasPercentage = data.some((d: any) => d.percentage !== undefined);
                                const hasNegativeValues = data.some((d: any) => d.value < 0);
                                const hasTimeSeries = data.some((d: any) => d.period || d.date || d.time);

                                if (hasTimeSeries) return 'area';
                                if (hasNegativeValues) return 'bar';
                                if (hasPercentage && dataCount <= 6) return 'donut';
                                if (dataCount > 10) return 'horizontal_bar';
                                if (dataCount <= 5) return 'pie';
                                return 'bar';
                              };

                              const selectedChart = getAutonomousChartType();

                              // DONUT CHART - for summary distributions
                              if (selectedChart === 'donut') {
                                return (
                                  <PieChart>
                                    <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3}>
                                      {data.map((item: any, idx: number) => (
                                        <Cell key={`donut-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                      ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Legend />
                                  </PieChart>
                                );
                              }

                              // PIE CHART - for distributions
                              if (selectedChart === 'pie') {
                                return (
                                  <PieChart>
                                    <Pie data={data.slice(0, 8)} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={30} outerRadius={70} paddingAngle={3}>
                                      {data.slice(0, 8).map((item: any, idx: number) => (
                                        <Cell key={`pie-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                      ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Legend />
                                  </PieChart>
                                );
                              }

                              // HORIZONTAL BAR - for category comparisons
                              if (selectedChart === 'horizontal_bar') {
                                return (
                                  <BarChartComponent data={data} layout="vertical" margin={{ left: 20, right: 30 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} horizontal={true} vertical={false} />
                                    <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} width={100} />
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                      {data.map((item: any, idx: number) => (
                                        <Cell key={`hbar-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                      ))}
                                    </Bar>
                                  </BarChartComponent>
                                );
                              }

                              // AREA CHART - for trends and forecasts
                              if (selectedChart === 'area' || selectedChart === 'line') {
                                return (
                                  <AreaChart data={data} margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
                                    <defs>
                                      <linearGradient id={`areaGrad-${i}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0.4} />
                                        <stop offset="95%" stopColor={CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0} />
                                      </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} vertical={false} />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />

                                    {/* Confidence Interval Band (Upper - Lower) */}
                                    {section.dataKeys && section.dataKeys.includes('upper') && (
                                      <Area
                                        type="monotone"
                                        dataKey="upper"
                                        stroke="none"
                                        fill={CHART_COLORS[i % CHART_COLORS.length]}
                                        fillOpacity={0.1}
                                        isAnimationActive={false}
                                      />
                                    )}
                                    {section.dataKeys && section.dataKeys.includes('lower') && (
                                      <Area
                                        type="monotone"
                                        dataKey="lower"
                                        stroke="none"
                                        fill={theme.cardBg}
                                        fillOpacity={1}
                                        isAnimationActive={false}
                                      />
                                    )}

                                    {/* Main Value Line/Area */}
                                    <Area
                                      type="monotone"
                                      dataKey="value"
                                      stroke={CHART_COLORS[i % CHART_COLORS.length]}
                                      strokeWidth={2}
                                      fill={`url(#areaGrad-${i})`}
                                    />
                                  </AreaChart>
                                );
                              }

                              // SCATTER CHART - for correlations and predictions
                              if (selectedChart === 'scatter') {
                                return (
                                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} />
                                    <XAxis type="number" dataKey="x" name={section.xLabel || "X"} axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <YAxis type="number" dataKey="y" name={section.yLabel || "Y"} axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Scatter name={section.title} data={data} fill={CHART_COLORS[0]}>
                                      {data.map((entry: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={entry.color || CHART_COLORS[index % CHART_COLORS.length]} />
                                      ))}
                                    </Scatter>
                                  </ScatterChart>
                                );
                              }

                              // BOX CHART (simulated) - for anomaly/outlier detection
                              if (selectedChart === 'box') {
                                // Use median for box plot data visualization
                                return (
                                  <BarChartComponent data={data} margin={{ left: 10, right: 30 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} vertical={false} />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <Tooltip
                                      contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }}
                                      formatter={(value: any, name: string, props: any) => {
                                        const item = props.payload;
                                        return [
                                          <div key="tooltip">
                                            <div>Min: {item.min}</div>
                                            <div>Q1: {item.q1}</div>
                                            <div>Median: {item.median}</div>
                                            <div>Q3: {item.q3}</div>
                                            <div>Max: {item.max}</div>
                                            <div>Outliers: {item.outliers}</div>
                                          </div>,
                                          ''
                                        ];
                                      }}
                                    />
                                    <Bar dataKey="median" radius={[4, 4, 4, 4]} name="Median">
                                      {data.map((item: any, idx: number) => (
                                        <Cell key={`box-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                      ))}
                                    </Bar>
                                  </BarChartComponent>
                                );
                              }

                              // GAUGE (simulated with radial) - for KPIs
                              if (selectedChart === 'gauge') {
                                return (
                                  <PieChart>
                                    <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" startAngle={180} endAngle={0} innerRadius={60} outerRadius={80}>
                                      {data.map((item: any, idx: number) => (
                                        <Cell key={`gauge-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                      ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Legend />
                                  </PieChart>
                                );
                              }

                              // RADAR CHART - for multi-metric comparison
                              if (selectedChart === 'radar') {
                                return (
                                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
                                    <PolarGrid stroke={theme.borderColor} />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    {section.keys && section.keys.map((key: string, idx: number) => (
                                      <Radar
                                        key={key}
                                        name={key}
                                        dataKey={key}
                                        stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                                        fill={CHART_COLORS[idx % CHART_COLORS.length]}
                                        fillOpacity={0.3}
                                      />
                                    ))}
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Legend />
                                  </RadarChart>
                                );
                              }

                              // FUNNEL CHART - for process stages
                              if (selectedChart === 'funnel') {
                                return (
                                  <FunnelChart>
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Funnel
                                      dataKey="value"
                                      data={data}
                                      isAnimationActive
                                    >
                                      <LabelList position="right" fill={theme.textPrimary} stroke="none" dataKey="name" />
                                    </Funnel>
                                  </FunnelChart>
                                );
                              }

                              // DEFAULT: VERTICAL BAR CHART or explicit 'bar' type
                              if (selectedChart === 'bar') {
                                return (
                                  <BarChartComponent data={data} margin={{ left: 10, right: 30 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} vertical={false} />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                    <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                      {data.map((item: any, idx: number) => (
                                        <Cell key={`vbar-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                      ))}
                                    </Bar>
                                  </BarChartComponent>
                                );
                              }

                              // DEFAULT: Horizontal BAR CHART (fallback)
                              return (
                                <BarChartComponent data={data} layout="vertical" margin={{ left: 20, right: 30 }}>
                                  <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} horizontal={true} vertical={false} />
                                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} />
                                  <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 10 }} width={80} />
                                  <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, borderRadius: '8px' }} />
                                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {data.map((item: any, idx: number) => (
                                      <Cell key={`bar-${idx}`} fill={item.color || CHART_COLORS[idx % CHART_COLORS.length]} />
                                    ))}
                                  </Bar>
                                </BarChartComponent>
                              );
                            })()}
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
