/**
 * 🏥 Data Health Card - Shows data quality score before training
 * 
 * Features:
 * - Overall health score (0-100) with grade
 * - Issue count by severity
 * - Expandable recommendations list
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Activity,
    AlertTriangle,
    AlertCircle,
    CheckCircle,
    ChevronDown,
    ChevronUp,
    RefreshCw,
    Info
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { getUserIdSync } from '@/utils/userId';

interface HealthIssue {
    severity: string;
    category: string;
    column: string | null;
    description: string;
    recommendation: string;
}

interface HealthResponse {
    success: boolean;
    overall_score: number;
    grade: string;
    issues: HealthIssue[];
    recommendations: string[];
    metrics: Record<string, any>;
    column_scores: Record<string, number>;
}

interface DataHealthCardProps {
    fileName: string;
    targetColumn?: string;
    onHealthChecked?: (health: HealthResponse) => void;
}

const DataHealthCard: React.FC<DataHealthCardProps> = ({
    fileName,
    targetColumn,
    onHealthChecked
}) => {
    const { isDark } = useUserStore();
    const [loading, setLoading] = useState(false);
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState(false);

    // Check health when file changes - reset state first
    useEffect(() => {
        // Reset state when file changes
        setHealth(null);
        setError(null);
        setLoading(true);

        if (fileName) {
            checkHealth();
        } else {
            setLoading(false);
        }
    }, [fileName, targetColumn]);

    const checkHealth = async () => {
        try {
            setLoading(true);
            setError(null);

            const userId = getUserIdSync();
            const response = await fetch('/api/v1/automl/health', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_name: fileName,
                    target_column: targetColumn,
                    user_id: userId
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setHealth(data);
                onHealthChecked?.(data);
            } else {
                setError(data.detail || 'Health check failed');
            }
        } catch (err) {
            setError('Failed to check data health');
        } finally {
            setLoading(false);
        }
    };

    const getGradeColor = (grade: string) => {
        switch (grade) {
            case 'A': return '#10b981'; // Green
            case 'B': return '#22c55e'; // Light green
            case 'C': return '#f59e0b'; // Yellow
            case 'D': return '#f97316'; // Orange
            case 'F': return '#ef4444'; // Red
            default: return '#6b7280'; // Gray
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#f59e0b';
        return '#ef4444';
    };

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case 'critical': return <AlertCircle className="w-4 h-4 text-red-400" />;
            case 'warning': return <AlertTriangle className="w-4 h-4 text-amber-400" />;
            default: return <Info className="w-4 h-4 text-blue-400" />;
        }
    };

    if (loading) {
        return (
            <div
                className="p-4 rounded-xl border flex items-center gap-3"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
            >
                <RefreshCw className="w-5 h-5 animate-spin text-primary-400" />
                <span style={{ color: 'var(--text-muted)' }}>Analyzing data quality...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div
                className="p-4 rounded-xl border border-red-500/30"
                style={{ backgroundColor: isDark ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.05)' }}
            >
                <div className="flex items-center gap-2 text-red-400">
                    <AlertCircle className="w-5 h-5" />
                    <span>Health check failed: {error}</span>
                </div>
            </div>
        );
    }

    if (!health) return null;

    const criticalCount = health.issues.filter(i => i.severity === 'critical').length;
    const warningCount = health.issues.filter(i => i.severity === 'warning').length;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border overflow-hidden"
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
            {/* Header with Score */}
            <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl font-bold"
                        style={{
                            backgroundColor: `${getGradeColor(health.grade)}20`,
                            color: getGradeColor(health.grade)
                        }}
                    >
                        {health.grade}
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4" style={{ color: getScoreColor(health.overall_score) }} />
                            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                Data Health Score
                            </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <span
                                className="text-lg font-bold"
                                style={{ color: getScoreColor(health.overall_score) }}
                            >
                                {health.overall_score.toFixed(0)}/100
                            </span>
                            {criticalCount > 0 && (
                                <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400">
                                    {criticalCount} critical
                                </span>
                            )}
                            {warningCount > 0 && (
                                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-400">
                                    {warningCount} warnings
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <button
                    onClick={() => setExpanded(!expanded)}
                    className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                    style={{ color: 'var(--text-muted)' }}
                >
                    {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
            </div>

            {/* Progress Bar */}
            <div className="px-4 pb-4">
                <div
                    className="h-2 rounded-full overflow-hidden"
                    style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}
                >
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${health.overall_score}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="h-full rounded-full"
                        style={{
                            background: `linear-gradient(to right, ${getGradeColor(health.grade)}, ${getScoreColor(health.overall_score)})`
                        }}
                    />
                </div>
            </div>

            {/* Expandable Details */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t overflow-hidden"
                        style={{ borderColor: 'var(--border-color)' }}
                    >
                        <div className="p-4 space-y-4">
                            {/* Issues List */}
                            {health.issues.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                        Issues Found ({health.issues.length})
                                    </h4>
                                    <div className="space-y-2 max-h-40 overflow-y-auto">
                                        {health.issues.slice(0, 5).map((issue, i) => (
                                            <div
                                                key={i}
                                                className="flex items-start gap-2 p-2 rounded-lg"
                                                style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                            >
                                                {getSeverityIcon(issue.severity)}
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
                                                        {issue.description}
                                                    </p>
                                                    {issue.column && (
                                                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                                            Column: {issue.column}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommendations */}
                            {health.recommendations.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                        💡 Recommendations
                                    </h4>
                                    <ul className="space-y-1">
                                        {health.recommendations.slice(0, 3).map((rec, i) => (
                                            <li
                                                key={i}
                                                className="text-sm flex items-start gap-2"
                                                style={{ color: 'var(--text-muted)' }}
                                            >
                                                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                                                {rec}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default DataHealthCard;
