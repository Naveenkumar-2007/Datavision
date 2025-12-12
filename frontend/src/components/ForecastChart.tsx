// ForecastChart.tsx - Enterprise Forecast Visualization Component
import React, { useEffect, useState } from 'react';
import {
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    ComposedChart,
    Legend,
    ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, Target } from 'lucide-react';

interface ForecastDataPoint {
    period: number;
    date: string;
    value: number;
    lower?: number;
    upper?: number;
    type: 'historical' | 'forecast';
}

interface ForecastChartProps {
    data: ForecastDataPoint[];
    title?: string;
    trend?: string;
    confidence?: number;
    insights?: string[];
    currency?: string;
}

// Animated number display
const AnimatedValue: React.FC<{ value: number; prefix?: string }> = ({ value, prefix = '' }) => {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        const duration = 1000;
        const startTime = Date.now();
        const startValue = display;

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            setDisplay(startValue + (value - startValue) * easeOut);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }, [value]);

    return <span>{prefix}{Math.round(display).toLocaleString()}</span>;
};

// Trend indicator component
const TrendIndicator: React.FC<{ trend: string }> = ({ trend }) => {
    const getTrendIcon = () => {
        if (trend.includes('increasing')) return <TrendingUp className="w-5 h-5 text-green-500" />;
        if (trend.includes('decreasing')) return <TrendingDown className="w-5 h-5 text-red-500" />;
        return <Minus className="w-5 h-5 text-gray-500" />;
    };

    const getTrendColor = () => {
        if (trend.includes('increasing')) return 'text-green-400';
        if (trend.includes('decreasing')) return 'text-red-400';
        return 'text-gray-400';
    };

    const formatTrend = () => {
        return trend.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    };

    return (
        <div className={`flex items-center gap-2 ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-medium">{formatTrend()}</span>
        </div>
    );
};

const ForecastChart: React.FC<ForecastChartProps> = ({
    data,
    title = 'Revenue Forecast',
    trend = 'stable',
    confidence = 85,
    insights = [],
    currency = '₹'
}) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Trigger animation after mount
        setTimeout(() => setIsVisible(true), 100);
    }, []);

    // Separate historical and forecast data
    const historicalData = data.filter(d => d.type === 'historical');
    const forecastData = data.filter(d => d.type === 'forecast');

    // Calculate summary stats
    const lastHistorical = historicalData[historicalData.length - 1]?.value || 0;
    const lastForecast = forecastData[forecastData.length - 1]?.value || 0;
    const forecastChange = lastHistorical > 0
        ? ((lastForecast - lastHistorical) / lastHistorical * 100).toFixed(1)
        : '0';

    // Custom tooltip
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (!active || !payload?.length) return null;

        const point = payload[0]?.payload as ForecastDataPoint;
        const isForecast = point?.type === 'forecast';

        return (
            <div className="bg-dark-card border border-dark-border rounded-xl p-3 shadow-xl">
                <p className="text-xs text-gray-400 mb-1">{label}</p>
                <p className="text-lg font-bold text-white">
                    {currency}{point?.value?.toLocaleString()}
                </p>
                {isForecast && point.lower && point.upper && (
                    <div className="mt-1 text-xs text-gray-500">
                        Range: {currency}{point.lower.toLocaleString()} - {currency}{point.upper.toLocaleString()}
                    </div>
                )}
                <div className={`mt-1 text-xs ${isForecast ? 'text-orange-400' : 'text-blue-400'}`}>
                    {isForecast ? '📊 Forecast' : '📈 Historical'}
                </div>
            </div>
        );
    };

    return (
        <div
            className={`premium-card p-6 chart-fade-in transition-all duration-500 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Target className="w-5 h-5 text-orange-400" />
                        {title}
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">
                        {forecastData.length} period forecast
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    <TrendIndicator trend={trend} />

                    {/* Confidence Badge */}
                    <div className={`confidence-badge ${confidence >= 80 ? 'confidence-high' :
                        confidence >= 60 ? 'confidence-medium' : 'confidence-low'
                        }`}>
                        <span className="text-xs">Confidence:</span>
                        <span className="font-bold">{confidence}%</span>
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-dark-surface/50 rounded-xl p-4 border border-dark-border">
                    <p className="text-xs text-gray-500 mb-1">Current</p>
                    <p className="text-xl font-bold text-white">
                        {currency}<AnimatedValue value={lastHistorical} />
                    </p>
                </div>
                <div className="bg-dark-surface/50 rounded-xl p-4 border border-orange-500/30">
                    <p className="text-xs text-orange-400 mb-1">Forecast</p>
                    <p className="text-xl font-bold text-orange-400">
                        {currency}<AnimatedValue value={lastForecast} />
                    </p>
                </div>
                <div className="bg-dark-surface/50 rounded-xl p-4 border border-dark-border">
                    <p className="text-xs text-gray-500 mb-1">Change</p>
                    <p className={`text-xl font-bold ${Number(forecastChange) > 0 ? 'text-green-400' :
                        Number(forecastChange) < 0 ? 'text-red-400' : 'text-gray-400'
                        }`}>
                        {Number(forecastChange) > 0 ? '+' : ''}{forecastChange}%
                    </p>
                </div>
            </div>

            {/* Chart */}
            <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                            {/* Gradient for confidence interval */}
                            <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#f97316" stopOpacity={0.05} />
                            </linearGradient>

                            {/* Gradient for historical line */}
                            <linearGradient id="historicalGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />

                        <XAxis
                            dataKey="date"
                            stroke="#6b7280"
                            fontSize={12}
                            tickLine={false}
                            axisLine={{ stroke: '#374151' }}
                        />

                        <YAxis
                            stroke="#6b7280"
                            fontSize={12}
                            tickLine={false}
                            axisLine={{ stroke: '#374151' }}
                            tickFormatter={(value) => `${currency}${(value / 1000).toFixed(0)}k`}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        <Legend
                            verticalAlign="top"
                            height={36}
                            formatter={(value: string) => (
                                <span className="text-sm text-gray-400">{value}</span>
                            )}
                        />

                        {/* Reference line at forecast start */}
                        {historicalData.length > 0 && (
                            <ReferenceLine
                                x={historicalData[historicalData.length - 1]?.date}
                                stroke="#f97316"
                                strokeDasharray="5 5"
                                label={{
                                    value: 'Forecast Start',
                                    fill: '#f97316',
                                    fontSize: 10,
                                    position: 'top'
                                }}
                            />
                        )}

                        {/* Confidence interval area (for forecast only) */}
                        <Area
                            dataKey="upper"
                            stroke="none"
                            fill="url(#confidenceGradient)"
                            name="Confidence Range"
                            connectNulls={false}
                        />

                        {/* Historical line - solid blue */}
                        <Line
                            type="monotone"
                            dataKey={(d: ForecastDataPoint) => d.type === 'historical' ? d.value : null}
                            stroke="#3b82f6"
                            strokeWidth={3}
                            dot={{ fill: '#3b82f6', strokeWidth: 0, r: 4 }}
                            name="Historical"
                            connectNulls={false}
                        />

                        {/* Forecast line - dotted orange */}
                        <Line
                            type="monotone"
                            dataKey={(d: ForecastDataPoint) => d.type === 'forecast' ? d.value : null}
                            stroke="#f97316"
                            strokeWidth={3}
                            strokeDasharray="8 4"
                            dot={{ fill: '#f97316', strokeWidth: 0, r: 4 }}
                            name="Forecast"
                            connectNulls={false}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Insights Section */}
            {insights.length > 0 && (
                <div className="mt-6 pt-4 border-t border-dark-border">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-3">
                        💡 Forecast Insights
                    </p>
                    <div className="space-y-2 stagger-children">
                        {insights.map((insight, i) => (
                            <div
                                key={i}
                                className="insight-card text-sm text-gray-300"
                            >
                                {insight}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ForecastChart;
