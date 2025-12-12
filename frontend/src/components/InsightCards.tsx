// InsightCards.tsx - Enterprise Automated Insights Display
import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    AlertTriangle,
    Lightbulb,
    Target,
    BarChart3,
    ArrowRight,
    AlertCircle
} from 'lucide-react';

interface Insight {
    type: 'trend' | 'risk' | 'opportunity' | 'anomaly' | 'performance' | 'recommendation';
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    metric?: string;
    value?: number;
    change_pct?: number;
    recommendation?: string;
    icon?: string;
}

interface InsightCardsProps {
    insights: Insight[];
    summary?: string;
    healthScore?: number;
    riskScore?: number;
    opportunityScore?: number;
    topPriority?: string;
}

// Type-specific icon mapping
const getTypeIcon = (type: string) => {
    switch (type) {
        case 'trend': return TrendingUp;
        case 'risk': return AlertTriangle;
        case 'opportunity': return Lightbulb;
        case 'anomaly': return AlertCircle;
        case 'performance': return BarChart3;
        case 'recommendation': return Target;
        default: return Lightbulb;
    }
};

// Type-specific styling
const getTypeStyle = (type: string) => {
    switch (type) {
        case 'trend': return { bg: 'from-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400' };
        case 'risk': return { bg: 'from-red-500/10', border: 'border-red-500/30', text: 'text-red-400' };
        case 'opportunity': return { bg: 'from-green-500/10', border: 'border-green-500/30', text: 'text-green-400' };
        case 'anomaly': return { bg: 'from-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400' };
        case 'performance': return { bg: 'from-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' };
        case 'recommendation': return { bg: 'from-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400' };
        default: return { bg: 'from-gray-500/10', border: 'border-gray-500/30', text: 'text-gray-400' };
    }
};

// Severity badge
const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
    const config = {
        low: { bg: 'bg-gray-500/20', text: 'text-gray-400' },
        medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
        high: { bg: 'bg-orange-500/20', text: 'text-orange-400' },
        critical: { bg: 'bg-red-500/20', text: 'text-red-400' }
    };

    const { bg, text } = config[severity as keyof typeof config] || config.medium;

    return (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${bg} ${text} capitalize`}>
            {severity}
        </span>
    );
};

// Health score gauge
const HealthGauge: React.FC<{ score: number; label: string }> = ({ score, label }) => {
    const getColor = () => {
        if (score >= 70) return 'text-green-400';
        if (score >= 40) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getBarColor = () => {
        if (score >= 70) return 'bg-green-500';
        if (score >= 40) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="flex-1 p-4 bg-dark-surface/50 rounded-xl border border-dark-border">
            <p className="text-xs text-gray-500 mb-2">{label}</p>
            <div className="flex items-center gap-3">
                <span className={`text-2xl font-bold ${getColor()}`}>{Math.round(score)}</span>
                <div className="flex-1 h-2 bg-dark-border rounded-full overflow-hidden">
                    <div
                        className={`h-full ${getBarColor()} transition-all duration-1000 ease-out`}
                        style={{ width: `${score}%` }}
                    />
                </div>
            </div>
        </div>
    );
};

// Individual insight card
const InsightCard: React.FC<{ insight: Insight; index: number }> = ({ insight, index }) => {
    const [isVisible, setIsVisible] = useState(false);
    const Icon = getTypeIcon(insight.type);
    const style = getTypeStyle(insight.type);

    useEffect(() => {
        setTimeout(() => setIsVisible(true), index * 100);
    }, [index]);

    return (
        <div
            className={`
        p-4 rounded-xl border transition-all duration-500
        bg-gradient-to-r ${style.bg} to-transparent
        ${style.border}
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}
        >
            <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${style.bg.replace('from-', 'bg-')}`}>
                    <Icon className={`w-4 h-4 ${style.text}`} />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                        <span className={`text-xs font-semibold uppercase ${style.text}`}>
                            {insight.type}
                        </span>
                        <SeverityBadge severity={insight.severity} />
                    </div>

                    <p className="text-sm text-gray-200">{insight.message}</p>

                    {insight.change_pct !== undefined && insight.change_pct !== null && (
                        <p className={`text-xs mt-1 ${insight.change_pct > 0 ? 'text-green-400' :
                            insight.change_pct < 0 ? 'text-red-400' : 'text-gray-500'
                            }`}>
                            {insight.change_pct > 0 ? '+' : ''}{insight.change_pct}% change
                        </p>
                    )}

                    {insight.recommendation && (
                        <div className="mt-2 flex items-center gap-2 text-xs text-gray-400 bg-dark-surface/50 rounded-lg px-3 py-2">
                            <ArrowRight className="w-3 h-3 text-orange-400" />
                            {insight.recommendation}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const InsightCards: React.FC<InsightCardsProps> = ({
    insights,
    summary = '',
    healthScore = 70,
    riskScore = 20,
    opportunityScore = 60,
    topPriority = ''
}) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setTimeout(() => setIsVisible(true), 100);
    }, []);

    // Group insights by type
    const risks = insights.filter(i => i.type === 'risk');
    const opportunities = insights.filter(i => i.type === 'opportunity');
    const trends = insights.filter(i => i.type === 'trend');
    const others = insights.filter(i => !['risk', 'opportunity', 'trend'].includes(i.type));

    return (
        <div
            className={`premium-card p-6 chart-fade-in transition-all duration-500 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-orange-400" />
                        Automated Insights
                    </h3>
                    {summary && (
                        <p className="text-sm text-gray-400 mt-1">{summary}</p>
                    )}
                </div>

                <div className="text-right">
                    <span className="text-2xl font-bold text-white">{insights.length}</span>
                    <span className="text-sm text-gray-500 ml-1">insights found</span>
                </div>
            </div>

            {/* Score Gauges */}
            <div className="grid grid-cols-3 gap-3 mb-6">
                <HealthGauge score={healthScore} label="Health Score" />
                <HealthGauge score={100 - riskScore} label="Risk Level" />
                <HealthGauge score={opportunityScore} label="Opportunity Score" />
            </div>

            {/* Top Priority Alert */}
            {topPriority && (
                <div className="mb-6 p-4 bg-orange-500/10 border border-orange-500/30 rounded-xl">
                    <div className="flex items-start gap-3">
                        <Target className="w-5 h-5 text-orange-400 mt-0.5" />
                        <div>
                            <p className="text-xs font-semibold text-orange-400 uppercase mb-1">
                                Top Priority
                            </p>
                            <p className="text-sm text-gray-200">{topPriority}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Insights Grid */}
            <div className="space-y-6">
                {/* Risks Section */}
                {risks.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-red-400 uppercase mb-3 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            Risks ({risks.length})
                        </h4>
                        <div className="space-y-3">
                            {risks.map((insight, i) => (
                                <InsightCard key={`risk-${i}`} insight={insight} index={i} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Opportunities Section */}
                {opportunities.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-green-400 uppercase mb-3 flex items-center gap-2">
                            <Lightbulb className="w-4 h-4" />
                            Opportunities ({opportunities.length})
                        </h4>
                        <div className="space-y-3">
                            {opportunities.map((insight, i) => (
                                <InsightCard key={`opp-${i}`} insight={insight} index={i} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Trends Section */}
                {trends.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-blue-400 uppercase mb-3 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            Trends ({trends.length})
                        </h4>
                        <div className="space-y-3">
                            {trends.map((insight, i) => (
                                <InsightCard key={`trend-${i}`} insight={insight} index={i} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Other Insights */}
                {others.length > 0 && (
                    <div>
                        <h4 className="text-xs font-semibold text-gray-400 uppercase mb-3 flex items-center gap-2">
                            <BarChart3 className="w-4 h-4" />
                            Other Insights ({others.length})
                        </h4>
                        <div className="space-y-3">
                            {others.map((insight, i) => (
                                <InsightCard key={`other-${i}`} insight={insight} index={i} />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InsightCards;
