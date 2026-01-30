/**
 * Drill Down Modal Component
 * Shows detailed data when user clicks on a chart element
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, TrendingDown, Package, Users } from 'lucide-react';
import { formatCurrency, formatCompactCurrency, Currency } from '@/utils/currency';

interface DrillDownData {
    title: string;
    type: 'product' | 'customer' | 'segment';
    mainValue: number;
    items: {
        name: string;
        value: number;
        percentage?: number;
        change?: number;
    }[];
}

interface DrillDownModalProps {
    isOpen: boolean;
    onClose: () => void;
    data: DrillDownData | null;
    currency: Currency;
}

export const DrillDownModal: React.FC<DrillDownModalProps> = ({
    isOpen,
    onClose,
    data,
    currency,
}) => {
    if (!data) return null;

    const getIcon = () => {
        switch (data.type) {
            case 'product': return <Package className="w-6 h-6 text-primary-400" />;
            case 'customer': return <Users className="w-6 h-6 text-accent-green" />;
            default: return <TrendingUp className="w-6 h-6 text-accent-amber" />;
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        onClick={onClose}
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="fixed inset-x-4 top-1/2 -translate-y-1/2 md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-full md:max-w-lg glass-card p-6 z-50 max-h-[80vh] overflow-y-auto"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                {getIcon()}
                                <div>
                                    <h2 className="text-xl font-semibold text-white">{data.title}</h2>
                                    <p className="text-sm text-gray-400">
                                        Total: {formatCurrency(data.mainValue, currency)}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        {/* Items */}
                        <div className="space-y-3">
                            {data.items.map((item, index) => (
                                <motion.div
                                    key={item.name}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="flex items-center justify-between p-3 rounded-xl bg-surface-700/30 hover:bg-surface-700/50 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center">
                                            <span className="text-sm font-bold text-primary-400">
                                                {index + 1}
                                            </span>
                                        </div>
                                        <div>
                                            <div className="text-white font-medium">{item.name}</div>
                                            {item.percentage !== undefined && (
                                                <div className="text-xs text-gray-400">
                                                    {item.percentage.toFixed(1)}% of total
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="text-right">
                                        <div className="text-white font-semibold">
                                            {formatCompactCurrency(item.value, currency)}
                                        </div>
                                        {item.change !== undefined && (
                                            <div className={`flex items-center justify-end text-xs ${item.change >= 0 ? 'text-accent-green' : 'text-accent-red'
                                                }`}>
                                                {item.change >= 0 ? (
                                                    <TrendingUp className="w-3 h-3 mr-1" />
                                                ) : (
                                                    <TrendingDown className="w-3 h-3 mr-1" />
                                                )}
                                                {Math.abs(item.change).toFixed(1)}%
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {/* Footer */}
                        <div className="mt-6 pt-4 border-t border-surface-700/50">
                            <button
                                onClick={onClose}
                                className="w-full py-3 bg-primary-500/20 hover:bg-primary-500/30 text-primary-400 font-medium rounded-xl transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default DrillDownModal;
