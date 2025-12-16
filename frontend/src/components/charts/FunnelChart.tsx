/**
 * Funnel Chart Component
 * Shows conversion/flow through stages
 */

import React from 'react';
import { motion } from 'framer-motion';
import { formatCompactCurrency, Currency } from '@/utils/currency';

interface FunnelDataPoint {
    name: string;
    value: number;
    color?: string;
}

interface FunnelChartProps {
    data: FunnelDataPoint[];
    currency?: Currency;
    height?: number;
    showPercentage?: boolean;
}

const FUNNEL_COLORS = [
    '#F97316', // Orange
    '#FB923C', // Light Orange
    '#FBBF24', // Amber
    '#22C55E', // Green
    '#3B82F6', // Blue
    '#8B5CF6', // Purple
];

export const FunnelChart: React.FC<FunnelChartProps> = ({
    data,
    currency,
    height = 300,
    showPercentage = true,
}) => {
    const maxValue = Math.max(...data.map(d => d.value));
    const totalSteps = data.length;

    return (
        <div style={{ height }} className="flex flex-col justify-center gap-2 px-4">
            {data.map((item, index) => {
                const widthPercent = (item.value / maxValue) * 100;
                const conversionRate = index > 0
                    ? ((item.value / data[index - 1].value) * 100).toFixed(1)
                    : '100';
                const color = item.color || FUNNEL_COLORS[index % FUNNEL_COLORS.length];

                return (
                    <motion.div
                        key={item.name}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="relative flex items-center gap-4"
                    >
                        {/* Stage Label */}
                        <div className="w-24 text-right">
                            <span className="text-sm font-medium text-gray-300 truncate">
                                {item.name}
                            </span>
                        </div>

                        {/* Funnel Bar */}
                        <div className="flex-1 relative">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${widthPercent}%` }}
                                transition={{ duration: 0.5, delay: index * 0.1 }}
                                className="h-10 rounded-r-lg relative overflow-hidden"
                                style={{
                                    backgroundColor: color,
                                    boxShadow: `0 4px 12px ${color}40`
                                }}
                            >
                                {/* Value inside bar */}
                                <div className="absolute inset-0 flex items-center justify-end pr-3">
                                    <span className="text-white font-semibold text-sm">
                                        {currency
                                            ? formatCompactCurrency(item.value, currency)
                                            : item.value.toLocaleString()
                                        }
                                    </span>
                                </div>
                            </motion.div>
                        </div>

                        {/* Conversion Rate */}
                        {showPercentage && index > 0 && (
                            <div className="w-16 text-right">
                                <span className={`text-xs font-medium ${parseFloat(conversionRate) >= 50 ? 'text-accent-green' : 'text-accent-amber'
                                    }`}>
                                    {conversionRate}%
                                </span>
                            </div>
                        )}
                    </motion.div>
                );
            })}
        </div>
    );
};

export default FunnelChart;
