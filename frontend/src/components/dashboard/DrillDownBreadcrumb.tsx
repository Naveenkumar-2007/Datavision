import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, Home, X, RotateCcw, Filter } from 'lucide-react';

/* ===================================================================
   DRILL-DOWN BREADCRUMB — Shows the drill-down path as user clicks
   chart data points. Each breadcrumb is a filter level.
   =================================================================== */

export interface DrillDownLevel {
    id: string;
    label: string;
    value: string;
    chartTitle: string;
    column?: string;
}

interface DrillDownBreadcrumbProps {
    levels: DrillDownLevel[];
    onNavigate: (index: number) => void;
    onClear: () => void;
    isDark: boolean;
    accentColor?: string;
}

export const DrillDownBreadcrumb: React.FC<DrillDownBreadcrumbProps> = ({
    levels,
    onNavigate,
    onClear,
    isDark,
    accentColor = '#818cf8'
}) => {
    if (levels.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -10, height: 0 }}
            className={`flex items-center gap-1 px-4 py-2.5 rounded-xl border mb-3 ${
                isDark
                    ? 'bg-indigo-500/5 border-indigo-500/20'
                    : 'bg-indigo-50/50 border-indigo-100'
            }`}
        >
            {/* Filter Icon */}
            <div className={`flex items-center gap-1.5 mr-2 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`}>
                <Filter className="w-3.5 h-3.5" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Drill-Down</span>
            </div>

            {/* Separator */}
            <div className={`h-4 w-px mx-1 ${isDark ? 'bg-indigo-500/20' : 'bg-indigo-200'}`} />

            {/* Home/Root */}
            <button
                onClick={() => onClear()}
                className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold transition-all ${
                    isDark
                        ? 'text-gray-400 hover:text-white hover:bg-white/5'
                        : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
            >
                <Home className="w-3 h-3" />
                <span>All Data</span>
            </button>

            {/* Breadcrumb Trail */}
            {levels.map((level, index) => (
                <React.Fragment key={level.id}>
                    <ChevronRight className={`w-3 h-3 ${isDark ? 'text-gray-600' : 'text-gray-300'}`} />
                    <motion.button
                        initial={{ opacity: 0, x: -5 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => onNavigate(index)}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-all ${
                            index === levels.length - 1
                                ? 'text-white'
                                : isDark
                                    ? 'text-gray-300 hover:bg-white/5'
                                    : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        style={index === levels.length - 1 ? { background: `${accentColor}30`, color: accentColor } : {}}
                    >
                        <span className={`text-[9px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                            {level.chartTitle}:
                        </span>
                        <span className="font-bold">{level.value}</span>
                    </motion.button>
                </React.Fragment>
            ))}

            {/* Clear All */}
            <div className="ml-auto flex items-center gap-1">
                <button
                    onClick={onClear}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold transition-all ${
                        isDark
                            ? 'text-red-400 hover:bg-red-500/10'
                            : 'text-red-500 hover:bg-red-50'
                    }`}
                >
                    <X className="w-3 h-3" />
                    <span>Clear</span>
                </button>
            </div>
        </motion.div>
    );
};

/* ===================================================================
   DRILL-DOWN INDICATOR — Small badge on charts that are drillable
   =================================================================== */
interface DrillDownIndicatorProps {
    isDark: boolean;
    level: number;
}

export const DrillDownIndicator: React.FC<DrillDownIndicatorProps> = ({ isDark, level }) => (
    <div className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[8px] font-bold ${
        isDark ? 'bg-indigo-500/20 text-indigo-400' : 'bg-indigo-100 text-indigo-600'
    }`}>
        <span>↘ Drill L{level}</span>
    </div>
);

export default DrillDownBreadcrumb;
