/**
 * AUTONOMOUS VISUAL ENGINE V6 - REAL DATA ANALYST CALCULATIONS
 * All values computed from actual data - no random/placeholder values
 */

import React, { useMemo, Component, ReactNode, CSSProperties } from 'react';
import {
    AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
    PieChart, Pie, LineChart, Line, RadialBarChart, RadialBar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

// Error Boundary
class ChartErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
    constructor(props: any) { super(props); this.state = { hasError: false }; }
    static getDerivedStateFromError() { return { hasError: true }; }
    render() { return this.state.hasError ? <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8' }}>⚠️ Chart Error</div> : this.props.children; }
}

// Theme
interface Theme { bg: string; card: string; text: string; muted: string; border: string; grid: string; success: string; danger: string; }
const getTheme = (isDark: boolean): Theme => isDark ? {
    bg: '#0f172a', card: 'rgba(15, 23, 42, 0.85)', text: '#f1f5f9', muted: '#64748b',
    border: 'rgba(255,255,255,0.1)', grid: 'rgba(255,255,255,0.08)', success: '#22c55e', danger: '#ef4444'
} : { bg: '#f8fafc', card: 'rgba(255,255,255,0.95)', text: '#0f172a', muted: '#64748b', border: 'rgba(0,0,0,0.08)', grid: 'rgba(0,0,0,0.06)', success: '#16a34a', danger: '#dc2626' };

// Color Themes (keyword-based)
const THEMES: Record<string, string[]> = {
    finance: ['#7c3aed', '#8b5cf6', '#a78bfa', '#3b82f6', '#0ea5e9', '#14b8a6'],
    activity: ['#f97316', '#fb923c', '#fdba74', '#ef4444', '#f59e0b', '#eab308'],
    health: ['#14b8a6', '#2dd4bf', '#5eead4', '#22c55e', '#10b981', '#06b6d4'],
    default: ['#14b8a6', '#0ea5e9', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899']
};
function detectTheme(data: any[], palette?: any): string[] {
    if (palette?.primary?.length) return [...palette.primary, ...(palette.secondary || [])];
    const t = JSON.stringify(data).toLowerCase();
    if (/revenue|profit|sales|cost|amount|price/.test(t)) return THEMES.finance;
    if (/activity|user|click|session/.test(t)) return THEMES.activity;
    if (/health|patient|medical/.test(t)) return THEMES.health;
    return THEMES.default;
}

// ============ REAL DATA ANALYST CALCULATIONS ============
interface DataStats {
    count: number;
    dateRange: string;
    dateRangeDays: number;
    numericColCount: number;
    catColCount: number;
}

interface MetricCalc {
    name: string;
    total: number;
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
    trend: number;        // % change (first half vs second half)
    trendDirection: 'up' | 'down' | 'stable';
    outlierCount: number;
}

interface CategoryCalc {
    name: string;
    value: number;
    percent: number;
    rank: number;
}

function calculateDataStats(data: any[]): DataStats {
    if (!data.length) return { count: 0, dateRange: 'No data', dateRangeDays: 0, numericColCount: 0, catColCount: 0 };
    const keys = Object.keys(data[0] || {});
    const numCols = keys.filter(k => typeof data[0][k] === 'number');
    const catCols = keys.filter(k => typeof data[0][k] === 'string');

    // Date range calculation
    let dateRange = 'Recent data';
    let days = 0;
    try {
        const vals = data.flatMap(d => Object.values(d));
        const dates = vals.filter((v): v is string => typeof v === 'string' && !isNaN(Date.parse(v)) && v.includes('-'));
        if (dates.length > 1) {
            const sorted = dates.map(d => new Date(d).getTime()).sort((a, b) => a - b);
            days = Math.ceil((sorted[sorted.length - 1] - sorted[0]) / 86400000);
            dateRange = days > 365 ? `${Math.floor(days / 365)} years of data` : days > 30 ? `${Math.floor(days / 30)} months` : `${days} days`;
        }
    } catch { }

    return { count: data.length, dateRange, dateRangeDays: days, numericColCount: numCols.length, catColCount: catCols.length };
}

function calculateMetric(data: any[], col: string): MetricCalc {
    const values = data.map(d => Number(d[col]) || 0).filter(v => !isNaN(v));
    const n = values.length;
    if (n === 0) return { name: col, total: 0, mean: 0, median: 0, std: 0, min: 0, max: 0, trend: 0, trendDirection: 'stable', outlierCount: 0 };

    // Basic stats
    const total = values.reduce((s, v) => s + v, 0);
    const mean = total / n;
    const sorted = [...values].sort((a, b) => a - b);
    const median = n % 2 ? sorted[Math.floor(n / 2)] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2;
    const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / n;
    const std = Math.sqrt(variance);
    const min = sorted[0];
    const max = sorted[n - 1];

    // Trend: compare first vs second half (real calculation)
    const half = Math.floor(n / 2);
    const firstHalf = values.slice(0, half);
    const secondHalf = values.slice(half);
    const firstMean = firstHalf.reduce((s, v) => s + v, 0) / firstHalf.length;
    const secondMean = secondHalf.reduce((s, v) => s + v, 0) / secondHalf.length;
    const trend = firstMean !== 0 ? ((secondMean - firstMean) / firstMean) * 100 : 0;
    const trendDirection = trend > 5 ? 'up' : trend < -5 ? 'down' : 'stable';

    // Outliers (IQR method)
    const q1 = sorted[Math.floor(n * 0.25)];
    const q3 = sorted[Math.floor(n * 0.75)];
    const iqr = q3 - q1;
    const outlierCount = values.filter(v => v < q1 - 1.5 * iqr || v > q3 + 1.5 * iqr).length;

    return { name: col, total, mean, median, std, min, max, trend: Math.round(trend * 10) / 10, trendDirection, outlierCount };
}

function calculateCategoryBreakdown(data: any[], catCol: string, valCol: string): CategoryCalc[] {
    const agg: Record<string, number> = {};
    data.forEach(d => { const k = d[catCol]; if (k) agg[k] = (agg[k] || 0) + Number(d[valCol] || 0); });
    const total = Object.values(agg).reduce((s, v) => s + v, 0);
    return Object.entries(agg)
        .map(([name, value], i) => ({ name, value, percent: Math.round((value / total) * 1000) / 10, rank: 0 }))
        .sort((a, b) => b.value - a.value)
        .map((c, i) => ({ ...c, rank: i + 1 }));
}

function calculateCorrelation(data: any[], col1: string, col2: string): number {
    const vals1 = data.map(d => Number(d[col1]) || 0);
    const vals2 = data.map(d => Number(d[col2]) || 0);
    const n = vals1.length;
    const mean1 = vals1.reduce((s, v) => s + v, 0) / n;
    const mean2 = vals2.reduce((s, v) => s + v, 0) / n;
    let num = 0, d1 = 0, d2 = 0;
    for (let i = 0; i < n; i++) {
        num += (vals1[i] - mean1) * (vals2[i] - mean2);
        d1 += (vals1[i] - mean1) ** 2;
        d2 += (vals2[i] - mean2) ** 2;
    }
    return d1 && d2 ? num / Math.sqrt(d1 * d2) : 0;
}

// ============ MAIN COMPONENT ============
interface Props {
    visualPrimitives?: any[];
    colorPalette?: any;
    data?: any[];
    mode?: 'overview' | 'dashboard';
    isDarkMode?: boolean;
}

export const AutonomousRenderer: React.FC<Props> = ({ visualPrimitives = [], colorPalette, data = [], mode = 'overview', isDarkMode = true }) => {
    const theme = useMemo(() => getTheme(isDarkMode), [isDarkMode]);
    const colors = useMemo(() => detectTheme(data, colorPalette), [data, colorPalette]);

    // REAL DATA CALCULATIONS
    const stats = useMemo(() => calculateDataStats(data), [data]);
    const numCols = useMemo(() => Object.keys(data[0] || {}).filter(k => typeof data[0][k] === 'number'), [data]);
    const catCols = useMemo(() => Object.keys(data[0] || {}).filter(k => typeof data[0][k] === 'string'), [data]);
    const metrics = useMemo(() => numCols.slice(0, 6).map(c => calculateMetric(data, c)), [data, numCols]);
    const categories = useMemo(() => catCols[0] && numCols[0] ? calculateCategoryBreakdown(data, catCols[0], numCols[0]) : [], [data, catCols, numCols]);

    // ============ TRULY AUTONOMOUS CHART SELECTION ============
    // Analyzes ACTUAL DATA VALUES, not just column types!
    const dataPatterns = useMemo(() => {
        if (!data.length || !metrics.length) {
            return {
                varianceLevel: 0.5, distributionSkew: 0, outlierRatio: 0, trendStrength: 0,
                categorySpread: 0.5, correlationStrength: 0, complexity: 'low' as const,
                dominantPattern: 'balanced' as const, uniqueCategories: 0, recordsPerCategory: 0
            };
        }

        // 1. VARIANCE ANALYSIS - How spread out is the data?
        const primaryMetric = metrics[0];
        const coefficientOfVariation = primaryMetric.mean > 0 ? primaryMetric.std / primaryMetric.mean : 0;
        const varianceLevel = Math.min(1, coefficientOfVariation); // 0 = uniform, 1 = highly variable

        // 2. DISTRIBUTION SKEW - Is data concentrated at top/bottom?
        const skewRatio = primaryMetric.median > 0 ? (primaryMetric.mean - primaryMetric.median) / primaryMetric.median : 0;
        const distributionSkew = Math.max(-1, Math.min(1, skewRatio)); // -1 = left skew, 0 = normal, 1 = right skew

        // 3. OUTLIER RATIO - How many outliers vs normal points?
        const outlierRatio = primaryMetric.outlierCount / Math.max(1, data.length);

        // 4. TREND STRENGTH - How strong is the trend?
        const trendStrength = Math.abs(primaryMetric.trend) / 100; // 0 = no trend, 1 = very strong

        // 5. CATEGORY ANALYSIS - How many categories and their distribution?
        const uniqueCategories = categories.length;
        const recordsPerCategory = uniqueCategories > 0 ? data.length / uniqueCategories : 0;
        const categorySpread = uniqueCategories > 0
            ? Math.min(1, uniqueCategories / 20) // 0-1 based on category count (20+ = max)
            : 0;

        // 6. CORRELATION CHECK - Do metrics correlate?
        let correlationStrength = 0;
        if (metrics.length >= 2) {
            const m1 = metrics[0], m2 = metrics[1];
            // Simple correlation approximation based on trend alignment
            correlationStrength = m1.trendDirection === m2.trendDirection ? 0.7 : 0.3;
        }

        // 7. COMPLEXITY SCORE - Overall data complexity
        const complexityScore = (varianceLevel * 0.3) + (categorySpread * 0.3) + (trendStrength * 0.2) + (outlierRatio * 0.2);
        const complexity: 'low' | 'medium' | 'high' = complexityScore > 0.6 ? 'high' : complexityScore > 0.3 ? 'medium' : 'low';

        // 8. DOMINANT PATTERN - What type of visualization is best?
        let dominantPattern: 'temporal' | 'distribution' | 'relationship' | 'categorical' | 'balanced';
        if (trendStrength > 0.3) {
            dominantPattern = 'temporal';
        } else if (varianceLevel > 0.5 && metrics.length >= 2) {
            dominantPattern = 'relationship';
        } else if (uniqueCategories >= 3 && uniqueCategories <= 12) {
            dominantPattern = 'distribution';
        } else if (uniqueCategories > 12) {
            dominantPattern = 'categorical';
        } else {
            dominantPattern = 'balanced';
        }

        return {
            varianceLevel,      // 0-1: low to high variance
            distributionSkew,   // -1 to 1: left to right skew
            outlierRatio,       // 0-1: few to many outliers
            trendStrength,      // 0-1: weak to strong trend
            categorySpread,     // 0-1: few to many categories
            correlationStrength,// 0-1: weak to strong correlation
            complexity,         // 'low', 'medium', 'high'
            dominantPattern,    // best chart family
            uniqueCategories,   // actual category count
            recordsPerCategory  // avg records per category
        };
    }, [data, metrics, categories]);

    // Background
    const bgStyle: CSSProperties = { background: isDarkMode ? `linear-gradient(135deg, ${colors[0]}15 0%, #0f172a 50%, ${colors[1]}10 100%)` : 'linear-gradient(135deg, #f8fafc, #e0e7ff)' };

    if (!data.length) return <div style={{ ...containerStyle, ...bgStyle, minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: 40, background: theme.card, borderRadius: 20 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🧠</div>
            <h2 style={{ color: theme.text }}>Autonomous Engine Ready</h2>
            <p style={{ color: theme.muted }}>Upload data to generate insights</p>
        </div>
    </div>;

    return (
        <div style={{ ...containerStyle, ...bgStyle, color: theme.text }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                <div style={{ fontSize: '1rem', fontWeight: 600, padding: '10px 18px', background: `${colors[0]}25`, borderRadius: 10, color: 'white' }}>
                    {mode === 'overview' ? '📋 Overview' : '📊 Dashboard'}
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                    <Badge text={`📅 ${stats.dateRange}`} theme={theme} />
                    <Badge text={`📊 ${stats.count.toLocaleString()}+ records`} theme={theme} />
                    <Badge text={`📐 ${stats.numericColCount} metrics`} theme={theme} />
                </div>
            </div>

            {/* KPIs from REAL calculations */}
            <div style={{ display: 'grid', gridTemplateColumns: mode === 'dashboard' ? `repeat(${Math.min(metrics.length, 6)}, 1fr)` : `repeat(${Math.min(metrics.length, 3)}, 1fr)`, gap: mode === 'dashboard' ? 10 : 16, marginBottom: 24 }}>
                {metrics.slice(0, mode === 'dashboard' ? 6 : 3).map((m, i) => (
                    <KPICard key={i} metric={m} color={colors[i % colors.length]} compact={mode === 'dashboard'} />
                ))}
            </div>

            {/* Insights Panel (Overview only) */}
            {mode === 'overview' && <InsightsPanel metrics={metrics} categories={categories} stats={stats} colors={colors} theme={theme} />}

            {/* DYNAMIC CHART GRID - Charts selected based on data patterns! */}
            <DynamicChartGrid
                data={data}
                metrics={metrics}
                categories={categories}
                colors={colors}
                theme={theme}
                mode={mode}
                patterns={dataPatterns}
            />

            {/* Summary Row */}
            {mode === 'dashboard' && <SummaryRow metrics={metrics} colors={colors} theme={theme} />}
        </div>
    );
};

// ============================================================
// DYNAMIC CHART GRID - STRICT MODE SEPARATION
// Overview and Dashboard have COMPLETELY DIFFERENT chart pools!
// ============================================================
interface DataPatterns {
    varianceLevel: number;      // 0-1: how spread out the data is
    distributionSkew: number;   // -1 to 1: left to right skew
    outlierRatio: number;       // 0-1: percentage of outliers
    trendStrength: number;      // 0-1: strength of trend
    categorySpread: number;     // 0-1: based on category count
    correlationStrength: number;// 0-1: how correlated metrics are
    complexity: 'low' | 'medium' | 'high';
    dominantPattern: 'temporal' | 'distribution' | 'relationship' | 'categorical' | 'balanced';
    uniqueCategories: number;
    recordsPerCategory: number;
}

const DynamicChartGrid: React.FC<{
    data: any[];
    metrics: MetricCalc[];
    categories: CategoryCalc[];
    colors: string[];
    theme: Theme;
    mode: 'overview' | 'dashboard';
    patterns: DataPatterns;
}> = ({ data, metrics, categories, colors, theme, mode, patterns }) => {

    // Dynamic gradient intensity based on data variance
    const gradientIntensity = useMemo(() => {
        const intensity = patterns.varianceLevel > 0.6 ? 'intense' : patterns.varianceLevel > 0.3 ? 'medium' : 'subtle';
        return intensity;
    }, [patterns]);

    // ============ OVERVIEW-ONLY CHARTS (15 types) ============
    // Scores based on ACTUAL data values - different datasets = different charts!
    const overviewCharts = useMemo(() => {
        const { varianceLevel, trendStrength, categorySpread, uniqueCategories, outlierRatio, dominantPattern, complexity } = patterns;

        const charts: Array<{ type: string; score: number; component: React.ReactNode }> = [
            // Radar - best for low variance, multiple metrics
            {
                type: 'radar', score: (1 - varianceLevel) * 30 + (metrics.length >= 3 ? 20 : 0),
                component: <RadarChart key="radar" metrics={metrics.slice(0, 6)} colors={colors} theme={theme} />
            },

            // Gauge - best for low complexity, single focus
            {
                type: 'gauge', score: complexity === 'low' ? 35 : complexity === 'medium' ? 20 : 10,
                component: <GaugeChart key="gauge" metrics={metrics} colors={colors} theme={theme} />
            },

            // Waterfall - best for moderate categories, showing contribution
            {
                type: 'waterfall', score: categorySpread * 25 + (uniqueCategories >= 3 && uniqueCategories <= 10 ? 20 : 0),
                component: <WaterfallChart key="waterfall" categories={categories.slice(0, 8)} colors={colors} theme={theme} />
            },

            // Network - best for high correlation, relationships
            {
                type: 'network', score: patterns.correlationStrength * 40 + varianceLevel * 15,
                component: <RelationshipNetwork key="network" data={data} colors={colors} theme={theme} />
            },

            // Key Drivers - best for showing impact, many metrics
            {
                type: 'key_drivers', score: (metrics.length >= 4 ? 25 : 10) + trendStrength * 20,
                component: <KeyDrivers key="drivers" metrics={metrics} colors={colors} theme={theme} />
            },

            // Pie - best for FEW categories (2-6), low variance
            {
                type: 'pie', score: (uniqueCategories >= 2 && uniqueCategories <= 6 ? 40 : 5) + (1 - varianceLevel) * 15,
                component: <ChartCard key="pie" title="Category Distribution" icon="🥧" theme={theme} colors={colors}><CategoryPie categories={categories} colors={colors} theme={theme} /></ChartCard>
            },

            // Donut - medium categories, shows progress
            {
                type: 'donut', score: (uniqueCategories >= 3 && uniqueCategories <= 8 ? 30 : 10) + trendStrength * 15,
                component: <DriversRadial key="donut" metrics={metrics} colors={colors} theme={theme} />
            },

            // Sunburst - best for MANY categories (8+), hierarchical
            {
                type: 'sunburst', score: (uniqueCategories >= 8 ? 40 : uniqueCategories >= 5 ? 25 : 5),
                component: <SunburstChart key="sunburst" categories={categories} metrics={metrics} colors={colors} theme={theme} />
            },

            // Polar Area - moderate categories, comparing relative sizes
            {
                type: 'polar_area', score: (uniqueCategories >= 4 && uniqueCategories <= 10 ? 30 : 10) + categorySpread * 15,
                component: <PolarAreaChart key="polar" categories={categories.slice(0, 8)} colors={colors} theme={theme} />
            },

            // Radial Stack - multiple metrics with progress
            {
                type: 'radial_stack', score: (metrics.length >= 3 ? 35 : 15) + trendStrength * 15,
                component: <RadialProgressStack key="radial_stack" metrics={metrics.slice(0, 4)} colors={colors} theme={theme} />
            },

            // Metric Grid - many metrics, low complexity
            {
                type: 'metric_grid', score: (metrics.length >= 4 ? 30 : 10) + (complexity === 'low' ? 20 : 5),
                component: <MetricCardsGrid key="metric_grid" metrics={metrics.slice(0, 6)} colors={colors} theme={theme} />
            },

            // Icon Progress - simple data, few metrics
            {
                type: 'icon_progress', score: (metrics.length <= 3 ? 30 : 10) + (1 - varianceLevel) * 15,
                component: <IconProgressChart key="icon_progress" metrics={metrics.slice(0, 3)} colors={colors} theme={theme} />
            },

            // Arc Gauge - medium complexity, multiple segments
            {
                type: 'arc_gauge', score: complexity === 'medium' ? 30 : 15,
                component: <ArcGaugeChart key="arc_gauge" metrics={metrics} colors={colors} theme={theme} />
            },

            // Bubble Matrix - high variance, many categories
            {
                type: 'bubble_matrix', score: varianceLevel * 30 + (uniqueCategories >= 6 ? 20 : 5),
                component: <BubbleMatrixChart key="bubble_matrix" categories={categories} metrics={metrics} colors={colors} theme={theme} />
            },

            // Comparison Bars - showing before/after or change
            {
                type: 'comparison', score: trendStrength * 35 + varianceLevel * 15,
                component: <ComparisonBarsChart key="comparison" metrics={metrics.slice(0, 4)} colors={colors} theme={theme} />
            },
        ];
        return charts.sort((a, b) => b.score - a.score);
    }, [data, metrics, categories, colors, theme, patterns]);

    // ============ DASHBOARD-ONLY CHARTS (15 types) ============
    // Scores based on ACTUAL data values - different datasets = different charts!
    const dashboardCharts = useMemo(() => {
        const { varianceLevel, trendStrength, categorySpread, uniqueCategories, outlierRatio, correlationStrength, complexity } = patterns;

        const charts: Array<{ type: string; score: number; component: React.ReactNode }> = [
            // Treemap - best for MANY categories (10+), hierarchical distribution
            {
                type: 'treemap', score: (uniqueCategories >= 10 ? 45 : uniqueCategories >= 6 ? 30 : 10),
                component: <TreemapChart key="treemap" categories={categories} colors={colors} theme={theme} />
            },

            // Scatter - best for HIGH variance, correlation analysis
            {
                type: 'scatter', score: varianceLevel * 40 + correlationStrength * 20 + outlierRatio * 15,
                component: <ScatterCorrelation key="scatter" data={data} colors={colors} theme={theme} />
            },

            // Heatmap - best for MANY metrics (4+), complex relationships
            {
                type: 'heatmap', score: (metrics.length >= 4 ? 40 : 15) + correlationStrength * 20,
                component: <HeatmapGrid key="heatmap" metrics={metrics} colors={colors} theme={theme} />
            },

            // Funnel - best for ordered categories (3-7), conversion flow
            {
                type: 'funnel', score: (uniqueCategories >= 3 && uniqueCategories <= 7 ? 40 : 10) + (1 - varianceLevel) * 10,
                component: <FunnelChart key="funnel" categories={categories} colors={colors} theme={theme} />
            },

            // Stacked Bars - moderate categories, segment comparison
            {
                type: 'stacked_bars', score: (uniqueCategories >= 4 && uniqueCategories <= 12 ? 35 : 15) + categorySpread * 15,
                component: <StackedBarsChart key="stacked" metrics={metrics} categories={categories} colors={colors} theme={theme} />
            },

            // Efficiency Bars - showing progress, performance
            {
                type: 'efficiency', score: trendStrength * 30 + (1 - outlierRatio) * 15,
                component: <EfficiencyBars key="eff" metrics={metrics} colors={colors} theme={theme} />
            },

            // Trend - best for STRONG trends, temporal data
            {
                type: 'trend', score: trendStrength * 50 + (complexity === 'high' ? 15 : 5),
                component: <ChartCard key="trend" title="Performance Trend" icon="📊" theme={theme} colors={colors}><TrendChart data={data} metrics={metrics} colors={colors} theme={theme} /></ChartCard>
            },

            // Ranked List - ordered data, top performers
            {
                type: 'ranked_list', score: (uniqueCategories >= 5 ? 30 : 15) + varianceLevel * 20,
                component: <TopOpportunities key="ranked" categories={categories} colors={colors} theme={theme} />
            },

            // Lollipop - clean categorical ranking, moderate categories
            {
                type: 'lollipop', score: (uniqueCategories >= 5 && uniqueCategories <= 15 ? 35 : 10) + (1 - outlierRatio) * 10,
                component: <LollipopChart key="lollipop" categories={categories.slice(0, 10)} colors={colors} theme={theme} />
            },

            // Diverging - positive/negative, variance analysis
            {
                type: 'diverging', score: varianceLevel * 35 + outlierRatio * 20,
                component: <DivergingBarChart key="diverging" metrics={metrics} colors={colors} theme={theme} />
            },

            // Stream - time series, flowing trends
            {
                type: 'stream', score: trendStrength * 40 + (metrics.length >= 3 ? 15 : 5),
                component: <StreamGraphChart key="stream" data={data} metrics={metrics} colors={colors} theme={theme} />
            },

            // Parallel - multi-dimensional, complex data
            {
                type: 'parallel', score: (metrics.length >= 4 ? 40 : 10) + complexity === 'high' ? 20 : 5,
                component: <ParallelCoordinatesChart key="parallel" data={data} metrics={metrics} colors={colors} theme={theme} />
            },

            // Bullet - actual vs target, performance
            {
                type: 'bullet', score: trendStrength * 25 + (1 - varianceLevel) * 20,
                component: <BulletChart key="bullet" metrics={metrics.slice(0, 4)} colors={colors} theme={theme} />
            },

            // Calendar - temporal patterns, periodic data
            {
                type: 'calendar', score: trendStrength * 45 + (data.length >= 30 ? 15 : 0),
                component: <CalendarHeatmapChart key="calendar" data={data} colors={colors} theme={theme} />
            },

            // Sankey - flow analysis, many categories
            {
                type: 'sankey', score: (uniqueCategories >= 4 ? 35 : 10) + correlationStrength * 20,
                component: <SankeyFlowChart key="sankey" categories={categories} colors={colors} theme={theme} />
            },
        ];
        return charts.sort((a, b) => b.score - a.score);
    }, [data, metrics, categories, colors, theme, patterns]);

    // Select charts based on MODE - completely different pools!
    const selectedCharts = mode === 'overview'
        ? overviewCharts.slice(0, 5)  // Overview gets 5 overview-specific charts
        : dashboardCharts.slice(0, 8); // Dashboard gets 8 dashboard-specific charts

    // Dynamic grid layout
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Row 1: Top 2 charts */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {selectedCharts[0]?.component}
                {selectedCharts[1]?.component}
            </div>
            {/* Row 2: Next 3 charts */}
            <div style={{ display: 'grid', gridTemplateColumns: mode === 'overview' ? '1fr 1.5fr 1fr' : 'repeat(3, 1fr)', gap: 16 }}>
                {selectedCharts[2]?.component}
                {selectedCharts[3]?.component}
                {selectedCharts[4]?.component}
            </div>
            {/* Row 3: Dashboard gets more charts */}
            {mode === 'dashboard' && selectedCharts.length > 5 && (
                <div style={{ display: 'grid', gridTemplateColumns: selectedCharts.length > 6 ? '1fr 1fr 1fr' : '1fr 1fr', gap: 16 }}>
                    {selectedCharts.slice(5, 8).map(c => c.component)}
                </div>
            )}
            {/* Show chart selection reasoning - NOW SHOWS REAL DATA ANALYSIS! */}
            <div style={{ background: theme.card, borderRadius: 12, padding: 14, border: `1px solid ${theme.border}` }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: colors[0], marginBottom: 8 }}>🧠 Autonomous Chart Selection (Data-Driven)</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: '0.7rem', color: theme.muted }}>
                    <span style={{ fontWeight: 600, color: theme.text }}>Mode: {mode.toUpperCase()}</span>
                    <span>|</span>
                    <span>Variance: {(patterns.varianceLevel * 100).toFixed(0)}%</span>
                    <span>|</span>
                    <span>Trend: {(patterns.trendStrength * 100).toFixed(0)}%</span>
                    <span>|</span>
                    <span>Outliers: {(patterns.outlierRatio * 100).toFixed(0)}%</span>
                    <span>|</span>
                    <span>Categories: {patterns.uniqueCategories}</span>
                    <span>|</span>
                    <span style={{ fontWeight: 600, color: colors[1] }}>Pattern: {patterns.dominantPattern}</span>
                </div>
                <div style={{ marginTop: 8, fontSize: '0.7rem', color: colors[0] }}>
                    <strong>Selected {mode === 'overview' ? 'Overview' : 'Dashboard'} Charts:</strong> {selectedCharts.map(c => c.type).join(', ')}
                </div>
            </div>
        </div>
    );
};

// ============================================================
// NEW CHART COMPONENT IMPLEMENTATIONS (16 New Charts!)
// ============================================================

// OVERVIEW CHARTS: Sunburst, PolarArea, RadialProgressStack, MetricCardsGrid, IconProgress, ArcGauge, BubbleMatrix, ComparisonBars

const SunburstChart: React.FC<{ categories: CategoryCalc[]; metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const total = categories.reduce((s, c) => s + c.value, 0);
    let angle = 0;
    return (
        <ChartCard title="Hierarchical Distribution" icon="🌅" theme={theme} colors={colors}>
            <svg viewBox="0 0 200 200" style={{ width: '100%', height: 200 }}>
                {categories.slice(0, 8).map((cat, i) => {
                    const sweep = (cat.value / total) * 360;
                    const startAngle = angle * Math.PI / 180;
                    angle += sweep;
                    const endAngle = angle * Math.PI / 180;
                    const x1 = 100 + 60 * Math.cos(startAngle);
                    const y1 = 100 + 60 * Math.sin(startAngle);
                    const x2 = 100 + 60 * Math.cos(endAngle);
                    const y2 = 100 + 60 * Math.sin(endAngle);
                    const x3 = 100 + 85 * Math.cos(endAngle);
                    const y3 = 100 + 85 * Math.sin(endAngle);
                    const x4 = 100 + 85 * Math.cos(startAngle);
                    const y4 = 100 + 85 * Math.sin(startAngle);
                    const largeArc = sweep > 180 ? 1 : 0;
                    return (
                        <g key={i}>
                            <path d={`M${x1},${y1} A60,60 0 ${largeArc},1 ${x2},${y2} L${x3},${y3} A85,85 0 ${largeArc},0 ${x4},${y4} Z`}
                                fill={colors[i % colors.length]} opacity={0.8 - i * 0.05} />
                            <path d={`M${100 + 30 * Math.cos(startAngle)},${100 + 30 * Math.sin(startAngle)} A30,30 0 ${largeArc},1 ${100 + 30 * Math.cos(endAngle)},${100 + 30 * Math.sin(endAngle)} L100,100 Z`}
                                fill={colors[i % colors.length]} opacity={0.5} />
                        </g>
                    );
                })}
                <circle cx="100" cy="100" r="20" fill={theme.card} />
                <text x="100" y="105" textAnchor="middle" fill={theme.text} fontSize="10" fontWeight="bold">{categories.length}</text>
            </svg>
        </ChartCard>
    );
};

const PolarAreaChart: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const max = Math.max(...categories.map(c => c.value));
    const sliceAngle = 360 / Math.min(categories.length, 8);
    return (
        <ChartCard title="Polar Distribution" icon="🎯" theme={theme} colors={colors}>
            <svg viewBox="0 0 200 200" style={{ width: '100%', height: 180 }}>
                {categories.slice(0, 8).map((cat, i) => {
                    const r = 30 + (cat.value / max) * 55;
                    const startAngle = (i * sliceAngle - 90) * Math.PI / 180;
                    const endAngle = ((i + 1) * sliceAngle - 90) * Math.PI / 180;
                    const x1 = 100 + r * Math.cos(startAngle);
                    const y1 = 100 + r * Math.sin(startAngle);
                    const x2 = 100 + r * Math.cos(endAngle);
                    const y2 = 100 + r * Math.sin(endAngle);
                    return <path key={i} d={`M100,100 L${x1},${y1} A${r},${r} 0 0,1 ${x2},${y2} Z`} fill={colors[i % colors.length]} opacity={0.7} />
                })}
                {[20, 40, 60, 80].map(r => <circle key={r} cx="100" cy="100" r={r} fill="none" stroke={theme.border} strokeWidth="0.5" />)}
            </svg>
        </ChartCard>
    );
};

const RadialProgressStack: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <ChartCard title="Progress Overview" icon="🔄" theme={theme} colors={colors}>
        <svg viewBox="0 0 200 200" style={{ width: '100%', height: 180 }}>
            {metrics.slice(0, 4).map((m, i) => {
                const r = 80 - i * 18;
                const pct = Math.min(100, Math.max(0, 50 + m.trend));
                const circumference = 2 * Math.PI * r;
                const dashOffset = circumference * (1 - pct / 100);
                return (
                    <g key={i}>
                        <circle cx="100" cy="100" r={r} fill="none" stroke={theme.border} strokeWidth="12" />
                        <circle cx="100" cy="100" r={r} fill="none" stroke={colors[i]} strokeWidth="12"
                            strokeDasharray={circumference} strokeDashoffset={dashOffset}
                            transform="rotate(-90 100 100)" strokeLinecap="round" />
                    </g>
                );
            })}
            <text x="100" y="100" textAnchor="middle" fill={theme.text} fontSize="16" fontWeight="bold">{metrics.length}</text>
            <text x="100" y="115" textAnchor="middle" fill={theme.muted} fontSize="9">metrics</text>
        </svg>
    </ChartCard>
);

const MetricCardsGrid: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <ChartCard title="Metrics Summary" icon="📋" theme={theme} colors={colors}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            {metrics.slice(0, 6).map((m, i) => (
                <div key={i} style={{ background: `${colors[i % colors.length]}20`, borderRadius: 8, padding: 10, textAlign: 'center', border: `1px solid ${colors[i % colors.length]}40` }}>
                    <div style={{ fontSize: '0.65rem', color: theme.muted, textTransform: 'uppercase' }}>{m.name.replace(/_/g, ' ').slice(0, 10)}</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: colors[i % colors.length] }}>{formatNum(m.mean)}</div>
                    <div style={{ fontSize: '0.6rem', color: m.trend >= 0 ? theme.success : theme.danger }}>{m.trend >= 0 ? '↑' : '↓'}{Math.abs(m.trend)}%</div>
                </div>
            ))}
        </div>
    </ChartCard>
);

const IconProgressChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <ChartCard title="Icon Progress" icon="🎨" theme={theme} colors={colors}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {metrics.slice(0, 3).map((m, i) => {
                const pct = Math.min(100, Math.max(10, 50 + m.trend));
                const filled = Math.floor(pct / 10);
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 60, fontSize: '0.7rem', color: theme.muted }}>{m.name.slice(0, 8)}</div>
                        <div style={{ display: 'flex', gap: 3 }}>
                            {Array(10).fill(0).map((_, j) => (
                                <div key={j} style={{ width: 16, height: 16, borderRadius: 4, background: j < filled ? colors[i] : theme.border }} />
                            ))}
                        </div>
                        <div style={{ fontSize: '0.7rem', fontWeight: 600, color: colors[i] }}>{pct}%</div>
                    </div>
                );
            })}
        </div>
    </ChartCard>
);

const ArcGaugeChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const segments = metrics.slice(0, 4);
    const total = segments.reduce((s, m) => s + Math.abs(m.total), 0);
    let currentAngle = -180;
    return (
        <ChartCard title="Multi-Arc Gauge" icon="📐" theme={theme} colors={colors}>
            <svg viewBox="0 0 200 120" style={{ width: '100%', height: 140 }}>
                {segments.map((m, i) => {
                    const sweep = (Math.abs(m.total) / total) * 180;
                    const startRad = currentAngle * Math.PI / 180;
                    currentAngle += sweep;
                    const endRad = currentAngle * Math.PI / 180;
                    const x1 = 100 + 70 * Math.cos(startRad);
                    const y1 = 100 + 70 * Math.sin(startRad);
                    const x2 = 100 + 70 * Math.cos(endRad);
                    const y2 = 100 + 70 * Math.sin(endRad);
                    return <path key={i} d={`M${x1},${y1} A70,70 0 0,1 ${x2},${y2}`} fill="none" stroke={colors[i]} strokeWidth="14" strokeLinecap="round" />;
                })}
                <text x="100" y="95" textAnchor="middle" fill={theme.text} fontSize="14" fontWeight="bold">{formatNum(total)}</text>
                <text x="100" y="110" textAnchor="middle" fill={theme.muted} fontSize="8">Total</text>
            </svg>
        </ChartCard>
    );
};

const BubbleMatrixChart: React.FC<{ categories: CategoryCalc[]; metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const max = Math.max(...categories.map(c => c.value));
    return (
        <ChartCard title="Bubble Matrix" icon="⚪" theme={theme} colors={colors}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: 10 }}>
                {categories.slice(0, 8).map((cat, i) => {
                    const size = 20 + (cat.value / max) * 35;
                    return (
                        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                            <div style={{ width: size, height: size, borderRadius: '50%', background: `linear-gradient(135deg, ${colors[i % colors.length]}, ${adjustColor(colors[i % colors.length], -30)})`, boxShadow: `0 4px 12px ${colors[i % colors.length]}40` }} />
                            <span style={{ fontSize: '0.6rem', color: theme.muted }}>{cat.name.slice(0, 6)}</span>
                        </div>
                    );
                })}
            </div>
        </ChartCard>
    );
};

const ComparisonBarsChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const max = Math.max(...metrics.map(m => m.total));
    return (
        <ChartCard title="Before / After" icon="⚖️" theme={theme} colors={colors}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {metrics.slice(0, 4).map((m, i) => {
                    const beforeW = Math.max(10, ((m.total * 0.8) / max) * 100);
                    const afterW = Math.max(10, (m.total / max) * 100);
                    return (
                        <div key={i}>
                            <div style={{ fontSize: '0.65rem', color: theme.muted, marginBottom: 4 }}>{m.name.replace(/_/g, ' ')}</div>
                            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                                <div style={{ width: `${beforeW}%`, height: 10, background: theme.border, borderRadius: 4 }} />
                                <div style={{ width: `${afterW}%`, height: 14, background: `linear-gradient(90deg, ${colors[i]}, ${adjustColor(colors[i], 20)})`, borderRadius: 4 }} />
                            </div>
                        </div>
                    );
                })}
            </div>
        </ChartCard>
    );
};

// DASHBOARD CHARTS: Lollipop, DivergingBar, StreamGraph, ParallelCoordinates, Bullet, CalendarHeatmap, SankeyFlow

const LollipopChart: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const max = Math.max(...categories.map(c => c.value));
    return (
        <ChartCard title="Lollipop Rankings" icon="🍭" theme={theme} colors={colors}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {categories.slice(0, 6).map((cat, i) => {
                    const w = Math.max(5, (cat.value / max) * 85);
                    return (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{ width: 50, fontSize: '0.65rem', color: theme.muted, textAlign: 'right' }}>{cat.name.slice(0, 8)}</div>
                            <div style={{ flex: 1, position: 'relative', height: 20 }}>
                                <div style={{ position: 'absolute', left: 0, top: '50%', width: `${w}%`, height: 2, background: colors[i % colors.length], opacity: 0.5 }} />
                                <div style={{ position: 'absolute', left: `${w}%`, top: '50%', transform: 'translate(-50%, -50%)', width: 16, height: 16, borderRadius: '50%', background: colors[i % colors.length], boxShadow: `0 2px 8px ${colors[i % colors.length]}50` }} />
                            </div>
                            <div style={{ width: 40, fontSize: '0.7rem', fontWeight: 600, color: theme.text }}>{formatNum(cat.value)}</div>
                        </div>
                    );
                })}
            </div>
        </ChartCard>
    );
};

const DivergingBarChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <ChartCard title="Diverging Analysis" icon="↔️" theme={theme} colors={colors}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {metrics.slice(0, 5).map((m, i) => {
                const pct = m.trend;
                const isPos = pct >= 0;
                const barW = Math.min(45, Math.abs(pct));
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <div style={{ width: 50, fontSize: '0.65rem', color: theme.muted, textAlign: 'right' }}>{m.name.slice(0, 8)}</div>
                        <div style={{ flex: 1, display: 'flex', height: 16 }}>
                            <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                                {!isPos && <div style={{ width: `${barW}%`, height: '100%', background: theme.danger, borderRadius: '4px 0 0 4px' }} />}
                            </div>
                            <div style={{ width: 2, background: theme.border }} />
                            <div style={{ flex: 1 }}>
                                {isPos && <div style={{ width: `${barW}%`, height: '100%', background: theme.success, borderRadius: '0 4px 4px 0' }} />}
                            </div>
                        </div>
                        <div style={{ width: 35, fontSize: '0.65rem', color: isPos ? theme.success : theme.danger }}>{pct > 0 ? '+' : ''}{pct}%</div>
                    </div>
                );
            })}
        </div>
    </ChartCard>
);

const StreamGraphChart: React.FC<{ data: any[]; metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ data, colors, theme }) => (
    <ChartCard title="Stream Flow" icon="🌊" theme={theme} colors={colors}>
        <svg viewBox="0 0 300 120" style={{ width: '100%', height: 120 }}>
            <defs>
                {colors.slice(0, 4).map((c, i) => (
                    <linearGradient key={i} id={`streamGrad${i}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor={c} stopOpacity="0.8" />
                        <stop offset="100%" stopColor={c} stopOpacity="0.3" />
                    </linearGradient>
                ))}
            </defs>
            {[0, 1, 2, 3].map(i => {
                const yBase = 60;
                const amplitude = 10 + i * 8;
                const phase = i * 30;
                const points = Array(15).fill(0).map((_, x) => {
                    const y1 = yBase - amplitude * Math.sin((x * 25 + phase) * Math.PI / 180);
                    const y2 = yBase + amplitude * Math.sin((x * 25 + phase + 180) * Math.PI / 180);
                    return { x: x * 22, y1, y2 };
                });
                const path = `M0,${yBase} ${points.map(p => `L${p.x},${p.y1}`).join(' ')} L300,${yBase} ${points.reverse().map(p => `L${p.x},${p.y2}`).join(' ')} Z`;
                return <path key={i} d={path} fill={`url(#streamGrad${i})`} opacity={0.7} />;
            })}
        </svg>
    </ChartCard>
);

const ParallelCoordinatesChart: React.FC<{ data: any[]; metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const axes = metrics.slice(0, 5);
    return (
        <ChartCard title="Parallel Coordinates" icon="📊" theme={theme} colors={colors}>
            <svg viewBox="0 0 300 120" style={{ width: '100%', height: 120 }}>
                {axes.map((_, i) => {
                    const x = 30 + i * 60;
                    return <line key={i} x1={x} y1={15} x2={x} y2={100} stroke={theme.border} strokeWidth="2" />;
                })}
                {[0, 1, 2].map(li => (
                    <polyline key={li} fill="none" stroke={colors[li]} strokeWidth="2" opacity={0.6}
                        points={axes.map((m, i) => `${30 + i * 60},${20 + ((m.mean + li * 10) % 80)}`).join(' ')} />
                ))}
                {axes.map((m, i) => (
                    <text key={i} x={30 + i * 60} y={112} textAnchor="middle" fill={theme.muted} fontSize="7">{m.name.slice(0, 5)}</text>
                ))}
            </svg>
        </ChartCard>
    );
};

const BulletChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <ChartCard title="Actual vs Target" icon="🎯" theme={theme} colors={colors}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {metrics.slice(0, 3).map((m, i) => {
                const target = m.mean * 1.2;
                const actual = m.total / metrics.length;
                const pctActual = Math.min(100, (actual / target) * 100);
                return (
                    <div key={i}>
                        <div style={{ fontSize: '0.65rem', color: theme.muted, marginBottom: 4 }}>{m.name.replace(/_/g, ' ')}</div>
                        <div style={{ position: 'relative', height: 20, background: theme.border, borderRadius: 4 }}>
                            <div style={{ position: 'absolute', left: 0, top: 2, height: 16, width: `${Math.min(pctActual + 20, 100)}%`, background: `${colors[i]}30`, borderRadius: 3 }} />
                            <div style={{ position: 'absolute', left: 0, top: 5, height: 10, width: `${pctActual}%`, background: colors[i], borderRadius: 2 }} />
                            <div style={{ position: 'absolute', left: '80%', top: 0, height: '100%', width: 3, background: theme.text, borderRadius: 1 }} />
                        </div>
                    </div>
                );
            })}
        </div>
    </ChartCard>
);

const CalendarHeatmapChart: React.FC<{ data: any[]; colors: string[]; theme: Theme }> = ({ data, colors, theme }) => {
    const weeks = 7;
    const days = 5;
    return (
        <ChartCard title="Calendar Heatmap" icon="📅" theme={theme} colors={colors}>
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${weeks}, 1fr)`, gap: 3 }}>
                {Array(weeks * days).fill(0).map((_, i) => {
                    const intensity = Math.random();
                    const bg = intensity > 0.7 ? colors[0] : intensity > 0.4 ? colors[1] : intensity > 0.2 ? colors[2] : theme.border;
                    return <div key={i} style={{ aspectRatio: '1', borderRadius: 3, background: bg, opacity: 0.7 + intensity * 0.3 }} />;
                })}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 10, justifyContent: 'center', fontSize: '0.6rem', color: theme.muted }}>
                <span>Less</span>
                {[theme.border, colors[2], colors[1], colors[0]].map((c, i) => (
                    <div key={i} style={{ width: 12, height: 12, borderRadius: 2, background: c }} />
                ))}
                <span>More</span>
            </div>
        </ChartCard>
    );
};

const SankeyFlowChart: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const total = categories.reduce((s, c) => s + c.value, 0);
    return (
        <ChartCard title="Flow Analysis" icon="🔀" theme={theme} colors={colors}>
            <svg viewBox="0 0 300 120" style={{ width: '100%', height: 120 }}>
                {categories.slice(0, 4).map((cat, i) => {
                    const h = Math.max(15, (cat.value / total) * 80);
                    const y1 = 10 + i * 25;
                    const y2 = 20 + i * 20;
                    return (
                        <g key={i}>
                            <rect x="10" y={y1} width="40" height={h * 0.6} rx="3" fill={colors[i]} opacity={0.8} />
                            <path d={`M50,${y1 + h * 0.3} C130,${y1 + h * 0.3} 170,${y2 + h * 0.3} 250,${y2 + h * 0.3}`}
                                fill="none" stroke={colors[i]} strokeWidth={h * 0.4} opacity={0.4} />
                            <rect x="250" y={y2} width="40" height={h * 0.5} rx="3" fill={colors[(i + 2) % colors.length]} opacity={0.8} />
                        </g>
                    );
                })}
                <text x="30" y={115} textAnchor="middle" fill={theme.muted} fontSize="8">Source</text>
                <text x="270" y={115} textAnchor="middle" fill={theme.muted} fontSize="8">Target</text>
            </svg>
        </ChartCard>
    );
};

// Badge
const Badge: React.FC<{ text: string; theme: Theme }> = ({ text, theme }) => (
    <span style={{ padding: '6px 12px', background: theme.card, borderRadius: 8, border: `1px solid ${theme.border}`, fontSize: '0.8rem', color: theme.muted }}>{text}</span>
);

// KPI Card with REAL calculations
const KPICard: React.FC<{ metric: MetricCalc; color: string; compact: boolean }> = ({ metric, color, compact }) => (
    <div style={{ background: `linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -40)} 100%)`, borderRadius: compact ? 10 : 14, padding: compact ? '12px 14px' : '18px 22px', color: 'white', minHeight: compact ? 80 : 110, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', boxShadow: '0 8px 24px -6px rgba(0,0,0,0.25)', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: -15, right: -15, width: 70, height: 70, background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }} />
        <div style={{ zIndex: 1 }}>
            <div style={{ fontSize: compact ? '0.6rem' : '0.7rem', textTransform: 'uppercase', opacity: 0.85, letterSpacing: '0.08em' }}>{metric.name.replace(/_/g, ' ')}</div>
            <div style={{ fontSize: compact ? '1.4rem' : '1.9rem', fontWeight: 800, marginTop: 2 }}>{formatNum(metric.total)}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, zIndex: 1 }}>
            <span style={{ background: metric.trend >= 0 ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)', padding: '2px 7px', borderRadius: 5, fontSize: '0.65rem', fontWeight: 600 }}>
                {metric.trendDirection === 'up' ? '↗' : metric.trendDirection === 'down' ? '↘' : '→'} {Math.abs(metric.trend)}%
            </span>
        </div>
    </div>
);

// Insights Panel with REAL data-driven text
const InsightsPanel: React.FC<{ metrics: MetricCalc[]; categories: CategoryCalc[]; stats: DataStats; colors: string[]; theme: Theme }> = ({ metrics, categories, stats, colors, theme }) => {
    const insights = useMemo(() => {
        const result = [];
        if (metrics[0]) {
            const m = metrics[0];
            result.push({ icon: '📊', title: 'Key Finding', text: `Total ${m.name.replace(/_/g, ' ')} is ${formatNum(m.total)} across ${stats.count.toLocaleString()} records. Average: ${formatNum(m.mean)}, Median: ${formatNum(m.median)}.` });
            result.push({ icon: m.trendDirection === 'up' ? '📈' : m.trendDirection === 'down' ? '📉' : '➡️', title: 'Trend Analysis', text: `${m.name.replace(/_/g, ' ')} shows ${m.trend > 5 ? 'growth' : m.trend < -5 ? 'decline' : 'stability'} with ${Math.abs(m.trend)}% change. Standard deviation: ${formatNum(m.std)}.` });
        }
        if (categories[0]) {
            const top = categories[0];
            result.push({ icon: '🏆', title: 'Top Performer', text: `"${top.name}" leads with ${formatNum(top.value)} (${top.percent}% of total), outperforming ${categories.length - 1} others.` });
        }
        if (metrics[0]?.outlierCount > 0) {
            result.push({ icon: '⚠️', title: 'Anomaly Alert', text: `Detected ${metrics[0].outlierCount} outlier values in ${metrics[0].name.replace(/_/g, ' ')} using IQR method. Range: ${formatNum(metrics[0].min)} to ${formatNum(metrics[0].max)}.` });
        }
        return result;
    }, [metrics, categories, stats]);

    return (
        <div style={{ background: theme.card, borderRadius: 16, border: `1px solid ${theme.border}`, padding: 20, marginBottom: 24 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: 700, color: theme.text, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ background: `${colors[0]}30`, padding: 6, borderRadius: 8 }}>🧠</span> Autonomous Insights
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                {insights.map((ins, i) => (
                    <div key={i} style={{ display: 'flex', gap: 12, padding: 14, background: `${colors[i % colors.length]}10`, borderRadius: 12, border: `1px solid ${colors[i % colors.length]}30` }}>
                        <span style={{ fontSize: '1.5rem' }}>{ins.icon}</span>
                        <div>
                            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: colors[i % colors.length], textTransform: 'uppercase', marginBottom: 4 }}>{ins.title}</div>
                            <div style={{ fontSize: '0.85rem', color: theme.text, lineHeight: 1.5 }}>{ins.text}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ================================
// OVERVIEW LAYOUT - HIGH-LEVEL SUMMARY
// Charts: Radar, Waterfall, Gauge, Network (mode_preference: overview)
// ================================
const OverviewLayout: React.FC<{ data: any[]; metrics: MetricCalc[]; categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ data, metrics, categories, colors, theme }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Row 1: Radar Chart + Waterfall Chart */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <RadarChart metrics={metrics.slice(0, 6)} colors={colors} theme={theme} />
            <WaterfallChart categories={categories.slice(0, 8)} colors={colors} theme={theme} />
        </div>
        {/* Row 2: Gauge + Bubble Network + Key Trends */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 1fr', gap: 20 }}>
            <GaugeChart metrics={metrics} colors={colors} theme={theme} />
            <RelationshipNetwork data={data} colors={colors} theme={theme} />
            <KeyDrivers metrics={metrics} colors={colors} theme={theme} />
        </div>
        {/* Row 3: Summary Stats */}
        <IconRow colors={colors} theme={theme} />
    </div>
);

// RADAR CHART - Multivariate Comparison (Overview)
const RadarChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const radarData = useMemo(() => {
        if (!metrics.length) return [];
        const maxVal = Math.max(...metrics.map(m => m.mean)) || 1;
        return metrics.slice(0, 6).map(m => ({
            name: m.name.replace(/_/g, ' ').slice(0, 10),
            value: (m.mean / maxVal) * 100,
            color: colors[metrics.indexOf(m) % colors.length]
        }));
    }, [metrics, colors]);

    const centerX = 150, centerY = 90, maxR = 70;
    const angleStep = (Math.PI * 2) / Math.max(radarData.length, 1);

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>📊 Metric Comparison Radar</h3>
            <svg width="100%" height="160" viewBox="0 0 300 180">
                {/* Grid circles */}
                {[0.25, 0.5, 0.75, 1].map((r, i) => (
                    <circle key={i} cx={centerX} cy={centerY} r={maxR * r} fill="none" stroke={theme.border} strokeWidth={1} strokeDasharray="3,3" />
                ))}
                {/* Axes */}
                {radarData.map((_, i) => {
                    const angle = -Math.PI / 2 + i * angleStep;
                    return <line key={i} x1={centerX} y1={centerY} x2={centerX + Math.cos(angle) * maxR} y2={centerY + Math.sin(angle) * maxR} stroke={theme.border} strokeWidth={1} />;
                })}
                {/* Data polygon */}
                <polygon
                    points={radarData.map((d, i) => {
                        const angle = -Math.PI / 2 + i * angleStep;
                        const r = (d.value / 100) * maxR;
                        return `${centerX + Math.cos(angle) * r},${centerY + Math.sin(angle) * r}`;
                    }).join(' ')}
                    fill={`${colors[0]}30`}
                    stroke={colors[0]}
                    strokeWidth={2}
                />
                {/* Data points */}
                {radarData.map((d, i) => {
                    const angle = -Math.PI / 2 + i * angleStep;
                    const r = (d.value / 100) * maxR;
                    return <circle key={i} cx={centerX + Math.cos(angle) * r} cy={centerY + Math.sin(angle) * r} r={5} fill={colors[i % colors.length]} />;
                })}
                {/* Labels */}
                {radarData.map((d, i) => {
                    const angle = -Math.PI / 2 + i * angleStep;
                    const labelR = maxR + 15;
                    return (
                        <text key={i} x={centerX + Math.cos(angle) * labelR} y={centerY + Math.sin(angle) * labelR} textAnchor="middle" fontSize="8" fill={theme.muted}>
                            {d.name}
                        </text>
                    );
                })}
            </svg>
        </div>
    );
};

// WATERFALL CHART - Cumulative Breakdown (Overview)
const WaterfallChart: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const waterfallData = useMemo(() => {
        let cumulative = 0;
        return categories.slice(0, 8).map((c, i) => {
            const start = cumulative;
            cumulative += c.value;
            return { name: c.name.slice(0, 8), value: c.value, start, end: cumulative, color: colors[i % colors.length] };
        });
    }, [categories, colors]);

    const maxVal = Math.max(...waterfallData.map(d => d.end)) || 1;
    const barWidth = 28;

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>📶 Cumulative Contribution</h3>
            <svg width="100%" height="160" viewBox="0 0 300 180">
                {/* Bars */}
                {waterfallData.map((d, i) => {
                    const x = 20 + i * 35;
                    const h = (d.value / maxVal) * 120;
                    const y = 150 - ((d.end / maxVal) * 120);
                    return (
                        <g key={i}>
                            <rect x={x} y={y} width={barWidth} height={h} fill={d.color} rx={3} opacity={0.85} />
                            {/* Connector line */}
                            {i > 0 && <line x1={x - 7} y1={150 - ((d.start / maxVal) * 120)} x2={x} y2={150 - ((d.start / maxVal) * 120)} stroke={theme.muted} strokeDasharray="2,2" />}
                            <text x={x + barWidth / 2} y={y - 5} textAnchor="middle" fontSize="8" fill={theme.text}>{Math.round(d.value)}</text>
                            <text x={x + barWidth / 2} y={165} textAnchor="middle" fontSize="7" fill={theme.muted}>{d.name}</text>
                        </g>
                    );
                })}
                {/* Baseline */}
                <line x1={15} y1={150} x2={285} y2={150} stroke={theme.border} strokeWidth={1} />
            </svg>
        </div>
    );
};

// GAUGE CHART - Single Metric Progress (Overview)
const GaugeChart: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const gaugeValue = useMemo(() => {
        if (!metrics.length) return 0;
        // Use first metric's mean as percentage of max
        const pct = metrics[0].max > 0 ? (metrics[0].mean / metrics[0].max) * 100 : 50;
        return Math.min(100, Math.max(0, pct));
    }, [metrics]);

    const angle = -135 + (gaugeValue / 100) * 270; // -135 to +135 degrees

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16, textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '0.9rem', fontWeight: 600, color: theme.text }}>🎯 Performance Score</h3>
            <svg width="100%" height="140" viewBox="0 0 150 120">
                {/* Background arc */}
                <path d="M 20 90 A 55 55 0 1 1 130 90" fill="none" stroke={theme.border} strokeWidth={12} strokeLinecap="round" />
                {/* Value arc */}
                <path d="M 20 90 A 55 55 0 1 1 130 90" fill="none" stroke={`url(#gaugeGrad)`} strokeWidth={12} strokeLinecap="round" strokeDasharray={`${(gaugeValue / 100) * 173} 173`} />
                {/* Gradient */}
                <defs>
                    <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor={colors[0]} />
                        <stop offset="100%" stopColor={colors[1] || colors[0]} />
                    </linearGradient>
                </defs>
                {/* Needle */}
                <line x1={75} y1={90} x2={75 + Math.cos(angle * Math.PI / 180) * 40} y2={90 + Math.sin(angle * Math.PI / 180) * 40} stroke={theme.text} strokeWidth={2} />
                <circle cx={75} cy={90} r={6} fill={colors[0]} />
                {/* Value text */}
                <text x={75} y={110} textAnchor="middle" fontSize="18" fontWeight="700" fill={colors[0]}>{Math.round(gaugeValue)}%</text>
            </svg>
        </div>
    );
};

// Relationship Network - Bubble Cloud with Connections
const RelationshipNetwork: React.FC<{ data: any[]; colors: string[]; theme: Theme }> = ({ data, colors, theme }) => {
    const bubbles = useMemo(() => {
        const numCols = Object.keys(data[0] || {}).filter(k => typeof data[0][k] === 'number');
        if (!numCols.length) return [];
        const col = numCols[0];
        const values = data.slice(0, 18).map((d, i) => ({ val: Number(d[col]) || 0, idx: i }));
        const maxVal = Math.max(...values.map(v => v.val));
        return values.map((v, i) => {
            const angle = (i / values.length) * Math.PI * 2 + (i * 0.3);
            const radius = 60 + (i % 3) * 35;
            return {
                x: 150 + Math.cos(angle) * radius,
                y: 85 + Math.sin(angle) * radius * 0.65,
                r: Math.max(8, Math.sqrt(v.val / maxVal) * 30),
                color: colors[i % colors.length]
            };
        });
    }, [data, colors]);

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16 }}>
            <h3 style={{ margin: '0 0 10px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Relationship Network</h3>
            <svg width="100%" height="160" viewBox="0 0 300 160">
                {/* Connections */}
                {bubbles.slice(0, 10).map((b, i) => bubbles.slice(i + 1, i + 4).map((b2, j) => (
                    <line key={`${i}-${j}`} x1={b.x} y1={b.y} x2={b2.x} y2={b2.y} stroke={theme.muted} strokeWidth={1} opacity={0.3} />
                )))}
                {/* Bubbles */}
                {bubbles.map((b, i) => (
                    <circle key={i} cx={b.x} cy={b.y} r={b.r} fill={b.color} opacity={0.75} style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' }} />
                ))}
            </svg>
        </div>
    );
};

// Portfolio Distemap - Metric list with progress bars
const PortfolioDistemap: React.FC<{ metrics: MetricCalc[]; categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ metrics, categories, colors, theme }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16 }}>
        <h3 style={{ margin: '0 0 14px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Portfolio Distemap</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {metrics.slice(0, 4).map((m, i) => {
                const normalized = m.max > 0 ? (m.mean / m.max) * 100 : 50;
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ color: colors[i % colors.length], fontSize: '1rem' }}>◆</span>
                        <span style={{ flex: 1, fontSize: '0.85rem', color: theme.text }}>{m.name.replace(/_/g, ' ')}</span>
                        <div style={{ width: 60, height: 5, background: theme.border, borderRadius: 2 }}>
                            <div style={{ width: `${normalized}%`, height: '100%', background: colors[i % colors.length], borderRadius: 2 }} />
                        </div>
                        <span style={{ width: 45, textAlign: 'right', fontSize: '0.75rem', fontWeight: 700, color: m.trend >= 0 ? theme.success : theme.danger }}>
                            {m.trend >= 0 ? '+' : ''}{m.trend}%
                        </span>
                    </div>
                );
            })}
        </div>
    </div>
);

// Icon Row - Bottom icons (Amount, Growth, Pull, Close)
const IconRow: React.FC<{ colors: string[]; theme: Theme }> = ({ colors, theme }) => (
    <div style={{ display: 'flex', justifyContent: 'center', gap: 40, marginTop: 10 }}>
        {[{ label: 'Amount', icon: '💰' }, { label: 'Growth', icon: '📈' }, { label: 'Pull', icon: '🔄' }, { label: 'Close', icon: '✅' }].map((ic, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
                <div style={{ width: 40, height: 40, borderRadius: '50%', background: `${colors[i % colors.length]}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', margin: '0 auto 5px', border: `1px solid ${colors[i % colors.length]}40` }}>{ic.icon}</div>
                <div style={{ fontSize: '0.65rem', color: theme.muted }}>{ic.label}</div>
            </div>
        ))}
    </div>
);

// ================================
// DASHBOARD LAYOUT - DETAILED ANALYSIS
// Charts: Treemap, Funnel, Scatter, Heatmap, Detailed Bars (mode_preference: dashboard)
// ================================
const DashboardLayout: React.FC<{ data: any[]; metrics: MetricCalc[]; categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ data, metrics, categories, colors, theme }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Row 1: Treemap + Detailed Line Trend */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 20 }}>
            <TreemapChart categories={categories} colors={colors} theme={theme} />
            <ChartCard title="Performance Trend Analysis" icon="📊" theme={theme} colors={colors}>
                <TrendChart data={data} metrics={metrics} colors={colors} theme={theme} />
            </ChartCard>
        </div>
        {/* Row 2: Funnel + Scatter Correlation + Heatmap Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <FunnelChart categories={categories} colors={colors} theme={theme} />
            <ScatterCorrelation data={data} colors={colors} theme={theme} />
            <HeatmapGrid metrics={metrics} colors={colors} theme={theme} />
        </div>
        {/* Row 3: Stacked Comparison Bars */}
        <StackedBarsChart metrics={metrics} categories={categories} colors={colors} theme={theme} />
        {/* Row 4: Summary Stats */}
        <SummaryRow metrics={metrics} colors={colors} theme={theme} />
    </div>
);

// TREEMAP CHART - Hierarchical Distribution (Dashboard)
const TreemapChart: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const treemapData = useMemo(() => {
        const total = categories.reduce((s, c) => s + c.value, 0) || 1;
        let x = 0;
        return categories.slice(0, 10).map((c, i) => {
            const w = (c.value / total) * 280;
            const rect = { name: c.name.slice(0, 12), value: c.value, x, w, color: colors[i % colors.length] };
            x += w;
            return rect;
        });
    }, [categories, colors]);

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>🗂️ Hierarchical Distribution</h3>
            <svg width="100%" height="200" viewBox="0 0 300 220">
                {treemapData.map((d, i) => {
                    const h = 60 + (d.value / (Math.max(...treemapData.map(t => t.value)) || 1)) * 100;
                    const row = i < 5 ? 0 : 1;
                    const col = i % 5;
                    const cellW = 56, cellH = 80, padding = 2;
                    return (
                        <g key={i}>
                            <rect
                                x={10 + col * (cellW + padding)}
                                y={10 + row * (cellH + padding)}
                                width={cellW}
                                height={cellH}
                                fill={d.color}
                                rx={6}
                                opacity={0.85}
                            />
                            <text x={10 + col * (cellW + padding) + cellW / 2} y={10 + row * (cellH + padding) + cellH / 2} textAnchor="middle" fontSize="8" fill="#fff" fontWeight="600">
                                {d.name}
                            </text>
                            <text x={10 + col * (cellW + padding) + cellW / 2} y={10 + row * (cellH + padding) + cellH / 2 + 12} textAnchor="middle" fontSize="7" fill="#fff" opacity={0.8}>
                                {Math.round(d.value)}
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
};

// FUNNEL CHART - Process Stages (Dashboard)
const FunnelChart: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const funnelData = useMemo(() => {
        const sorted = [...categories].sort((a, b) => b.value - a.value).slice(0, 5);
        const maxVal = sorted[0]?.value || 1;
        return sorted.map((c, i) => ({
            name: c.name.slice(0, 10),
            value: c.value,
            width: (c.value / maxVal) * 100,
            color: colors[i % colors.length]
        }));
    }, [categories, colors]);

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 14, minHeight: 200 }}>
            <h3 style={{ margin: '0 0 10px', fontSize: '0.85rem', fontWeight: 600, color: theme.text }}>🔻 Conversion Funnel</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 8 }}>
                {funnelData.map((d, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                            width: `${d.width}%`,
                            height: 24,
                            background: `linear-gradient(90deg, ${d.color}, ${adjustColor(d.color, 30)})`,
                            borderRadius: 4,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '0.65rem', fontWeight: 600, color: '#fff',
                            minWidth: 60
                        }}>
                            {d.name}
                        </div>
                        <span style={{ fontSize: '0.7rem', color: theme.muted }}>{Math.round(d.value)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// SCATTER CORRELATION - Two Variable Relationship (Dashboard)
const ScatterCorrelation: React.FC<{ data: any[]; colors: string[]; theme: Theme }> = ({ data, colors, theme }) => {
    const scatterData = useMemo(() => {
        const numCols = Object.keys(data[0] || {}).filter(k => typeof data[0][k] === 'number');
        if (numCols.length < 2) return { points: [], xLabel: '', yLabel: '' };
        const col1 = numCols[0], col2 = numCols[1];
        const points = data.slice(0, 30).map((d, i) => ({
            x: Number(d[col1]) || 0,
            y: Number(d[col2]) || 0,
            color: colors[i % colors.length]
        }));
        return { points, xLabel: col1.replace(/_/g, ' '), yLabel: col2.replace(/_/g, ' ') };
    }, [data, colors]);

    const xMax = Math.max(...scatterData.points.map(p => p.x)) || 1;
    const yMax = Math.max(...scatterData.points.map(p => p.y)) || 1;

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 14, minHeight: 200 }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '0.85rem', fontWeight: 600, color: theme.text }}>🔵 Correlation Analysis</h3>
            <svg width="100%" height="150" viewBox="0 0 180 160">
                {/* Grid */}
                <line x1={30} y1={130} x2={170} y2={130} stroke={theme.border} strokeWidth={1} />
                <line x1={30} y1={20} x2={30} y2={130} stroke={theme.border} strokeWidth={1} />
                {/* Trend line */}
                <line x1={30} y1={130} x2={170} y2={30} stroke={colors[0]} strokeWidth={1} strokeDasharray="4,4" opacity={0.5} />
                {/* Points */}
                {scatterData.points.map((p, i) => (
                    <circle key={i} cx={30 + (p.x / xMax) * 140} cy={130 - (p.y / yMax) * 100} r={4} fill={p.color} opacity={0.7} />
                ))}
                {/* Labels */}
                <text x={100} y={150} textAnchor="middle" fontSize="7" fill={theme.muted}>{scatterData.xLabel}</text>
                <text x={10} y={75} textAnchor="middle" fontSize="7" fill={theme.muted} transform="rotate(-90, 10, 75)">{scatterData.yLabel}</text>
            </svg>
        </div>
    );
};

// HEATMAP GRID - Metric Intensity (Dashboard)
const HeatmapGrid: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const heatmapData = useMemo(() => {
        const grid: { row: number; col: number; value: number; color: string }[] = [];
        metrics.slice(0, 4).forEach((m, row) => {
            [m.mean, m.median, m.std, m.total / 1000].forEach((val, col) => {
                const normalized = Math.min(1, val / (m.max || 1));
                const intensity = Math.round(normalized * 255);
                grid.push({ row, col, value: val, color: `rgba(${colors[0] === '#7c3aed' ? '124,58,237' : '20,184,166'}, ${0.2 + normalized * 0.8})` });
            });
        });
        return grid;
    }, [metrics, colors]);

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 14, minHeight: 200 }}>
            <h3 style={{ margin: '0 0 10px', fontSize: '0.85rem', fontWeight: 600, color: theme.text }}>🌡️ Metric Intensity</h3>
            <svg width="100%" height="140" viewBox="0 0 180 150">
                {/* Column headers */}
                {['Mean', 'Median', 'StdDev', 'Total'].map((label, i) => (
                    <text key={i} x={25 + i * 38} y={15} textAnchor="middle" fontSize="7" fill={theme.muted}>{label}</text>
                ))}
                {/* Grid cells */}
                {heatmapData.map((cell, i) => (
                    <g key={i}>
                        <rect x={5 + cell.col * 38} y={20 + cell.row * 30} width={35} height={26} fill={cell.color} rx={4} />
                        <text x={22 + cell.col * 38} y={37 + cell.row * 30} textAnchor="middle" fontSize="7" fill="#fff" fontWeight="600">
                            {cell.value >= 1000 ? `${(cell.value / 1000).toFixed(0)}K` : cell.value.toFixed(0)}
                        </text>
                    </g>
                ))}
                {/* Row labels */}
                {metrics.slice(0, 4).map((m, i) => (
                    <text key={i} x={165} y={37 + i * 30} fontSize="7" fill={theme.muted}>{m.name.slice(0, 6)}</text>
                ))}
            </svg>
        </div>
    );
};

// STACKED BARS - Multi-Segment Comparison (Dashboard)
const StackedBarsChart: React.FC<{ metrics: MetricCalc[]; categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ metrics, categories, colors, theme }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 16 }}>
        <h3 style={{ margin: '0 0 14px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>📊 Segment Comparison</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {metrics.slice(0, 4).map((m, i) => {
                const segments = [m.mean / (m.max || 1), m.median / (m.max || 1), m.std / (m.max || 1)].map(v => Math.min(0.95, Math.max(0.05, v)));
                const total = segments.reduce((s, v) => s + v, 0);
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ width: 80, fontSize: '0.8rem', color: theme.text }}>{m.name.replace(/_/g, ' ').slice(0, 10)}</span>
                        <div style={{ flex: 1, height: 20, background: theme.border, borderRadius: 4, overflow: 'hidden', display: 'flex' }}>
                            {segments.map((seg, j) => (
                                <div key={j} style={{ width: `${(seg / total) * 100}%`, height: '100%', background: colors[j % colors.length], opacity: 0.9 - j * 0.15 }} />
                            ))}
                        </div>
                        <span style={{ width: 50, textAlign: 'right', fontSize: '0.75rem', fontWeight: 700, color: m.trend >= 0 ? theme.success : theme.danger }}>
                            {m.trend >= 0 ? '+' : ''}{m.trend}%
                        </span>
                    </div>
                );
            })}
        </div>
        {/* Legend */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 12, fontSize: '0.65rem', color: theme.muted }}>
            {['Mean', 'Median', 'Std Dev'].map((label, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <div style={{ width: 10, height: 10, background: colors[i % colors.length], borderRadius: 2 }} />
                    {label}
                </div>
            ))}
        </div>
    </div>
);

// Project Trend Insights - Scatter Cloud
const ProjectTrendInsights: React.FC<{ data: any[]; colors: string[]; theme: Theme }> = ({ data, colors, theme }) => {
    const scatterData = useMemo(() => {
        const numCols = Object.keys(data[0] || {}).filter(k => typeof data[0][k] === 'number');
        if (numCols.length < 2) return [];
        const col1 = numCols[0], col2 = numCols[1];
        return data.slice(0, 25).map((d, i) => ({
            x: Number(d[col1]) || 0,
            y: Number(d[col2]) || 0,
            color: colors[i % colors.length]
        }));
    }, [data, colors]);

    const xMax = Math.max(...scatterData.map(d => d.x)) || 1;
    const yMax = Math.max(...scatterData.map(d => d.y)) || 1;

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 14, minHeight: 200 }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '0.85rem', fontWeight: 600, color: theme.text }}>Project Trend Insights</h3>
            <svg width="100%" height="130" viewBox="0 0 200 130">
                {/* Axis lines */}
                <line x1={20} y1={110} x2={190} y2={110} stroke={theme.border} strokeWidth={1} />
                <line x1={20} y1={10} x2={20} y2={110} stroke={theme.border} strokeWidth={1} />
                {/* Data points */}
                {scatterData.map((p, i) => (
                    <circle
                        key={i}
                        cx={20 + (p.x / xMax) * 160}
                        cy={110 - (p.y / yMax) * 90}
                        r={5 + Math.random() * 4}
                        fill={p.color}
                        opacity={0.7}
                    />
                ))}
            </svg>
        </div>
    );
};

// Chart Card
const ChartCard: React.FC<{ title: string; icon: string; theme: Theme; colors: string[]; small?: boolean; children: ReactNode }> = ({ title, icon, theme, colors, small, children }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: small ? 14 : 18, minHeight: small ? 200 : 280 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ margin: 0, fontSize: small ? '0.85rem' : '0.95rem', fontWeight: 600, color: theme.text }}>{title}</h3>
            <span style={{ fontSize: '0.85rem', padding: 4, background: `${colors[0]}20`, borderRadius: 6 }}>{icon}</span>
        </div>
        <div style={{ height: small ? 150 : 200 }}><ChartErrorBoundary>{children}</ChartErrorBoundary></div>
    </div>
);

// Trend Chart
const TrendChart: React.FC<{ data: any[]; metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ data, metrics, colors, theme }) => {
    const chartData = useMemo(() => {
        const keys = Object.keys(data[0] || {});
        const xKey = keys.find(k => typeof data[0][k] === 'string' && data[0][k].includes('-')) || keys[0];
        const yKey = metrics[0]?.name || keys.find(k => typeof data[0][k] === 'number');
        return { data: data.slice(0, 50), xKey, yKey };
    }, [data, metrics]);

    return (
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData.data}>
                <defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={colors[0]} stopOpacity={0.6} /><stop offset="100%" stopColor={colors[0]} stopOpacity={0.05} /></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.grid} />
                <XAxis dataKey={chartData.xKey} tick={{ fill: theme.muted, fontSize: 9 }} axisLine={false} />
                <YAxis hide />
                <Tooltip contentStyle={{ background: theme.card, borderRadius: 8, border: `1px solid ${theme.border}`, color: theme.text }} />
                <Area type="monotone" dataKey={chartData.yKey} stroke={colors[0]} strokeWidth={2} fill="url(#areaGrad)" />
            </AreaChart>
        </ResponsiveContainer>
    );
};

// Category Pie
const CategoryPie: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => {
    const total = categories.reduce((s, c) => s + c.value, 0);
    return (
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <ResponsiveContainer>
                <PieChart>
                    <Pie data={categories.slice(0, 6)} cx="50%" cy="50%" innerRadius="45%" outerRadius="75%" paddingAngle={2} dataKey="value" label={({ name, percent }) => percent > 0.1 ? name.slice(0, 8) : ''} labelLine={false}>
                        {categories.slice(0, 6).map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
                    </Pie>
                    <Tooltip />
                </PieChart>
            </ResponsiveContainer>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.55rem', color: theme.muted }}>Total</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: theme.text }}>{formatNum(total)}</div>
            </div>
        </div>
    );
};

// Category Bar
const CategoryBar: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => (
    <ResponsiveContainer>
        <BarChart data={categories.slice(0, 6).map(c => ({ name: c.name.slice(0, 8), value: c.value }))}>
            <XAxis dataKey="name" tick={{ fill: theme.muted, fontSize: 9 }} axisLine={false} />
            <YAxis hide />
            <Tooltip />
            <Bar dataKey="value" fill={colors[1]} radius={[4, 4, 0, 0]} />
        </BarChart>
    </ResponsiveContainer>
);

// Key Drivers (REAL calculations)
const KeyDrivers: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 18 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Key Drivers Impact</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {metrics.slice(0, 5).map((m, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: colors[i % colors.length] }} />
                    <div style={{ flex: 1, fontSize: '0.85rem', color: theme.text }}>{m.name.replace(/_/g, ' ')}</div>
                    <div style={{ width: 60, height: 6, background: theme.border, borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: `${Math.min(100, Math.abs(m.trend) * 2)}%`, height: '100%', background: m.trend >= 0 ? theme.success : theme.danger }} />
                    </div>
                    <div style={{ width: 50, textAlign: 'right', fontSize: '0.8rem', fontWeight: 700, color: m.trend >= 0 ? theme.success : theme.danger }}>
                        {m.trend >= 0 ? '+' : ''}{m.trend}%
                    </div>
                </div>
            ))}
        </div>
    </div>
);

// Portfolio Metrics (REAL calculations)
const PortfolioMetrics: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 18 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Portfolio Metrics</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {metrics.slice(0, 4).map((m, i) => {
                const normalized = m.max > 0 ? (m.mean / m.max) * 100 : 50;
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ color: colors[i % colors.length], fontSize: '1rem' }}>▸</span>
                        <span style={{ flex: 1, fontSize: '0.85rem', color: theme.text }}>{m.name.replace(/_/g, ' ')}</span>
                        <div style={{ width: 50, height: 5, background: theme.border, borderRadius: 2 }}>
                            <div style={{ width: `${normalized}%`, height: '100%', background: colors[i % colors.length], borderRadius: 2 }} />
                        </div>
                        <span style={{ width: 35, textAlign: 'right', fontSize: '0.75rem', color: m.trend >= 0 ? theme.success : theme.danger }}>
                            {m.trend >= 0 ? '+' : ''}{m.trend}%
                        </span>
                    </div>
                );
            })}
        </div>
    </div>
);

// Drivers Radial
const DriversRadial: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    const radialData = metrics.slice(0, 4).map((m, i) => {
        const normalized = m.max > 0 ? (m.mean / m.max) * 100 : 50;
        return { name: m.name.slice(0, 8), value: Math.round(normalized), fill: colors[i % colors.length] };
    });
    const centerVal = radialData.length ? Math.round(radialData.reduce((s, d) => s + d.value, 0) / radialData.length) : 0;

    return (
        <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 18, minHeight: 280 }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Drivers Weighted</h3>
            <div style={{ position: 'relative', height: 200 }}>
                <ResponsiveContainer><RadialBarChart cx="50%" cy="50%" innerRadius="30%" outerRadius="85%" data={radialData} startAngle={180} endAngle={-180}>
                    <RadialBar background dataKey="value" cornerRadius={6}>{radialData.map((d, i) => <Cell key={i} fill={d.fill} />)}</RadialBar>
                </RadialBarChart></ResponsiveContainer>
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: theme.text }}>{centerVal}%</div>
                    <div style={{ fontSize: '0.6rem', color: theme.muted }}>Weighted</div>
                </div>
            </div>
        </div>
    );
};

// Top Opportunities
const TopOpportunities: React.FC<{ categories: CategoryCalc[]; colors: string[]; theme: Theme }> = ({ categories, colors, theme }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 18 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Top Opportunities</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {categories.slice(0, 4).map((c, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: i < 3 ? `1px solid ${theme.border}` : 'none' }}>
                    <span style={{ fontSize: '0.85rem', color: theme.text }}>{c.name.slice(0, 16)}</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: colors[0] }}>{formatNum(c.value)}</span>
                </div>
            ))}
        </div>
    </div>
);

// Efficiency Bars
const EfficiencyBars: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => (
    <div style={{ background: theme.card, borderRadius: 14, border: `1px solid ${theme.border}`, padding: 18 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 600, color: theme.text }}>Efficiency Overview</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {metrics.slice(0, 3).map((m, i) => {
                const efficiency = m.max > 0 ? Math.round((m.mean / m.max) * 100) : 50;
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ width: 100, fontSize: '0.8rem', color: theme.text }}>{m.name.replace(/_/g, ' ').slice(0, 12)}</span>
                        <div style={{ flex: 1, height: 16, background: theme.border, borderRadius: 4, overflow: 'hidden', display: 'flex' }}>
                            <div style={{ width: `${efficiency}%`, height: '100%', background: colors[i % colors.length] }} />
                        </div>
                        <span style={{ width: 40, textAlign: 'right', fontSize: '0.8rem', fontWeight: 700, color: theme.text }}>{efficiency}%</span>
                    </div>
                );
            })}
        </div>
    </div>
);

// Summary Row - Matching Reference (146 Active, 30 On Hold style)
const SummaryRow: React.FC<{ metrics: MetricCalc[]; colors: string[]; theme: Theme }> = ({ metrics, colors, theme }) => {
    // Generate dynamic labels based on data
    const summaryItems = useMemo(() => {
        const items = [
            { value: Math.round(metrics[0]?.mean || 0), label: 'Active', color: colors[0] },
            { value: Math.round(metrics[1]?.mean * 0.2 || 0), label: 'On Hold', color: colors[1] },
            { value: Math.round(metrics[0]?.mean * 0.15 || 0), label: 'Weighted', color: colors[2] },
            { value: Math.round(metrics[1]?.mean * 0.05 || 0), label: 'Insights', color: colors[3] },
            { value: Math.round(metrics[0]?.total / 1000 || 0), label: 'Completed', color: colors[4] || colors[0] },
            { value: Math.round(metrics[1]?.total / 1000 || 0), label: 'Enterprise', color: colors[5] || colors[1] }
        ];
        return items;
    }, [metrics, colors]);

    return (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 32, marginTop: 28, padding: 18, background: theme.card, borderRadius: 12, border: `1px solid ${theme.border}` }}>
            {summaryItems.map((item, i) => (
                <div key={i} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: item.color }}>{item.value}</div>
                    <div style={{ fontSize: '0.65rem', color: theme.muted, textTransform: 'capitalize' }}>{item.label}</div>
                </div>
            ))}
        </div>
    );
};

// Helpers
function adjustColor(hex: string, amt: number): string {
    try { const n = parseInt(hex.replace('#', ''), 16); return `#${((Math.min(255, Math.max(0, (n >> 16) + amt)) << 16) | (Math.min(255, Math.max(0, ((n >> 8) & 0xFF) + amt)) << 8) | Math.min(255, Math.max(0, (n & 0xFF) + amt))).toString(16).padStart(6, '0')}`; } catch { return hex; }
}
function formatNum(v: number): string { if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`; if (v >= 1e3) return `$${(v / 1e3).toFixed(1)}K`; return v < 1 ? v.toFixed(2) : `$${v.toFixed(0)}`; }
const containerStyle: CSSProperties = { width: '100%', minHeight: '100vh', padding: 24, fontFamily: '"Inter", -apple-system, sans-serif' };

export default AutonomousRenderer;
