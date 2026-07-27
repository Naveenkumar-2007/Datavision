import React, { Suspense, useCallback, useState, useEffect } from 'react';
import { Loader2, Settings, MessageSquare, Lightbulb, Maximize2 } from 'lucide-react';

const Plot = React.lazy(() => import('react-plotly.js'));

interface ChartData {
    chart_id: string;
    title: string;
    type: string;
    analysis?: string;
    plotly_config?: { data: any[]; layout: any };
}

interface DashboardWidgetProps {
    chart: ChartData;
    height: number;
    isDark: boolean;
    accentColor: string;
    overrideType?: string;
    explanation?: string;
    onExplain: (chart: ChartData) => void;
    explaining: boolean;
    onToggleExpand: () => void;
    isExpanded: boolean;
    onTypeOverride: (type: string) => void;
    onChatRequest: (title: string) => void;
    onFilter: (value: string) => void;
    isStreaming?: boolean; // New prop for real-time streaming
}

export const DashboardWidget = React.memo(({
    chart,
    height,
    isDark,
    accentColor,
    overrideType,
    explanation,
    onExplain,
    explaining,
    onToggleExpand,
    isExpanded,
    onTypeOverride,
    onChatRequest,
    onFilter,
    isStreaming = false
}: DashboardWidgetProps) => {
    const [activeDropdown, setActiveDropdown] = useState(false);
    
    // Simulate real-time pulsing effect for the data
    const [pulse, setPulse] = useState(false);

    useEffect(() => {
        if (isStreaming) {
            const interval = setInterval(() => {
                setPulse(p => !p);
            }, 2000);
            return () => clearInterval(interval);
        }
    }, [isStreaming]);

    const renderChart = useCallback(() => {
        if (!chart.plotly_config) return null;

        const plotlyConfig = {
            displayModeBar: false,
            responsive: true,
            staticPlot: false,
            scrollZoom: false,
            doubleClick: false as const,
            showTips: false
        };

        const chartData = chart.plotly_config.data.map(trace => ({
            ...trace,
            type: overrideType || trace.type
        }));

        const layout = {
            ...(chart.plotly_config.layout || {}),
            autosize: true,
            height,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: isDark ? '#e2e8f0' : '#334155',
                size: 9,
                family: 'Inter, sans-serif'
            },
            margin: { l: 30, r: 15, t: 30, b: 25 },
            xaxis: {
                ...(chart.plotly_config.layout?.xaxis || {}),
                gridcolor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.05)',
                color: isDark ? '#94a3b8' : '#64748b',
                zerolinecolor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.05)',
                fixedrange: true,
                tickangle: 0
            },
            yaxis: {
                ...(chart.plotly_config.layout?.yaxis || {}),
                gridcolor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.05)',
                color: isDark ? '#94a3b8' : '#64748b',
                zerolinecolor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.05)',
                fixedrange: true
            },
            legend: {
                orientation: 'h' as const,
                y: -0.2,
                font: { size: 9, color: isDark ? '#cbd5e1' : '#475569' }
            },
            dragmode: false as const,
            hovermode: 'closest' as const
        };

        return (
            <Suspense fallback={
                <div className="h-full flex items-center justify-center">
                    <Loader2 className="w-5 h-5 animate-spin" style={{ color: accentColor }} />
                </div>
            }>
                <div className={pulse ? 'opacity-80 transition-opacity duration-1000' : 'opacity-100 transition-opacity duration-1000'} style={{ width: '100%', height: '100%' }}>
                    <Plot
                        data={chartData as any}
                        layout={layout}
                        config={plotlyConfig}
                        style={{ width: '100%', height: '100%' }}
                        useResizeHandler={true}
                        onClick={(e: any) => {
                            if (e.points && e.points.length > 0) {
                                const pt = e.points[0];
                                const filterVal = pt.label || pt.x;
                                if (filterVal) onFilter(String(filterVal));
                            }
                        }}
                    />
                </div>
            </Suspense>
        );
    }, [chart, height, isDark, accentColor, overrideType, onFilter, pulse]);

    return (
        <div className={`overflow-visible h-full flex flex-col relative`}>
            {/* Chart Header */}
            <div className={`flex items-center justify-between px-3 py-2 border-b ${isDark ? 'border-gray-800 bg-gray-900/50 text-white' : 'border-gray-200 bg-gray-50/50 text-gray-900'} drag-handle cursor-move rounded-t-xl`}>
                <div className="flex items-center gap-2 min-w-0">
                    {isStreaming && (
                        <div className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </div>
                    )}
                    <h3 className="text-[11px] font-semibold truncate text-inherit">
                        {chart.title}
                    </h3>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => onExplain(chart)}
                        disabled={explaining}
                        className={`flex items-center gap-1 p-1 rounded transition-all text-[9px] font-semibold ${isDark ? 'hover:bg-indigo-500/20 text-indigo-400' : 'hover:bg-indigo-100 text-indigo-600'}`}
                        title="Generate AI Explanation"
                    >
                        {explaining ? <Loader2 className="w-3 h-3 animate-spin" /> : <Lightbulb className="w-3 h-3" />}
                    </button>
                    <button
                        onClick={onToggleExpand}
                        className={`p-1 rounded transition-all ${isDark ? 'hover:bg-white/5 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                    >
                        <Maximize2 className="w-3 h-3" />
                    </button>
                    
                    {/* Settings Dropdown */}
                    <div className="relative">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setActiveDropdown(!activeDropdown);
                            }}
                            className={`p-1 rounded transition-all ${isDark ? 'hover:bg-white/5 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                        >
                            <Settings className="w-3 h-3" />
                        </button>
                        
                        {activeDropdown && (
                            <div className={`absolute right-0 mt-1 w-32 rounded-lg shadow-xl border z-[60] overflow-hidden ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                                <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-b ${isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                    Chart Type
                                </div>
                                <div className="py-1 max-h-48 overflow-y-auto">
                                    {[
                                        { type: 'bar', icon: '📊', label: 'Bar' },
                                        { type: 'line', icon: '📈', label: 'Line' },
                                        { type: 'scatter', icon: '⚬', label: 'Scatter' },
                                        { type: 'pie', icon: '🥧', label: 'Pie' },
                                        { type: 'box', icon: '📦', label: 'Box Plot' },
                                        { type: 'violin', icon: '🎻', label: 'Violin' },
                                        { type: 'histogram', icon: '📶', label: 'Histogram' },
                                        { type: 'heatmap', icon: '🗺️', label: 'Heatmap' },
                                        { type: 'waterfall', icon: '🌊', label: 'Waterfall' },
                                        { type: 'funnel', icon: '🔻', label: 'Funnel' },
                                        { type: 'indicator', icon: '⏱️', label: 'Gauge' },
                                        { type: 'treemap', icon: '🌳', label: 'Treemap' },
                                        { type: 'sunburst', icon: '☀️', label: 'Sunburst' },
                                        { type: 'scatterpolar', icon: '🕸️', label: 'Radar' },
                                        { type: 'sankey', icon: '🔀', label: 'Sankey' },
                                        { type: 'scatter3d', icon: '🌐', label: '3D Scatter' },
                                        { type: 'surface', icon: '🏔️', label: '3D Surface' },
                                    ].map(({ type: tType, icon, label }) => (
                                        <button
                                            key={tType}
                                            onClick={() => {
                                                onTypeOverride(tType);
                                                setActiveDropdown(false);
                                            }}
                                            className={`w-full text-left px-3 py-1.5 text-[10px] flex items-center gap-2 hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors ${
                                                (overrideType || chart.plotly_config?.data?.[0]?.type) === tType 
                                                    ? 'bg-indigo-500/10 text-indigo-500 font-bold' 
                                                    : isDark ? 'text-gray-300' : 'text-gray-700'
                                            }`}
                                        >
                                            <span className="text-sm">{icon}</span>
                                            {label}
                                        </button>
                                    ))}
                                </div>
                                
                                <div className={`px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider border-y mt-1 ${isDark ? 'border-gray-700 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                    AI Actions
                                </div>
                                <div className="py-1">
                                    <button
                                        onClick={() => {
                                            setActiveDropdown(false);
                                            onChatRequest(chart.title);
                                        }}
                                        className={`w-full text-left px-3 py-1.5 text-[10px] flex items-center gap-2 hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors ${isDark ? 'text-gray-300' : 'text-gray-700'}`}
                                    >
                                        <MessageSquare className="w-3 h-3" />
                                        Chat about this
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            
            {/* AI Explanation Banner */}
            {explanation && (
                <div className={`px-3 py-2 text-xs border-b ${isDark ? 'bg-indigo-900/20 border-indigo-500/20 text-indigo-200' : 'bg-indigo-50/50 border-indigo-100 text-indigo-800'}`}>
                    <div className="flex items-start gap-2">
                        <Lightbulb className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                        <p className="leading-relaxed">{explanation}</p>
                    </div>
                </div>
            )}

            {/* Chart Content */}
            <div className={`px-1 pb-1 relative flex-1 h-full min-h-0 bg-transparent rounded-b-xl`}>
                {renderChart()}
            </div>
        </div>
    );
});
