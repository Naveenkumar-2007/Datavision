// ScenarioChart.tsx - Enterprise What-If Scenario Visualization
import React, { useState, useEffect } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from 'recharts';
import {
    CheckCircle,
    Lightbulb,
    DollarSign
} from 'lucide-react';

interface Scenario {
    name: string;
    revenue: number;
    profit: number;
    customers?: number;
    churn_rate?: number;
    change_pct: number;
    risk: 'low' | 'medium' | 'high';
    description?: string;
}

interface ScenarioChartProps {
    scenarios: Scenario[];
    recommendation?: string;
    bestScenario?: string;
    riskLevel?: string;
    insights?: string[];
    currency?: string;
}

// Risk badge component
const RiskBadge: React.FC<{ risk: string }> = ({ risk }) => {
    const config = {
        low: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Low Risk' },
        medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Medium Risk' },
        high: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'High Risk' }
    };

    const { bg, text, label } = config[risk as keyof typeof config] || config.medium;

    return (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${bg} ${text}`}>
            {label}
        </span>
    );
};

const ScenarioChart: React.FC<ScenarioChartProps> = ({
    scenarios,
    recommendation = '',
    bestScenario = '',
    // riskLevel not used in component
    insights = [],
    currency = '₹'
}) => {
    const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'profit'>('profit');
    const [isVisible, setIsVisible] = useState(false);
    const [activeIndex, setActiveIndex] = useState<number | null>(null);

    useEffect(() => {
        setTimeout(() => setIsVisible(true), 100);
    }, []);

    // Get bar colors - Purple/Violet theme for scenarios
    const getBarColor = (entry: Scenario, _index: number) => {
        if (entry.name === bestScenario) return '#10b981'; // Emerald for best
        if (entry.name === 'Current State') return '#6b7280'; // Gray for current
        if (entry.risk === 'high') return '#f43f5e'; // Rose for high risk
        if (entry.risk === 'medium') return '#a855f7'; // Purple for medium
        return '#8b5cf6'; // Violet for low risk
    };

    // Custom tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (!active || !payload?.length) return null;

        const scenario = payload[0]?.payload as Scenario;

        return (
            <div className="bg-dark-card border border-dark-border rounded-xl p-4 shadow-xl min-w-[200px]">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-white">{scenario.name}</p>
                    <RiskBadge risk={scenario.risk} />
                </div>

                <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                        <span className="text-gray-400">Revenue:</span>
                        <span className="text-white font-medium">
                            {currency}{scenario.revenue.toLocaleString()}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-400">Profit:</span>
                        <span className="text-green-400 font-medium">
                            {currency}{scenario.profit.toLocaleString()}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-400">Change:</span>
                        <span className={`font-medium ${scenario.change_pct > 0 ? 'text-green-400' :
                            scenario.change_pct < 0 ? 'text-red-400' : 'text-gray-400'
                            }`}>
                            {scenario.change_pct > 0 ? '+' : ''}{scenario.change_pct}%
                        </span>
                    </div>
                </div>

                {scenario.description && (
                    <p className="mt-2 text-xs text-gray-500 border-t border-dark-border pt-2">
                        {scenario.description}
                    </p>
                )}
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
                        <DollarSign className="w-5 h-5 text-orange-400" />
                        Scenario Comparison
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">
                        {scenarios.length} scenarios analyzed
                    </p>
                </div>

                {/* Metric Toggle */}
                <div className="flex items-center gap-2 bg-dark-surface rounded-lg p-1">
                    <button
                        onClick={() => setSelectedMetric('revenue')}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${selectedMetric === 'revenue'
                            ? 'bg-orange-500 text-white'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        Revenue
                    </button>
                    <button
                        onClick={() => setSelectedMetric('profit')}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${selectedMetric === 'profit'
                            ? 'bg-orange-500 text-white'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        Profit
                    </button>
                </div>
            </div>

            {/* Best Scenario Highlight */}
            {bestScenario && bestScenario !== 'Current State' && (
                <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-xl flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-green-400">Recommended: {bestScenario}</p>
                        {recommendation && (
                            <p className="text-xs text-gray-400 mt-1">{recommendation}</p>
                        )}
                    </div>
                </div>
            )}

            {/* Chart */}
            <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={scenarios}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        onMouseMove={(state) => {
                            if (state?.activeTooltipIndex !== undefined) {
                                setActiveIndex(state.activeTooltipIndex);
                            }
                        }}
                        onMouseLeave={() => setActiveIndex(null)}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />

                        <XAxis
                            dataKey="name"
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={{ stroke: '#374151' }}
                            angle={-20}
                            textAnchor="end"
                            height={60}
                        />

                        <YAxis
                            stroke="#6b7280"
                            fontSize={12}
                            tickLine={false}
                            axisLine={{ stroke: '#374151' }}
                            tickFormatter={(value) => `${currency}${(value / 1000).toFixed(0)}k`}
                        />

                        <Tooltip content={<CustomTooltip />} cursor={false} />

                        <Bar
                            dataKey={selectedMetric}
                            radius={[8, 8, 0, 0]}
                            animationDuration={800}
                            animationEasing="ease-out"
                        >
                            {scenarios.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={getBarColor(entry, index)}
                                    opacity={activeIndex === null || activeIndex === index ? 1 : 0.4}
                                    className="transition-opacity duration-200"
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Scenario Cards Grid */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
                {scenarios.slice(0, 4).map((scenario, i) => (
                    <div
                        key={i}
                        className={`p-3 rounded-xl border transition-all duration-200 ${scenario.name === bestScenario
                            ? 'bg-green-500/10 border-green-500/30'
                            : 'bg-dark-surface/50 border-dark-border hover:border-orange-500/30'
                            }`}
                    >
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-gray-400 truncate">{scenario.name}</span>
                            <RiskBadge risk={scenario.risk} />
                        </div>
                        <p className="text-lg font-bold text-white">
                            {currency}{(scenario[selectedMetric] / 1000).toFixed(0)}k
                        </p>
                        <p className={`text-xs ${scenario.change_pct > 0 ? 'text-green-400' :
                            scenario.change_pct < 0 ? 'text-red-400' : 'text-gray-500'
                            }`}>
                            {scenario.change_pct > 0 ? '+' : ''}{scenario.change_pct}%
                        </p>
                    </div>
                ))}
            </div>

            {/* Insights Section */}
            {insights.length > 0 && (
                <div className="mt-6 pt-4 border-t border-dark-border">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-3 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        Simulation Insights
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

export default ScenarioChart;
