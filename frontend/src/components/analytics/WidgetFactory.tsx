import {
    ExecutiveKPICard,
    DonutWidget,
    RegionalMatrix,
    RankingOverviewPro,
    MasterPortfolioTable,
    TreemapWidget,
    PerformerWidget
} from './VisualWidgets';
import {
    BarChart, Bar, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

interface WidgetFactoryProps {
    analysis: any;
    theme: any;
}

const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4'];

export const WidgetFactory: React.FC<WidgetFactoryProps> = ({ analysis, theme }) => {
    const { chart_type, widget_size, title, data } = analysis;

    // CSS class for widget size
    const getSizeClass = () => {
        switch (widget_size) {
            case 'small': return 'col-span-12 sm:col-span-6 lg:col-span-3 h-32';
            case 'medium': return 'col-span-12 sm:col-span-6 lg:col-span-4 h-80';
            case 'large': return 'col-span-12 lg:col-span-8 h-80';
            case 'full': return 'col-span-12 h-[32rem]';
            default: return 'col-span-12 sm:col-span-6 lg:col-span-4 h-64';
        }
    };

    const renderWidget = () => {
        if (!data || data.length === 0) {
            return (
                <div className="flex items-center justify-center p-4 border rounded-2xl h-full opacity-50" style={{ borderColor: theme.borderColor }}>
                    <span className="text-[10px]" style={{ color: theme.textMuted }}>No data for {title}</span>
                </div>
            );
        }

        switch (chart_type) {
            case 'executive_kpi':
            case 'kpi':
                return <ExecutiveKPICard data={analysis} theme={theme} />;
            case 'donut':
            case 'donut_group':
                return <DonutWidget data={analysis} theme={theme} />;
            case 'ranking':
            case 'ranking_pro':
                return <RankingOverviewPro data={analysis} theme={theme} />;
            case 'matrix':
                return <RegionalMatrix data={analysis} theme={theme} />;
            case 'master_table':
                return <MasterPortfolioTable data={analysis} theme={theme} />;
            case 'performer':
                return <PerformerWidget data={analysis} theme={theme} />;
            case 'treemap':
                return <TreemapWidget data={analysis} theme={theme} />;

            case 'bar':
                return (
                    <div className="p-4 rounded-2xl border h-full" style={{ borderColor: theme.borderColor }}>
                        <h4 className="text-[11px] font-bold uppercase mb-4" style={{ color: theme.textMuted }}>{title}</h4>
                        <ResponsiveContainer width="100%" height="90%">
                            <BarChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} vertical={false} opacity={0.5} />
                                <XAxis dataKey="category" hide />
                                <YAxis hide />
                                <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, fontSize: '10px' }} />
                                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                    {data.map((_: any, i: number) => (
                                        <Cell key={`cell-${i}`} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                );

            case 'line':
            case 'area':
                return (
                    <div className="p-4 rounded-2xl border h-full" style={{ borderColor: theme.borderColor }}>
                        <h4 className="text-[11px] font-bold uppercase mb-4" style={{ color: theme.textMuted }}>{title}</h4>
                        <ResponsiveContainer width="100%" height="90%">
                            <AreaChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke={theme.borderColor} vertical={false} opacity={0.5} />
                                <XAxis dataKey="x" hide />
                                <YAxis hide />
                                <Tooltip contentStyle={{ backgroundColor: theme.cardBg, border: `1px solid ${theme.borderColor}`, fontSize: '10px' }} />
                                <Area
                                    type="monotone"
                                    dataKey="y"
                                    stroke={CHART_COLORS[0]}
                                    fill={CHART_COLORS[0]}
                                    fillOpacity={0.1}
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                );

            default:
                return (
                    <div className="p-4 border rounded-2xl h-full flex items-center justify-center" style={{ borderColor: theme.borderColor }}>
                        <span className="text-xs" style={{ color: theme.textMuted }}>Widget: {chart_type}</span>
                    </div>
                );
        }
    };

    return (
        <div className={getSizeClass()}>
            {renderWidget()}
        </div>
    );
};
