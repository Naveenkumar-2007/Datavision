/**
 * 🗄️ Model History Component
 * 
 * Displays all trained models for the current user with:
 * - Version history
 * - Metrics comparison
 * - Rollback functionality
 * - Delete options
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    History,
    Award,
    Clock,
    Target,
    TrendingUp,
    RotateCcw,
    Trash2,
    ChevronRight,
    CheckCircle,
    AlertCircle,
    Loader,
    Database,
    Download,
    RefreshCw,
} from 'lucide-react';

interface ModelMetadata {
    model_id: string;
    user_id: string;
    model_name: string;
    task_type: string;
    target_column: string;
    feature_columns: string[];
    metrics: Record<string, number>;
    training_date: string;
    dataset_info: {
        n_features: number;
        n_numeric: number;
        n_categorical: number;
        n_text: number;
        is_nlp_task: boolean;
    };
    version: number;
    is_active: boolean;
}

interface ModelHistoryProps {
    theme: {
        isDark: boolean;
        bgColor: string;
        cardBg: string;
        textPrimary: string;
        textMuted: string;
        borderColor: string;
    };
    userId?: string;
}

const ModelHistory: React.FC<ModelHistoryProps> = ({ theme, userId = 'default' }) => {
    const [models, setModels] = useState<ModelMetadata[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [rollingBack, setRollingBack] = useState<number | null>(null);
    const [deleting, setDeleting] = useState<number | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Fetch models on mount
    useEffect(() => {
        fetchModels();
    }, [userId]);

    const fetchModels = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/v2/autonomous/models/${userId}`);
            const data = await response.json();

            if (data.success) {
                setModels(data.models || []);
            } else {
                setError(data.message || 'Failed to load models');
            }
        } catch (err) {
            setError('Failed to connect to API');
            console.error('Fetch models error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRollback = async (version: number) => {
        setRollingBack(version);
        setSuccessMessage(null);
        try {
            const response = await fetch('/api/v2/autonomous/models/rollback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, version })
            });
            const data = await response.json();

            if (data.success) {
                setSuccessMessage(`Rolled back to version ${version}`);
                await fetchModels();
            } else {
                setError(data.detail || 'Rollback failed');
            }
        } catch (err) {
            setError('Rollback failed');
        } finally {
            setRollingBack(null);
        }
    };

    const handleDelete = async (version?: number) => {
        if (!confirm(version ? `Delete version ${version}?` : 'Delete all models?')) return;

        setDeleting(version || -1);
        try {
            const url = version
                ? `/api/v2/autonomous/models/${userId}/version/${version}`
                : `/api/v2/autonomous/models/${userId}`;

            const response = await fetch(url, { method: 'DELETE' });
            const data = await response.json();

            if (data.success) {
                setSuccessMessage(version ? `Deleted version ${version}` : 'All models deleted');
                await fetchModels();
            }
        } catch (err) {
            setError('Delete failed');
        } finally {
            setDeleting(null);
        }
    };

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    };

    const getMetricColor = (value: number) => {
        if (value >= 0.9) return '#10b981';
        if (value >= 0.7) return '#f59e0b';
        return '#ef4444';
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <Loader className="w-8 h-8 animate-spin text-emerald-400 mb-4" />
                <p style={{ color: theme.textMuted }}>Loading model history...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div
                className="p-6 rounded-2xl border bg-red-500/10 border-red-500/30 flex items-center gap-4"
            >
                <AlertCircle className="w-6 h-6 text-red-400" />
                <div>
                    <p className="font-medium text-red-400">Error loading models</p>
                    <p style={{ color: theme.textMuted }}>{error}</p>
                </div>
                <button
                    onClick={fetchModels}
                    className="ml-auto px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-xl text-red-400 transition-colors"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (models.length === 0) {
        return (
            <div
                className="p-12 rounded-2xl border text-center"
                style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
            >
                <Database className="w-16 h-16 mx-auto mb-4" style={{ color: theme.textMuted }} />
                <h3 className="text-xl font-semibold mb-2" style={{ color: theme.textPrimary }}>
                    No Trained Models
                </h3>
                <p style={{ color: theme.textMuted }}>
                    Train a model in DataHub to see your model history here.
                </p>
            </div>
        );
    }

    const activeModel = models.find(m => m.is_active);
    const historyModels = models.filter(m => !m.is_active);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-gradient-to-r from-emerald-500/20 to-teal-500/20">
                        <History className="w-6 h-6 text-emerald-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold" style={{ color: theme.textPrimary }}>
                            Model History
                        </h2>
                        <p className="text-sm" style={{ color: theme.textMuted }}>
                            {models.length} model version{models.length !== 1 ? 's' : ''} saved
                        </p>
                    </div>
                </div>
                <button
                    onClick={fetchModels}
                    className="p-2 rounded-xl hover:bg-white/10 transition-colors"
                    style={{ color: theme.textMuted }}
                >
                    <RefreshCw className="w-5 h-5" />
                </button>
            </div>

            {/* Success Message */}
            <AnimatePresence>
                {successMessage && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center gap-3"
                    >
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                        <span className="text-emerald-400">{successMessage}</span>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Active Model */}
            {activeModel && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-6 rounded-2xl border-2 border-emerald-500/50 bg-gradient-to-br from-emerald-500/10 to-teal-500/10"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="px-3 py-1 bg-emerald-500 text-white text-xs font-bold rounded-full">
                            ACTIVE
                        </div>
                        <span className="text-sm" style={{ color: theme.textMuted }}>
                            Version {activeModel.version}
                        </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm mb-1" style={{ color: theme.textMuted }}>Model</p>
                            <p className="font-bold text-emerald-400 text-lg">{activeModel.model_name}</p>
                        </div>
                        <div>
                            <p className="text-sm mb-1" style={{ color: theme.textMuted }}>Task</p>
                            <p className="font-medium" style={{ color: theme.textPrimary }}>{activeModel.task_type}</p>
                        </div>
                        <div>
                            <p className="text-sm mb-1" style={{ color: theme.textMuted }}>Target</p>
                            <p className="font-medium" style={{ color: theme.textPrimary }}>{activeModel.target_column}</p>
                        </div>
                        <div>
                            <p className="text-sm mb-1" style={{ color: theme.textMuted }}>Trained</p>
                            <p className="font-medium" style={{ color: theme.textPrimary }}>{formatDate(activeModel.training_date)}</p>
                        </div>
                    </div>

                    {/* Metrics */}
                    <div className="mt-4 pt-4 border-t border-emerald-500/20 flex flex-wrap gap-4">
                        {Object.entries(activeModel.metrics).slice(0, 4).map(([key, value]) => (
                            <div key={key} className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" style={{ color: getMetricColor(value) }} />
                                <span style={{ color: theme.textMuted }}>{key.toUpperCase()}:</span>
                                <span className="font-bold" style={{ color: getMetricColor(value) }}>
                                    {key === 'mae' || key === 'rmse' ? value.toFixed(3) : `${(value * 100).toFixed(1)}%`}
                                </span>
                            </div>
                        ))}
                    </div>
                </motion.div>
            )}

            {/* Version History */}
            {historyModels.length > 0 && (
                <div className="space-y-3">
                    <h3 className="font-semibold flex items-center gap-2" style={{ color: theme.textPrimary }}>
                        <Clock className="w-4 h-4" />
                        Previous Versions
                    </h3>

                    {historyModels.map((model, index) => (
                        <motion.div
                            key={model.model_id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="p-4 rounded-xl border flex items-center gap-4"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <div className="w-10 h-10 rounded-full bg-gray-500/20 flex items-center justify-center">
                                <span className="text-sm font-bold" style={{ color: theme.textMuted }}>
                                    v{model.version}
                                </span>
                            </div>

                            <div className="flex-1">
                                <p className="font-medium" style={{ color: theme.textPrimary }}>
                                    {model.model_name}
                                </p>
                                <p className="text-sm" style={{ color: theme.textMuted }}>
                                    {formatDate(model.training_date)}
                                </p>
                            </div>

                            {/* Metrics preview */}
                            <div className="hidden md:flex items-center gap-4">
                                {Object.entries(model.metrics).slice(0, 2).map(([key, value]) => (
                                    <span key={key} className="text-sm" style={{ color: theme.textMuted }}>
                                        {key}: <span style={{ color: getMetricColor(value) }}>{(value * 100).toFixed(1)}%</span>
                                    </span>
                                ))}
                            </div>

                            {/* Actions */}
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleRollback(model.version)}
                                    disabled={rollingBack === model.version}
                                    className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 transition-colors disabled:opacity-50"
                                    title="Rollback to this version"
                                >
                                    {rollingBack === model.version ? (
                                        <Loader className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <RotateCcw className="w-4 h-4" />
                                    )}
                                </button>
                                <button
                                    onClick={() => handleDelete(model.version)}
                                    disabled={deleting === model.version}
                                    className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors disabled:opacity-50"
                                    title="Delete this version"
                                >
                                    {deleting === model.version ? (
                                        <Loader className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Trash2 className="w-4 h-4" />
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Delete All */}
            {models.length > 1 && (
                <div className="pt-4 border-t" style={{ borderColor: theme.borderColor }}>
                    <button
                        onClick={() => handleDelete()}
                        disabled={deleting === -1}
                        className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50"
                    >
                        {deleting === -1 ? (
                            <Loader className="w-4 h-4 animate-spin" />
                        ) : (
                            <Trash2 className="w-4 h-4" />
                        )}
                        Delete All Models
                    </button>
                </div>
            )}
        </div>
    );
};

export default ModelHistory;
