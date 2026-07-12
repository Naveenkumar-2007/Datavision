import React, { useState, useEffect, lazy, Suspense, useCallback, useRef, useMemo } from 'react';
import {
    LayoutDashboard, TrendingUp, TrendingDown,
    BarChart3, PieChart, LineChart, Loader2,
    Database, Calendar, Layers, Activity, Target, Zap,
    RefreshCw, Maximize2, Grid3X3, List, Upload, Download, FileText,
    ChevronLeft, ChevronRight, X, Eye, Lightbulb, Filter,
    Briefcase, HeartPulse, ShoppingBag, DollarSign, Laptop,
    MessageSquare, Send, Settings, Mic, Volume2, Square, Save
} from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { useUserStore } from '../store/userStore';
import { useLiveStore } from '../store/liveStore';
import { api, apiService } from '../services/api';
import { getUserIdSync, getAuthHeadersSync } from '../utils/userId';
import { motion } from 'framer-motion';
import { BackgroundPattern } from '../components/BackgroundPattern';
import html2pdf from 'html2pdf.js';
// @ts-ignore
import { Responsive } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const GridWrapper = ({ children, layouts, breakpoints, cols, rowHeight, isDraggable, isResizable, draggableHandle, margin }: any) => {
    const ref = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(1200);
    useEffect(() => {
        if (!ref.current) return;
        const observer = new ResizeObserver(entries => {
            if (entries[0]) setWidth(entries[0].contentRect.width);
        });
        observer.observe(ref.current);
        return () => observer.disconnect();
    }, []);
    const rglProps: any = {
        width,
        layouts,
        breakpoints,
        cols,
        rowHeight,
        isDraggable,
        isResizable,
        draggableHandle,
        margin
    };

    return (
        <div ref={ref} className="w-full overflow-hidden">
            <Responsive {...rglProps}>
                {children}
            </Responsive>
        </div>
    );
};

// Dynamic Plotly import
const Plot = lazy(() => import('react-plotly.js'));

/* ===================================================================
   TYPE DEFINITIONS
   =================================================================== */
interface KPI {
    title: string;
    value: number | string;
    format: string;
    trend?: 'up' | 'down' | 'neutral';
    comparison?: string;
    kpi_type?: string;
    sparkline?: number[];
}

interface ChartData {
    chart_id: string;
    title: string;
    type: string;
    analysis?: string;
    plotly_config?: { data: any[]; layout: any };
}

interface DashboardSection {
    name: string;
    charts: ChartData[];
}

interface DashboardData {
    dashboard_title: string;
    domain?: string;
    kpis: KPI[];
    charts: ChartData[];
    sections?: DashboardSection[];
    insights: string[];
    recommendations: string[];
    filters?: { column: string; options: string[] }[];
    executive_summary?: string;
    data_grid?: { columns: string[]; rows: Record<string, any>[] };
    data_source: string;
    generated_at: string;
    theme?: any;
}

/* ===================================================================
   SECTION ACCENT COLORS — Each section gets its own identity
   =================================================================== */
const SECTION_ACCENTS = [
    { border: '#14b8a6', bg: 'rgba(20,184,166,0.08)', bgLight: 'rgba(20,184,166,0.06)', label: 'text-teal-400' },
    { border: '#8b5cf6', bg: 'rgba(139,92,246,0.08)', bgLight: 'rgba(139,92,246,0.06)', label: 'text-violet-400' },
    { border: '#f59e0b', bg: 'rgba(245,158,11,0.08)', bgLight: 'rgba(245,158,11,0.06)', label: 'text-amber-400' },
    { border: '#ec4899', bg: 'rgba(236,72,153,0.08)', bgLight: 'rgba(236,72,153,0.06)', label: 'text-pink-400' },
    { border: '#3b82f6', bg: 'rgba(59,130,246,0.08)', bgLight: 'rgba(59,130,246,0.06)', label: 'text-blue-400' },
    { border: '#22c55e', bg: 'rgba(34,197,94,0.08)', bgLight: 'rgba(34,197,94,0.06)', label: 'text-green-400' },
    { border: '#f97316', bg: 'rgba(249,115,22,0.08)', bgLight: 'rgba(249,115,22,0.06)', label: 'text-orange-400' },
    { border: '#06b6d4', bg: 'rgba(6,182,212,0.08)', bgLight: 'rgba(6,182,212,0.06)', label: 'text-cyan-400' },
];

/* ===================================================================
   ERROR BOUNDARY
   =================================================================== */
class ChartErrorBoundary extends React.Component<{ children: React.ReactNode; chartTitle?: string }> {
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

/* ===================================================================
   MAIN COMPONENT
   =================================================================== */
const VisualIntelligenceDashboard: React.FC = () => {
    const { user, isDark: globalIsDark } = useUserStore();
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [expandedChart, setExpandedChart] = useState<string | null>(null);
    const [exporting, setExporting] = useState(false);
    const [exportingPDF, setExportingPDF] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [activeFilters, setActiveFilters] = useState<Record<string, string[]>>({});
    const [pendingFilters, setPendingFilters] = useState<Record<string, string[]>>({});
    const [explainingChart, setExplainingChart] = useState<string | null>(null);
    const [chartExplanations, setChartExplanations] = useState<Record<string, string>>({});
    const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

    useEffect(() => {
        setPendingFilters(activeFilters);
    }, [activeFilters]);

    const [isChatOpen, setIsChatOpen] = useState(false);
    const [chatMessages, setChatMessages] = useState<{role: 'user'|'assistant', text: string}[]>([
        { role: 'assistant', text: 'Hi! I am your AI Data Assistant. Ask me anything about your dashboard data.' }
    ]);
    const [chatInput, setChatInput] = useState('');
    const [chatLoading, setChatLoading] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);
    
    // Voice State
    const [isListening, setIsListening] = useState(false);
    const [playingAudio, setPlayingAudio] = useState<HTMLAudioElement | null>(null);
    const recognitionRef = useRef<any>(null);

    const [chartOverrides, setChartOverrides] = useState<Record<string, string>>({});
    const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

    const isDark = globalIsDark;
    
    const aiTheme = dashboard?.theme || null;
    // Check if the theme has either the new bg_gradient or the old background_color
    const hasAiTheme = aiTheme && (aiTheme.bg_gradient || aiTheme.background_color);

    // Theme configuration (Dynamic Generative AI Theme + Premium Defaults)
    const t = {
        bg: hasAiTheme ? 'ai-theme-bg' : (isDark ? 'bg-[#0b1120]' : 'bg-[#f8fafc]'),
        bgSecondary: hasAiTheme ? 'ai-theme-bg' : (isDark ? 'bg-[#0f172a]' : 'bg-[#f1f5f9]'),
        card: hasAiTheme ? 'ai-theme-card shadow-2xl backdrop-blur-xl' : (isDark ? 'bg-[#151e32] border-[#2a3441] shadow-2xl' : 'bg-[#ffffff] border-[#e2e8f0] shadow-xl'),
        cardHover: hasAiTheme ? 'hover:-translate-y-1 hover:shadow-2xl transition-all duration-300' : (isDark ? 'hover:bg-[#1e293b] transition-all duration-300' : 'hover:shadow-2xl hover:-translate-y-1 transition-all duration-300'),
        border: hasAiTheme ? 'ai-theme-border' : (isDark ? 'border-[#2a3441]' : 'border-[#e2e8f0]'),
        text: hasAiTheme ? 'ai-theme-text' : (isDark ? 'text-[#f8fafc]' : 'text-[#0f172a]'),
        textSecondary: hasAiTheme ? 'ai-theme-text-secondary' : (isDark ? 'text-[#e2e8f0]' : 'text-[#334155]'),
        textMuted: hasAiTheme ? 'ai-theme-text-secondary opacity-70' : (isDark ? 'text-[#94a3b8]' : 'text-[#64748b]'),
        accent: isDark ? '#38bdf8' : '#0ea5e9',
        accentSecondary: isDark ? '#818cf8' : '#6366f1',
        cardHeader: hasAiTheme ? 'ai-theme-card-header backdrop-blur-md' : (isDark ? 'bg-[#1a233a]' : 'bg-slate-50')
    };

    // Prepare dynamic style object based on new or legacy theme variables
    const dynamicStyles = hasAiTheme ? {
        '--ai-bg': aiTheme.bg_gradient || aiTheme.background_color,
        '--ai-card-bg': aiTheme.card_bg || aiTheme.card_background,
        '--ai-border': aiTheme.border_color,
        '--ai-text-primary': aiTheme.text_primary || aiTheme.text_color,
        '--ai-text-secondary': aiTheme.text_secondary
    } as React.CSSProperties : {};
    
    const { setDashboardCache, getDashboardCache, lastRowCount, setLastRowCount } = useLiveStore();

    /* -----------------------------------------------------------
       DATA LOADING
       ----------------------------------------------------------- */
    const loadDashboard = useCallback(async (forceRefresh = false) => {
        const userId = user?.id || getUserIdSync();
        const cacheKey = `dashboard_cache_${userId}_${JSON.stringify(activeFilters)}`;
        
        if (!forceRefresh) {
            const cached = getDashboardCache(cacheKey);
            if (cached) {
                setDashboard(cached);
                setLoading(false);
                return;
            }
        }
        
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/v1/dashboard/generate', { 
                user_id: userId,
                active_filters: activeFilters
            });
            if (response.data.success && response.data.dashboard) {
                const dashboardData = response.data.dashboard;
                setDashboard(dashboardData);
                setDashboardCache(cacheKey, dashboardData);
            } else {
                setError(response.data.error || 'Please upload data in DataHub first');
            }
        } catch (err: any) {
            console.error("Dashboard error:", err);
            setError(err.response?.data?.error || 'Failed to load dashboard. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [user?.id, activeFilters, getDashboardCache, setDashboardCache]);

    // Auto-load dashboard
    useEffect(() => {
        loadDashboard();
    }, [user?.id, loadDashboard]);

    const saveDashboard = async () => {
        if (!dashboard) return;
        try {
            setLoading(true);
            const response = await api.post('/api/v1/dashboard/save', {
                title: dashboard.kpis?.[0]?.title || 'Saved Dashboard',
                layout: [],
                charts: dashboard.charts || []
            });
            if (response.data.success) {
                alert('Dashboard saved to PostgreSQL database successfully!');
            } else {
                alert('Failed to save dashboard: ' + response.data.error);
            }
        } catch (err) {
            console.error(err);
            alert('Failed to save dashboard.');
        } finally {
            setLoading(false);
        }
    };

    // Listen for live data updates (Delta Auto-Regeneration)
    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        
        const checkDelta = async () => {
            try {
                const res = await api.get('/api/v1/live/delta');
                if (res.data && res.data.total_rows !== undefined) {
                    const currentCount = res.data.total_rows;
                    
                    if (lastRowCount !== null && currentCount > lastRowCount + 500) {
                        console.log(`[LIVE] Detected ${currentCount - lastRowCount} new rows. Auto-regenerating dashboard...`);
                        setLastRowCount(currentCount);
                        loadDashboard(true); // Force refresh
                    } else if (lastRowCount === null) {
                        setLastRowCount(currentCount);
                    }
                }
            } catch (err) {
                console.error("Delta check failed", err);
            }
        };

        // Poll every 10 seconds
        interval = setInterval(checkDelta, 10000);
        return () => clearInterval(interval);
    }, [lastRowCount, setLastRowCount, loadDashboard]);

    // Listen for file updates from DataHub - refresh dashboard when files change
    useEffect(() => {
        const handleFilesUpdated = () => {
            console.log('📁 Files updated - refreshing dashboard...');
            // Clear all dashboard caches
            Object.keys(sessionStorage).forEach(key => {
                if (key.startsWith('dashboard_cache_')) {
                    sessionStorage.removeItem(key);
                }
            });
            loadDashboard(true);
        };
        window.addEventListener('filesUpdated', handleFilesUpdated);
        return () => window.removeEventListener('filesUpdated', handleFilesUpdated);
    }, [loadDashboard]);

    // Apply Premium Glassmorphism Theme
    useEffect(() => {
        if (!dashboard) return;
        const d = (dashboard.domain || '').toLowerCase();
        let themeClass = 'theme-obsidian';
        if (d.includes('tech') || d.includes('cyber') || d.includes('ai') || d.includes('software')) themeClass = 'theme-cyber';
        else if (d.includes('health') || d.includes('science') || d.includes('medical')) themeClass = 'theme-aurora';
        
        document.documentElement.classList.add(themeClass);
        // Force dark mode to ensure glass variables pop properly
        document.documentElement.classList.remove('light-theme');
        return () => {
            document.documentElement.classList.remove(themeClass);
        };
    }, [dashboard?.domain]);

    /* -----------------------------------------------------------
       COMPUTED SECTIONS — fall back to flat charts
       ----------------------------------------------------------- */
    const resolvedSections: DashboardSection[] = useMemo(() => {
        if (!dashboard) return [];
        if (dashboard.sections && dashboard.sections.length > 0) {
            return dashboard.sections;
        }
        // Backward compat: wrap flat charts in a single section
        if (dashboard.charts && dashboard.charts.length > 0) {
            return [{ name: 'All Visualizations', charts: dashboard.charts }];
        }
        return [];
    }, [dashboard]);

    /* -----------------------------------------------------------
       ALL CHARTS (flat) — for modal & export
       ----------------------------------------------------------- */
    const allCharts: ChartData[] = useMemo(() => {
        if (!dashboard) return [];
        if (dashboard.sections && dashboard.sections.length > 0) {
            return dashboard.sections.flatMap(s => s.charts);
        }
        return dashboard.charts || [];
    }, [dashboard]);

    /* -----------------------------------------------------------
       SIDEBAR NAV SCROLL
       ----------------------------------------------------------- */
    const scrollToSection = (name: string) => {
        const el = sectionRefs.current[name];
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    /* -----------------------------------------------------------
       HELPERS
       ----------------------------------------------------------- */
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

    const getDomainIcon = (domain: string) => {
        const d = (domain || '').toLowerCase();
        if (d.includes('finance') || d.includes('sales') || d.includes('revenue')) return DollarSign;
        if (d.includes('health') || d.includes('medical') || d.includes('patient')) return HeartPulse;
        if (d.includes('tech') || d.includes('it') || d.includes('software')) return Laptop;
        if (d.includes('retail') || d.includes('ecommerce') || d.includes('shop')) return ShoppingBag;
        return LayoutDashboard;
    };

    const getChartIcon = (type: string) => {
        if (['pie', 'donut', 'sunburst', 'treemap'].includes(type)) return PieChart;
        if (['line', 'area', 'scatter', 'bubble'].includes(type)) return LineChart;
        return BarChart3;
    };

    /* -----------------------------------------------------------
       RENDER CHART (Plotly)
       ----------------------------------------------------------- */
    const renderChart = useCallback((chart: ChartData, height = 230) => {
        if (!chart.plotly_config) return null;

        const plotlyConfig = {
            displayModeBar: false,
            responsive: true,
            staticPlot: false,
            scrollZoom: false,
            doubleClick: false as const,
            showTips: false
        };

        // Apply dynamic type override
        const overrideType = chartOverrides[chart.chart_id];
        const chartData = chart.plotly_config.data.map(trace => ({
            ...trace,
            type: overrideType || trace.type
        }));

        const layout = {
            ...(chart.plotly_config.layout || {}),
            autosize: true,
            height,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: '#e2e8f0', // Always dark mode text
                size: 9,
                family: 'Inter, sans-serif'
            },
            margin: { l: 30, r: 15, t: 30, b: 25 },
            xaxis: {
                ...(chart.plotly_config.layout?.xaxis || {}),
                gridcolor: 'rgba(255,255,255,0.03)',
                color: '#94a3b8',
                zerolinecolor: 'rgba(255,255,255,0.03)',
                fixedrange: true,
                tickangle: 0
            },
            yaxis: {
                ...(chart.plotly_config.layout?.yaxis || {}),
                gridcolor: 'rgba(255,255,255,0.03)',
                color: '#94a3b8',
                zerolinecolor: 'rgba(255,255,255,0.03)',
                fixedrange: true
            },
            legend: {
                orientation: 'h' as const,
                y: -0.2,
                font: { size: 9, color: '#cbd5e1' }
            },
            dragmode: false as const,
            hovermode: 'closest' as const
        };

        return (
            <Suspense fallback={
                <div className="h-full flex items-center justify-center">
                    <Loader2 className="w-5 h-5 animate-spin" style={{ color: t.accent }} />
                </div>
            }>
                <ChartErrorBoundary chartTitle={chart.title}>
                    <Plot
                        data={chartData as any}
                        layout={layout}
                        config={plotlyConfig}
                        style={{ width: '100%', height: '100%' }}
                        useResizeHandler={true}
                        onClick={(e: any) => {
                            if (e.points && e.points.length > 0) {
                                const pt = e.points[0];
                                const filterVal = pt.label || pt.x;
                                if (filterVal) {
                                    const valStr = String(filterVal);
                                    if (dashboard?.filters) {
                                        for (const filter of dashboard.filters) {
                                            if (filter.options.includes(valStr)) {
                                                setActiveFilters((prev: Record<string, string[]>) => {
                                                    const colFilters = prev[filter.column] || [];
                                                    const newFilters = colFilters.includes(valStr) 
                                                        ? colFilters.filter((v: string) => v !== valStr)
                                                        : [...colFilters, valStr];
                                                    return { ...prev, [filter.column]: newFilters };
                                                });
                                                break;
                                            }
                                        }
                                    }
                                }
                            }
                        }}
                    />
                </ChartErrorBoundary>
            </Suspense>
        );
    }, [isDark, t.accent, dashboard?.filters, setActiveFilters, chartOverrides]);

    /* -----------------------------------------------------------
       AI EXPLAIN HANDLER
       ----------------------------------------------------------- */
    const handleExplainChart = useCallback(async (chart: ChartData) => {
        if (chartExplanations[chart.chart_id]) return; // Already have it
        setExplainingChart(chart.chart_id);
        try {
            const response = await api.post('/api/v1/dashboard/explain-chart', {
                chart_title: chart.title,
                chart_type: chart.type,
                chart_data: chart.plotly_config?.data || {}
            });
            if (response.data.success) {
                setChartExplanations(prev => ({ ...prev, [chart.chart_id]: response.data.explanation }));
            }
        } catch (err) {
            console.error("AI Explain failed", err);
        } finally {
            setExplainingChart(null);
        }
    }, [chartExplanations]);

    /* -----------------------------------------------------------
       EXPORT PPT HANDLER
       ----------------------------------------------------------- */
    const handleExport = useCallback(async () => {
        if (!dashboard) return;
        setExporting(true);
        try {
            const content = `# ${dashboard.dashboard_title}\n\n## Key Metrics\n${dashboard.kpis?.map(k => `- ${k.title}: ${k.value}`).join('\n') || 'No KPIs'}\n\n## Insights\n${dashboard.insights?.map(i => `- ${i}`).join('\n') || 'No insights'}\n\n## Recommendations\n${dashboard.recommendations?.map(r => `- ${r}`).join('\n') || 'No recommendations'}`;

            // Capture chart images from Plotly
            const chartImages: Array<{ title: string; type: string; image_base64?: string; data?: any }> = [];
            const chartsToExport = allCharts;

            if (chartsToExport.length > 0) {
                const chartDivs = document.querySelectorAll('[class*="js-plotly-plot"]');
                for (let i = 0; i < Math.min(chartsToExport.length, chartDivs.length); i++) {
                    const chart = chartsToExport[i];
                    const chartDiv = chartDivs[i] as HTMLElement;
                    try {
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

            const apiBase = import.meta.env.VITE_API_URL || '';
            const response = await fetch(`${apiBase}/api/v1/exports/download/pptx`, {
                method: 'POST',
                headers: getAuthHeadersSync(),
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
    }, [dashboard, allCharts]);

    const handleExportCSV = useCallback(() => {
        if (!dashboard?.data_grid) return;
        const { columns, rows } = dashboard.data_grid;
        
        // Escape quotes and format as CSV
        const csvContent = [
            columns.join(','),
            ...rows.map(row => 
                columns.map(col => {
                    const cell = row[col] === null || row[col] === undefined ? '' : String(row[col]);
                    // Escape quotes and wrap in quotes if contains comma
                    if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
                        return `"${cell.replace(/"/g, '""')}"`;
                    }
                    return cell;
                }).join(',')
            )
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `data_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);        
    }, [dashboard?.data_grid]);

    const handleExportPDF = useCallback(async () => {
        if (!dashboard) return;
        setExportingPDF(true);
        try {
            const element = document.getElementById('dashboard-content');
            if (!element) return;
            
            const opt = {
                margin:       0.5,
                filename:     `${dashboard.dashboard_title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`,
                image:        { type: 'jpeg' as const, quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true },
                jsPDF:        { unit: 'in', format: 'a3', orientation: 'landscape' as const }
            };
            
            await html2pdf().set(opt).from(element).save();
        } catch (error) {
            console.error('Error exporting PDF:', error);
            alert('Failed to export PDF');
        } finally {
            setExportingPDF(false);
        }
    }, [dashboard]);

    const playVoice = async (text: string) => {
        try {
            const apiBase = import.meta.env.VITE_API_URL || '';
            const response = await fetch(`${apiBase}/api/v1/voice/synthesize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                if (playingAudio) {
                    playingAudio.pause();
                }
                const audio = new Audio(url);
                setPlayingAudio(audio);
                audio.play();
                audio.onended = () => setPlayingAudio(null);
            }
        } catch (e) {
            console.error("TTS Error", e);
        }
    };

    const toggleSpeechRecognition = () => {
        if (isListening) {
            if (recognitionRef.current) recognitionRef.current.stop();
            setIsListening(false);
            return;
        }

        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Speech recognition is not supported in this browser.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => setIsListening(true);
        recognition.onresult = (event: any) => {
            const transcript = Array.from(event.results)
                .map((result: any) => result[0])
                .map((result) => result.transcript)
                .join('');
            setChatInput(transcript);
        };
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);

        recognitionRef.current = recognition;
        recognition.start();
    };

    const handleSendMessage = async () => {
        if (!chatInput.trim() || !dashboard) return;
        
        const userMsg = chatInput.trim();
        setChatMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setChatInput('');
        setChatLoading(true);
        
        try {
            let fullText = '';
            setChatMessages(prev => [...prev, { role: 'assistant', text: '' }]);
            
            await apiService.streamMessage(
                userMsg,
                'llama',
                (chunk: string) => {
                    fullText += chunk;
                    setChatMessages(prev => {
                        const newMsgs = [...prev];
                        newMsgs[newMsgs.length - 1].text = fullText;
                        return newMsgs;
                    });
                },
                () => { setChatLoading(false); },
                (err) => { throw new Error(err); }
            );
        } catch (err) {
            console.error('Chat error:', err);
            setChatMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, there was a network error.' }]);
        } finally {
            setChatLoading(false);
        }
    };

    useEffect(() => {
        if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [chatMessages, isChatOpen]);

    /* ================================================================
       LOADING STATE
       ================================================================ */
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
                <div className="text-center max-w-md px-6">
                    <div className="relative w-24 h-24 mx-auto mb-6">
                        <div className={`absolute inset-0 rounded-2xl ${isDark ? 'bg-gradient-to-br from-teal-500/20 to-indigo-500/20' : 'bg-gradient-to-br from-teal-100 to-indigo-100'} animate-pulse`} />
                        <div className={`absolute inset-2 rounded-xl ${isDark ? 'bg-gradient-to-br from-teal-500/30 to-indigo-500/30' : 'bg-gradient-to-br from-teal-200 to-indigo-200'} animate-pulse`} style={{ animationDelay: '150ms' }} />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <BarChart3 className={`w-10 h-10 ${isDark ? 'text-teal-400' : 'text-teal-600'} animate-bounce`} style={{ animationDuration: '1.5s' }} />
                        </div>
                    </div>
                    <h2 className={`text-xl font-semibold mb-2 ${t.text}`}>🚀 Building Your Dashboard</h2>
                    <p className={`text-sm mb-6 ${t.textMuted}`}>AI is analyzing your data and generating insights...</p>
                    <div className="flex items-center justify-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-teal-400' : 'bg-teal-500'} animate-bounce`} style={{ animationDelay: '0ms' }} />
                        <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-teal-400' : 'bg-teal-500'} animate-bounce`} style={{ animationDelay: '150ms' }} />
                        <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-teal-400' : 'bg-teal-500'} animate-bounce`} style={{ animationDelay: '300ms' }} />
                    </div>
                    <p className={`text-xs mt-6 ${t.textMuted}`}>💡 This may take a few seconds depending on your data size</p>
                </div>
            </div>
        );
    }

    /* ================================================================
       ERROR / NO DATA STATE
       ================================================================ */
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
                            onClick={() => loadDashboard()}
                            className={`px-5 py-2.5 rounded-xl font-medium transition-all border ${t.border} ${t.text}`}
                        >
                            <RefreshCw className="w-4 h-4 inline mr-2" />Try Again
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    /* ================================================================
       MAIN DASHBOARD RENDER
       ================================================================ */
    return (
        <>
        <div className={`min-h-screen ${t.bg} ${t.text} transition-colors duration-500`} style={hasAiTheme ? dynamicStyles : { backgroundColor: 'var(--bg-primary)' }}>
            <BackgroundPattern 
                pattern={dashboard?.theme?.bg_pattern || 'none'} 
                accentColor={dashboard?.theme?.chart_palette?.[0] || '#3b82f6'} 
                isDark={isDark} 
            />
            {/* ====================== HEADER ====================== */}
            <header className={`sticky top-0 z-40 border-b ${t.border} ${t.cardHeader}`}>
                <div className="max-w-[2000px] mx-auto px-3 lg:px-5 py-2.5">
                    <div className="flex items-center justify-between gap-3">
                        {/* Left: Sidebar toggle + Title */}
                        <div className="flex items-center gap-2.5 min-w-0">
                            <button
                                onClick={() => setSidebarOpen(p => !p)}
                                className={`p-1.5 rounded-lg transition-all flex-shrink-0 ${isDark ? 'hover:bg-white/5 text-gray-400' : 'hover:bg-gray-100 text-gray-500'}`}
                                title="Toggle sidebar"
                            >
                                {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </button>
                            <div className="p-1.5 rounded-lg flex-shrink-0" style={{ background: `linear-gradient(135deg, ${t.accent}, ${t.accentSecondary})` }}>
                                {React.createElement(getDomainIcon(dashboard.domain || ''), { className: 'w-4 h-4 text-white' })}
                            </div>
                            <div className="min-w-0">
                                <h1 className={`text-sm font-bold truncate ${t.text}`}>{dashboard.dashboard_title}</h1>
                                <p className={`text-[10px] ${t.textMuted} truncate`}>{dashboard.data_source} • {dashboard.domain || 'General'} Domain</p>
                            </div>
                        </div>

                        {/* Right: Controls */}
                        <div className="flex items-center gap-1.5">
                            {/* View Toggle */}
                            <div className={`hidden sm:flex items-center gap-0.5 p-0.5 rounded-md ${isDark ? 'bg-gray-800/80' : 'bg-gray-100'}`}>
                                <button onClick={() => setViewMode('grid')} className={`p-1 rounded transition-all ${viewMode === 'grid' ? (isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900 shadow-sm') : t.textMuted}`}>
                                    <Grid3X3 className="w-3.5 h-3.5" />
                                </button>
                                <button onClick={() => setViewMode('list')} className={`p-1 rounded transition-all ${viewMode === 'list' ? (isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900 shadow-sm') : t.textMuted}`}>
                                    <List className="w-3.5 h-3.5" />
                                </button>
                            </div>

                            {/* Save to DB */}
                            <button
                                onClick={saveDashboard}
                                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${isDark ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30' : 'bg-emerald-100 text-emerald-600 hover:bg-emerald-200'}`}
                                title="Save to Database"
                            >
                                <Save className="w-3.5 h-3.5" />
                                <span className="text-[10px] font-semibold hidden sm:inline">Save</span>
                            </button>

                            {/* Export PPT */}
                            <button
                                onClick={handleExport}
                                disabled={exporting}
                                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${isDark ? 'bg-orange-500/20 text-orange-400 hover:bg-orange-500/30' : 'bg-orange-100 text-orange-600 hover:bg-orange-200'} ${exporting ? 'opacity-50 cursor-wait' : ''}`}
                                title="Export to PowerPoint"
                            >
                                {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
                                <span className="text-[10px] font-semibold hidden sm:inline">PPT</span>
                            </button>

                            {/* Export PDF */}
                            <button
                                onClick={handleExportPDF}
                                disabled={exportingPDF}
                                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${isDark ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-red-100 text-red-600 hover:bg-red-200'} ${exportingPDF ? 'opacity-50 cursor-wait' : ''}`}
                                title="Export to PDF"
                            >
                                {exportingPDF ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
                                <span className="text-[10px] font-semibold hidden sm:inline">PDF</span>
                            </button>

                            {/* Chat Toggle */}
                            <button
                                onClick={() => setIsChatOpen(!isChatOpen)}
                                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${isChatOpen ? (isDark ? 'bg-indigo-600 text-white' : 'bg-indigo-600 text-white') : (isDark ? 'bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30' : 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200')}`}
                                title="Chat with Data"
                            >
                                <MessageSquare className="w-4 h-4" />
                            </button>

                            {/* Regenerate Dashboard */}
                            <button
                                onClick={() => {
                                    // Clear cache before regenerating
                                    const userId = user?.id || getUserIdSync();
                                    const cacheKey = `dashboard_cache_${userId}_${JSON.stringify(activeFilters)}`;
                                    setDashboardCache(cacheKey, null);
                                    loadDashboard(true);
                                }}
                                className={`p-1.5 rounded-lg transition-all flex items-center gap-1 ${isDark ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30' : 'bg-purple-100 text-purple-600 hover:bg-purple-200'}`}
                                title="Force AI to regenerate the dashboard from scratch"
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                                <span className="text-[10px] font-semibold hidden sm:inline">Regenerate</span>
                            </button>

                            {/* Refresh */}
                            <button
                                onClick={() => loadDashboard()}
                                className={`p-1.5 rounded-lg transition-all ${isDark ? 'bg-gray-800 text-gray-400 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                                title="Refresh dashboard"
                            >
                                <RefreshCw className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* ====================== BODY LAYOUT (Sidebar + Main) ====================== */}
            <div className="flex max-w-[2000px] mx-auto">

                {/* ============ LEFT SIDEBAR NAV ============ */}
                <aside
                    className={`sticky top-[49px] h-[calc(100vh-49px)] flex-shrink-0 overflow-y-auto transition-all duration-300 ease-in-out border-r ${t.border} ${t.bgSecondary}`}
                    style={{ width: sidebarOpen ? 200 : 0, opacity: sidebarOpen ? 1 : 0, padding: sidebarOpen ? undefined : 0 }}
                >
                    {sidebarOpen && (
                        <nav className="p-3 space-y-1">
                            {/* ============ DATA SLICERS ============ */}
                            {dashboard?.filters && dashboard.filters.length > 0 && (
                                <div className="mb-6">
                                    <div className="flex items-center gap-1.5 mb-3 px-2">
                                        <Filter className={`w-3 h-3 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                                        <h3 className={`text-[10px] uppercase tracking-widest font-bold ${t.textMuted}`}>Data Slicers</h3>
                                    </div>
                                    <div className="space-y-4">
                                        {dashboard.filters.map(filter => (
                                            <div key={filter.column} className="px-2">
                                                <div className={`text-xs font-semibold mb-2 ${t.textSecondary}`}>{filter.column.replace(/_/g, ' ')}</div>
                                                <div className="space-y-1.5 max-h-[150px] overflow-y-auto custom-scrollbar">
                                                    {filter.options.map(opt => {
                                                        const isChecked = pendingFilters[filter.column]?.includes(opt);
                                                        return (
                                                            <label key={opt} className={`flex items-start gap-2 text-xs cursor-pointer group ${t.text}`}>
                                                                <input
                                                                    type="checkbox"
                                                                    checked={isChecked || false}
                                                                    onChange={() => {
                                                                        setPendingFilters(prev => {
                                                                            const colFilters = prev[filter.column] || [];
                                                                            const newFilters = isChecked
                                                                                ? colFilters.filter(v => v !== opt)
                                                                                : [...colFilters, opt];
                                                                            return { ...prev, [filter.column]: newFilters };
                                                                        });
                                                                    }}
                                                                    className={`mt-0.5 rounded ${t.border} ${isDark || hasAiTheme ? 'bg-black/20' : 'bg-white'} text-blue-500 focus:ring-blue-500`}
                                                                />
                                                                <span className="truncate group-hover:opacity-80">{opt}</span>
                                                            </label>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="px-2 mt-4">
                                        <button 
                                            onClick={() => setActiveFilters(pendingFilters)}
                                            className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold py-2 rounded-lg transition-colors"
                                        >
                                            Apply Filters
                                        </button>
                                    </div>
                                    <div className={`border-t my-4 ${t.border}`} />
                                </div>
                            )}

                            <p className={`text-[9px] uppercase tracking-widest font-bold mb-3 px-2 ${t.textMuted}`}>Sections</p>

                            {resolvedSections.map((section, i) => {
                                const accent = SECTION_ACCENTS[i % SECTION_ACCENTS.length];
                                return (
                                    <button
                                        key={section.name}
                                        onClick={() => scrollToSection(section.name)}
                                        className={`w-full text-left px-2.5 py-2 rounded-lg text-xs font-medium transition-all group flex items-center gap-2 ${isDark ? 'hover:bg-white/5 text-gray-300' : 'hover:bg-gray-200/60 text-gray-700'}`}
                                    >
                                        <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: accent.border }} />
                                        <span className="truncate">{section.name}</span>
                                        <span className={`ml-auto text-[9px] ${t.textMuted}`}>{section.charts.length}</span>
                                    </button>
                                );
                            })}

                            {/* Insights & Recs nav */}
                            {(dashboard.insights?.length > 0 || dashboard.recommendations?.length > 0) && (
                                <>
                                    <div className={`border-t my-2 ${t.border}`} />
                                    {dashboard.insights?.length > 0 && (
                                        <button
                                            onClick={() => scrollToSection('__insights')}
                                            className={`w-full text-left px-2.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${isDark ? 'hover:bg-white/5 text-gray-300' : 'hover:bg-gray-200/60 text-gray-700'}`}
                                        >
                                            <Zap className="w-3 h-3 text-amber-400 flex-shrink-0" />
                                            <span className="truncate">Insights</span>
                                            <span className={`ml-auto text-[9px] ${t.textMuted}`}>{dashboard.insights.length}</span>
                                        </button>
                                    )}
                                    {dashboard.recommendations?.length > 0 && (
                                        <button
                                            onClick={() => scrollToSection('__recommendations')}
                                            className={`w-full text-left px-2.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${isDark ? 'hover:bg-white/5 text-gray-300' : 'hover:bg-gray-200/60 text-gray-700'}`}
                                        >
                                            <Target className="w-3 h-3 text-indigo-400 flex-shrink-0" />
                                            <span className="truncate">Recommendations</span>
                                            <span className={`ml-auto text-[9px] ${t.textMuted}`}>{dashboard.recommendations.length}</span>
                                        </button>
                                    )}
                                </>
                            )}

                            {/* Dataset Summary */}
                            <div className={`mt-6 pt-4 border-t ${t.border}`}>
                                <h3 className={`text-[10px] uppercase tracking-widest font-bold mb-3 px-2 ${t.textMuted}`}>Dataset Summary</h3>
                                <div className="space-y-2 px-2">
                                    <div className="flex justify-between items-center text-xs">
                                        <span className={t.textSecondary}>Total Records</span>
                                        <span className={`font-bold ${t.text}`}>{dashboard.data_source?.split('×')[0]?.replace('rows', '')?.trim() || '-'}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs">
                                        <span className={t.textSecondary}>Total Features</span>
                                        <span className={`font-bold ${t.text}`}>{dashboard.data_source?.split('×')[1]?.replace('columns', '')?.trim() || '-'}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs">
                                        <span className={t.textSecondary}>Domain</span>
                                        <span className={`font-bold capitalize ${t.text}`}>{dashboard.domain || 'General'}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs">
                                        <span className={t.textSecondary}>Visualizations</span>
                                        <span className={`font-bold ${t.text}`}>{allCharts.length}</span>
                                    </div>
                                </div>
                            </div>
                        </nav>
                    )}
                </aside>

                {/* ============ MAIN CONTENT ============ */}
                <main 
                    className="flex-1 min-w-0 p-3 lg:p-4 space-y-4 overflow-x-hidden"
                    onClick={() => setActiveDropdown(null)}
                >
                    {/* ─────── EXECUTIVE SUMMARY TICKER ─────── */}
                    {dashboard.executive_summary && (
                        <div className={`w-full overflow-hidden flex items-center px-3 py-1.5 rounded-lg mb-2 glass-card border-l-4 border-l-indigo-500`}>
                            <Lightbulb className="w-4 h-4 text-indigo-400 mr-2 flex-shrink-0" />
                            <div className="w-full relative whitespace-nowrap overflow-hidden">
                                <p className={`text-xs font-medium animate-marquee whitespace-nowrap inline-block`} style={{ paddingLeft: '100%' }}>
                                    {dashboard.executive_summary}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* ─────── KPI ROW ─────── */}
                    {dashboard.kpis?.length > 0 && (
                        <section>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2.5">
                                {dashboard.kpis.slice(0, 10).map((kpi, i) => {
                                    const kpiColors = [
                                        '#22c55e', '#8b5cf6', '#f97316', '#10b981', '#ec4899',
                                        '#3b82f6', '#14b8a6', '#ef4444', '#eab308', '#6366f1'
                                    ];

                                    const getKPIIcon = () => {
                                        switch (kpi.kpi_type) {
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

                                    const renderSparkline = () => {
                                        if (!kpi.sparkline || !Array.isArray(kpi.sparkline) || kpi.sparkline.length < 3) return null;
                                        const data = kpi.sparkline.slice(-20);
                                        const max = Math.max(...data);
                                        const min = Math.min(...data);
                                        const MathMax = Math.max;
                                        const range = MathMax(max - min, 1);
                                        const svgH = 24;
                                        const svgW = 80;
                                        const points = data.map((v: number, idx: number) => {
                                            const x = (idx / (data.length - 1)) * svgW;
                                            const y = svgH - ((v - min) / range) * (svgH - 4) - 2; // leave 2px padding top/bottom
                                            return `${x},${y}`;
                                        }).join(' ');
                                        // polygon for fill
                                        const fillPoints = `${0},${svgH} ${points} ${svgW},${svgH}`;
                                        const sparkColor = kpi.trend === 'up' ? '#22c55e' : kpi.trend === 'down' ? '#ef4444' : '#3b82f6';
                                        return (
                                            <svg width="100%" height={svgH} className="mt-1.5 opacity-80" preserveAspectRatio="none" viewBox={`0 0 ${svgW} ${svgH}`}>
                                                <polygon
                                                    points={fillPoints}
                                                    fill={sparkColor}
                                                    opacity="0.15"
                                                />
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
                                            className={`animate-fade-up relative overflow-hidden ${t.card} hover:shadow-2xl transition-all duration-300`}
                                            style={{
                                                '--kpi-color': kpiColors[i % 10],
                                                padding: '12px 14px',
                                                borderRadius: '12px',
                                                borderTop: `3px solid ${kpiColors[i % 10]}`
                                            } as React.CSSProperties}
                                        >
                                            {kpi.kpi_type && kpi.kpi_type !== 'count' && kpi.kpi_type !== 'sum' && (
                                                <span className="absolute top-1 right-1.5 text-[10px] opacity-40">{getKPIIcon()}</span>
                                            )}
                                            <p className="kpi-label" style={{ fontSize: '0.65rem', marginBottom: 4 }}>{kpi.title}</p>
                                            <p className="kpi-value" style={{ fontSize: '1.35rem', lineHeight: 1.1 }}>{formatValue(kpi.value, kpi.format)}</p>
                                            {renderSparkline()}
                                            {kpi.trend && (
                                                <div className={`kpi-trend ${kpi.trend}`} style={{ marginTop: 3 }}>
                                                    {kpi.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                                                    {kpi.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                                                    <span className="truncate text-[10px]">{kpi.comparison}</span>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                    )}

                    {/* ─────── INFO PILLS ─────── */}
                    <section className="flex flex-wrap gap-1.5">
                        {[
                            { icon: Calendar, label: dashboard.data_source?.split('×')[0]?.trim() },
                            { icon: Layers, label: dashboard.data_source?.split('×')[1]?.trim() },
                            { icon: Activity, label: `${allCharts.length} visualizations` },
                            { icon: Target, label: `${dashboard.insights?.length || 0} insights` },
                            { icon: Zap, label: `${new Set(allCharts.map(c => c.type)).size || 0} chart types` }
                        ].map((p, i) => (
                            <span key={i} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-medium ${isDark ? 'bg-gray-800/60 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
                                <p.icon className="w-2.5 h-2.5" />{p.label}
                            </span>
                        ))}
                    </section>

                    {/* ─────── SECTIONED CHART GRID ─────── */}
                    {(() => { let globalChartCounter = 0; return resolvedSections.map((section, sIdx) => {
                        const accent = SECTION_ACCENTS[sIdx % SECTION_ACCENTS.length];
                        const globalChartIndex = globalChartCounter;
                        globalChartCounter += section.charts.length;
                        return (
                            <section
                                key={section.name}
                                ref={el => { sectionRefs.current[section.name] = el; }}
                                className="scroll-mt-16"
                            >
                                {viewMode === 'list' ? (
                                    <div className="space-y-2.5">
                                        {section.charts.map((chart, cIdx) => {
                                        const Icon = getChartIcon(chart.type);
                                        const isExpanded = expandedChart === chart.chart_id;
                                        const chartHeight = viewMode === 'list' ? 280 : (isExpanded ? 400 : 220);

                                        // Premium chart type badges
                                        const premiumTypes = ['combo_bar_line', 'lollipop', 'diverging_bar', 'slope', 'dumbbell', 'range_plot', 'band_chart', 'pareto', 'radar', 'sankey', 'sunburst'];
                                        const isPremium = premiumTypes.includes(chart.type);

                                        const getAnalysisLabel = () => {
                                            if (!chart.analysis) return null;
                                            const labels: Record<string, string> = {
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
                                        };

                                        return (
                                            <div
                                                key={chart.chart_id || `${sIdx}-${cIdx}`}
                                                className={`overflow-visible ${t.card} transition-all duration-300 hover:border-blue-400 flex flex-col`}
                                                style={{ padding: 0, borderRadius: 12 }}
                                            >
                                                {/* Chart Header — numbered like Power BI */}
                                                <div className={`flex items-center justify-between px-3 py-2 border-b ${t.border} ${t.cardHeader} drag-handle cursor-move`}>
                                                    <div className="flex items-center gap-1.5 min-w-0">
                                                        <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color: accent.border }} />
                                                        <h3 className={`text-[11px] font-semibold truncate ${t.text}`}>
                                                            <span style={{ color: accent.border }} className="font-bold">{globalChartIndex + cIdx + 1}.</span> {chart.title}
                                                        </h3>
                                                        <span className={`badge-info text-[9px] flex-shrink-0`}>{chart.type.replace(/_/g, ' ')}</span>
                                                        {isPremium && (
                                                            <span className="text-[8px] px-1 py-0.5 rounded bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 font-bold flex-shrink-0">PRO</span>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        {getAnalysisLabel() && (
                                                            <span className={`text-[9px] ${t.textMuted} hidden lg:inline`}>{getAnalysisLabel()}</span>
                                                        )}
                                                        <button
                                                            onClick={() => handleExplainChart(chart)}
                                                            disabled={explainingChart === chart.chart_id}
                                                            className={`flex items-center gap-1 p-1 rounded transition-all text-[9px] font-semibold ${isDark ? 'hover:bg-indigo-500/20 text-indigo-400' : 'hover:bg-indigo-100 text-indigo-600'}`}
                                                            title="Generate AI Explanation"
                                                        >
                                                            {explainingChart === chart.chart_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Lightbulb className="w-3 h-3" />}
                                                            <span className="hidden lg:inline">AI Explain</span>
                                                        </button>
                                                        <button
                                                            onClick={() => setExpandedChart(isExpanded ? null : chart.chart_id)}
                                                            className={`p-1 rounded transition-all ${isDark ? 'hover:bg-white/5 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                                                        >
                                                            <Maximize2 className="w-3 h-3" />
                                                        </button>
                                                        
                                                        {/* Dynamic Chart Settings */}
                                                        <div className="relative">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setActiveDropdown(activeDropdown === chart.chart_id ? null : chart.chart_id);
                                                                }}
                                                                className={`p-1 rounded transition-all ${isDark ? 'hover:bg-white/5 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                                                            >
                                                                <Settings className="w-3 h-3" />
                                                            </button>
                                                            
                                                            {activeDropdown === chart.chart_id && (
                                                                <div className={`absolute right-0 mt-1 w-32 rounded-lg shadow-xl border z-50 overflow-hidden ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                                                                    <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-b ${isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                                                        Chart Type
                                                                    </div>
                                                                    <div className="py-1">
                                                                        {['bar', 'line', 'scatter', 'pie', 'box', 'violin'].map(tType => (
                                                                            <button
                                                                                key={tType}
                                                                                onClick={() => {
                                                                                    setChartOverrides(prev => ({ ...prev, [chart.chart_id]: tType }));
                                                                                    setActiveDropdown(null);
                                                                                }}
                                                                                className={`w-full text-left px-3 py-1.5 text-[10px] hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors ${
                                                                                    (chartOverrides[chart.chart_id] || chart.plotly_config?.data?.[0]?.type) === tType 
                                                                                        ? 'bg-indigo-500/10 text-indigo-500 font-bold' 
                                                                                        : isDark ? 'text-gray-300' : 'text-gray-700'
                                                                                }`}
                                                                            >
                                                                                {tType.charAt(0).toUpperCase() + tType.slice(1)}
                                                                            </button>
                                                                        ))}
                                                                    </div>
                                                                    
                                                                    <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-y mt-1 ${isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                                                        AI Actions
                                                                    </div>
                                                                    <div className="py-1">
                                                                        <button
                                                                            onClick={() => {
                                                                                setActiveDropdown(null);
                                                                                setChatInput(`Tell me about the ${chart.title} chart.`);
                                                                                setIsChatOpen(true);
                                                                            }}
                                                                            className={`w-full text-left px-3 py-1.5 text-[10px] flex items-center gap-2 hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                                                                        >
                                                                            <MessageSquare className="w-3 h-3" />
                                                                            Chat about this
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                {/* AI Explanation Banner */}
                                                {chartExplanations[chart.chart_id] && (
                                                    <div className={`px-3 py-2 text-xs border-b ${isDark ? 'bg-indigo-900/20 border-indigo-500/20 text-indigo-200' : 'bg-indigo-50/50 border-indigo-100 text-indigo-800'}`}>
                                                        <div className="flex items-start gap-2">
                                                            <Lightbulb className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                                                            <p className="leading-relaxed">{chartExplanations[chart.chart_id]}</p>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Chart Content */}
                                                <div className="px-1 pb-1 relative flex-1 h-full min-h-0">
                                                    {renderChart(chart, chartExplanations[chart.chart_id] ? chartHeight - 50 : chartHeight - 10)}
                                                </div>
                                            </div>
                                        );
                                    })}
                                    </div>
                                ) : (
                                    <GridWrapper
                                        className="layout"
                                        layouts={{
                                            lg: section.charts.map((chart, i) => {
                                                const isWide = ['sankey', 'combo_bar_line', 'parcoords', 'slope'].includes(chart.type) || ['sankey', 'scattermatrix'].includes(chart.plotly_config?.data?.[0]?.type);
                                                return {
                                                    i: chart.chart_id || `${sIdx}-${i}`,
                                                    x: isWide ? 0 : (i % 3) * 4,
                                                    y: Math.floor(i / (isWide ? 1 : 3)) * 4,
                                                    w: isWide ? 12 : 4,
                                                    h: chartExplanations[chart.chart_id] ? 5.5 : 4.5,
                                                    minW: 3
                                                };
                                            }),
                                            md: section.charts.map((chart, i) => ({
                                                i: chart.chart_id || `${sIdx}-${i}`,
                                                x: (i % 2) * 6,
                                                y: Math.floor(i / 2) * 4,
                                                w: 6,
                                                h: 4.5,
                                                minW: 4
                                            })),
                                            sm: section.charts.map((chart, i) => ({
                                                i: chart.chart_id || `${sIdx}-${i}`,
                                                x: 0,
                                                y: i * 4,
                                                w: 1,
                                                h: 4.5,
                                                minW: 1
                                            }))
                                        }}
                                        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
                                        cols={{ lg: 12, md: 12, sm: 1, xs: 1, xxs: 1 }}
                                        rowHeight={80}
                                        isDraggable={true}
                                        isResizable={true}
                                        draggableHandle=".drag-handle"
                                        margin={[16, 16]}
                                    >
                                        {section.charts.map((chart, cIdx) => {
                                            const Icon = getChartIcon(chart.type);
                                            const isExpanded = expandedChart === chart.chart_id;
                                            const chartHeight = isExpanded ? 400 : 220;

                                            // Premium chart type badges
                                            const premiumTypes = ['combo_bar_line', 'lollipop', 'diverging_bar', 'slope', 'dumbbell', 'range_plot', 'band_chart', 'pareto', 'radar', 'sankey', 'sunburst'];
                                            const isPremium = premiumTypes.includes(chart.type);

                                            const getAnalysisLabel = () => {
                                                if (!chart.analysis) return null;
                                                const labels: Record<string, string> = {
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
                                            };

                                            return (
                                                <div
                                                    key={chart.chart_id || `${sIdx}-${cIdx}`}
                                                    className={`overflow-visible ${t.card} transition-all duration-300 hover:border-blue-400 flex flex-col`}
                                                    style={{ padding: 0, borderRadius: 12 }}
                                                >
                                                    {/* Chart Header — numbered like Power BI */}
                                                    <div className={`flex items-center justify-between px-3 py-2 border-b ${t.border} ${t.cardHeader} drag-handle cursor-move`}>
                                                        <div className="flex items-center gap-1.5 min-w-0">
                                                            <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color: accent.border }} />
                                                            <h3 className={`text-[11px] font-semibold truncate ${t.text}`}>
                                                                <span style={{ color: accent.border }} className="font-bold">{globalChartIndex + cIdx + 1}.</span> {chart.title}
                                                            </h3>
                                                            <span className={`badge-info text-[9px] flex-shrink-0`}>{chart.type.replace(/_/g, ' ')}</span>
                                                            {isPremium && (
                                                                <span className="text-[8px] px-1 py-0.5 rounded bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 font-bold flex-shrink-0">PRO</span>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-1">
                                                            {getAnalysisLabel() && (
                                                                <span className={`text-[9px] ${t.textMuted} hidden lg:inline`}>{getAnalysisLabel()}</span>
                                                            )}
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); handleExplainChart(chart); }}
                                                                disabled={explainingChart === chart.chart_id}
                                                                className={`flex items-center gap-1 p-1 rounded transition-all text-[9px] font-semibold ${isDark ? 'hover:bg-indigo-500/20 text-indigo-400' : 'hover:bg-indigo-100 text-indigo-600'}`}
                                                                title="Generate AI Explanation"
                                                            >
                                                                {explainingChart === chart.chart_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Lightbulb className="w-3 h-3" />}
                                                                <span className="hidden lg:inline">AI Explain</span>
                                                            </button>
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); setExpandedChart(isExpanded ? null : chart.chart_id); }}
                                                                className={`p-1 rounded transition-all ${isDark ? 'hover:bg-white/5 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                                                            >
                                                                <Maximize2 className="w-3 h-3" />
                                                            </button>
                                                            
                                                            {/* Dynamic Chart Settings */}
                                                            <div className="relative">
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        setActiveDropdown(activeDropdown === chart.chart_id ? null : chart.chart_id);
                                                                    }}
                                                                    className={`p-1 rounded transition-all ${isDark ? 'hover:bg-white/5 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                                                                >
                                                                    <Settings className="w-3 h-3" />
                                                                </button>
                                                                
                                                                {activeDropdown === chart.chart_id && (
                                                                    <div className={`absolute right-0 mt-1 w-32 rounded-lg shadow-xl border z-50 overflow-hidden ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                                                                        <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-b ${isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                                                            Chart Type
                                                                        </div>
                                                                        <div className="py-1">
                                                                            {['bar', 'line', 'scatter', 'pie', 'box', 'violin'].map(tType => (
                                                                                <button
                                                                                    key={tType}
                                                                                    onClick={(e) => {
                                                                                        e.stopPropagation();
                                                                                        setChartOverrides(prev => ({ ...prev, [chart.chart_id]: tType }));
                                                                                        setActiveDropdown(null);
                                                                                    }}
                                                                                    className={`w-full text-left px-3 py-1.5 text-[10px] hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors ${
                                                                                        (chartOverrides[chart.chart_id] || chart.plotly_config?.data?.[0]?.type) === tType 
                                                                                            ? 'bg-indigo-500/10 text-indigo-500 font-bold' 
                                                                                            : isDark ? 'text-gray-300' : 'text-gray-700'
                                                                                    }`}
                                                                                >
                                                                                    {tType.charAt(0).toUpperCase() + tType.slice(1)}
                                                                                </button>
                                                                            ))}
                                                                        </div>
                                                                        
                                                                        <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-y mt-1 ${isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                                                            AI Actions
                                                                        </div>
                                                                        <div className="py-1">
                                                                            <button
                                                                                onClick={(e) => {
                                                                                    e.stopPropagation();
                                                                                    setActiveDropdown(null);
                                                                                    setChatInput(`Tell me about the ${chart.title} chart.`);
                                                                                    setIsChatOpen(true);
                                                                                }}
                                                                                className={`w-full text-left px-3 py-1.5 text-[10px] flex items-center gap-2 hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                                                                            >
                                                                                <MessageSquare className="w-3 h-3" />
                                                                                Chat about this
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    
                                                    {/* AI Explanation Banner */}
                                                    {chartExplanations[chart.chart_id] && (
                                                        <div className={`px-3 py-2 text-xs border-b ${isDark ? 'bg-indigo-900/20 border-indigo-500/20 text-indigo-200' : 'bg-indigo-50/50 border-indigo-100 text-indigo-800'}`}>
                                                            <div className="flex items-start gap-2">
                                                                <Lightbulb className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                                                                <p className="leading-relaxed">{chartExplanations[chart.chart_id]}</p>
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Chart Content */}
                                                    <div className="px-1 pb-1 relative flex-1 h-full min-h-0">
                                                        {renderChart(chart, chartExplanations[chart.chart_id] ? chartHeight - 50 : chartHeight - 10)}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </GridWrapper>
                                )}
                            </section>
                        );
                    }); })()}

                    {/* ─────── AI INSIGHTS & RECOMMENDATIONS ─────── */}
                    <section className="grid grid-cols-1 xl:grid-cols-3 gap-3">
                        {/* AI Insights - Takes 2 columns */}
                        {dashboard.insights?.length > 0 && (
                            <div
                                ref={el => { sectionRefs.current['__insights'] = el; }}
                                className={`xl:col-span-2 rounded-xl border p-4 scroll-mt-16 ${t.card} border-[var(--border-color)]`}
                                style={{ borderLeft: '4px solid #f59e0b' }}
                            >
                                <div className="flex items-center gap-3 mb-4">
                                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#f59e0b' }} />
                                    <h3 className="text-sm font-extrabold uppercase tracking-widest" style={{ color: '#f59e0b' }}>
                                        AI Insights
                                    </h3>
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${isDark ? 'bg-amber-500/10 text-amber-400' : 'bg-amber-100 text-amber-700'}`}>
                                        Automated
                                    </span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {dashboard.insights.map((insight, i) => (
                                        <div key={i} className={`flex items-start gap-2.5 p-2.5 rounded-lg ${isDark ? 'bg-white/3' : 'bg-gray-50'}`}>
                                            <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5" style={{ backgroundColor: ['#14b8a6', '#8b5cf6', '#f59e0b', '#ec4899', '#3b82f6'][i % 5] + '20', color: ['#14b8a6', '#8b5cf6', '#f59e0b', '#ec4899', '#3b82f6'][i % 5] }}>
                                                {i + 1}
                                            </span>
                                            <p className={`text-[11px] leading-relaxed ${t.textSecondary}`}>{insight}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recommendations - Takes 1 column */}
                        {dashboard.recommendations?.length > 0 && (
                            <div
                                ref={el => { sectionRefs.current['__recommendations'] = el; }}
                                className={`rounded-xl border p-4 scroll-mt-16 ${t.card} border-[var(--border-color)]`}
                                style={{ borderLeft: '4px solid #6366f1' }}
                            >
                                <div className="flex items-center gap-3 mb-4">
                                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#6366f1' }} />
                                    <h3 className="text-sm font-extrabold uppercase tracking-widest" style={{ color: '#6366f1' }}>
                                        Recommendations
                                    </h3>
                                </div>
                                <div className="space-y-2">
                                    {dashboard.recommendations.map((rec, i) => (
                                        <div key={i} className={`flex items-start gap-2 p-2.5 rounded-lg ${isDark ? 'bg-white/3' : 'bg-gray-50'}`}>
                                            <span className="text-emerald-500 font-bold text-xs flex-shrink-0 mt-0.5">→</span>
                                            <div className="flex-1 min-w-0">
                                                <p className={`text-[11px] ${t.textSecondary}`}>{rec}</p>
                                            </div>
                                            <span className="text-[10px] font-bold text-emerald-500 flex-shrink-0">+{(15 + i * 8).toFixed(0)}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </section>

                    {/* ─────── DATA GRID VIEW ─────── */}
                    {dashboard.data_grid && dashboard.data_grid.rows.length > 0 && (
                        <section className="mt-8">
                            <div className="flex items-center gap-3 mb-4 px-1">
                                <Database className={`w-4 h-4 text-indigo-400`} />
                                <h3 className={`text-sm font-extrabold uppercase tracking-widest ${t.text}`}>
                                    Raw Data Snapshot
                                </h3>
                                <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${isDark ? 'bg-white/8 text-gray-400' : 'bg-gray-200 text-gray-600'}`}>
                                    Sample ({dashboard.data_grid.rows.length} rows)
                                </span>
                                <button 
                                    onClick={handleExportCSV}
                                    className={`ml-auto flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${isDark ? 'bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'}`}
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    Download CSV
                                </button>
                            </div>
                            <div className={`overflow-x-auto rounded-xl border ${t.border} ${t.card}`}>
                                <table className="w-full text-left text-xs whitespace-nowrap">
                                    <thead className={`border-b ${t.border} ${isDark ? 'bg-white/5' : 'bg-gray-50/80'}`}>
                                        <tr>
                                            {dashboard.data_grid.columns.map(col => (
                                                <th key={col} className={`px-4 py-3 font-bold ${t.textSecondary}`}>{col.replace(/_/g, ' ')}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className={`divide-y ${isDark ? 'divide-gray-800' : 'divide-gray-100'}`}>
                                        {dashboard.data_grid.rows.map((row, i) => (
                                            <tr key={i} className={`transition-colors ${isDark ? 'hover:bg-white/5' : 'hover:bg-blue-50/50'}`}>
                                                {dashboard.data_grid!.columns.map(col => (
                                                    <td key={col} className={`px-4 py-2.5 ${t.textMuted}`}>
                                                        {String(row[col])}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    )}

                </main>
            </div>

            {/* ====================== EXPANDED CHART MODAL ====================== */}
            {expandedChart && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
                    onClick={() => setExpandedChart(null)}
                >
                    <div
                        className={`w-full max-w-6xl max-h-[85vh] rounded-2xl border overflow-hidden ${isDark ? 'bg-[#0f1219] border-gray-700/60' : 'bg-white border-gray-200'}`}
                        onClick={e => e.stopPropagation()}
                    >
                        {allCharts.filter(c => c.chart_id === expandedChart).map(chart => (
                            <div key={chart.chart_id}>
                                <div className={`flex items-center justify-between px-5 py-3 border-b ${t.border}`}>
                                    <div className="flex items-center gap-2">
                                        {React.createElement(getChartIcon(chart.type), { className: 'w-4 h-4', style: { color: t.accent } })}
                                        <h3 className={`text-base font-semibold ${t.text}`}>{chart.title}</h3>
                                        <span className="badge-info text-[10px]">{chart.type.replace(/_/g, ' ')}</span>
                                    </div>
                                    <button
                                        onClick={() => setExpandedChart(null)}
                                        className={`p-1.5 rounded-lg transition-all ${isDark ? 'hover:bg-white/10 text-gray-400' : 'hover:bg-gray-100 text-gray-500'}`}
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="p-4" style={{ height: '65vh' }}>
                                    {renderChart(chart, window.innerHeight * 0.6)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ====================== CHAT DRAWER ====================== */}
            <div 
                className={`fixed top-0 right-0 h-full w-[350px] sm:w-[400px] z-50 transform transition-transform duration-300 ease-in-out ${isChatOpen ? 'translate-x-0' : 'translate-x-full'} ${isDark ? 'glass-panel border-l border-white/10' : 'bg-white/90 backdrop-blur-xl border-l border-gray-200'} shadow-2xl flex flex-col`}
            >
                {/* Header */}
                <div className={`p-4 border-b ${isDark ? 'border-white/10' : 'border-gray-200'} flex items-center justify-between`}>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center">
                            <MessageSquare className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div>
                            <h3 className={`font-semibold ${t.text}`}>Data Assistant</h3>
                            <p className="text-[10px] text-emerald-500 font-medium flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                Online & Analyzing
                            </p>
                        </div>
                    </div>
                    <button 
                        onClick={() => setIsChatOpen(false)}
                        className={`p-1.5 rounded-lg transition-all ${isDark ? 'hover:bg-white/10 text-gray-400' : 'hover:bg-gray-100 text-gray-500'}`}
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
                
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {chatMessages.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} group`}>
                            <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm relative ${
                                msg.role === 'user' 
                                    ? 'bg-indigo-600 text-white rounded-br-none' 
                                    : isDark ? 'bg-white/10 text-gray-200 rounded-bl-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'
                            }`}>
                                {msg.text}
                                {msg.role === 'assistant' && (
                                    <button 
                                        onClick={() => playVoice(msg.text)}
                                        className={`absolute -right-8 top-2 p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-indigo-600'}`}
                                        title="Read aloud"
                                    >
                                        <Volume2 className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                    {chatLoading && (
                        <div className="flex justify-start">
                            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${isDark ? 'bg-white/10' : 'bg-gray-100'} rounded-bl-none flex gap-1.5`}>
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>
                
                {/* Input */}
                <div className={`p-4 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                    <form 
                        onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                        className={`flex items-center gap-2 px-3 py-2 rounded-xl border ${isDark ? 'bg-black/20 border-white/10' : 'bg-white border-gray-200'} focus-within:border-indigo-500 transition-colors`}
                    >
                        <input
                            type="text"
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            placeholder={isListening ? "Listening..." : "Ask about your data..."}
                            className={`flex-1 bg-transparent border-none outline-none text-sm text-inherit ${isListening ? 'text-indigo-400 font-medium' : 'placeholder:opacity-50'}`}
                        />
                        <button
                            type="button"
                            onClick={toggleSpeechRecognition}
                            className={`p-1.5 rounded-lg transition-all ${isListening ? 'text-red-500 bg-red-500/10 animate-pulse' : (isDark ? 'text-gray-400 hover:text-white hover:bg-white/10' : 'text-gray-500 hover:text-indigo-600 hover:bg-gray-100')}`}
                        >
                            {isListening ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                        </button>
                        <button
                            type="submit"
                            disabled={!chatInput.trim() || chatLoading}
                            className={`p-1.5 rounded-lg transition-all ${!chatInput.trim() || chatLoading ? 'opacity-50 cursor-not-allowed' : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
        </>
    );
};

export default VisualIntelligenceDashboard;
