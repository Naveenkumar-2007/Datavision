import React, { useState, useEffect, lazy, Suspense, useCallback } from 'react';
import {
    LayoutDashboard, TrendingUp, TrendingDown,
    BarChart3, PieChart, LineChart, Loader2,
    Database, Calendar, Layers, Activity, Target, Zap,
    RefreshCw, Maximize2, Grid3X3, List
} from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { useUserStore } from '../store/userStore';
import { api } from '../services/api';

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

    // Theme configuration
    const t = isDark ? {
        bg: 'bg-[#0a0f1a]',
        bgSecondary: 'bg-[#111827]',
        card: 'bg-[#1a2332]/80',
        cardHover: 'hover:bg-[#1f2a3d]/90',
        border: 'border-[#2d3748]',
        text: 'text-white',
        textSecondary: 'text-gray-300',
        textMuted: 'text-gray-500',
        accent: '#14b8a6',
        accentSecondary: '#6366f1'
    } : {
        bg: 'bg-gray-50',
        bgSecondary: 'bg-white',
        card: 'bg-white',
        cardHover: 'hover:bg-gray-50',
        border: 'border-gray-200',
        text: 'text-gray-900',
        textSecondary: 'text-gray-700',
        textMuted: 'text-gray-500',
        accent: '#0d9488',
        accentSecondary: '#4f46e5'
    };

    const loadDashboard = useCallback(async () => {
        const userId = user?.id || localStorage.getItem('userId') || 'guest';
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/v1/dashboard/generate', { user_id: userId });
            if (response.data.success && response.data.dashboard) {
                setDashboard(response.data.dashboard);
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

    // Loading state with Skeleton
    if (loading) {
        return (
            <div className={`min-h-screen ${t.bg}`}>
                {/* Header Skeleton */}
                <div className={`border-b ${t.border} ${isDark ? 'bg-[#0a0f1a]/90' : 'bg-white/90'} px-6 py-3`}>
                    <div className="flex justify-between items-center max-w-[1920px] mx-auto">
                        <div className="flex items-center gap-3">
                            <Skeleton className="w-10 h-10 rounded-xl" />
                            <div className="space-y-2">
                                <Skeleton className="h-4 w-48" />
                                <Skeleton className="h-3 w-32" />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Skeleton className="w-8 h-8 rounded-lg" />
                            <Skeleton className="w-8 h-8 rounded-lg" />
                        </div>
                    </div>
                </div>

                <div className="max-w-[1920px] mx-auto p-6 space-y-6">
                    {/* KPIs Skeleton */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <div key={i} className={`p-4 rounded-xl border ${t.border} ${t.card}`}>
                                <Skeleton className="h-3 w-16 mb-2" />
                                <Skeleton className="h-8 w-24 mb-2" />
                                <Skeleton className="h-3 w-12" />
                            </div>
                        ))}
                    </div>

                    {/* Pills Skeleton */}
                    <div className="flex gap-2">
                        {[1, 2, 3, 4].map((i) => (
                            <Skeleton key={i} className="h-8 w-24 rounded-full" />
                        ))}
                    </div>

                    {/* Charts Grid Skeleton */}
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <div key={i} className={`rounded-xl border ${t.border} ${t.card} p-4 h-[300px]`}>
                                <div className="flex justify-between items-center mb-4">
                                    <div className="flex gap-2 items-center">
                                        <Skeleton className="w-4 h-4 rounded-full" />
                                        <Skeleton className="h-4 w-32" />
                                    </div>
                                    <Skeleton className="w-4 h-4" />
                                </div>
                                <Skeleton className="w-full h-[220px] rounded-lg" />
                            </div>
                        ))}
                    </div>
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
                    <p className={`mt-2 text-sm ${t.textMuted}`}>{error || 'Upload files in DataHub to generate your AI dashboard.'}</p>
                    <button onClick={loadDashboard} className="mt-6 px-5 py-2.5 rounded-xl text-white font-medium transition-all hover:scale-105" style={{ background: `linear-gradient(135deg, ${t.accent}, ${t.accentSecondary})` }}>
                        <RefreshCw className="w-4 h-4 inline mr-2" />Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`min-h-screen ${t.bg}`}>
            {/* Header */}
            <header className={`sticky top-0 z-30 backdrop-blur-xl border-b ${t.border} ${isDark ? 'bg-[#0a0f1a]/90' : 'bg-white/90'}`}>
                <div className="max-w-[1920px] mx-auto px-4 lg:px-6 py-3">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="p-2 rounded-xl" style={{ background: `linear-gradient(135deg, ${t.accent}, ${t.accentSecondary})` }}>
                                <LayoutDashboard className="w-5 h-5 text-white" />
                            </div>
                            <div className="min-w-0">
                                <h1 className={`text-lg font-bold truncate ${t.text}`}>{dashboard.dashboard_title}</h1>
                                <p className={`text-xs ${t.textMuted} truncate`}>{dashboard.data_source} • {dashboard.domain || 'General'} Domain</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {/* View Toggle */}
                            <div className={`hidden sm:flex items-center gap-1 p-1 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
                                <button onClick={() => setViewMode('grid')} className={`p-1.5 rounded-md transition-all ${viewMode === 'grid' ? (isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900 shadow') : t.textMuted}`}>
                                    <Grid3X3 className="w-4 h-4" />
                                </button>
                                <button onClick={() => setViewMode('list')} className={`p-1.5 rounded-md transition-all ${viewMode === 'list' ? (isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900 shadow') : t.textMuted}`}>
                                    <List className="w-4 h-4" />
                                </button>
                            </div>



                            <button onClick={loadDashboard} className={`p-2 rounded-lg transition-all ${isDark ? 'bg-gray-800 text-gray-400 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Dashboard */}
            <main className="max-w-[1920px] mx-auto p-4 lg:p-6 space-y-5">

                {/* Hero KPIs */}
                <section>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                        {dashboard.kpis?.map((kpi, i) => {
                            const gradients = [
                                'from-teal-500 to-cyan-500', 'from-purple-500 to-indigo-500',
                                'from-orange-500 to-amber-500', 'from-emerald-500 to-green-500',
                                'from-pink-500 to-rose-500', 'from-blue-500 to-indigo-500'
                            ];

                            return (
                                <div key={i} className={`relative overflow-hidden rounded-xl p-4 border transition-all duration-300 hover:scale-[1.02] ${t.card} ${t.border}`}>
                                    <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${gradients[i % 6]}`} />
                                    <p className={`text-xs font-medium ${t.textMuted} mb-1 truncate`}>{kpi.title}</p>
                                    <p className={`text-2xl lg:text-3xl font-bold ${t.text}`}>{formatValue(kpi.value, kpi.format)}</p>
                                    {kpi.trend && (
                                        <div className={`mt-1.5 flex items-center gap-1 text-xs ${kpi.trend === 'up' ? 'text-emerald-500' : kpi.trend === 'down' ? 'text-rose-500' : t.textMuted}`}>
                                            {kpi.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                                            {kpi.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                                            <span className="truncate">{kpi.comparison}</span>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </section>

                {/* Info Pills */}
                <section className="flex flex-wrap gap-2">
                    {[
                        { icon: Calendar, label: dashboard.data_source.split('×')[0]?.trim() },
                        { icon: Layers, label: dashboard.data_source.split('×')[1]?.trim() },
                        { icon: Activity, label: `${dashboard.charts?.length || 0} visualizations` },
                        { icon: Target, label: `${dashboard.insights?.length || 0} insights` }
                    ].map((p, i) => (
                        <span key={i} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${isDark ? 'bg-gray-800/60 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
                            <p.icon className="w-3 h-3" />{p.label}
                        </span>
                    ))}
                </section>

                {/* Charts Grid */}
                <section>
                    <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4' : 'space-y-4'}>
                        {dashboard.charts?.map((chart, i) => {
                            const Icon = getChartIcon(chart.type);
                            const isExpanded = expandedChart === chart.chart_id;
                            const chartHeight = viewMode === 'list' ? 300 : (isExpanded ? 400 : 260);

                            return (
                                <div
                                    key={chart.chart_id || i}
                                    className={`rounded-xl border overflow-hidden transition-all duration-300 ${t.card} ${t.border} ${t.cardHover} ${isExpanded ? 'md:col-span-2 xl:col-span-3' : ''}`}
                                >
                                    {/* Chart Header */}
                                    <div className={`flex items-center justify-between px-4 py-3 border-b ${t.border}`}>
                                        <div className="flex items-center gap-2 min-w-0">
                                            <Icon className="w-4 h-4 flex-shrink-0" style={{ color: t.accent }} />
                                            <h3 className={`text-sm font-semibold truncate ${t.text}`}>{chart.title}</h3>
                                            <span className={`px-2 py-0.5 rounded-full text-xs ${isDark ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
                                                {chart.type}
                                            </span>
                                        </div>
                                        <button
                                            onClick={() => setExpandedChart(isExpanded ? null : chart.chart_id)}
                                            className={`p-1.5 rounded-lg transition-all ${isDark ? 'hover:bg-gray-700 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                                        >
                                            <Maximize2 className="w-4 h-4" />
                                        </button>
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
                        <div className={`rounded-xl border p-5 ${t.card} ${t.border}`}>
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
                        <div className={`rounded-xl border p-5 ${t.card} ${t.border}`}>
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

                {/* Footer */}
                <footer className={`text-center py-4 text-xs ${t.textMuted}`}>
                    Autonomous Visual Intelligence Engine • Generated {new Date(dashboard.generated_at).toLocaleString()}
                </footer>
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
