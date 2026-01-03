/**
 * 🤖 ML Predictions - Real Machine Learning Results Page
 * 
 * Shows:
 * - Real matplotlib-generated charts
 * - Model comparison
 * - Feature importance
 * - Confusion matrix / Residual plots
 * - Make predictions
 */

import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Brain,
    TrendingUp,
    BarChart3,
    AlertTriangle,
    CheckCircle,
    ChevronRight,
    Target,
    Zap,
    ArrowLeft,
    RefreshCw,
    Sparkles,
    Award,
    Layers,
    PieChart,
    Activity,
    Play,
} from 'lucide-react';

interface ThemeContext {
    isDark: boolean;
    bgColor: string;
    cardBg: string;
    textPrimary: string;
    textMuted: string;
    borderColor: string;
}

interface FeatureMetadata {
    name: string;
    type: 'numeric' | 'categorical';
    min?: number;
    max?: number;
    mean?: number;
    options?: string[];
}

interface MLResult {
    success: boolean;
    task_type: string;
    target_column: string;
    best_model: {
        name: string;
        metrics: Record<string, number>;
    };
    all_models: Array<{
        name: string;
        metrics: Record<string, number>;
    }>;
    feature_importance: Array<{
        feature: string;
        importance: number;
        rank: number;
    }>;
    feature_metadata?: FeatureMetadata[];
    bias_reports: Array<{
        type: string;
        description: string;
        severity: string;
        corrected: boolean;
    }>;
    insights: string[];
    recommendations: string[];
    charts: Record<string, string>;  // base64 images
    data_summary: {
        rows: number;
        columns: number;
        features_engineered: number;
    };
    processing_time_seconds: number;
}

const MLPredictions: React.FC = () => {
    const theme = useOutletContext<ThemeContext>() || {
        isDark: true,
        bgColor: '#0F172A',
        cardBg: '#1E293B',
        textPrimary: '#F8FAFC',
        textMuted: '#94A3B8',
        borderColor: '#334155',
    };

    const navigate = useNavigate();
    const location = useLocation();

    const [result, setResult] = useState<MLResult | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'features' | 'predict'>('overview');
    const [predictionInput, setPredictionInput] = useState<Record<string, string>>({});
    const [predictionResult, setPredictionResult] = useState<any>(null);

    // Load result from location state or localStorage
    useEffect(() => {
        if (location.state?.automlResult) {
            setResult(location.state.automlResult);
        } else {
            const saved = localStorage.getItem('mlResults');
            if (saved) {
                try {
                    setResult(JSON.parse(saved));
                } catch (e) {
                    console.error('Failed to parse saved result:', e);
                }
            }
        }
    }, [location.state]);

    const getMetricColor = (value: number) => {
        if (value >= 0.9) return '#10b981';
        if (value >= 0.7) return '#f59e0b';
        return '#ef4444';
    };

    if (!result) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center p-12 rounded-3xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <Brain className="w-20 h-20 mx-auto mb-6" style={{ color: theme.textMuted }} />
                    <h2 className="text-2xl font-bold mb-3" style={{ color: theme.textPrimary }}>No ML Results Yet</h2>
                    <p className="mb-8 max-w-md" style={{ color: theme.textMuted }}>
                        Go to DataHub, upload a dataset, and click "🤖 Auto ML Train" to train ML models.
                    </p>
                    <button
                        onClick={() => navigate('/datahub')}
                        className="px-6 py-3 bg-gradient-to-r from-teal-500 to-emerald-500 rounded-xl text-white font-semibold hover:opacity-90 transition-opacity flex items-center gap-2 mx-auto"
                    >
                        <Zap className="w-5 h-5" />
                        Go to DataHub
                    </button>
                </motion.div>
            </div>
        );
    }

    const bestMetric = Object.entries(result.best_model.metrics)[0] || ['accuracy', 0];

    return (
        <div className="space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between"
            >
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/datahub')}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" style={{ color: theme.textMuted }} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-3" style={{ color: theme.textPrimary }}>
                            <Brain className="w-8 h-8 text-teal-400" />
                            ML Predictions
                        </h1>
                        <p className="text-sm" style={{ color: theme.textMuted }}>
                            Target: <span className="text-teal-400 font-medium">{result.target_column}</span>
                            {' • '}
                            Task: <span className="text-blue-400 font-medium">{result.task_type}</span>
                            {' • '}
                            <span className="text-amber-400 font-medium">{result.processing_time_seconds?.toFixed(1)}s</span>
                        </p>
                    </div>
                </div>
                <button
                    onClick={() => navigate('/datahub')}
                    className="px-4 py-2 rounded-xl border transition-colors flex items-center gap-2"
                    style={{ borderColor: theme.borderColor, color: theme.textMuted }}
                >
                    <RefreshCw className="w-4 h-4" />
                    New Training
                </button>
            </motion.div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-teal-500/20">
                            <Award className="w-5 h-5 text-teal-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Best Model</span>
                    </div>
                    <p className="text-2xl font-bold text-teal-400">{result.best_model.name}</p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Target className="w-5 h-5 text-blue-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>{bestMetric[0]?.toUpperCase()}</span>
                    </div>
                    <p className="text-2xl font-bold" style={{ color: getMetricColor(bestMetric[1] as number) }}>
                        {((bestMetric[1] as number) * 100).toFixed(1)}%
                    </p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-emerald-500/20">
                            <Layers className="w-5 h-5 text-emerald-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Models Trained</span>
                    </div>
                    <p className="text-2xl font-bold text-emerald-400">{result.all_models?.length || 0}</p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-amber-500/20">
                            <Sparkles className="w-5 h-5 text-amber-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Features</span>
                    </div>
                    <p className="text-2xl font-bold text-amber-400">{result.feature_importance?.length || 0}</p>
                </motion.div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 p-1 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                {[
                    { id: 'overview', label: 'Overview', icon: PieChart },
                    { id: 'charts', label: 'ML Charts', icon: BarChart3 },
                    { id: 'features', label: 'Features', icon: TrendingUp },
                    { id: 'predict', label: 'Make Prediction', icon: Play },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${activeTab === tab.id
                            ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                {activeTab === 'overview' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* All Models */}
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Activity className="w-5 h-5 text-blue-400" />
                                All Models Performance
                            </h3>
                            <div className="space-y-3">
                                {result.all_models?.slice(0, 8).map((model, i) => {
                                    const mainMetric = Object.values(model.metrics)[0] || 0;
                                    return (
                                        <div key={i} className="flex items-center gap-3">
                                            <span className="w-24 text-sm font-medium truncate" style={{ color: theme.textPrimary }}>
                                                {model.name}
                                            </span>
                                            <div className="flex-1 bg-gray-700 rounded-full h-3">
                                                <div
                                                    className={`h-3 rounded-full ${model.name === result.best_model.name ? 'bg-gradient-to-r from-teal-500 to-emerald-500' : 'bg-blue-500'}`}
                                                    style={{ width: `${mainMetric * 100}%` }}
                                                />
                                            </div>
                                            <span className="w-16 text-sm font-bold text-right" style={{ color: theme.textPrimary }}>
                                                {(mainMetric * 100).toFixed(1)}%
                                            </span>
                                            {model.name === result.best_model.name && (
                                                <span className="text-xs px-2 py-0.5 bg-teal-500 text-white rounded">BEST</span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Insights */}
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Sparkles className="w-5 h-5 text-amber-400" />
                                AI Insights
                            </h3>
                            <div className="space-y-3">
                                {result.insights?.slice(0, 5).map((insight, i) => (
                                    <div
                                        key={i}
                                        className="p-4 rounded-xl border-l-4 border-l-teal-500"
                                        style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                    >
                                        <p className="text-sm" style={{ color: theme.textPrimary }}>{insight}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'charts' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Real Charts from matplotlib */}
                        {result.charts && Object.entries(result.charts).map(([chartName, chartBase64]) => (
                            <div
                                key={chartName}
                                className="p-6 rounded-2xl border"
                                style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                            >
                                <h3 className="text-lg font-semibold mb-4 capitalize" style={{ color: theme.textPrimary }}>
                                    {chartName.replace(/_/g, ' ')}
                                </h3>
                                <img
                                    src={chartBase64}
                                    alt={chartName}
                                    className="w-full rounded-lg"
                                    style={{ maxHeight: '400px', objectFit: 'contain' }}
                                />
                            </div>
                        ))}

                        {(!result.charts || Object.keys(result.charts).length === 0) && (
                            <div className="col-span-2 text-center p-12" style={{ color: theme.textMuted }}>
                                <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                <p>No charts generated. Charts require matplotlib to be installed.</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'features' && (
                    <div
                        className="p-6 rounded-2xl border"
                        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                    >
                        <h3 className="text-lg font-semibold mb-6" style={{ color: theme.textPrimary }}>
                            Feature Importance Ranking
                        </h3>
                        <div className="space-y-3">
                            {result.feature_importance?.slice(0, 15).map((f, i) => (
                                <div
                                    key={i}
                                    className="flex items-center gap-4 p-3 rounded-xl"
                                    style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                >
                                    <span className="w-8 h-8 rounded-lg bg-gradient-to-r from-teal-500 to-emerald-500 flex items-center justify-center text-white font-bold">
                                        {f.rank || i + 1}
                                    </span>
                                    <div className="flex-1">
                                        <span className="font-medium" style={{ color: theme.textPrimary }}>{f.feature}</span>
                                        <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                                            <div
                                                className="h-2 rounded-full bg-gradient-to-r from-teal-500 to-emerald-500"
                                                style={{ width: `${f.importance * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                    <span className="font-bold text-teal-400">{(f.importance * 100).toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'predict' && (
                    <div
                        className="p-6 rounded-2xl border"
                        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                    >
                        <h3 className="text-lg font-semibold mb-6" style={{ color: theme.textPrimary }}>
                            Make a Prediction with {result.best_model.name}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                            {(result.feature_metadata || result.feature_importance?.slice(0, 9).map(f => ({
                                name: f.feature,
                                type: 'numeric' as const,
                                min: 0,
                                max: 100,
                                mean: 50
                            }))).slice(0, 9).map((meta) => {
                                const featureName = meta.name;
                                const isNumeric = meta.type === 'numeric';

                                return (
                                    <div key={featureName}>
                                        <label className="block text-sm font-medium mb-2" style={{ color: theme.textMuted }}>
                                            {featureName}
                                            <span className="ml-2 text-xs opacity-60">
                                                ({isNumeric ? 'numeric' : 'select'})
                                            </span>
                                        </label>

                                        {isNumeric ? (
                                            <input
                                                type="number"
                                                placeholder={meta.mean !== undefined ? `e.g. ${meta.mean.toFixed(1)}` : `Enter ${featureName}`}
                                                value={predictionInput[featureName] || ''}
                                                onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                min={meta.min}
                                                max={meta.max}
                                                step="any"
                                                className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-teal-500 transition-colors"
                                                style={{
                                                    backgroundColor: theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                    borderColor: theme.borderColor,
                                                    color: theme.textPrimary,
                                                }}
                                            />
                                        ) : (
                                            <select
                                                value={predictionInput[featureName] || ''}
                                                onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-teal-500 transition-colors cursor-pointer"
                                                style={{
                                                    backgroundColor: theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                    borderColor: theme.borderColor,
                                                    color: theme.textPrimary,
                                                }}
                                            >
                                                <option value="">Select {featureName}</option>
                                                {meta.options?.map((opt) => (
                                                    <option key={opt} value={opt}>{opt}</option>
                                                ))}
                                            </select>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    const response = await fetch('http://localhost:8000/api/v2/automl/predict', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                            user_id: localStorage.getItem('userId') || 'default',
                                            model_name: result.best_model.name,
                                            data: Object.fromEntries(
                                                Object.entries(predictionInput).map(([k, v]) => [k, parseFloat(v) || v])
                                            )
                                        })
                                    });
                                    const data = await response.json();
                                    setPredictionResult(data);
                                } catch (e: any) {
                                    alert(`Prediction failed: ${e.message}`);
                                }
                            }}
                            className="px-6 py-3 bg-gradient-to-r from-teal-500 to-emerald-500 rounded-xl text-white font-semibold hover:opacity-90 transition-opacity flex items-center gap-2"
                        >
                            <Play className="w-5 h-5" />
                            Get Prediction
                        </button>

                        {predictionResult && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mt-6 p-6 rounded-xl bg-gradient-to-r from-teal-500/20 to-emerald-500/20 border border-teal-500/30"
                            >
                                <h4 className="text-lg font-bold mb-2" style={{ color: theme.textPrimary }}>
                                    Prediction Result
                                </h4>
                                <p className="text-3xl font-bold text-teal-400">
                                    {predictionResult.prediction}
                                </p>
                                {predictionResult.probability && (
                                    <p className="text-sm mt-2" style={{ color: theme.textMuted }}>
                                        Confidence: {(Math.max(...predictionResult.probability) * 100).toFixed(1)}%
                                    </p>
                                )}
                            </motion.div>
                        )}
                    </div>
                )}
            </motion.div>

            {/* Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="p-4 rounded-xl flex items-center justify-between"
                style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
            >
                <div className="flex items-center gap-6 text-sm" style={{ color: theme.textMuted }}>
                    <span>📊 {result.data_summary?.rows?.toLocaleString() || 0} rows</span>
                    <span>📁 {result.data_summary?.columns || 0} columns</span>
                    <span>⚙️ {result.data_summary?.features_engineered || 0} features engineered</span>
                </div>
            </motion.div>
        </div>
    );
};

export default MLPredictions;
