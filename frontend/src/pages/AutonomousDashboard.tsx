import React, { useState, useEffect, lazy, Suspense, useCallback } from 'react';
import {
    LayoutDashboard, TrendingUp, TrendingDown,
    BarChart3, PieChart, LineChart, Loader2,
    Database, Calendar, Layers, Activity, Target, Zap,
    RefreshCw, Maximize2, Grid3X3, List, Upload, Download, FileText
} from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { useUserStore } from '../store/userStore';
import { api } from '../services/api';
import { getUserIdSync } from '../utils/userId';

// Dynamic Plotly import
const Plot = lazy(() => import('react-plotly.js'));

interface KPI {
    title: string;
    value: number | string;
    format: string;
    trend?: 'up' | 'down' | 'neutral';
    comparison?: string;
}

interface ChartData {
    chart_id: string;
    title: string;
    type: string;
    plotly_config?: { data: any[]; layout: any };
}

interface DashboardData {
    dashboard_title: string;
    domain?: string;
    kpis: KPI[];
    charts: ChartData[];
    insights: string[];
    recommendations: string[];
    data_source: string;
    generated_at: string;
}

// Error boundary
class ChartErrorBoundary extends React.Component<{ children: React.ReactNode, chartTitle?: string }> {
    state = { hasError: false };
    static getDerivedStateFromError() { return { hasError: true }; }
    render() {
        if (this.state.hasError) {
            return (
                <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                    <span>Unable to render chart</span>
                </div>
            );
        }
        return this.props.children;
    }
}

const VisualIntelligenceDashboard: React.FC = () => {
    const { user, isDark } = useUserStore();
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [expandedChart, setExpandedChart] = useState<string | null>(null);
    const [exporting, setExporting] = useState(false);

    // Theme configuration
    // Theme configuration - Using global consistency where possible
    const t = isDark ? {
        bg: 'bg-[var(--bg-primary)]',
        bgSecondary: 'bg-[var(--bg-secondary)]',
        card: isDark ? 'glass-card' : 'bg-white border border-slate-200 shadow-sm',
        cardHover: 'hover-glow',
        border: 'border-[var(--border-color)]',
        text: 'text-[var(--text-primary)]',
        textSecondary: 'text-[var(--text-secondary)]',
        textMuted: 'text-[var(--text-muted)]',
        accent: '#14b8a6',
        accentSecondary: '#6366f1'
    } : {
        bg: 'bg-[var(--bg-primary)]',
        bgSecondary: 'bg-[var(--bg-secondary)]',
        card: 'bg-white border border-slate-200 shadow-sm',
        cardHover: 'hover:shadow-md',
        border: 'border-[var(--border-color)]',
        text: 'text-gray-900',
        textSecondary: 'text-gray-700',
        textMuted: 'text-gray-500',
        accent: '#0d9488',
        accentSecondary: '#4f46e5'
    };

    const loadDashboard = useCallback(async () => {
        const userId = user?.id || getUserIdSync();
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/v1/dashboard/generate', { user_id: userId });
            if (response.data.success && response.data.dashboard) {
                const dashboardData = response.data.dashboard;

                // Deduplicate charts by type and title to prevent repeated charts
                if (dashboardData.charts && Array.isArray(dashboardData.charts)) {
                    const seenTypes = new Set<string>();
                    const seenTitles = new Set<string>();
                    dashboardData.charts = dashboardData.charts.filter((chart: ChartData) => {
                        const typeKey = chart.type?.toLowerCase() || '';
                        const titleKey = chart.title?.toLowerCase() || '';

                        // Skip if we've already seen this chart type or exact title
                        if (seenTypes.has(typeKey) || seenTitles.has(titleKey)) {
                            return false;
                        }

                        seenTypes.add(typeKey);
                        seenTitles.add(titleKey);
                        return true;
                    });
                }

                setDashboard(dashboardData);
            } else {
                setError(response.data.error || 'Please upload data in DataHub first');
            }
        } catch (err: any) {
            setError(err.response?.data?.error || 'Please upload data in DataHub first');
        } finally {
            setLoading(false);
        }
    }, [user?.id]);

    // Auto-load dashboard
    useEffect(() => {
        loadDashboard();
    }, [user?.id, loadDashboard]);

    // Listen for file updates from DataHub - refresh dashboard when files change
    useEffect(() => {
        const handleFilesUpdated = () => {
            console.log('📁 Files updated - refreshing dashboard...');
            loadDashboard();
        };

        window.addEventListener('filesUpdated', handleFilesUpdated);
        return () => window.removeEventListener('filesUpdated', handleFilesUpdated);
    }, [loadDashboard]);

    const formatValue = (value: number | string, format: string): string => {
        if (typeof value === 'string') return value;
        if (value == null) return '0';
        try {
            if (format === 'currency') {
                if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
                return `$${value.toFixed(0)}`;
            }
            if (format === 'percentage') return `${Number(value).toFixed(1)}%`;
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
            return new Intl.NumberFormat().format(Math.round(value));
        } catch { return String(value); }
    };

    // Smooth chart rendering with proper Plotly config
    const renderChart = useCallback((chart: ChartData, height = 240) => {
        if (!chart.plotly_config) return null;

        const plotlyConfig = {
            displayModeBar: false,
            responsive: true,
            staticPlot: false, // Allow hover but no drag
            scrollZoom: false,
            doubleClick: false as const,
            showTips: false
        };

        const layout = {
            ...(chart.plotly_config.layout || {}),
            autosize: true,
            height,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: isDark ? '#e2e8f0' : '#1e293b',
                size: 11,
                family: 'Inter, sans-serif'
            },
            margin: { l: 45, r: 20, t: 30, b: 45 },
            xaxis: {
                ...(chart.plotly_config.layout?.xaxis || {}),
                gridcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                color: isDark ? '#94a3b8' : '#64748b',
                zerolinecolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                fixedrange: true
            },
            yaxis: {
                ...(chart.plotly_config.layout?.yaxis || {}),
                gridcolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                color: isDark ? '#94a3b8' : '#64748b',
                zerolinecolor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                fixedrange: true
            },
            legend: {
                orientation: 'h',
                y: -0.2,
                font: { color: isDark ? '#e2e8f0' : '#1e293b' }
            },
            dragmode: false, // Disable all drag
            hovermode: 'closest'
        };

        return (
            <Suspense fallback={
                <div className="h-full flex items-center justify-center">
                    <Loader2 className="w-6 h-6 animate-spin" style={{ color: t.accent }} />
                </div>
            }>
                <ChartErrorBoundary chartTitle={chart.title}>
                    <Plot
                        data={chart.plotly_config.data}
                        layout={layout}
                        config={plotlyConfig}
                        style={{ width: '100%', height: '100%' }}
                        useResizeHandler={true}
                    />
                </ChartErrorBoundary>
            </Suspense>
        );
    }, [isDark, t.accent]);

    // Get chart icon based on type
    const getChartIcon = (type: string) => {
        if (['pie', 'donut', 'sunburst', 'treemap'].includes(type)) return PieChart;
        if (['line', 'area', 'scatter', 'bubble'].includes(type)) return LineChart;
        return BarChart3;
    };

    // Loading state - Building Dashboard Message
    if (loading) {
        return (
            <div className={`min-h-screen flex items-center justify-center`} style={{ backgroundColor: 'var(--bg-primary)' }}>
                <div className="text-center max-w-md px-6">
                    {/* Animated Building Icon */}
                    <div className="relative w-24 h-24 mx-auto mb-6">
                        <div className={`absolute inset-0 rounded-2xl ${isDark ? 'bg-gradient-to-br from-teal-500/20 to-indigo-500/20' : 'bg-gradient-to-br from-teal-100 to-indigo-100'} animate-pulse`}></div>
                        <div className={`absolute inset-2 rounded-xl ${isDark ? 'bg-gradient-to-br from-teal-500/30 to-indigo-500/30' : 'bg-gradient-to-br from-teal-200 to-indigo-200'} animate-pulse`} style={{ animationDelay: '150ms' }}></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <BarChart3 className={`w-10 h-10 ${isDark ? 'text-teal-400' : 'text-teal-600'} animate-bounce`} style={{ animationDuration: '1.5s' }} />
                        </div>
                    </div>
                    
                    {/* Title */}
                    <h2 className={`text-xl font-semibold mb-2 ${t.text}`}>
                        🚀 Building Your Dashboard
                    </h2>
                    
                    {/* Subtitle */}
                    <p className={`text-sm mb-6 ${t.textMuted}`}>
                        AI is analyzing your data and generating insights...
                    </p>
                    
                    {/* Progress Indicator */}
                    <div className="flex items-center justify-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-teal-400' : 'bg-teal-500'} animate-bounce`} style={{ animationDelay: '0ms' }}></div>
                        <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-teal-400' : 'bg-teal-500'} animate-bounce`} style={{ animationDelay: '150ms' }}></div>
                        <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-teal-400' : 'bg-teal-500'} animate-bounce`} style={{ animationDelay: '300ms' }}></div>
                    </div>
                    
                    {/* Tip */}
                    <p className={`text-xs mt-6 ${t.textMuted}`}>
                        💡 This may take a few seconds depending on your data size
                    </p>
                </div>
            </div>
        );
    }

    // Error/No data state
    if (error || !dashboard) {
        return (
            <div className={`min-h-screen flex items-center justify-center ${t.bg}`}>
                <div className="text-center max-w-md px-6">
                    <Database className={`w-14 h-14 mx-auto mb-4 ${t.textMuted}`} />
                    <h2 className={`text-xl font-semibold ${t.text}`}>No Dashboard Data</h2>
                    <p className={`mt-2 text-sm ${t.textMuted}`}>
                        {error || 'Upload your data files in DataHub to generate AI-powered visualizations and insights.'}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
                        <button
                            onClick={() => window.location.href = '/datahub'}
                            className="px-5 py-2.5 rounded-xl text-white font-medium transition-all hover:scale-105"
                            style={{ background: `linear-gradient(135deg, ${t.accent}, ${t.accentSecondary})` }}
                        >
                            <Upload className="w-4 h-4 inline mr-2" />Upload Data
                        </button>
                        <button
                            onClick={loadDashboard}
                            className={`px-5 py-2.5 rounded-xl font-medium transition-all border ${t.border} ${t.text}`}
                        >
                            <RefreshCw className="w-4 h-4 inline mr-2" />Try Again
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={`min-h-screen`} style={{ backgroundColor: 'var(--bg-primary)' }}>
            {/* Header */}
            <header className={`sticky top-0 z-30 backdrop-blur-xl border-b border-[var(--border-color)] ${isDark ? 'glass-panel' : 'bg-white/90'}`}>
                <div className="max-w-[1920px] mx-auto px-4 lg:px-6 py-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-center gap-3 min-w-0 w-full sm:w-auto">
                            <div className="p-2 rounded-xl flex-shrink-0" style={{ background: `linear-gradient(135deg, ${t.accent}, ${t.accentSecondary})` }}>
                                <LayoutDashboard className="w-5 h-5 text-white" />
                            </div>
                            <div className="min-w-0 flex-1">
                                <h1 className={`text-lg font-bold truncate ${t.text}`}>{dashboard.dashboard_title}</h1>
                                <p className={`text-xs ${t.textMuted} truncate`}>{dashboard.data_source} • {dashboard.domain || 'General'} Domain</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-end gap-2 w-full sm:w-auto">
                            {/* View Toggle */}
                            <div className={`hidden sm:flex items-center gap-1 p-1 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
                                <button onClick={() => setViewMode('grid')} className={`p-1.5 rounded-md transition-all ${viewMode === 'grid' ? (isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900 shadow') : t.textMuted}`}>
                                    <Grid3X3 className="w-4 h-4" />
                                </button>
                                <button onClick={() => setViewMode('list')} className={`p-1.5 rounded-md transition-all ${viewMode === 'list' ? (isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900 shadow') : t.textMuted}`}>
                                    <List className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Export PPT Button */}
                            <button
                                onClick={async () => {
                                    if (!dashboard) return;
                                    setExporting(true);
                                    try {
                                        const content = `# ${dashboard.dashboard_title}\n\n## Key Metrics\n${dashboard.kpis?.map(k => `- ${k.title}: ${k.value}`).join('\n') || 'No KPIs'}\n\n## Insights\n${dashboard.insights?.map(i => `- ${i}`).join('\n') || 'No insights'}\n\n## Recommendations\n${dashboard.recommendations?.map(r => `- ${r}`).join('\n') || 'No recommendations'}`;
                                        
                                        // Capture chart images from Plotly
                                        const chartImages: Array<{title: string; type: string; image_base64?: string; data?: any}> = [];
                                        
                                        if (dashboard.charts && dashboard.charts.length > 0) {
                                            // Get all Plotly chart divs
                                            const chartDivs = document.querySelectorAll('[class*="js-plotly-plot"]');
                                            
                                            for (let i = 0; i < Math.min(dashboard.charts.length, chartDivs.length); i++) {
                                                const chart = dashboard.charts[i];
                                                const chartDiv = chartDivs[i] as HTMLElement;
                                                
                                                try {
                                                    // Use Plotly's toImage to capture chart as PNG
                                                    const Plotly = (window as any).Plotly;
                                                    if (Plotly && chartDiv) {
                                                        const imageData = await Plotly.toImage(chartDiv, {
                                                            format: 'png',
                                                            width: 1200,
                                                            height: 700,
                                                            scale: 2
                                                        });
                                                        
                                                        chartImages.push({
                                                            title: chart.title || `Chart ${i + 1}`,
                                                            type: chart.type || 'chart',
                                                            image_base64: imageData
                                                        });
                                                    } else {
                                                        // Fallback: send chart info without image
                                                        chartImages.push({
                                                            title: chart.title || `Chart ${i + 1}`,
                                                            type: chart.type || 'chart'
                                                        });
                                                    }
                                                } catch (imgErr) {
                                                    console.warn('Failed to capture chart image:', imgErr);
                                                    chartImages.push({
                                                        title: chart.title || `Chart ${i + 1}`,
                                                        type: chart.type || 'chart'
                                                    });
                                                }
                                            }
                                        }
                                        
                                        // Use proper API base URL
                                        const apiBase = import.meta.env.VITE_API_URL || '';
                                        const response = await fetch(`${apiBase}/api/v1/exports/download/pptx`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ 
                                                content, 
                                                title: dashboard.dashboard_title,
                                                charts: chartImages
                                            })
                                        });
                                        
                                        if (response.ok) {
                                            const blob = await response.blob();
                                            const url = URL.createObjectURL(blob);
                                            const a = document.createElement('a');
                                            a.href = url;
                                            a.download = `dashboard_${Date.now()}.pptx`;
                                            document.body.appendChild(a);
                                            a.click();
                                            document.body.removeChild(a);
                                            URL.revokeObjectURL(url);
                                        } else {
                                            const errorText = await response.text();
                                            console.error('Export failed:', errorText);
                                            alert(`Export failed: ${errorText}`);
                                        }
                                    } catch (e) {
                                        console.error('Export failed:', e);
                                        alert('Export failed. Please try again.');
                                    } finally {
                                        setExporting(false);
                                    }
                                }}
                                disabled={exporting}
                                className={`p-2 rounded-lg transition-all flex items-center gap-1.5 ${isDark ? 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30' : 'bg-orange-100 text-orange-600 hover:bg-orange-200'} ${exporting ? 'opacity-50 cursor-wait' : ''}`}
                                title="Export to PowerPoint"
                            >
                                {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                                <span className="text-xs font-medium hidden sm:inline">PPT</span>
                            </button>

                            <button onClick={loadDashboard} className={`p-2 rounded-lg transition-all ${isDark ? 'bg-gray-800 text-gray-400 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Dashboard */}
            <main className="max-w-[1920px] mx-auto p-4 lg:p-6 space-y-5">


                {/* Hero KPIs - Enterprise Grade */}
                <section>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-5 gap-3">
                        {dashboard.kpis?.slice(0, 10).map((kpi: any, i: number) => {
                            const kpiColors = [
                                '#22c55e', '#8b5cf6', '#f97316', '#10b981', '#ec4899', 
                                '#3b82f6', '#14b8a6', '#ef4444', '#eab308', '#6366f1'
                            ];
                            
                            // Get KPI type-specific styling
                            const getKPIIcon = () => {
                                switch(kpi.kpi_type) {
                                    case 'anomaly': return '⚠️';
                                    case 'concentration': return '🏆';
                                    case 'momentum': return kpi.trend === 'up' ? '🚀' : '📉';
                                    case 'percentile': return '📊';
                                    case 'seasonality': return '🔄';
                                    case 'volatility': return kpi.trend === 'up' ? '✅' : '⚡';
                                    case 'growth': return kpi.trend === 'up' ? '📈' : '📉';
                                    case 'sum_with_cagr': return '💰';
                                    default: return '📋';
                                }
                            };
                            
                            // Render mini sparkline if available
                            const renderSparkline = () => {
                                if (!kpi.sparkline || !Array.isArray(kpi.sparkline) || kpi.sparkline.length < 3) return null;
                                
                                const data = kpi.sparkline.slice(-15);
                                const max = Math.max(...data);
                                const min = Math.min(...data);
                                const range = max - min || 1;
                                const height = 24;
                                const width = 60;
                                
                                const points = data.map((v: number, i: number) => {
                                    const x = (i / (data.length - 1)) * width;
                                    const y = height - ((v - min) / range) * height;
                                    return `${x},${y}`;
                                }).join(' ');
                                
                                const sparkColor = kpi.trend === 'up' ? '#22c55e' : (kpi.trend === 'down' ? '#ef4444' : '#6b7280');
                                
                                return (
                                    <svg width={width} height={height} className="mt-1 opacity-60">
                                        <polyline
                                            points={points}
                                            fill="none"
                                            stroke={sparkColor}
                                            strokeWidth="1.5"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                );
                            };

                            return (
                                <div
                                    key={i}
                                    className={`kpi-card animate-fade-up stagger-${i + 1} relative overflow-hidden`}
                                    style={{ '--kpi-color': kpiColors[i % 10] } as React.CSSProperties}
                                >
                                    {/* KPI Type Badge */}
                                    {kpi.kpi_type && kpi.kpi_type !== 'count' && kpi.kpi_type !== 'sum' && (
                                        <span className="absolute top-1 right-1 text-xs opacity-50">
                                            {getKPIIcon()}
                                        </span>
                                    )}
                                    
                                    <p className={`kpi-label`}>{kpi.title}</p>
                                    <p className={`kpi-value`}>{formatValue(kpi.value, kpi.format)}</p>
                                    
                                    {/* Sparkline */}
                                    {renderSparkline()}
                                    
                                    {kpi.trend && (
                                        <div className={`kpi-trend ${kpi.trend}`}>
                                            {kpi.trend === 'up' && <TrendingUp className="w-3.5 h-3.5" />}
                                            {kpi.trend === 'down' && <TrendingDown className="w-3.5 h-3.5" />}
                                            <span className="truncate text-xs">{kpi.comparison}</span>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </section>

                {/* Info Pills - Enhanced with Chart Types */}
                <section className="flex flex-wrap gap-2">
                    {[
                        { icon: Calendar, label: dashboard.data_source.split('×')[0]?.trim() },
                        { icon: Layers, label: dashboard.data_source.split('×')[1]?.trim() },
                        { icon: Activity, label: `${dashboard.charts?.length || 0} visualizations` },
                        { icon: Target, label: `${dashboard.insights?.length || 0} insights` },
                        { icon: Zap, label: `${new Set(dashboard.charts?.map((c: ChartData) => c.type)).size || 0} chart types` }
                    ].map((p, i) => (
                        <span key={i} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${isDark ? 'bg-gray-800/60 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
                            <p.icon className="w-3 h-3" />{p.label}
                        </span>
                    ))}
                </section>

                {/* Charts Grid - Premium Layout */}
                <section>
                    <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4' : 'space-y-4'}>
                        {dashboard.charts?.map((chart: any, i: number) => {
                            const Icon = getChartIcon(chart.type);
                            const isExpanded = expandedChart === chart.chart_id;
                            const chartHeight = viewMode === 'list' ? 300 : (isExpanded ? 400 : 260);
                            
                            // Premium chart type badges
                            const getPremiumBadge = () => {
                                const premiumTypes = ['combo_bar_line', 'lollipop', 'diverging_bar', 'slope', 'dumbbell', 'range_plot', 'band_chart', 'pareto', 'radar', 'sankey', 'sunburst'];
                                if (premiumTypes.includes(chart.type)) {
                                    return <span className="text-xs px-1.5 py-0.5 rounded bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 font-medium ml-1">PRO</span>;
                                }
                                return null;
                            };
                            
                            // Get analysis type if available
                            const getAnalysisLabel = () => {
                                if (chart.analysis) {
                                    const labels: {[key: string]: string} = {
                                        'dual_axis_comparison': '📊 Dual Axis',
                                        'ranking_visualization': '🏆 Ranking',
                                        'variance_from_mean': '📈 Variance',
                                        'period_comparison': '🔄 Period',
                                        'comparison_visualization': '⚖️ Compare',
                                        'min_max_spread': '📏 Range',
                                        'confidence_interval': '🎯 Confidence',
                                        'power_bi_80_20': '📊 Pareto 80/20'
                                    };
                                    return labels[chart.analysis] || null;
                                }
                                return null;
                            };

                            return (
                                <div
                                    key={chart.chart_id || i}
                                    className={`card-premium animate-fade-up overflow-hidden ${isExpanded ? 'md:col-span-2 xl:col-span-3' : ''}`}
                                    style={{ animationDelay: `${i * 0.05}s`, padding: 0 }}
                                >
                                    {/* Chart Header */}
                                    <div className={`flex items-center justify-between px-4 py-3 border-b ${t.border}`}>
                                        <div className="flex items-center gap-2 min-w-0">
                                            <Icon className="w-4 h-4 flex-shrink-0" style={{ color: t.accent }} />
                                            <h3 className={`text-sm font-semibold truncate ${t.text}`}>{chart.title}</h3>
                                            <span className="badge-info text-xs">{chart.type.replace('_', ' ')}</span>
                                            {getPremiumBadge()}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {getAnalysisLabel() && (
                                                <span className={`text-xs ${t.textMuted} hidden sm:inline`}>{getAnalysisLabel()}</span>
                                            )}
                                            <button
                                                onClick={() => setExpandedChart(isExpanded ? null : chart.chart_id)}
                                                className="btn-icon"
                                            >
                                                <Maximize2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Chart Content */}
                                    <div className="p-3" style={{ height: chartHeight }}>
                                        {renderChart(chart, chartHeight - 20)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </section>

                {/* Insights & Recommendations */}
                <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Key Insights */}
                    {dashboard.insights?.length > 0 && (
                        <div className={`rounded-xl border p-5 ${t.card} border-[var(--border-color)]`}>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${t.text}`}>
                                <Zap className="w-4 h-4" style={{ color: '#f59e0b' }} />
                                Key Insights
                            </h3>
                            <ul className="space-y-3">
                                {dashboard.insights.map((insight, i) => (
                                    <li key={i} className="flex items-start gap-3">
                                        <span className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: ['#14b8a6', '#8b5cf6', '#f59e0b', '#10b981', '#ec4899'][i % 5] }} />
                                        <p className={`text-sm ${t.textSecondary}`}>{insight}</p>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Recommendations */}
                    {dashboard.recommendations?.length > 0 && (
                        <div className={`rounded-xl border p-5 ${t.card} border-[var(--border-color)]`}>
                            <h3 className={`text-sm font-semibold mb-4 flex items-center gap-2 ${t.text}`}>
                                <Target className="w-4 h-4" style={{ color: '#6366f1' }} />
                                Recommendations
                            </h3>
                            <div className="space-y-2">
                                {dashboard.recommendations.map((rec, i) => (
                                    <div key={i} className={`flex items-center justify-between p-3 rounded-lg ${isDark ? 'bg-gray-800/50' : 'bg-gray-50'}`}>
                                        <span className={`text-sm ${t.textSecondary}`}>{rec}</span>
                                        <span className="text-xs font-bold text-emerald-500">+{(15 + i * 8).toFixed(0)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </section>


            </main>

            {/* Expanded Chart Modal */}
            {expandedChart && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setExpandedChart(null)}>
                    <div className={`w-full max-w-5xl max-h-[80vh] rounded-2xl border overflow-hidden ${t.card} ${t.border}`} onClick={e => e.stopPropagation()}>
                        {dashboard.charts?.filter(c => c.chart_id === expandedChart).map(chart => (
                            <div key={chart.chart_id}>
                                <div className={`flex items-center justify-between px-5 py-4 border-b ${t.border}`}>
                                    <h3 className={`text-lg font-semibold ${t.text}`}>{chart.title}</h3>
                                    <button onClick={() => setExpandedChart(null)} className={`p-2 rounded-lg ${isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
                                        ✕
                                    </button>
                                </div>
                                <div className="p-5" style={{ height: '60vh' }}>
                                    {renderChart(chart, window.innerHeight * 0.55)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default VisualIntelligenceDashboard;
