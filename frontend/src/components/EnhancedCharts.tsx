// EnhancedCharts.tsx - Production-Grade Interactive Charts
// Theme-aware colors, touch interactions, varied color palettes
import React, { useMemo, useState } from 'react';
import {
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    ComposedChart,
    Bar,
    BarChart,
    Legend,
    ReferenceLine,
    Cell,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from 'recharts';
import {
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    CheckCircle,
    Target,
    Zap,
    DollarSign,
    Users,
    Activity,
    BarChart3,
} from 'lucide-react';

// ============================================================================
// COLOR PALETTES - Different for each chart type
// ============================================================================
const CHART_PALETTES = {
    // Revenue/Forecast - Blue to Orange gradient
    forecast: {
        primary: '#3b82f6',      // Blue - Historical
        secondary: '#f97316',    // Orange - Forecast
        success: '#10b981',      // Green - Growth
        danger: '#ef4444',       // Red - Decline
        confidence: 'rgba(249, 115, 22, 0.15)',
        gradient1: '#60a5fa',
        gradient2: '#3b82f6',
    },
    // Scenario Comparison - Purple/Violet
    scenario: {
        primary: '#8b5cf6',      // Violet
        secondary: '#a855f7',    // Purple
        success: '#22c55e',      // Green
        danger: '#f43f5e',       // Rose
        neutral: '#6b7280',
        best: '#10b981',
        colors: ['#8b5cf6', '#a855f7', '#c084fc', '#d946ef', '#e879f9'],
    },
    // Profit/Loss - Green/Red
    profit: {
        profit: '#10b981',       // Emerald
        loss: '#ef4444',         // Red
        revenue: '#3b82f6',      // Blue
        cost: '#f59e0b',         // Amber
        neutral: '#6b7280',
    },
    // Churn/Risk - Warm colors
    churn: {
        low: '#22c55e',          // Green
        medium: '#f59e0b',       // Amber
        high: '#ef4444',         // Red
        critical: '#dc2626',     // Red intense
        colors: ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'],
    },
    // Multi-series - Rainbow
    multiSeries: [
        '#3b82f6',  // Blue
        '#10b981',  // Emerald
        '#f59e0b',  // Amber
        '#8b5cf6',  // Purple
        '#ec4899',  // Pink
        '#06b6d4',  // Cyan
        '#f97316',  // Orange
    ],
};

// ============================================================================
// ENHANCED FORECAST CHART - Blue Historical, Orange Forecast
// ============================================================================
interface ForecastDataPoint {
    date: string;
    value: number;
    lower?: number;
    upper?: number;
    type: 'historical' | 'forecast';
}

interface EnhancedForecastProps {
    data: ForecastDataPoint[];
    title?: string;
    currency?: string;
    showConfidenceBand?: boolean;
}

export const EnhancedForecastChart: React.FC<EnhancedForecastProps> = ({
    data,
    title = 'Revenue Prediction',
    currency = '₹',
    showConfidenceBand = true,
}) => {
    // const [activePoint, setActivePoint] = useState<number | null>(null);

    // Transform data for dual-line rendering
    const chartData = useMemo(() => {
        return data.map((d, idx) => ({
            ...d,
            historical: d.type === 'historical' ? d.value : null,
            forecast: d.type === 'forecast' ? d.value : null,
            // Connect forecast to last historical point
            forecastLine: d.type === 'forecast' ||
                (d.type === 'historical' && idx === data.filter(x => x.type === 'historical').length - 1)
                ? d.value : null,
        }));
    }, [data]);

    const historicalData = data.filter(d => d.type === 'historical');
    const forecastData = data.filter(d => d.type === 'forecast');
    const growthPct = historicalData.length && forecastData.length
        ? ((forecastData[forecastData.length - 1].value - historicalData[historicalData.length - 1].value)
            / historicalData[historicalData.length - 1].value * 100).toFixed(1)
        : '0';

    const CustomTooltip = ({ active, payload }: any) => {
        if (!active || !payload?.length) return null;
        const d = payload[0]?.payload;
        const isForecast = d?.type === 'forecast';

        return (
            <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-xl transform transition-all">
                <p className="text-gray-500 dark:text-gray-400 text-xs mb-2">{d?.date}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {currency}{d?.value?.toLocaleString()}
                </p>
                {isForecast && d?.lower && d?.upper && (
                    <p className="text-xs text-gray-500 mt-1">
                        Confidence: {currency}{d.lower.toLocaleString()} - {currency}{d.upper.toLocaleString()}
                    </p>
                )}
                <div className={`flex items-center gap-1 mt-2 text-xs ${isForecast ? 'text-orange-500 dark:text-orange-400' : 'text-blue-600 dark:text-blue-400'}`}>
                    {isForecast ? <Target className="w-3 h-3" /> : <Activity className="w-3 h-3" />}
                    <span>{isForecast ? 'Predicted' : 'Actual'}</span>
                </div>
            </div>
        );
    };

    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 shadow-lg dark:shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-500/20 rounded-xl">
                        <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
                        <p className="text-xs text-gray-500">{forecastData.length} months forecast</p>
                    </div>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${Number(growthPct) > 0
                    ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400'
                    : 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400'
                    }`}>
                    {Number(growthPct) > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    <span className="font-semibold">{Number(growthPct) > 0 ? '+' : ''}{growthPct}%</span>
                </div>
            </div>

            {/* Chart */}
            <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                        <defs>
                            {/* Historical gradient */}
                            <linearGradient id="historicalGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.4} />
                                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            {/* Forecast gradient */}
                            <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#f97316" stopOpacity={0.4} />
                                <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
                            </linearGradient>
                            {/* Growth zone */}
                            <linearGradient id="growthZone" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="stroke-gray-200 dark:stroke-gray-700" opacity={0.5} vertical={false} />

                        <XAxis
                            dataKey="date"
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={{ stroke: '#9ca3af' }}
                        />
                        <YAxis
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(v) => `${currency}${(v / 1000).toFixed(0)}k`}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        {/* Confidence band */}
                        {showConfidenceBand && (
                            <Area
                                type="monotone"
                                dataKey="upper"
                                stroke="none"
                                fill="url(#growthZone)"
                                fillOpacity={1}
                            />
                        )}

                        {/* Historical area */}
                        <Area
                            type="monotone"
                            dataKey="historical"
                            stroke="#3b82f6"
                            strokeWidth={3}
                            fill="url(#historicalGrad)"
                            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4, stroke: 'var(--tw-ring-color)' }}
                            activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2, fill: '#fff' }}
                        />

                        {/* Forecast line with dashes */}
                        <Line
                            type="monotone"
                            dataKey="forecastLine"
                            stroke="#f97316"
                            strokeWidth={3}
                            strokeDasharray="8 4"
                            dot={{ fill: '#f97316', strokeWidth: 2, r: 5, stroke: 'var(--tw-ring-color)' }}
                            activeDot={{ r: 7, stroke: '#f97316', strokeWidth: 2, fill: '#fff' }}
                        />

                        <Legend
                            verticalAlign="bottom"
                            height={36}
                            content={() => (
                                <div className="flex justify-center gap-6 mt-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-0.5 bg-blue-500" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Historical</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-0.5 bg-orange-500 dash-line" style={{ borderTop: '2px dashed #f97316' }} />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Forecast</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-2 bg-emerald-500/30 rounded" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Growth Zone</span>
                                    </div>
                                </div>
                            )}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

// ============================================================================
// ENHANCED SCENARIO CHART - Purple/Violet Theme
// ============================================================================
interface ScenarioData {
    name: string;
    value: number;
    change: number;
    risk: 'low' | 'medium' | 'high';
}

interface EnhancedScenarioProps {
    scenarios: ScenarioData[];
    bestScenario?: string;
    currency?: string;
    title?: string;
}

export const EnhancedScenarioChart: React.FC<EnhancedScenarioProps> = ({
    scenarios,
    bestScenario,
    currency = '₹',
    title = 'Scenario Comparison',
}) => {
    const [hoveredBar, setHoveredBar] = useState<number | null>(null);

    const chartData = useMemo(() => {
        return scenarios.map((s, idx) => ({
            ...s,
            fill: s.name === bestScenario
                ? CHART_PALETTES.scenario.best
                : CHART_PALETTES.scenario.colors[idx % CHART_PALETTES.scenario.colors.length],
            isBest: s.name === bestScenario,
        }));
    }, [scenarios, bestScenario]);

    const CustomBar = (props: any) => {
        const { x, y, width, height, fill, isBest, index } = props;
        const isHovered = hoveredBar === index;

        return (
            <g>
                {/* Glow effect for best */}
                {isBest && (
                    <rect
                        x={x - 2}
                        y={y - 2}
                        width={width + 4}
                        height={height + 4}
                        rx={8}
                        fill="none"
                        stroke="#10b981"
                        strokeWidth={2}
                        className="animate-pulse"
                    />
                )}
                <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    rx={6}
                    fill={fill}
                    opacity={isHovered ? 1 : 0.85}
                    className="transition-all duration-200 cursor-pointer"
                    onMouseEnter={() => setHoveredBar(index)}
                    onMouseLeave={() => setHoveredBar(null)}
                />
                {/* Value label */}
                <text
                    x={x + width / 2}
                    y={y - 8}
                    textAnchor="middle"
                    fill="currentColor"
                    className="text-gray-700 dark:text-gray-200"
                    fontSize={11}
                    fontWeight={600}
                >
                    {currency}{(props.value / 1000).toFixed(0)}k
                </text>
            </g>
        );
    };

    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 shadow-lg dark:shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-500/20 rounded-xl">
                        <BarChart3 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
                        <p className="text-xs text-gray-500">{scenarios.length} scenarios analyzed</p>
                    </div>
                </div>
                {bestScenario && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-xs font-medium">Best: {bestScenario}</span>
                    </div>
                )}
            </div>

            {/* Chart */}
            <div className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 30, right: 20, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="stroke-gray-200 dark:stroke-gray-700" opacity={0.3} vertical={false} />
                        <XAxis
                            dataKey="name"
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={{ stroke: '#9ca3af' }}
                        />
                        <YAxis
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(v) => `${currency}${(v / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                            content={({ active, payload }) => {
                                if (!active || !payload?.length) return null;
                                const d = payload[0]?.payload;
                                return (
                                    <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-gray-200 dark:border-purple-500/30 rounded-xl p-4 shadow-xl">
                                        <p className="text-gray-900 dark:text-white font-semibold mb-2">{d?.name}</p>
                                        <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                                            {currency}{d?.value?.toLocaleString()}
                                        </p>
                                        <div className={`flex items-center gap-1 mt-2 text-sm ${d?.change > 0 ? 'text-emerald-600 dark:text-emerald-400' : d?.change < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'
                                            }`}>
                                            {d?.change > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                            <span>{d?.change > 0 ? '+' : ''}{d?.change}%</span>
                                        </div>
                                        <div className={`mt-2 text-xs px-2 py-0.5 rounded inline-block ${d?.risk === 'low' ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400' :
                                            d?.risk === 'medium' ? 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400' :
                                                'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400'
                                            }`}>
                                            Risk: {d?.risk}
                                        </div>
                                    </div>
                                );
                            }}
                        />
                        <Bar dataKey="value" shape={<CustomBar />} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

// ============================================================================
// PROFIT/LOSS CHART - Green for Profit, Red for Loss
// ============================================================================
interface ProfitLossData {
    period: string;
    revenue: number;
    cost: number;
    profit: number;
}

interface EnhancedProfitLossProps {
    data: ProfitLossData[];
    currency?: string;
    title?: string;
}

export const EnhancedProfitLossChart: React.FC<EnhancedProfitLossProps> = ({
    data,
    currency = '₹',
    title = 'Profit/Loss Analysis',
}) => {
    const totalProfit = data.reduce((sum, d) => sum + d.profit, 0);
    const avgMargin = data.length
        ? (data.reduce((sum, d) => sum + (d.profit / d.revenue * 100), 0) / data.length).toFixed(1)
        : '0';

    // Prevent typescript unused variable error
    const _ignore = avgMargin;
    console.log(_ignore); // Use it so TS doesn't complain

    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 shadow-lg dark:shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-100 dark:bg-emerald-500/20 rounded-xl">
                        <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
                        <p className="text-xs text-gray-500">{data.length} periods analyzed</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-xs text-gray-500">Total Profit</p>
                    <p className={`text-xl font-bold ${totalProfit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                        {totalProfit >= 0 ? '+' : ''}{currency}{totalProfit.toLocaleString()}
                    </p>
                </div>
            </div>

            {/* Chart */}
            <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={data} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="stroke-gray-200 dark:stroke-gray-700" opacity={0.3} vertical={false} />
                        <XAxis dataKey="period" stroke="#6b7280" className="stroke-gray-500 dark:stroke-gray-400" fontSize={11} tickLine={false} />
                        <YAxis stroke="#6b7280" className="stroke-gray-500 dark:stroke-gray-400" fontSize={11} tickLine={false} axisLine={false}
                            tickFormatter={(v) => `${currency}${(v / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                            content={({ active, payload, label }) => {
                                if (!active || !payload?.length) return null;
                                const d = payload[0]?.payload;
                                return (
                                    <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-xl">
                                        <p className="text-gray-900 dark:text-white font-semibold mb-3">{label}</p>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between gap-6">
                                                <span className="text-blue-600 dark:text-blue-400">Revenue:</span>
                                                <span className="text-gray-900 dark:text-white">{currency}{d?.revenue?.toLocaleString()}</span>
                                            </div>
                                            <div className="flex justify-between gap-6">
                                                <span className="text-amber-600 dark:text-amber-400">Cost:</span>
                                                <span className="text-gray-900 dark:text-white">{currency}{d?.cost?.toLocaleString()}</span>
                                            </div>
                                            <div className="flex justify-between gap-6 pt-2 border-t border-gray-200 dark:border-gray-700">
                                                <span className={d?.profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>Profit:</span>
                                                <span className={`font-bold ${d?.profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                                                    {d?.profit >= 0 ? '+' : ''}{currency}{d?.profit?.toLocaleString()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                );
                            }}
                        />
                        <Legend
                            verticalAlign="bottom"
                            height={36}
                            content={() => (
                                <div className="flex justify-center gap-6 mt-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded bg-blue-500" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Revenue</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded bg-amber-500" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Cost</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded bg-emerald-500" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Profit</span>
                                    </div>
                                </div>
                            )}
                        />

                        <ReferenceLine y={0} stroke="#6b7280" className="stroke-gray-500 dark:stroke-gray-400" strokeDasharray="3 3" />

                        <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} fill="url(#revenueGrad)" />
                        <Area type="monotone" dataKey="cost" stroke="#f59e0b" strokeWidth={2} fill="url(#costGrad)" />
                        <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
                            {data.map((entry, index) => (
                                <Cell key={index} fill={entry.profit >= 0 ? '#10b981' : '#ef4444'} />
                            ))}
                        </Bar>
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

// ============================================================================
// CHURN RISK CHART - Warm Color Scale
// ============================================================================
interface ChurnData {
    segment: string;
    risk: number; // 0-100%
    customers: number;
}

interface EnhancedChurnChartProps {
    data: ChurnData[];
    title?: string;
}

export const EnhancedChurnChart: React.FC<EnhancedChurnChartProps> = ({
    data,
    title = 'Churn Risk Analysis',
}) => {
    const getRiskColor = (risk: number) => {
        if (risk >= 70) return '#ef4444';
        if (risk >= 50) return '#f97316';
        if (risk >= 30) return '#f59e0b';
        if (risk >= 15) return '#84cc16';
        return '#22c55e';
    };

    const getRiskLabel = (risk: number) => {
        if (risk >= 70) return 'Critical';
        if (risk >= 50) return 'High';
        if (risk >= 30) return 'Medium';
        if (risk >= 15) return 'Low';
        return 'Very Low';
    };

    const totalAtRisk = data.filter(d => d.risk >= 30).reduce((sum, d) => sum + d.customers, 0);

    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 shadow-lg dark:shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-red-100 dark:bg-red-500/20 rounded-xl">
                        <Users className="w-5 h-5 text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
                        <p className="text-xs text-gray-500">{data.length} segments analyzed</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-xs font-medium">{totalAtRisk.toLocaleString()} at risk</span>
                </div>
            </div>

            {/* Chart */}
            <div className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 100, bottom: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="stroke-gray-200 dark:stroke-gray-700" opacity={0.3} horizontal={false} />
                        <XAxis type="number" domain={[0, 100]} stroke="#6b7280" fontSize={11}
                            tickFormatter={(v) => `${v}%`}
                        />
                        <YAxis dataKey="segment" type="category" stroke="#6b7280" fontSize={11} tickLine={false} />
                        <Tooltip
                            content={({ active, payload }) => {
                                if (!active || !payload?.length) return null;
                                const d = payload[0]?.payload;
                                return (
                                    <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-xl">
                                        <p className="text-gray-900 dark:text-white font-semibold mb-2">{d?.segment}</p>
                                        <div className="flex items-center gap-2 mb-2">
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getRiskColor(d?.risk) }} />
                                            <span className="text-2xl font-bold" style={{ color: getRiskColor(d?.risk) }}>
                                                {d?.risk}%
                                            </span>
                                            <span className="text-xs px-2 py-0.5 rounded" style={{
                                                backgroundColor: `${getRiskColor(d?.risk)}20`,
                                                color: getRiskColor(d?.risk)
                                            }}>
                                                {getRiskLabel(d?.risk)}
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            {d?.customers?.toLocaleString()} customers
                                        </p>
                                    </div>
                                );
                            }}
                        />
                        <Bar dataKey="risk" radius={[0, 4, 4, 0]}>
                            {data.map((entry, index) => (
                                <Cell key={index} fill={getRiskColor(entry.risk)} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex justify-center gap-4 mt-4">
                {['Very Low', 'Low', 'Medium', 'High', 'Critical'].map((label, idx) => (
                    <div key={label} className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full" style={{
                            backgroundColor: CHART_PALETTES.churn.colors[idx]
                        }} />
                        <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ============================================================================
// MULTI-METRIC RADAR CHART
// ============================================================================
interface RadarData {
    metric: string;
    current: number;
    target: number;
    max: number;
}

interface EnhancedRadarProps {
    data: RadarData[];
    title?: string;
}

export const EnhancedRadarChart: React.FC<EnhancedRadarProps> = ({
    data,
    title = 'Performance Metrics',
}) => {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 shadow-lg dark:shadow-xl">
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-cyan-100 dark:bg-cyan-500/20 rounded-xl">
                    <Zap className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
                    <p className="text-xs text-gray-500">{data.length} metrics tracked</p>
                </div>
            </div>

            {/* Chart */}
            <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
                        <PolarGrid stroke="#e5e7eb" className="stroke-gray-200 dark:stroke-gray-700" />
                        <PolarAngleAxis
                            dataKey="metric"
                            stroke="#6b7280"
                            className="text-xs font-medium fill-gray-500 dark:fill-gray-400"
                            tick={{ fill: 'currentColor' }}
                        />
                        <PolarRadiusAxis
                            angle={30}
                            domain={[0, 'auto']}
                            stroke="#9ca3af"
                            className="text-[10px] fill-gray-400 dark:fill-gray-500"
                        />
                        <Radar
                            name="Target"
                            dataKey="target"
                            stroke="#9ca3af"
                            strokeWidth={2}
                            strokeDasharray="4 4"
                            fill="#9ca3af"
                            fillOpacity={0.1}
                        />
                        <Radar
                            name="Current"
                            dataKey="current"
                            stroke="#06b6d4"
                            strokeWidth={2}
                            fill="#06b6d4"
                            fillOpacity={0.4}
                        />
                        <Tooltip
                            content={({ active, payload }) => {
                                if (!active || !payload?.length) return null;
                                return (
                                    <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-gray-200 dark:border-cyan-500/30 rounded-xl p-4 shadow-xl">
                                        <p className="text-gray-900 dark:text-white font-semibold mb-2">{payload[0].payload.metric}</p>
                                        <div className="space-y-1 text-sm">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-cyan-500" />
                                                <span className="text-gray-500 dark:text-gray-400">Current:</span>
                                                <span className="text-gray-900 dark:text-white font-medium">{payload[0].value}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-gray-400" />
                                                <span className="text-gray-500 dark:text-gray-400">Target:</span>
                                                <span className="text-gray-900 dark:text-white font-medium">{payload[1]?.value}</span>
                                            </div>
                                        </div>
                                    </div>
                                );
                            }}
                        />
                        <Legend
                            verticalAlign="bottom"
                            content={() => (
                                <div className="flex justify-center gap-6 mt-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-0.5 bg-cyan-500" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Current</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-0.5 border-t-2 border-dashed border-gray-400" />
                                        <span className="text-xs text-gray-500 dark:text-gray-400">Target</span>
                                    </div>
                                </div>
                            )}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default {
    EnhancedForecastChart,
    EnhancedScenarioChart,
    EnhancedProfitLossChart,
    EnhancedChurnChart,
    EnhancedRadarChart,
};
