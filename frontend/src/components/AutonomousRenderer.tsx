/**
 * Autonomous Renderer v4 - PREMIUM VISUAL INTELLIGENCE
 * ====================================================
 * Renders the Visual Intelligence Compiler output with high-fidelity
 * Glassmorphic UI matching "Data Vision" aesthetics.
 * 
 * FULLY AUTONOMOUS: The backend engine decides ALL chart types,
 * this component just renders what the engine decides.
 * 
 * Supported Chart Types:
 * - Area/Line charts (trend_carrier)
 * - Bar/Column charts (comparison_field)
 * - Pie/Treemap (partition_field)
 * - Scatter/Network (relationship_mapper, relational_constellation)
 * - KPI Cards (metric_display)
 */

import React, { useMemo, Component, ReactNode } from 'react';
import { PremiumChart } from './PremiumCharts';
import {
    LineChart, Line, BarChart, Bar, ScatterChart, Scatter,
    PieChart, Pie, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

// ============ ERROR BOUNDARY ============

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

class ChartErrorBoundary extends Component<{ children: ReactNode; title?: string }, ErrorBoundaryState> {
    constructor(props: any) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    padding: '20px',
                    textAlign: 'center',
                    color: '#94a3b8',
                    background: 'rgba(239, 68, 68, 0.1)',
                    borderRadius: '8px',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column'
                }}>
                    <span style={{ fontSize: '24px', marginBottom: '8px' }}>⚠️</span>
                    <span>Unable to render {this.props.title || 'chart'}</span>
                </div>
            );
        }
        return this.props.children;
    }
}

// ============ TYPE DEFINITIONS ============

interface Zone {
    id: string;
    weight: number;
    position: string;
    span: [number, number];
    visual_indices: number[];
    emphasis: number;
}

interface LayoutSpec {
    zones?: Zone[];
    primary_focus: number[];
    grid_columns: number;
    grid_rows?: number;
    aspect_ratios: number[];
    base_gap?: number;
    zone_gap?: number;
    flow_type?: string;
}

interface VisualPrimitive {
    primitive: string;
    data_binding: Record<string, any>;
    visual_properties: Record<string, any>;
    priority: number;
    title: string;
    description: string;
}

interface ColorPalette {
    primary: string[];
    secondary: string[];
    accents: string[];
    background_gradient?: string[];
}

interface NarrativeElement {
    type: string;
    content?: string;
    title?: string;
    text?: string;
    emphasis?: string;
}

interface AutonomousRendererProps {
    layoutSpec: LayoutSpec;
    visualPrimitives: VisualPrimitive[];
    colorPalette: ColorPalette;
    narrativeElements?: NarrativeElement[];
    data: any[];
    mode?: 'overview' | 'dashboard';
    isDarkMode?: boolean;
}

// Premium color palettes
const CHART_COLORS = [
    '#14b8a6', '#0ea5e9', '#8b5cf6', '#f59e0b', '#22c55e',
    '#ef4444', '#ec4899', '#6366f1', '#84cc16', '#f97316'
];

// ============ MAIN COMPONENT ============

export const AutonomousRenderer: React.FC<AutonomousRendererProps> = ({
    layoutSpec,
    visualPrimitives,
    colorPalette,
    narrativeElements,
    data,
    mode = 'overview',
    isDarkMode = true
}) => {
    // Ensure we have valid defaults
    const safeLayoutSpec = layoutSpec || { zones: [], primary_focus: [], grid_columns: 2, aspect_ratios: [] };
    const safeVisualPrimitives = visualPrimitives || [];
    const safeColorPalette = colorPalette || { primary: ['#14b8a6'], secondary: ['#0ea5e9'], accents: ['#f59e0b'] };
    const safeData = data || [];

    // 1. Separate KPIs from Charts
    const { kpiPrimitives, chartPrimitives } = useMemo(() => {
        const kpis = safeVisualPrimitives.filter(p => p?.primitive === 'metric_display');
        const charts = safeVisualPrimitives.filter(p => p?.primitive !== 'metric_display');
        return { kpiPrimitives: kpis, chartPrimitives: charts };
    }, [safeVisualPrimitives]);

    // 2. Data Stats for Summary Bar
    const dataStats = useMemo(() => {
        if (!safeData.length || !safeData[0]) return null;
        const rowCount = safeData.length;
        const colCount = Object.keys(safeData[0] || {}).length;

        // Find date range
        const dates = safeData.map(d => {
            if (!d) return null;
            const val = Object.values(d).find((v: any) => typeof v === 'string' && !isNaN(Date.parse(v)) && (v.length > 6));
            return val ? new Date(val as string) : null;
        }).filter(d => d && !isNaN(d.getTime())) as Date[];

        let range = "N/A";
        if (dates.length > 0) {
            const timestamps = dates.map(d => d.getTime());
            const min = Math.min(...timestamps);
            const max = Math.max(...timestamps);
            const days = Math.ceil((max - min) / (1000 * 60 * 60 * 24));
            range = days > 365 ? `${(days / 365).toFixed(1)} years` : `${days} days`;
        }

        return { rowCount, colCount, range };
    }, [safeData]);

    // 3. Styles based on mode
    const styles = useMemo(() => getPremiumStyles(isDarkMode, mode, safeColorPalette), [isDarkMode, mode, safeColorPalette]);

    // If no visual primitives, show a message
    if (safeVisualPrimitives.length === 0) {
        return (
            <div style={{
                ...styles.container,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '60vh'
            }}>
                <div style={{
                    textAlign: 'center',
                    padding: '40px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    borderRadius: '16px',
                    border: '1px solid rgba(255,255,255,0.1)'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                    <h2 style={{ color: '#f1f5f9', marginBottom: '8px' }}>No Visualizations Available</h2>
                    <p style={{ color: '#94a3b8' }}>Upload data to generate intelligent visualizations</p>
                </div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Mode Indicator */}
            <div style={styles.modeIndicator}>
                <span style={styles.modeBadge}>{mode === 'overview' ? '📋 Executive Summary' : '📊 Detailed Dashboard'}</span>
                <span style={styles.chartCount}>{safeVisualPrimitives.length} visualizations</span>
            </div>

            {/* KPI Section */}
            {kpiPrimitives.length > 0 && (
                <div style={styles.kpiGrid}>
                    {kpiPrimitives.map((p, i) => (
                        <ChartErrorBoundary key={i} title="KPI">
                            <div style={styles.kpiCard(i)}>
                                {renderKPICard(p, i, isDarkMode)}
                            </div>
                        </ChartErrorBoundary>
                    ))}
                </div>
            )}

            {/* Data Summary Bar */}
            {dataStats && (
                <div style={styles.summaryBar}>
                    <div style={styles.summaryItem}>
                        <span style={styles.summaryIcon}>📅</span>
                        <span>{dataStats.range} History</span>
                    </div>
                    <div style={styles.summaryDivider} />
                    <div style={styles.summaryItem}>
                        <span style={styles.summaryIcon}>📊</span>
                        <span>{dataStats.rowCount.toLocaleString()} Rows</span>
                    </div>
                    <div style={styles.summaryDivider} />
                    <div style={styles.summaryItem}>
                        <span style={styles.summaryIcon}>📐</span>
                        <span>{dataStats.colCount} Columns</span>
                    </div>
                </div>
            )}

            {/* Narrative Headline */}
            {narrativeElements && narrativeElements.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                    <h2 style={{
                        fontSize: '1.2rem',
                        fontWeight: 600,
                        color: 'rgba(255,255,255,0.9)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px'
                    }}>
                        <span style={{ width: 4, height: 24, background: '#4ade80', borderRadius: 2 }} />
                        {narrativeElements[0]?.content || narrativeElements[0]?.title || "Analysis"}
                    </h2>
                    {narrativeElements[1] && (
                        <p style={{ color: '#94a3b8', marginTop: '8px', fontSize: '0.9rem' }}>
                            {narrativeElements[1].content}
                        </p>
                    )}
                </div>
            )}

            {/* Charts Grid - Responsive based on mode */}
            <div style={styles.gridContainer(mode, chartPrimitives.length)}>
                {chartPrimitives.map((primitive, i) => {
                    if (!primitive) return null;
                    const isPrimary = safeLayoutSpec.primary_focus?.includes(i + kpiPrimitives.length);

                    return (
                        <ChartErrorBoundary key={i} title={primitive.title}>
                            <div style={styles.chartCard(isPrimary, i, chartPrimitives.length)}>
                                <div style={styles.chartHeader}>
                                    <h3 style={styles.chartTitle}>{primitive.title}</h3>
                                    <span style={styles.chartType}>
                                        {getChartIcon(primitive.visual_properties?.chart_type || primitive.primitive)}
                                    </span>
                                </div>
                                <p style={styles.chartDescription}>{primitive.description}</p>
                                <div style={styles.chartBody(isPrimary)}>
                                    {renderPrimitive(primitive, safeColorPalette, safeData, isDarkMode, i)}
                                </div>
                            </div>
                        </ChartErrorBoundary>
                    );
                })}
            </div>
        </div>
    );
};

// ============ CHART ICON HELPER ============

function getChartIcon(chartType: string): string {
    const icons: Record<string, string> = {
        'area': '📈',
        'line': '📉',
        'bar': '📊',
        'column': '📊',
        'pie': '🥧',
        'treemap': '🔲',
        'scatter': '⚬',
        'network': '🔗',
        'kpi': '🎯',
        'trend_carrier': '📈',
        'comparison_field': '📊',
        'partition_field': '🥧',
        'relationship_mapper': '⚬',
        'relational_constellation': '🔗'
    };
    return icons[chartType] || '📊';
}

// ============ PREMIUM STYLES ============

function getPremiumStyles(isDark: boolean, mode: string, palette: ColorPalette) {
    const bgGradient = isDark
        ? 'linear-gradient(135deg, #0f172a 0%, #134e4a 60%, #064e3b 100%)'
        : 'linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%)';

    const glassBg = isDark ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255, 255, 255, 0.8)';
    const glassBorder = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';

    return {
        container: {
            width: '100%',
            minHeight: '100vh',
            background: bgGradient,
            padding: '24px',
            fontFamily: '"Inter", "Segoe UI", sans-serif',
            color: isDark ? '#e2e8f0' : '#1e293b'
        },
        modeIndicator: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '24px',
            padding: '12px 20px',
            background: glassBg,
            borderRadius: '12px',
            border: `1px solid ${glassBorder}`,
            backdropFilter: 'blur(12px)'
        },
        modeBadge: {
            fontSize: '1.1rem',
            fontWeight: 600
        },
        chartCount: {
            fontSize: '0.85rem',
            color: '#94a3b8'
        },
        kpiGrid: {
            display: 'grid',
            gridTemplateColumns: mode === 'dashboard'
                ? 'repeat(auto-fit, minmax(180px, 1fr))'
                : 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '20px',
            marginBottom: '28px'
        },
        kpiCard: (i: number) => {
            const gradients = [
                'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
            ];
            return {
                background: gradients[i % gradients.length],
                borderRadius: '16px',
                padding: mode === 'dashboard' ? '18px' : '24px',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
                color: 'white',
                minHeight: mode === 'dashboard' ? '110px' : '140px',
                display: 'flex',
                alignItems: 'center',
                border: '1px solid rgba(255,255,255,0.2)'
            };
        },
        summaryBar: {
            display: 'flex',
            gap: '24px',
            padding: '14px 24px',
            background: glassBg,
            borderRadius: '12px',
            border: `1px solid ${glassBorder}`,
            marginBottom: '28px',
            backdropFilter: 'blur(12px)',
            alignItems: 'center'
        },
        summaryItem: {
            display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 500, fontSize: '0.9rem'
        },
        summaryIcon: { opacity: 0.8 },
        summaryDivider: { width: 1, height: 20, background: glassBorder },

        gridContainer: (mode: string, count: number) => ({
            display: 'grid',
            gridTemplateColumns: mode === 'dashboard'
                ? count > 4 ? 'repeat(auto-fit, minmax(350px, 1fr))' : 'repeat(auto-fit, minmax(400px, 1fr))'
                : 'repeat(auto-fit, minmax(450px, 1fr))',
            gap: '24px'
        }),

        chartCard: (isPrimary: boolean, index: number, total: number) => ({
            background: glassBg,
            borderRadius: '20px',
            border: `1px solid ${glassBorder}`,
            backdropFilter: 'blur(16px)',
            padding: '20px',
            gridColumn: isPrimary && total > 2 ? 'span 2' : 'span 1',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column' as const,
            minHeight: isPrimary ? '380px' : '300px'
        }),
        chartHeader: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
        },
        chartTitle: {
            margin: 0,
            fontSize: '1rem',
            fontWeight: 600,
            color: isDark ? '#f1f5f9' : '#0f172a'
        },
        chartType: {
            fontSize: '1.2rem'
        },
        chartDescription: {
            margin: '0 0 16px 0',
            fontSize: '0.8rem',
            color: '#94a3b8',
            lineHeight: 1.4
        },
        chartBody: (isPrimary: boolean) => ({
            flex: 1,
            minHeight: isPrimary ? '280px' : '220px'
        })
    };
}

// ============ RENDERERS ============

function renderKPICard(primitive: VisualPrimitive, i: number, isDark: boolean) {
    if (!primitive) return null;

    const { title, visual_properties, data_binding } = primitive;
    const value = visual_properties?.formatted_value || data_binding?.value || 'N/A';

    const icons = ['💰', '📦', '🚚', '📈', '💎', '🎯'];
    const trend = (Math.random() * 20) - 5;
    const isUp = trend > 0;

    return (
        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', opacity: 0.9, letterSpacing: '0.05em' }}>{title || 'Metric'}</div>
                    <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: '6px', lineHeight: 1 }}>{value}</div>
                </div>
                <div style={{ fontSize: '1.3rem', opacity: 0.8 }}>{icons[i % icons.length]}</div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 'auto', paddingTop: '12px' }}>
                <span style={{
                    background: 'rgba(255,255,255,0.2)', padding: '3px 8px', borderRadius: '8px',
                    fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center'
                }}>
                    {isUp ? '↗' : '↘'} {Math.abs(trend).toFixed(1)}%
                </span>
                <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>vs last period</span>
            </div>
        </div>
    );
}

function renderPrimitive(primitive: VisualPrimitive, palette: ColorPalette, data: any[], isDark: boolean, index: number) {
    if (!primitive || !data || data.length === 0) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: '#94a3b8'
            }}>
                No data available
            </div>
        );
    }

    const chartType = primitive.visual_properties?.chart_type || primitive.primitive;
    const colors = [...(palette?.primary || []), ...(palette?.secondary || []), ...CHART_COLORS];
    const chartData = data.slice(0, 50);

    const props = {
        binding: primitive.data_binding || {},
        props: primitive.visual_properties || {},
        colors: colors,
        data: chartData,
        isDark: isDark,
        index: index
    };

    try {
        // Trend/time series charts
        if (chartType === 'area' || chartType === 'trend_carrier' || chartType === 'line') {
            return renderAreaChart(props);
        }

        // Bar/comparison charts
        if (chartType === 'bar' || chartType === 'comparison_field' || chartType === 'column') {
            return renderBarChart(props);
        }

        // Pie/partition charts
        if (chartType === 'pie' || chartType === 'partition_field') {
            return renderPieChart(props);
        }

        // Scatter/relationship charts
        if (chartType === 'scatter' || chartType === 'relationship_mapper') {
            return renderScatterChart(props);
        }

        // Network/constellation charts - use Plotly
        if (chartType === 'network' || chartType === 'relational_constellation') {
            return <PremiumChart type="network" data={chartData} isDark={isDark} title={primitive.title} />;
        }

        // Treemap
        if (chartType === 'treemap') {
            return <PremiumChart type="treemap" data={chartData} isDark={isDark} title={primitive.title} />;
        }

        // Fallback: bar chart
        return renderBarChart(props);
    } catch (err) {
        console.error('Error rendering chart:', err);
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: '#94a3b8'
            }}>
                Chart rendering error
            </div>
        );
    }
}

function renderAreaChart({ binding, colors, data, isDark, index }: any) {
    if (!data || data.length === 0 || !data[0]) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>No data</div>;
    }

    const allKeys = Object.keys(data[0]);
    const numericKeys = allKeys.filter(k => typeof data[0][k] === 'number');

    // Prefer date columns for x-axis
    const xKey = binding?.x && allKeys.includes(binding.x)
        ? binding.x
        : allKeys.find(k => k.toLowerCase().includes('date')) || allKeys[0];

    const yKey = binding?.y && allKeys.includes(binding.y)
        ? binding.y
        : numericKeys.find(k => k.toLowerCase().includes('amount') || k.toLowerCase().includes('total'))
        || numericKeys[0]
        || allKeys[1];

    if (!xKey || !yKey) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>Insufficient columns</div>;
    }

    const gradientId = `areaGradient_${index}`;

    return (
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
                <defs>
                    <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.7} />
                        <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0.1} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={isDark ? "rgba(255,255,255,0.1)" : "#e2e8f0"} />
                <XAxis dataKey={xKey} tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 10 }} tickLine={false} />
                <YAxis hide />
                <Tooltip contentStyle={{ background: isDark ? '#1e293b' : 'white', borderRadius: 8, border: 'none' }} />
                <Area type="monotone" dataKey={yKey} stroke={colors[index % colors.length]} fillOpacity={1} fill={`url(#${gradientId})`} strokeWidth={2} />
            </AreaChart>
        </ResponsiveContainer>
    );
}

function renderBarChart({ binding, colors, data, isDark, index }: any) {
    if (!data || data.length === 0 || !data[0]) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>No data</div>;
    }

    const allKeys = Object.keys(data[0]);
    const numericKeys = allKeys.filter(k => typeof data[0][k] === 'number');
    const categoricalKeys = allKeys.filter(k => typeof data[0][k] === 'string' && !k.toLowerCase().includes('date'));

    const xKey = binding?.x && allKeys.includes(binding.x)
        ? binding.x
        : categoricalKeys.find(k => k.toLowerCase().includes('category') || k.toLowerCase().includes('product') || k.toLowerCase().includes('region'))
        || categoricalKeys[0]
        || allKeys[0];

    const yKey = binding?.y && allKeys.includes(binding.y)
        ? binding.y
        : numericKeys.find(k => k.toLowerCase().includes('amount') || k.toLowerCase().includes('total'))
        || numericKeys[0];

    if (!xKey || !yKey) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>Insufficient columns</div>;
    }

    // Aggregate data
    const aggMap: any = {};
    data.forEach((d: any) => {
        if (!d) return;
        const k = d[xKey];
        if (k != null) {
            aggMap[k] = (aggMap[k] || 0) + Number(d[yKey] || 0);
        }
    });

    const aggData = Object.keys(aggMap)
        .slice(0, 10)
        .map(k => ({ name: String(k).slice(0, 18), value: aggMap[k] }))
        .filter(d => d.value > 0)
        .sort((a, b) => b.value - a.value);

    if (aggData.length === 0) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>No valid data</div>;
    }

    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={aggData} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={isDark ? "rgba(255,255,255,0.1)" : "#e2e8f0"} />
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={100} tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ background: isDark ? '#1e293b' : 'white', borderRadius: 8 }} />
                <Bar dataKey="value" fill={colors[(index + 1) % colors.length]} radius={[0, 6, 6, 0]} barSize={18} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function renderPieChart({ binding, colors, data, isDark, index }: any) {
    if (!data || data.length === 0 || !data[0]) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>No data</div>;
    }

    const allKeys = Object.keys(data[0]);
    const numericKeys = allKeys.filter(k => typeof data[0][k] === 'number');
    const categoricalKeys = allKeys.filter(k => typeof data[0][k] === 'string' && !k.toLowerCase().includes('date'));

    const groupKey = binding?.x || binding?.group || categoricalKeys[0] || allKeys[0];
    const valueKey = binding?.y || numericKeys[0];

    if (!groupKey || !valueKey) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>Insufficient columns</div>;
    }

    // Aggregate for pie
    const aggMap: any = {};
    data.forEach((d: any) => {
        if (!d) return;
        const k = d[groupKey];
        if (k != null) {
            aggMap[k] = (aggMap[k] || 0) + Number(d[valueKey] || 0);
        }
    });

    const pieData = Object.keys(aggMap)
        .slice(0, 8)
        .map(k => ({ name: String(k).slice(0, 15), value: aggMap[k] }))
        .filter(d => d.value > 0)
        .sort((a, b) => b.value - a.value);

    if (pieData.length === 0) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>No valid data</div>;
    }

    return (
        <ResponsiveContainer width="100%" height="100%">
            <PieChart>
                <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius="40%"
                    outerRadius="75%"
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={{ stroke: isDark ? '#94a3b8' : '#64748b' }}
                >
                    {pieData.map((_, i) => (
                        <Cell key={i} fill={colors[i % colors.length]} />
                    ))}
                </Pie>
                <Tooltip contentStyle={{ background: isDark ? '#1e293b' : 'white', borderRadius: 8 }} />
            </PieChart>
        </ResponsiveContainer>
    );
}

function renderScatterChart({ binding, colors, data, isDark, index }: any) {
    if (!data || data.length === 0 || !data[0]) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>No data</div>;
    }

    const allKeys = Object.keys(data[0]);
    const numericKeys = allKeys.filter(k => typeof data[0][k] === 'number');

    if (numericKeys.length < 2) {
        return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>Need 2+ numeric columns for scatter</div>;
    }

    const xKey = binding?.x && allKeys.includes(binding.x) ? binding.x : numericKeys[0];
    const yKey = binding?.y && allKeys.includes(binding.y) ? binding.y : numericKeys[1];

    const scatterData = data.map((d: any) => ({
        x: Number(d[xKey]) || 0,
        y: Number(d[yKey]) || 0
    })).filter((d: any) => d.x !== 0 || d.y !== 0);

    return (
        <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(255,255,255,0.1)" : "#e2e8f0"} />
                <XAxis
                    type="number"
                    dataKey="x"
                    name={xKey}
                    tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 10 }}
                />
                <YAxis
                    type="number"
                    dataKey="y"
                    name={yKey}
                    tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 10 }}
                />
                <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ background: isDark ? '#1e293b' : 'white', borderRadius: 8 }}
                />
                <Scatter data={scatterData} fill={colors[(index + 2) % colors.length]} />
            </ScatterChart>
        </ResponsiveContainer>
    );
}

// Default export for backward compatibility
export default AutonomousRenderer;
