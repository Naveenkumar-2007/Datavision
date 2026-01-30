import React from 'react';
import { motion } from 'framer-motion';
import {
    TrendingUp, TrendingDown, Layout, ChevronRight, ChevronLeft, Info
} from 'lucide-react';
import {
    ResponsiveContainer, AreaChart, Area,
    PieChart, Pie, Cell, Tooltip, Treemap, BarChart, Bar
} from 'recharts';

// ============================================================================
// UTILS & SHARED
// ============================================================================

const formatValue = (v: number) => {
    if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`;
    if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
    return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
};

const formatPercent = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;

const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4'];

interface WidgetProps {
    data: any;
    theme?: any;
    config?: any;
}

// ============================================================================
// EXECUTIVE KPI CARD (Image 2 style)
// ============================================================================

export const ExecutiveKPICard: React.FC<WidgetProps> = ({ data }) => {
    const comp = data.comparison || { change_pct: 0, prev_value: 0, is_positive: true };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 rounded-xl border bg-[#0a192f]/50 backdrop-blur-md relative overflow-hidden group h-full"
            style={{ borderColor: 'rgba(45, 212, 191, 0.2)' }}
        >
            <div className="flex justify-between items-start relative z-10">
                <div>
                    <span className="text-[10px] font-bold text-green-400/80 uppercase tracking-widest">{data.title}</span>
                    <div className="flex items-baseline gap-2 mt-1">
                        <h2 className="text-2xl font-black text-white">{formatValue(data.value)}</h2>
                        <span className={`text-[10px] font-bold flex items-center gap-0.5 ${comp.is_positive ? 'text-green-400' : 'text-rose-400'}`}>
                            {comp.is_positive ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                            {formatPercent(comp.change_pct)}
                        </span>
                    </div>
                    <div className="mt-1 text-[9px] text-slate-400 font-medium">
                        PY: <span className="text-slate-300">{formatValue(comp.prev_value)}</span>
                    </div>
                </div>
                <Info className="w-3 h-3 text-slate-500 cursor-help" />
            </div>

            <div className="absolute inset-x-0 bottom-0 h-14 opacity-30 group-hover:opacity-60 transition-opacity">
                {data.sparkline && (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.sparkline}>
                            <defs>
                                <linearGradient id={`grad-${data.title}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <Area
                                type="monotone"
                                dataKey="y"
                                stroke="#2DD4BF"
                                fill={`url(#grad-${data.title})`}
                                strokeWidth={2}
                                isAnimationActive={true}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>
        </motion.div>
    );
};

// ============================================================================
// REGIONAL MATRIX (Image 2 style)
// ============================================================================

export const RegionalMatrix: React.FC<WidgetProps> = ({ data }) => {
    return (
        <div className="p-4 rounded-xl border bg-[#0a192f]/50 backdrop-blur-md h-full flex flex-col" style={{ borderColor: 'rgba(45, 212, 191, 0.1)' }}>
            <h4 className="text-[10px] font-bold text-green-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                <Layout className="w-3 h-3" />
                {data.title}
            </h4>
            <div className="flex-1 overflow-auto custom-scrollbar">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/5">
                            <th className="py-2 text-[10px] font-bold text-slate-400 uppercase">Region</th>
                            {data.columns?.map((col: string) => (
                                <th key={col} className="py-2 text-[10px] font-bold text-slate-400 uppercase text-right">{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {data.data.map((row: any, i: number) => (
                            <tr key={i} className="hover:bg-white/5 transition-colors group">
                                <td className="py-2.5 text-xs font-bold text-white group-hover:text-green-400">{row.dimension}</td>
                                {data.columns?.map((col: string) => (
                                    <td key={col} className="py-2.5 text-xs font-mono text-slate-300 text-right">{formatValue(row[col])}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// ============================================================================
// RANKING OVERVIEW PRO (Image 2 style)
// ============================================================================

export const RankingOverviewPro: React.FC<WidgetProps> = ({ data }) => {
    const [mode, setMode] = React.useState<'top' | 'bottom'>('top');
    const items = mode === 'top' ? data.top : data.bottom;

    return (
        <div className="p-4 rounded-xl border bg-[#0a192f]/50 backdrop-blur-md h-full flex flex-col" style={{ borderColor: 'rgba(244, 63, 94, 0.1)' }}>
            <div className="flex justify-between items-center mb-4">
                <h4 className="text-[10px] font-bold text-rose-400 uppercase tracking-widest">{data.title}</h4>
                <div className="flex bg-white/5 p-0.5 rounded-lg border border-white/5">
                    <button
                        onClick={() => setMode('top')}
                        className={`px-3 py-1 rounded-md text-[9px] font-bold uppercase transition-all ${mode === 'top' ? 'bg-rose-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
                    >Top</button>
                    <button
                        onClick={() => setMode('bottom')}
                        className={`px-3 py-1 rounded-md text-[9px] font-bold uppercase transition-all ${mode === 'bottom' ? 'bg-rose-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
                    >Bottom</button>
                </div>
            </div>

            <div className="space-y-4 flex-1 justify-center flex flex-col">
                {items?.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 group">
                        <span className="text-[10px] font-mono text-rose-400/50">{mode === 'top' ? `#${i + 1}` : `-${i + 1}`}</span>
                        <div className="flex-1">
                            <div className="flex justify-between items-end mb-1">
                                <span className="text-xs font-bold text-white truncate max-w-[120px]">{item.name}</span>
                                <span className="text-xs font-black text-rose-400">{formatValue(item.value)}</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${(item.value / items[0].value) * 100}%` }}
                                    className={`h-full ${mode === 'top' ? 'bg-rose-500' : 'bg-orange-500'}`}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ============================================================================
// MASTER PORTFOLIO TABLE (Image 1 style)
// ============================================================================

export const MasterPortfolioTable: React.FC<WidgetProps> = ({ data }) => {
    const rows = Array.isArray(data) ? data : (data?.data || []);

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden h-full flex flex-col">
            <div className="overflow-auto flex-1">
                <table className="w-full text-left">
                    <thead className="bg-slate-50 border-b border-slate-200 sticky top-0 z-10">
                        <tr>
                            <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Project Name</th>
                            <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Status</th>
                            <th className="px-4 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider text-right">Progress</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {rows.map((row: any, i: number) => {
                            const health = row.Health || (i % 3 === 0 ? 100 : (i % 2 === 0 ? 60 : 30));
                            const healthColor = health > 70 ? 'bg-emerald-500' : health > 40 ? 'bg-amber-500' : 'bg-rose-500';
                            const status = row.Status || (health > 70 ? 'Ready' : 'In Progress');

                            return (
                                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-4 py-3 text-sm font-semibold text-slate-800">{row.Project || row.dimension || 'Untitled'}</td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2.5 py-1 rounded-md text-[9px] font-black uppercase tracking-wider ${status === 'Ready' ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' :
                                                status === 'In Progress' ? 'bg-blue-50 text-blue-600 border border-blue-100' :
                                                    'bg-slate-50 text-slate-500 border border-slate-100'
                                            }`}>
                                            {status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-3">
                                            <div className="w-24 h-5 bg-slate-100 rounded-sm relative overflow-hidden ring-1 ring-slate-200">
                                                <div
                                                    className={`h-full ${healthColor}`}
                                                    style={{ width: `${health}%` }}
                                                />
                                            </div>
                                            <span className="text-[11px] font-black text-slate-700 w-8">{health}%</span>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-between items-center">
                <span className="text-[10px] text-slate-500 font-medium">Page 1 of 4</span>
                <div className="flex gap-2">
                    <button className="p-1 rounded bg-white border border-slate-200"><ChevronLeft className="w-3 h-3" /></button>
                    <button className="p-1 rounded bg-white border border-slate-200"><ChevronRight className="w-3 h-3" /></button>
                </div>
            </div>
        </div>
    );
};

// ============================================================================
// DONUT WIDGET (Image $ style - Light)
// ============================================================================

export const DonutWidget: React.FC<WidgetProps> = ({ data }) => {
    return (
        <div className="p-4 rounded-xl border h-full flex flex-col bg-white" style={{ borderColor: '#e2e8f0' }}>
            <h4 className="text-[10px] font-black uppercase mb-4 tracking-tighter text-slate-500">{data.title}</h4>
            <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data.data}
                            innerRadius={25}
                            outerRadius={40}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {data.data.map((_: any, index: number) => (
                                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{ backgroundColor: '#fff', border: 'none', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', fontSize: '10px' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

// ============================================================================
// TREEMAP
// ============================================================================

export const TreemapWidget: React.FC<WidgetProps> = ({ data }) => {
    return (
        <div className="p-4 rounded-xl border flex flex-col h-full bg-[#0a192f]/50 backdrop-blur-md" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">{data.title}</h4>
            <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                    <Treemap
                        data={data.data}
                        dataKey="value"
                        stroke="rgba(0,0,0,0.2)"
                        fill="#3B82F6"
                    >
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0a192f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '10px' }}
                        />
                    </Treemap>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

// ============================================================================
// PERFORMER SNAPSHOT
// ============================================================================

export const PerformerWidget: React.FC<WidgetProps> = ({ data }) => {
    if (!data.performance_snapshot || data.performance_snapshot.length === 0) return null;

    const snapshot = data.performance_snapshot[0];
    const { top, bottom, dimension, metric } = snapshot;

    return (
        <div className="p-4 rounded-xl border flex flex-col h-full bg-gradient-to-br from-[#0a192f] to-[#0d2a4a] shadow-xl" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
            <h4 className="text-[10px] font-bold text-green-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <TrendingUp className="w-3 h-3" />
                Performance Summary: {dimension}
            </h4>

            <div className="flex-1 flex flex-col justify-center gap-4">
                <div className="group relative">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-[8px] uppercase font-bold text-green-400">🏆 Top</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{top.name}</span>
                        <span className="text-xs font-black text-white">{formatValue(top.value)}</span>
                    </div>
                </div>

                <div className="group relative">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-[8px] uppercase font-bold text-rose-400">⚠️ Risk</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-slate-300">{bottom.name}</span>
                        <span className="text-xs font-bold text-slate-300">{formatValue(bottom.value)}</span>
                    </div>
                </div>
            </div>
            <div className="mt-2 text-[8px] italic text-slate-500">Analytics powered by AI</div>
        </div>
    );
};
