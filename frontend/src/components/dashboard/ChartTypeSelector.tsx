import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, Search, ChevronDown } from 'lucide-react';

/* ===================================================================
   CHART TYPE SELECTOR — Visual grid for switching chart types
   Supports 20+ Plotly chart types with icons and categories
   =================================================================== */

export interface ChartTypeOption {
    id: string;
    name: string;
    icon: string; // Emoji icon for simplicity
    category: 'basic' | 'statistical' | 'finance' | 'scientific' | 'geo' | '3d';
    plotlyType: string;
    description: string;
}

export const CHART_TYPES: ChartTypeOption[] = [
    // Basic
    { id: 'bar', name: 'Bar', icon: '📊', category: 'basic', plotlyType: 'bar', description: 'Compare categories' },
    { id: 'line', name: 'Line', icon: '📈', category: 'basic', plotlyType: 'scatter', description: 'Trend over time' },
    { id: 'scatter', name: 'Scatter', icon: '⚬', category: 'basic', plotlyType: 'scatter', description: 'Correlations' },
    { id: 'pie', name: 'Pie', icon: '🥧', category: 'basic', plotlyType: 'pie', description: 'Proportions' },
    { id: 'area', name: 'Area', icon: '🏔️', category: 'basic', plotlyType: 'scatter', description: 'Volume trends' },
    { id: 'hbar', name: 'Horizontal Bar', icon: '📏', category: 'basic', plotlyType: 'bar', description: 'Horizontal compare' },
    { id: 'donut', name: 'Donut', icon: '🍩', category: 'basic', plotlyType: 'pie', description: 'Ring proportions' },
    
    // Statistical
    { id: 'box', name: 'Box Plot', icon: '📦', category: 'statistical', plotlyType: 'box', description: 'Distribution' },
    { id: 'violin', name: 'Violin', icon: '🎻', category: 'statistical', plotlyType: 'violin', description: 'Density shape' },
    { id: 'histogram', name: 'Histogram', icon: '📶', category: 'statistical', plotlyType: 'histogram', description: 'Frequency' },
    { id: 'heatmap', name: 'Heatmap', icon: '🗺️', category: 'statistical', plotlyType: 'heatmap', description: 'Matrix values' },
    
    // Finance
    { id: 'waterfall', name: 'Waterfall', icon: '🌊', category: 'finance', plotlyType: 'waterfall', description: 'Cumulative effect' },
    { id: 'funnel', name: 'Funnel', icon: '🔻', category: 'finance', plotlyType: 'funnel', description: 'Conversion stages' },
    { id: 'gauge', name: 'Gauge', icon: '⏱️', category: 'finance', plotlyType: 'indicator', description: 'KPI meter' },
    { id: 'candlestick', name: 'Candlestick', icon: '📊', category: 'finance', plotlyType: 'candlestick', description: 'OHLC data' },
    
    // Scientific
    { id: 'treemap', name: 'Treemap', icon: '🌳', category: 'scientific', plotlyType: 'treemap', description: 'Hierarchical data' },
    { id: 'sunburst', name: 'Sunburst', icon: '☀️', category: 'scientific', plotlyType: 'sunburst', description: 'Radial hierarchy' },
    { id: 'radar', name: 'Radar', icon: '🕸️', category: 'scientific', plotlyType: 'scatterpolar', description: 'Multi-axis compare' },
    { id: 'parallel', name: 'Parallel', icon: '≡', category: 'scientific', plotlyType: 'parcoords', description: 'Multi-dimensional' },
    { id: 'sankey', name: 'Sankey', icon: '🔀', category: 'scientific', plotlyType: 'sankey', description: 'Flow diagram' },
    
    // 3D
    { id: 'scatter3d', name: '3D Scatter', icon: '🌐', category: '3d', plotlyType: 'scatter3d', description: '3D correlations' },
    { id: 'surface3d', name: '3D Surface', icon: '🏔️', category: '3d', plotlyType: 'surface', description: '3D surface map' },
];

const CATEGORIES = [
    { id: 'all', name: 'All' },
    { id: 'basic', name: 'Basic' },
    { id: 'statistical', name: 'Statistical' },
    { id: 'finance', name: 'Finance' },
    { id: 'scientific', name: 'Scientific' },
    { id: '3d', name: '3D' },
];

interface ChartTypeSelectorProps {
    currentType: string;
    onTypeChange: (type: string, plotlyType: string) => void;
    isDark: boolean;
    isCompact?: boolean; // Use compact mode for widget dropdown
    onClose?: () => void;
}

export const ChartTypeSelector: React.FC<ChartTypeSelectorProps> = ({
    currentType,
    onTypeChange,
    isDark,
    isCompact = false,
    onClose
}) => {
    const [search, setSearch] = useState('');
    const [activeCategory, setActiveCategory] = useState('all');

    const filteredTypes = CHART_TYPES.filter(ct => {
        const matchesSearch = ct.name.toLowerCase().includes(search.toLowerCase()) ||
                              ct.description.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = activeCategory === 'all' || ct.category === activeCategory;
        return matchesSearch && matchesCategory;
    });

    if (isCompact) {
        return (
            <div className={`w-48 max-h-64 overflow-y-auto rounded-xl border shadow-xl ${
                isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
                <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-b ${
                    isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'
                }`}>
                    Chart Type
                </div>
                <div className="py-1">
                    {CHART_TYPES.slice(0, 12).map(ct => (
                        <button
                            key={ct.id}
                            onClick={() => { onTypeChange(ct.id, ct.plotlyType); onClose?.(); }}
                            className={`w-full text-left px-3 py-1.5 text-[10px] flex items-center gap-2 transition-colors ${
                                currentType === ct.id
                                    ? 'bg-indigo-500/10 text-indigo-500 font-bold'
                                    : isDark
                                        ? 'text-gray-300 hover:bg-indigo-500/10 hover:text-indigo-400'
                                        : 'text-gray-700 hover:bg-indigo-50 hover:text-indigo-600'
                            }`}
                        >
                            <span className="text-sm">{ct.icon}</span>
                            <span>{ct.name}</span>
                            {currentType === ct.id && <Check className="w-3 h-3 ml-auto" />}
                        </button>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`rounded-2xl border shadow-2xl overflow-hidden ${
                isDark ? 'bg-gray-900/95 border-gray-700/50 backdrop-blur-2xl' : 'bg-white/95 border-gray-200 backdrop-blur-2xl'
            }`}
        >
            {/* Header */}
            <div className={`px-4 py-3 border-b flex items-center justify-between ${
                isDark ? 'border-gray-700/50' : 'border-gray-200'
            }`}>
                <span className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    Chart Types
                </span>
                {onClose && (
                    <button onClick={onClose} className={`p-1 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10' : 'hover:bg-gray-100'}`}>
                        <X className="w-4 h-4" />
                    </button>
                )}
            </div>

            {/* Search */}
            <div className={`px-4 py-2 border-b ${isDark ? 'border-gray-700/50' : 'border-gray-200'}`}>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                    isDark ? 'bg-white/5' : 'bg-gray-100'
                }`}>
                    <Search className={`w-3.5 h-3.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                    <input
                        type="text"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        placeholder="Search charts..."
                        className={`bg-transparent text-xs outline-none flex-1 ${
                            isDark ? 'text-white placeholder:text-gray-500' : 'text-gray-900 placeholder:text-gray-400'
                        }`}
                    />
                </div>
            </div>

            {/* Category Tabs */}
            <div className={`px-3 py-2 flex gap-1 overflow-x-auto border-b ${isDark ? 'border-gray-700/50' : 'border-gray-200'}`}>
                {CATEGORIES.map(cat => (
                    <button
                        key={cat.id}
                        onClick={() => setActiveCategory(cat.id)}
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold whitespace-nowrap transition-colors ${
                            activeCategory === cat.id
                                ? 'bg-indigo-500/20 text-indigo-400'
                                : isDark
                                    ? 'text-gray-400 hover:bg-white/5'
                                    : 'text-gray-500 hover:bg-gray-100'
                        }`}
                    >
                        {cat.name}
                    </button>
                ))}
            </div>

            {/* Chart Grid */}
            <div className="p-3 grid grid-cols-4 gap-2 max-h-64 overflow-y-auto">
                {filteredTypes.map(ct => (
                    <motion.button
                        key={ct.id}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => { onTypeChange(ct.id, ct.plotlyType); onClose?.(); }}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl border transition-all ${
                            currentType === ct.id
                                ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500/30'
                                : isDark
                                    ? 'border-white/5 hover:border-white/20 hover:bg-white/5'
                                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                    >
                        <span className="text-lg">{ct.icon}</span>
                        <span className={`text-[9px] font-semibold ${
                            currentType === ct.id
                                ? 'text-indigo-400'
                                : isDark ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                            {ct.name}
                        </span>
                    </motion.button>
                ))}
            </div>

            {filteredTypes.length === 0 && (
                <div className={`p-4 text-center text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    No charts match your search
                </div>
            )}
        </motion.div>
    );
};

/* ===================================================================
   CHART TYPE DROPDOWN BUTTON
   Compact trigger that opens the selector
   =================================================================== */
interface ChartTypeDropdownProps {
    currentType: string;
    onTypeChange: (type: string, plotlyType: string) => void;
    isDark: boolean;
}

export const ChartTypeDropdown: React.FC<ChartTypeDropdownProps> = ({ currentType, onTypeChange, isDark }) => {
    const [isOpen, setIsOpen] = useState(false);
    const current = CHART_TYPES.find(ct => ct.id === currentType) || CHART_TYPES[0];

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-semibold transition-all border ${
                    isDark
                        ? 'bg-white/5 border-white/10 text-white hover:bg-white/10'
                        : 'bg-gray-100 border-gray-200 text-gray-700 hover:bg-gray-200'
                }`}
            >
                <span className="text-sm">{current.icon}</span>
                <span>{current.name}</span>
                <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
                        <motion.div
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -5 }}
                            className="absolute right-0 mt-1 z-50"
                        >
                            <ChartTypeSelector
                                currentType={currentType}
                                onTypeChange={(type, plotly) => { onTypeChange(type, plotly); setIsOpen(false); }}
                                isDark={isDark}
                                isCompact
                                onClose={() => setIsOpen(false)}
                            />
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ChartTypeSelector;
