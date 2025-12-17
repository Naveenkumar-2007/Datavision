/**
 * Waterfall Chart Component
 * Shows cumulative effect of sequential positive/negative values
 */

import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ReferenceLine,
    CartesianGrid,
} from 'recharts';
import { formatCompactCurrency, Currency } from '@/utils/currency';

interface WaterfallDataPoint {
    name: string;
    value: number;
    isTotal?: boolean;
}

interface WaterfallChartProps {
    data: WaterfallDataPoint[];
    currency: Currency;
    height?: number;
}

// Process data to create waterfall structure
const processWaterfallData = (data: WaterfallDataPoint[]) => {
    let runningTotal = 0;

    return data.map((item, _index) => {
        const start = item.isTotal ? 0 : runningTotal;
        const end = item.isTotal ? item.value : runningTotal + item.value;

        if (!item.isTotal) {
            runningTotal += item.value;
        }

        return {
            name: item.name,
            value: Math.abs(item.value),
            start: Math.min(start, end),
            end: Math.max(start, end),
            isPositive: item.value >= 0,
            isTotal: item.isTotal,
            displayValue: item.value,
        };
    });
};

export const WaterfallChart: React.FC<WaterfallChartProps> = ({
    data,
    currency,
    height = 300,
}) => {
    const processedData = processWaterfallData(data);

    const getBarColor = (entry: any) => {
        if (entry.isTotal) return '#F97316'; // Orange for total
        return entry.isPositive ? '#22C55E' : '#EF4444'; // Green/Red
    };

    return (
        <ResponsiveContainer width="100%" height={height}>
            <BarChart data={processedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 11 }}
                />
                <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9CA3AF', fontSize: 11 }}
                    tickFormatter={(v) => formatCompactCurrency(v, currency)}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: '#1E293B',
                        border: '1px solid #475569',
                        borderRadius: '12px',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
                    }}
                    labelStyle={{ color: '#E5E7EB', fontWeight: 600 }}
                    formatter={(_value: number, _name: string, props: any) => [
                        formatCompactCurrency(props.payload.displayValue, currency),
                        props.payload.isTotal ? 'Total' : (props.payload.isPositive ? 'Increase' : 'Decrease')
                    ]}
                />
                <ReferenceLine y={0} stroke="#6B7280" />

                {/* Invisible bar for positioning */}
                <Bar dataKey="start" stackId="a" fill="transparent" />

                {/* Visible bar */}
                <Bar dataKey="value" stackId="a" radius={[4, 4, 0, 0]}>
                    {processedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getBarColor(entry)} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};

export default WaterfallChart;
