// PredictionChartRenderer.tsx - Renders prediction charts from AI responses
// Uses EnhancedCharts for production-grade visualizations
import React, { useMemo } from 'react';
import {
    EnhancedForecastChart,
    EnhancedScenarioChart,
    EnhancedProfitLossChart,
    EnhancedChurnChart,
} from './EnhancedCharts';

// Chart payload interface matching backend output
export interface ForecastChartPayload {
    chart_type: 'forecast_line' | 'scenario_bar' | 'churn_distribution' | 'profit_loss_curve';
    title: string;
    x: string[];
    y_actual?: (number | null)[];
    y_forecast?: (number | null)[];
    y_upper?: (number | null)[];
    y_lower?: (number | null)[];
    confidence_band?: boolean;
    currency?: string;
    series?: Array<{
        name: string;
        data: (number | null)[];
        type: string;
        color?: string;
        colors?: string[];
    }>;
    values?: number[];
    changes?: number[];
    risks?: string[];
    colors?: string[];
    best_scenario?: string;
    options?: Record<string, unknown>;
}

export interface PredictionChartRendererProps {
    payload: ForecastChartPayload | string;
    className?: string;
}

// Parse payload if it's a JSON string
const parsePayload = (payload: ForecastChartPayload | string): ForecastChartPayload | null => {
    if (typeof payload === 'string') {
        try {
            return JSON.parse(payload);
        } catch {
            console.error('Failed to parse chart payload');
            return null;
        }
    }
    return payload;
};

// Main Prediction Chart Renderer
export const PredictionChartRenderer: React.FC<PredictionChartRendererProps> = ({
    payload,
    className = ''
}) => {
    const parsedPayload = parsePayload(payload);

    // Transform backend payload to chart data format
    const chartData = useMemo(() => {
        if (!parsedPayload) return null;

        const { chart_type, x, y_actual, y_forecast, y_upper, y_lower } = parsedPayload;

        if (chart_type === 'forecast_line') {
            // Build forecast data points
            const data = x.map((date, idx) => {
                const actual = y_actual?.[idx];
                const forecast = y_forecast?.[idx];
                const value = actual ?? forecast ?? 0;

                return {
                    date,
                    value,
                    lower: y_lower?.[idx] ?? undefined,
                    upper: y_upper?.[idx] ?? undefined,
                    type: (actual !== null && actual !== undefined ? 'historical' : 'forecast') as 'historical' | 'forecast',
                };
            }).filter(d => d.value !== null && d.value !== undefined);

            return { type: 'forecast', data };
        }

        if (chart_type === 'scenario_bar') {
            const scenarios = x.map((name, idx) => ({
                name,
                value: parsedPayload.values?.[idx] ?? 0,
                change: parsedPayload.changes?.[idx] ?? 0,
                risk: (parsedPayload.risks?.[idx] as 'low' | 'medium' | 'high') ?? 'medium',
            }));
            return { type: 'scenario', data: scenarios, bestScenario: parsedPayload.best_scenario };
        }

        if (chart_type === 'churn_distribution') {
            const churnData = x.map((segment, idx) => ({
                segment,
                risk: parsedPayload.values?.[idx] ?? 0,
                customers: Math.round(Math.random() * 1000 + 100), // Placeholder
            }));
            return { type: 'churn', data: churnData };
        }

        if (chart_type === 'profit_loss_curve') {
            const profitData = x.map((period, idx) => {
                const revenue = parsedPayload.series?.find(s => s.name === 'Revenue')?.data[idx] ?? 0;
                const cost = parsedPayload.series?.find(s => s.name === 'Cost')?.data[idx] ?? 0;
                return {
                    period,
                    revenue: revenue ?? 0,
                    cost: cost ?? 0,
                    profit: (revenue ?? 0) - (cost ?? 0),
                };
            });
            return { type: 'profit', data: profitData };
        }

        return null;
    }, [parsedPayload]);

    if (!parsedPayload || !chartData) {
        return (
            <div className="text-gray-400 text-sm p-4 border border-gray-700 rounded-xl bg-gray-900/50">
                Unable to render chart
            </div>
        );
    }

    const currency = parsedPayload.currency || '₹';
    const title = parsedPayload.title || 'Chart';

    return (
        <div className={`w-full ${className}`}>
            {chartData.type === 'forecast' && (
                <EnhancedForecastChart
                    data={chartData.data as Array<{ date: string; value: number; lower?: number; upper?: number; type: 'historical' | 'forecast' }>}
                    title={title}
                    currency={currency}
                    showConfidenceBand={parsedPayload.confidence_band !== false}
                />
            )}
            {chartData.type === 'scenario' && (
                <EnhancedScenarioChart
                    scenarios={chartData.data as Array<{ name: string; value: number; change: number; risk: 'low' | 'medium' | 'high' }>}
                    bestScenario={(chartData as { type: string; data: unknown[]; bestScenario?: string }).bestScenario}
                    title={title}
                    currency={currency}
                />
            )}
            {chartData.type === 'churn' && (
                <EnhancedChurnChart
                    data={chartData.data as Array<{ segment: string; risk: number; customers: number }>}
                    title={title}
                />
            )}
            {chartData.type === 'profit' && (
                <EnhancedProfitLossChart
                    data={chartData.data as Array<{ period: string; revenue: number; cost: number; profit: number }>}
                    title={title}
                    currency={currency}
                />
            )}
        </div>
    );
};

// Utility function to extract chart payloads from AI message content
export const extractChartPayloads = (content: string): ForecastChartPayload[] => {
    const payloads: ForecastChartPayload[] = [];

    // Match ```forecast_chart ... ``` blocks
    const regex = /```forecast_chart\s*([\s\S]*?)```/g;
    let match;

    while ((match = regex.exec(content)) !== null) {
        try {
            const json = match[1].trim();
            const parsed = JSON.parse(json);
            payloads.push(parsed);
        } catch (e) {
            console.error('Failed to parse chart payload:', e);
        }
    }

    return payloads;
};

// Check if message contains chart payloads
export const hasChartPayload = (content: string): boolean => {
    return content.includes('```forecast_chart');
};

export default PredictionChartRenderer;
