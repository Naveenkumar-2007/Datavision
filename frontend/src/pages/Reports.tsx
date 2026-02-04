/**
 * Reports Page - Business Intelligence Reports
 * Supports dark/light theme matching Landing page design
 */

import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
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
import { getUserIdSync, getAuthHeadersSync } from '@/utils/userId';

interface ReportSection {
  title: string;
  content: string;
  data?: any[];
  chartType?: string;
  plotlyData?: any;  // For real ML charts (confusion matrix, feature importance, etc.)
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
  const { isDark } = useUserStore();

  // Derived theme object for JS-side libraries (Charts) that need explicit hex values
  const theme = {
    isDark,
    bgColor: isDark ? '#0a0a0f' : '#f8fafc',
    cardBg: isDark ? '#18181b' : '#ffffff',
    textPrimary: isDark ? '#ffffff' : '#0f172a',
    textMuted: isDark ? '#a1a1aa' : '#64748b',
    borderColor: isDark ? '#3f3f46' : '#cbd5e1',
  };

  const [report, setReport] = useState<GeneratedReport | null>(null);
  const [generating, setGenerating] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('metrics');
  const [analytics, setAnalytics] = useState<any>(null);
  const [hasMLModel, setHasMLModel] = useState(false);
  const [mlModelInfo, setMlModelInfo] = useState<any>(null);

  const CHART_COLORS = ['#22c55e', '#16a34a', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899'];
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
      const userId = getUserIdSync();
      let foundModel = false;

      // 1. Try Backend API first
      try {
        const response = await fetch(`/api/v2/autonomous/models/${userId}`, {
          headers: getAuthHeadersSync()
        });
        const data = await response.json();
        if (data.success && data.has_models) {
          setHasMLModel(true);
          setMlModelInfo(data.active_model);
          foundModel = true;
        }
      } catch (err) {
        console.log('Backend model check failed, checking local storage...');
      }

      // 2. Fallback to LocalStorage if backend fails or returns false
      if (!foundModel) {
        const savedResult = localStorage.getItem('automlResult');
        if (savedResult) {
          try {
            const parsed = JSON.parse(savedResult);
            if (parsed && parsed.success) {
              console.log('✅ Found trained model in localStorage (fallback)');
              setHasMLModel(true);
              setMlModelInfo({
                model_name: parsed.best_model?.name || 'Local Model',
                task_type: parsed.task_type || 'classification',
                target_column: parsed.target_column || 'target',
                metrics: parsed.best_model?.metrics || {},
                version: '1.0 (Local)'
              });
            }
          } catch (e) {
            console.error('Failed to parse local model result');
          }
        }
      }
    } catch (err) {
      console.log('Error checking for ML models');
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      // Get local fallback model if available
      let fallbackModel = null;
      try {
        const savedResult = localStorage.getItem('automlResult');
        if (savedResult) {
          const parsed = JSON.parse(savedResult);

          // Map to backend structure if valid
          if (parsed && parsed.success) {
            console.log("📤 Sending local model as fallback:", parsed.best_model?.name);
            fallbackModel = {
              model_name: parsed.best_model?.name || 'Local Model',
              task_type: parsed.task_type || 'classification',
              target_column: parsed.target_column || 'target',
              metrics: parsed.best_model?.metrics || {},
              feature_importance: parsed.feature_importance || {},
              features: parsed.feature_columns || []
            };
          }
        }
      } catch (e) {
        console.warn('Could not load local fallback model', e);
      }

      const response = await apiService.generateReport(selectedType, undefined, fallbackModel);
      setReport(response.data);
    } catch (err: any) {
      console.error("Report generation failed:", err);
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    
    // Clean content for better readability
    const cleanContent = (text: string) => {
      return text
        .replace(/\*\*/g, '')  // Remove bold markers
        .replace(/`/g, '')     // Remove code markers
        .replace(/\|/g, ' ')   // Replace table pipes with spaces
        .replace(/---+/g, '-'.repeat(40))  // Normalize horizontal rules
        .trim();
    };
    
    // Build formatted text content
    let content = `${'='.repeat(60)}\n`;
    content += `${report.title}\n`;
    content += `${'='.repeat(60)}\n\n`;
    content += `Generated: ${new Date(report.generatedAt).toLocaleString()}\n`;
    content += `Source: ${report.dataSource}\n`;
    content += `Report Type: ${report.reportType}\n\n`;
    content += `${'='.repeat(60)}\n\n`;
    
    // Add sections with proper formatting
    report.sections.forEach((s: any, index: number) => {
      content += `${index + 1}. ${s.title}\n`;
      content += `${'-'.repeat(s.title.length + 3)}\n\n`;
      content += `${cleanContent(s.content)}\n\n`;
      
      // Add chart data summary if present
      if (s.data && Array.isArray(s.data)) {
        content += `[Chart Data: ${s.chartType || 'visualization'}]\n`;
        s.data.slice(0, 10).forEach((item: any) => {
          if (item.name && item.value !== undefined) {
            content += `  - ${item.name}: ${typeof item.value === 'number' ? item.value.toLocaleString() : item.value}\n`;
          }
        });
        content += '\n';
      }
      
      content += '\n';
    });
    
    content += `${'='.repeat(60)}\n`;
    content += `End of Report\n`;
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${report.reportType}_report_${new Date().toISOString().split('T')[0]}.txt`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
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
    { value: 'metrics', label: 'Metrics Analysis', description: 'Analyze numeric data with trends', icon: TrendingUp, color: '#22c55e' },
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

  const renderFormattedText = (text: string) => {
    if (!text) return null;

    // Split by newlines to handle paragraphs
    return text.split('\n').map((line, i) => {
      // Split by bold markers
      const parts = line.split(/(\*\*.*?\*\*)/g);

      return (
        <div key={i} className="min-h-[1.5em] mb-1">
          {parts.map((part, j) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={j} className="text-primary-400 font-semibold">{part.slice(2, -2)}</strong>;
            }
            return <span key={j}>{part}</span>;
          })}
        </div>
      );
    });
  };

  // PlotlyChart component for rendering real ML charts from backend
  const PlotlyChart: React.FC<{ data: any; isDark: boolean }> = ({ data, isDark }) => {
    const plotRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      if (!plotRef.current || !data) return;

      // Dynamically load Plotly
      const loadPlotly = async () => {
        try {
          // @ts-ignore
          if (typeof window.Plotly === 'undefined') {
            // Load Plotly from CDN if not available
            const script = document.createElement('script');
            script.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
            script.async = true;
            script.onload = () => renderChart();
            document.head.appendChild(script);
          } else {
            renderChart();
          }
        } catch (error) {
          console.error('Failed to load Plotly:', error);
        }
      };

      const renderChart = () => {
        try {
          // @ts-ignore
          if (window.Plotly && plotRef.current) {
            const plotData = data.data || data;
            const layout = {
              ...(data.layout || {}),
              paper_bgcolor: 'transparent',
              plot_bgcolor: isDark ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)',
              font: { color: isDark ? '#e2e8f0' : '#1e293b' },
              margin: { l: 60, r: 30, t: 40, b: 60 },
              height: 320,
            };
            // @ts-ignore
            window.Plotly.newPlot(plotRef.current, plotData, layout, { responsive: true, displayModeBar: false });
          }
        } catch (error) {
          console.error('Plotly render error:', error);
        }
      };

      loadPlotly();
    }, [data, isDark]);

    return (
      <div ref={plotRef} className="w-full min-h-[320px]" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="px-1">
        <h1 className="text-2xl font-bold">Data Reports</h1>
        <p className="text-sm text-muted-foreground">Automatic reports generated from your uploaded data</p>
      </motion.div>

      {/* ML Model Status Banner */}
      {hasMLModel && mlModelInfo && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl border bg-gradient-to-r from-amber-500/10 to-primary-500/10"
          style={{ borderColor: '#F59E0B' }}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">🤖</span>
            <div className="flex-1">
              <div className="font-semibold" style={{ color: theme.textPrimary }}>
                AutoML Model Ready: {mlModelInfo.model_name}
              </div>
              <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {mlModelInfo.task_type?.toUpperCase()} • Target: {mlModelInfo.target_column} •
                Score: {(() => {
                  const m = mlModelInfo.metrics || {};
                  const score = m.accuracy || m.f1_score || m.f1 || m.precision || m.r2 || m.r2_score || 0;
                  return (score * 100).toFixed(1);
                })()}%
              </div>
            </div>
            <div className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded-full">
              Ready
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
                    <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {analytics.currencyBreakdown?.currencies_count} Currencies Detected
                    </div>
                    <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                      Auto-converted to {currencySymbol} ({currency})
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
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
                      className="p-4 rounded-2xl border relative overflow-hidden glass-card"
                      style={{ borderColor: 'var(--border-color)' }}
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
                          <div className="text-2xl font-black" style={{ color: 'var(--text-primary)' }}>
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
                            <div className="text-[10px] mt-2" style={{ color: 'var(--text-muted)' }}>Current value</div>
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

              // Fallback if no KPIs from unified analytics - show Total Records & Columns
              const dataShape = analytics?.dataShape || {};
              const totalRows = dataShape.rows || analytics?.totalRows || 0;
              const totalCols = dataShape.columns || analytics?.totalColumns || 0;
              
              return (
                <>
                  <div className="p-4 rounded-2xl border glass-card" style={{ borderColor: 'var(--border-color)' }}>
                    <div className="flex items-center gap-3">
                      <FileText className="w-8 h-8" style={{ color: '#22C55E' }} />
                      <div>
                        <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{totalRows.toLocaleString()}</div>
                        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Total Records</div>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 rounded-2xl border glass-card" style={{ borderColor: 'var(--border-color)' }}>
                    <div className="flex items-center gap-3">
                      <BarChart3 className="w-8 h-8" style={{ color: '#14B8A6' }} />
                      <div>
                        <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{totalCols}</div>
                        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Data Columns</div>
                      </div>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </motion.div>
      )
      }

      {/* Generate Report */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="p-6 rounded-2xl border glass-panel"
        style={{ borderColor: 'var(--border-color)' }}
      >
        <h2 className="text-lg font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>Generate New Report</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4 mb-6">
          {reportTypes.map((type, idx) => (
            <motion.button
              key={type.value}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => setSelectedType(type.value)}
              className={`p-4 md:p-5 rounded-xl transition-all text-left border relative overflow-hidden group ${selectedType === type.value
                ? 'ring-2 ring-offset-2 ring-offset-transparent'
                : 'hover:scale-[1.02]'
                }`}
              style={{
                backgroundColor: selectedType === type.value ? `${type.color}15` : 'var(--bg-card)',
                borderColor: selectedType === type.value ? type.color : 'var(--border-color)',
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
                  style={{ color: selectedType === type.value ? type.color : 'var(--text-muted)' }}
                />
                <div className="font-semibold text-base mb-1" style={{ color: 'var(--text-primary)' }}>
                  {type.label}
                </div>
                <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
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
          className="btn-primary w-full py-4 flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {generating ? (
            <>
              <div className="loading-spinner" />
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
                <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{error}</div>
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Generated Report */}
      {
        report && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 rounded-2xl border"
            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-6 h-6 text-emerald-400 flex-shrink-0" />
                  <h2 className="text-xl font-semibold break-words" style={{ color: 'var(--text-primary)' }}>{report.title}</h2>
                </div>
                <div className="text-sm break-words" style={{ color: 'var(--text-muted)' }}>
                  Generated: {new Date(report.generatedAt).toLocaleString()} | Source: {report.dataSource}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 w-full sm:w-auto">
                <button onClick={handleExportPDF} disabled={exportingPDF} className="flex-1 sm:flex-none px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 font-medium hover:bg-emerald-500/20 transition-colors flex items-center justify-center gap-2">
                  {exportingPDF ? <Loader className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                  <span className="whitespace-nowrap">{exportingPDF ? 'Exporting...' : 'Export PDF'}</span>
                </button>
                <button onClick={handleDownload} className="flex-1 sm:flex-none px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 font-medium hover:bg-green-500/20 transition-colors flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  <span className="whitespace-nowrap">Download TXT</span>
                </button>
              </div>
            </div>

            <div id="report-content" className="p-6 rounded-xl border pdf-export-content" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)', borderColor: theme.borderColor }}>
              {/* Header only visible in PDF export */}
              <div className="mb-6 pb-4 border-b-2 pdf-only-header" style={{ borderColor: '#14B8A6', display: 'none' }}>
                <h1 className="text-xl font-bold" style={{ color: '#1a1a2e' }}>{report.title}</h1>
                <p className="text-sm mt-1" style={{ color: '#4a4a5a' }}>Generated: {new Date(report.generatedAt).toLocaleString()} | Source: {report.dataSource}</p>
              </div>

              {/* AI Key Findings Section - Fully Autonomous */}
              {report.sections && report.sections.length > 0 && (() => {
                // Helper to check if a line is metadata (not a real insight)
                const isMetadataLine = (line: string): boolean => {
                  const lower = line.toLowerCase().trim();
                  // Comprehensive metadata patterns to filter out
                  const metadataPatterns = [
                    /^dataset:/i,
                    /^numeric/i,
                    /^categorical/i,
                    /^missing/i,
                    /^duplicates/i,
                    /^total\s*(rows|records|columns)/i,
                    /^\d+\s*(rows|records|columns|numeric|categorical)/i,
                    /columns?:\s*\d+/i,
                    /rows?:\s*\d+/i,
                    /rows\s*[×x,]\s*\d+/i,
                    /\d+\s*rows?\s*[×x,]/i,
                    /^[a-z]+\s+columns?:\s*\d+$/i,  // "Categorical Columns: 0"
                    /^(no|none|0)\s+(categorical|numeric|missing)/i,
                    /^data\s*(type|shape|size|info)/i,
                    /^(shape|size|dtype|info):/i,
                  ];
                  
                  return (
                    lower.length < 20 ||
                    metadataPatterns.some(pattern => pattern.test(lower)) ||
                    // Also filter generic short phrases
                    (lower.length < 30 && /^\w+\s+(columns?|rows?|data|values?):\s*\d+$/i.test(lower))
                  );
                };

                // Helper to clean insight text
                const cleanInsight = (text: string): string => {
                  return text
                    .replace(/^\d+\.\s*/, '')
                    .replace(/^\*\s*/, '')
                    .replace(/\*\*/g, '')
                    .replace(/•/g, '')
                    .replace(/^[-–—]\s*/, '')
                    .trim();
                };

                // Extract UNIQUE meaningful insights from report sections
                const seenInsights = new Set<string>();
                let topInsight = '';
                let actionText = '';

                // Search all sections for meaningful insights
                for (const section of report.sections) {
                  if (!section?.content) continue;

                  // Look for specific insight patterns
                  const patterns = [
                    /Key\s*Finding[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/i,
                    /Performance\s*Assessment:\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/i,
                    /Insight[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/i,
                    /Analysis:\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/i,
                    /Trend[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/i,
                  ];

                  for (const pattern of patterns) {
                    const match = section.content.match(pattern);
                    if (match && !topInsight) {
                      const extracted = cleanInsight(match[1]).replace(/\n/g, ' ').slice(0, 150);
                      if (!isMetadataLine(extracted) && extracted.length > 20) {
                        topInsight = extracted;
                        seenInsights.add(extracted.toLowerCase().trim());
                        break;
                      }
                    }
                  }

                  // Get meaningful lines if no pattern matched
                  if (!topInsight) {
                    const lines = section.content.split('\n').filter((l: string) => {
                      const cleaned = cleanInsight(l);
                      return cleaned.length > 20 && !isMetadataLine(cleaned);
                    });
                    if (lines.length > 0) {
                      topInsight = cleanInsight(lines[0]).slice(0, 150);
                      seenInsights.add(topInsight.toLowerCase().trim());
                    }
                  }

                  if (topInsight) break;
                }

                // Find action/recommendation
                const actionPatterns = [
                  /Recommendation[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z0-9]|$)/i,
                  /Action[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z0-9]|$)/i,
                  /Strategic\s*Recommendation[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z0-9]|$)/i,
                  /Next\s*Step[s]?:\s*([\s\S]*?)(?=\n\n|\n[A-Z0-9]|$)/i,
                ];

                // Search for action items
                for (const section of report.sections) {
                  if (!section?.content) continue;

                  // Check section title first
                  if (section.title?.toLowerCase().includes('recommend') || 
                      section.title?.toLowerCase().includes('action') ||
                      section.title?.toLowerCase().includes('strategic')) {
                    const lines = section.content.split('\n').filter((l: string) => {
                      const cleaned = cleanInsight(l);
                      const normalized = cleaned.toLowerCase().trim();
                      return cleaned.length > 15 && 
                             !isMetadataLine(cleaned) && 
                             !seenInsights.has(normalized);
                    });
                    if (lines.length > 0) {
                      actionText = cleanInsight(lines[0]).slice(0, 150);
                      break;
                    }
                  }

                  // Try patterns
                  for (const pattern of actionPatterns) {
                    const match = section.content.match(pattern);
                    if (match && !actionText) {
                      const extracted = cleanInsight(match[1]).replace(/\n/g, ' ').slice(0, 150);
                      if (!isMetadataLine(extracted) && 
                          extracted.length > 15 && 
                          !seenInsights.has(extracted.toLowerCase().trim())) {
                        actionText = extracted;
                        break;
                      }
                    }
                  }
                  if (actionText) break;
                }

                // Fallback: if still no insights, use section titles as context
                if (!topInsight && report.sections.length > 0) {
                  const sectionTitles = report.sections.map((s: any) => s.title).filter(Boolean).slice(0, 3);
                  topInsight = `Analysis covers: ${sectionTitles.join(', ')}`;
                }
                if (!actionText && report.sections.length > 1) {
                  const lastSection = report.sections[report.sections.length - 1];
                  if (lastSection?.title) {
                    actionText = `Review ${lastSection.title} for detailed insights`;
                  }
                }

                // Final fallback with actual data info
                if (!topInsight) topInsight = `Complete ${report.reportType} analysis generated`;
                if (!actionText) actionText = `Explore the ${report.sections.length} report sections below`;

                // Calculate confidence based on actual data richness
                const dataPoints = report.sections.reduce((acc: number, s: any) => {
                  if (s.data && Array.isArray(s.data)) return acc + s.data.length;
                  if (s.data && typeof s.data === 'object') return acc + Object.keys(s.data).length;
                  return acc + 1;
                }, 0);
                const confidence = dataPoints > 20 ? 'Very High' : dataPoints > 10 ? 'High' : dataPoints > 5 ? 'Medium' : 'Standard';

                return (
                  <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-green-500/10 to-indigo-500/10 border border-green-500/30">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-lg">🤖</span>
                      <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>AI Key Findings</h3>
                      <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-[10px] font-bold rounded-full">AUTO-GENERATED</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-green-400">📈</span>
                          <span className="text-xs font-bold text-green-400">TOP INSIGHT</span>
                        </div>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          {topInsight.slice(0, 100)}{topInsight.length > 100 ? '...' : ''}
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-amber-400">⚡</span>
                          <span className="text-xs font-bold text-amber-400">ACTION ITEM</span>
                        </div>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          {actionText.slice(0, 100)}{actionText.length > 100 ? '...' : ''}
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-blue-400">🎯</span>
                          <span className="text-xs font-bold text-blue-400">CONFIDENCE</span>
                        </div>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
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
                    // Allow object data for images (base64 string is usually in data.image or data itself)
                    const hasChartData = (Array.isArray(section.data) && section.data.length > 0) ||
                      (section.chartType === 'image' && section.data);
                    // Check for Plotly data in both plotlyData and data fields
                    const plotlyChartData = section.plotlyData || (section.chartType === 'plotly' && section.data);
                    const hasPlotlyData = section.chartType === 'plotly' && plotlyChartData;

                    return (
                      <div key={i} className="border-l-4 pl-4" style={{ borderColor: CHART_COLORS[i % CHART_COLORS.length] }}>
                        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>{section.title}</h3>

                        {/* Text content */}
                        <div className="text-sm leading-relaxed mb-4 font-mono whitespace-pre-wrap" style={{ color: 'var(--text-muted)' }}>
                          {renderFormattedText(section.content)}
                        </div>

                        {/* Plotly ML Charts (Confusion Matrix, Feature Importance, etc.) */}
                        {hasPlotlyData && (
                          <div className="mt-4 p-4 rounded-xl border" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)', borderColor: theme.borderColor }}>
                            <PlotlyChart data={plotlyChartData} isDark={theme.isDark} />
                          </div>
                        )}

                        {/* Chart visualization if available */}
                        {hasChartData && !hasPlotlyData && (
                          <div className="mt-4 p-4 rounded-xl border" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)', borderColor: theme.borderColor }}>
                            {section.chartType === 'image' ? (
                              <div className="flex justify-center">
                                <img
                                  src={section.data.image || section.data}
                                  alt={section.title}
                                  className="max-w-full h-auto rounded-lg" // Removed max-h constraint to allow full view
                                  style={{ maxHeight: '500px' }}
                                />
                              </div>
                            ) : (
                              <ResponsiveContainer width="100%" height={250}>
                                {(() => {
                                  // AUTONOMOUS CHART SELECTOR - decides best chart based on data
                                  const chartType = section.chartType || 'bar';
                                  const data = section.data || [];
                                  const dataCount = Array.isArray(data) ? data.length : 0;

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
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </motion.div>
        )
      }

      {/* Empty State */}
      {!report && !generating && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-12 rounded-2xl text-center border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <FileText className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
          <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>No Report Generated Yet</h3>
          <p className="mb-4" style={{ color: 'var(--text-muted)' }}>Select a report type above and click generate.</p>
          {!analytics?.hasData && (
            <a href="/data-hub" className="inline-block px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded-full transition-colors">
              Upload Files First
            </a>
          )}
        </motion.div>
      )
      }
    </div>
  );
};

export default Reports;
