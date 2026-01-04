/**
 * 🤖 AutoML Dashboard - DataVision ML Results Page
 * 
 * Shows:
 * - Model comparison chart
 * - Feature importance visualization
 * - Bias detection reports
 * - Predictions with confidence
 * - AI-generated insights
 */

import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import Plot from 'react-plotly.js';
import {
    Brain,
    TrendingUp,
    BarChart3,
    AlertTriangle,
    CheckCircle,
    Loader,
    ChevronRight,
    Target,
    Zap,
    ArrowLeft,
    Download,
    RefreshCw,
    Sparkles,
    Info,
    XCircle,
    Award,
    Activity,
    PieChart,
    Layers,
} from 'lucide-react';

interface ThemeContext {
    isDark: boolean;
    bgColor: string;
    cardBg: string;
    textPrimary: string;
    textMuted: string;
    borderColor: string;
}

interface ModelResult {
    name: string;
    metrics: {
        f1?: number;
        accuracy?: number;
        precision?: number;
        recall?: number;
        auc?: number;
        r2?: number;
        mae?: number;
        rmse?: number;
    };
    training_time?: number;
}

interface FeatureImportance {
    feature: string;
    importance: number;
    rank: number;
    impact: string;
}

interface BiasReport {
    detected: boolean;
    type: string | null;
    description: string;
    severity: string;
    corrected: boolean;
}

interface ClusteringResult {
    algorithm: string;
    n_clusters: number;
    silhouette_score: number;
    cluster_distribution: Record<string, number>;
}

interface FeatureMetadata {
    name: string;
    type: 'numeric' | 'categorical' | 'text';
    sample_values?: (string | number)[];
    min?: number;
    max?: number;
    mean?: number;
}

interface AutoMLResult {
    success: boolean;
    task_type: string;
    target_column: string;
    best_model: {
        name: string;
        metrics: Record<string, number>;
    };
    all_models: ModelResult[];
    feature_importance: FeatureImportance[];
    feature_columns: string[];
    feature_metadata?: Record<string, FeatureMetadata>;
    bias_reports: BiasReport[];
    insights: string[];
    recommendations: string[];
    data_summary: {
        rows: number;
        columns: number;
        features_engineered: number;
        business_context?: string;
    };
    processing_time_seconds: number;
    api_endpoint: string | null;
    charts?: Record<string, any>;
    clustering?: ClusteringResult;
}

const AutoML: React.FC = () => {
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

    const [result, setResult] = useState<AutoMLResult | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'charts' | 'features' | 'clustering' | 'predictions' | 'insights'>('overview');

    // Prediction state
    const [predictionInputs, setPredictionInputs] = useState<Record<string, string>>({});
    const [predictionResult, setPredictionResult] = useState<{
        prediction: number | string;
        probability?: number;
        confidence?: number;
        model?: string;
    } | null>(null);
    const [isPredicting, setIsPredicting] = useState(false);
    const [predictionError, setPredictionError] = useState<string | null>(null);

    // Load result from location state or localStorage
    useEffect(() => {
        if (location.state?.automlResult) {
            setResult(location.state.automlResult);
        } else {
            // Try to load from localStorage
            const saved = localStorage.getItem('automlResult');
            if (saved) {
                try {
                    setResult(JSON.parse(saved));
                } catch (e) {
                    console.error('Failed to parse saved result:', e);
                }
            }
        }
    }, [location.state]);

    // Save result to localStorage when it changes
    useEffect(() => {
        if (result) {
            localStorage.setItem('automlResult', JSON.stringify(result));
        }
    }, [result]);

    const getBestMetric = () => {
        if (!result) return { key: 'f1', value: 0 };
        const metrics = result.best_model.metrics;
        const key = Object.keys(metrics)[0];
        return { key, value: metrics[key] || 0 };
    };

    const getMetricColor = (value: number) => {
        if (value >= 0.9) return '#10b981';
        if (value >= 0.7) return '#f59e0b';
        return '#ef4444';
    };

    // Handle prediction API call
    const handlePredict = async () => {
        if (!result) return;

        setIsPredicting(true);
        setPredictionError(null);
        setPredictionResult(null);

        try {
            // Convert string inputs to appropriate types
            const dataPayload: Record<string, any> = {};

            for (const [key, value] of Object.entries(predictionInputs)) {
                if (value === '' || value === undefined) continue;

                // Try to convert to number if it looks numeric
                const numValue = parseFloat(value);
                if (!isNaN(numValue)) {
                    dataPayload[key] = numValue;
                } else {
                    dataPayload[key] = value;
                }
            }

            console.log('🔮 Making prediction with:', dataPayload);

            const response = await fetch('/api/v2/automl/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: 'default',
                    model_name: result.best_model.name,
                    data: dataPayload
                })
            });

            const data = await response.json();

            if (data.success) {
                setPredictionResult({
                    prediction: data.prediction,
                    probability: data.probability,
                    confidence: data.confidence,
                    model: data.model
                });
            } else {
                setPredictionError(data.detail || 'Prediction failed');
            }
        } catch (error) {
            setPredictionError('Failed to connect to prediction API');
            console.error('Prediction error:', error);
        } finally {
            setIsPredicting(false);
        }
    };

    // Update input value
    const handleInputChange = (feature: string, value: string) => {
        setPredictionInputs(prev => ({
            ...prev,
            [feature]: value
        }));
    };

    // Model comparison chart data
    const getModelComparisonData = () => {
        if (!result) return null;

        const models = result.all_models.slice(0, 8);
        const metricKey = result.task_type === 'regression' ? 'r2' : 'f1';

        return {
            data: [{
                type: 'bar' as const,
                x: models.map(m => m.metrics[metricKey as keyof typeof m.metrics] || 0),
                y: models.map(m => m.name),
                orientation: 'h' as const,
                marker: {
                    color: models.map(m => m.name === result.best_model.name ? '#10b981' : '#3b82f6'),
                    line: { color: '#fff', width: 1 }
                },
                text: models.map(m => (m.metrics[metricKey as keyof typeof m.metrics] || 0).toFixed(3)),
                textposition: 'outside' as const,
            }],
            layout: {
                title: { text: `Model Comparison (${metricKey.toUpperCase()})`, font: { color: theme.textPrimary } },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: theme.textMuted },
                xaxis: {
                    gridcolor: theme.borderColor,
                    range: [0, 1.1],
                    title: metricKey.toUpperCase()
                },
                yaxis: { gridcolor: 'transparent', automargin: true },
                margin: { l: 120, r: 60, t: 50, b: 50 },
                height: 350,
            },
        };
    };

    // Feature importance chart
    const getFeatureImportanceData = () => {
        if (!result) return null;

        const features = result.feature_importance.slice(0, 10);

        return {
            data: [{
                type: 'bar' as const,
                x: features.map(f => f.importance * 100),
                y: features.map(f => f.feature),
                orientation: 'h' as const,
                marker: {
                    color: features.map((_, i) => {
                        const colors = ['#10b981', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#f97316', '#eab308'];
                        return colors[i % colors.length];
                    }),
                },
                text: features.map(f => `${(f.importance * 100).toFixed(1)}%`),
                textposition: 'outside' as const,
            }],
            layout: {
                title: { text: 'Feature Importance', font: { color: theme.textPrimary } },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: theme.textMuted },
                xaxis: {
                    gridcolor: theme.borderColor,
                    title: 'Impact (%)',
                    range: [0, Math.max(...features.map(f => f.importance * 100)) * 1.2]
                },
                yaxis: { gridcolor: 'transparent', automargin: true },
                margin: { l: 150, r: 60, t: 50, b: 50 },
                height: 400,
            },
        };
    };

    // Metrics radar chart
    const getMetricsRadarData = () => {
        if (!result || result.task_type === 'regression') return null;

        const metrics = result.best_model.metrics;
        const labels = ['Accuracy', 'Precision', 'Recall', 'F1 Score'];
        const values = [
            metrics.accuracy || 0,
            metrics.precision || 0,
            metrics.recall || 0,
            metrics.f1 || 0,
        ];

        return {
            data: [{
                type: 'scatterpolar' as const,
                r: [...values, values[0]],
                theta: [...labels, labels[0]],
                fill: 'toself' as const,
                fillcolor: 'rgba(16, 185, 129, 0.3)',
                line: { color: '#10b981', width: 2 },
                marker: { size: 8, color: '#10b981' },
            }],
            layout: {
                polar: {
                    radialaxis: {
                        visible: true,
                        range: [0, 1],
                        gridcolor: theme.borderColor,
                    },
                    angularaxis: {
                        gridcolor: theme.borderColor,
                    },
                    bgcolor: 'transparent',
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: theme.textMuted },
                showlegend: false,
                height: 350,
                margin: { l: 60, r: 60, t: 30, b: 30 },
            },
        };
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
                    <h2 className="text-2xl font-bold mb-3" style={{ color: theme.textPrimary }}>No AutoML Results</h2>
                    <p className="mb-8 max-w-md" style={{ color: theme.textMuted }}>
                        Upload a dataset in DataHub to automatically train ML models and view results here.
                    </p>
                    <button
                        onClick={() => navigate('/datahub')}
                        className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-xl text-white font-semibold hover:opacity-90 transition-opacity flex items-center gap-2 mx-auto"
                    >
                        <Zap className="w-5 h-5" />
                        Go to DataHub
                    </button>
                </motion.div>
            </div>
        );
    }

    const bestMetric = getBestMetric();
    const modelComparison = getModelComparisonData();
    const featureImportance = getFeatureImportanceData();
    const metricsRadar = getMetricsRadarData();

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
                            <Brain className="w-8 h-8 text-emerald-400" />
                            AutoML Results
                        </h1>
                        <p className="text-sm" style={{ color: theme.textMuted }}>
                            Target: <span className="text-emerald-400 font-medium">{result.target_column}</span>
                            {' • '}
                            Task: <span className="text-blue-400 font-medium">{result.task_type}</span>
                            {' • '}
                            Processed in <span className="text-amber-400 font-medium">{result.processing_time_seconds.toFixed(1)}s</span>
                        </p>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => navigate('/datahub')}
                        className="px-4 py-2 rounded-xl border transition-colors flex items-center gap-2"
                        style={{ borderColor: theme.borderColor, color: theme.textMuted }}
                    >
                        <RefreshCw className="w-4 h-4" />
                        New Analysis
                    </button>
                </div>
            </motion.div>

            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-emerald-500/20">
                            <Award className="w-5 h-5 text-emerald-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Best Model</span>
                    </div>
                    <p className="text-2xl font-bold text-emerald-400">{result.best_model.name}</p>
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
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>{bestMetric.key.toUpperCase()}</span>
                    </div>
                    <p className="text-2xl font-bold" style={{ color: getMetricColor(bestMetric.value) }}>
                        {(bestMetric.value * 100).toFixed(1)}%
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
                        <div className="p-2 rounded-lg bg-purple-500/20">
                            <Layers className="w-5 h-5 text-purple-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Models Tested</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-400">{result.all_models.length}</p>
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
                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Features Engineered</span>
                    </div>
                    <p className="text-2xl font-bold text-amber-400">{result.data_summary.features_engineered}</p>
                </motion.div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 p-1 rounded-xl overflow-x-auto" style={{ backgroundColor: theme.cardBg }}>
                {[
                    { id: 'overview', label: 'Overview', icon: PieChart },
                    { id: 'models', label: 'Model Comparison', icon: BarChart3 },
                    { id: 'charts', label: 'ML Charts', icon: Activity },
                    { id: 'features', label: 'Feature Importance', icon: TrendingUp },
                    { id: 'clustering', label: 'Clustering', icon: Layers },
                    { id: 'predictions', label: 'Predictions', icon: Target },
                    { id: 'insights', label: 'AI Insights', icon: Sparkles },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${activeTab === tab.id
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white'
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
                        {/* Best Model Metrics */}
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Award className="w-5 h-5 text-emerald-400" />
                                {result.best_model.name} Metrics
                            </h3>
                            {metricsRadar ? (
                                <Plot
                                    data={metricsRadar.data}
                                    layout={metricsRadar.layout as any}
                                    config={{ displayModeBar: false, responsive: true }}
                                    style={{ width: '100%' }}
                                />
                            ) : (
                                <div className="space-y-3">
                                    {Object.entries(result.best_model.metrics).map(([key, value]) => (
                                        <div key={key} className="flex items-center justify-between">
                                            <span className="font-medium" style={{ color: theme.textMuted }}>{key.toUpperCase()}</span>
                                            <span className="font-bold" style={{ color: getMetricColor(value as number) }}>
                                                {((value as number) * (key === 'mae' || key === 'rmse' ? 1 : 100)).toFixed(2)}
                                                {key !== 'mae' && key !== 'rmse' && '%'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Bias Detection */}
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <AlertTriangle className="w-5 h-5 text-amber-400" />
                                Bias Detection
                            </h3>
                            {result.bias_reports.length > 0 ? (
                                <div className="space-y-3">
                                    {result.bias_reports.map((bias, i) => (
                                        <div
                                            key={i}
                                            className="p-4 rounded-xl border"
                                            style={{
                                                borderColor: bias.corrected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)',
                                                backgroundColor: bias.corrected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)'
                                            }}
                                        >
                                            <div className="flex items-center gap-2 mb-2">
                                                {bias.corrected ? (
                                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                                ) : (
                                                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                                                )}
                                                <span className="font-medium" style={{ color: theme.textPrimary }}>
                                                    {bias.type || 'Unknown'}
                                                </span>
                                                <span className={`text-xs px-2 py-0.5 rounded ${bias.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                                                    bias.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                                                        'bg-green-500/20 text-green-400'
                                                    }`}>
                                                    {bias.severity}
                                                </span>
                                            </div>
                                            <p className="text-sm" style={{ color: theme.textMuted }}>{bias.description}</p>
                                            {bias.corrected && (
                                                <p className="text-sm text-emerald-400 mt-1">✓ Auto-corrected</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                    <CheckCircle className="w-6 h-6 text-emerald-400" />
                                    <span className="text-emerald-400 font-medium">No significant bias detected</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'models' && modelComparison && (
                    <div
                        className="p-6 rounded-2xl border"
                        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                    >
                        <Plot
                            data={modelComparison.data}
                            layout={modelComparison.layout as any}
                            config={{ displayModeBar: false, responsive: true }}
                            style={{ width: '100%' }}
                        />
                        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {result.all_models.slice(0, 6).map((model, i) => (
                                <div
                                    key={i}
                                    className={`p-4 rounded-xl border ${model.name === result.best_model.name ? 'border-emerald-500 bg-emerald-500/10' : ''}`}
                                    style={{ borderColor: model.name === result.best_model.name ? undefined : theme.borderColor }}
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium" style={{ color: theme.textPrimary }}>{model.name}</span>
                                        {model.name === result.best_model.name && (
                                            <span className="text-xs px-2 py-0.5 bg-emerald-500 text-white rounded">Best</span>
                                        )}
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                        {Object.entries(model.metrics).slice(0, 4).map(([key, val]) => (
                                            <div key={key}>
                                                <span style={{ color: theme.textMuted }}>{key}: </span>
                                                <span style={{ color: theme.textPrimary }}>{(val as number).toFixed(3)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ML Charts Tab - Production Visualizations */}
                {activeTab === 'charts' && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Activity className="w-5 h-5 text-blue-400" />
                                Production ML Visualizations
                                <span className="ml-2 px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs">
                                    {result.charts ? Object.keys(result.charts).length : 0} Charts
                                </span>
                            </h3>
                            <span className="px-3 py-1 rounded-full text-sm font-medium" style={{
                                backgroundColor: result.task_type.includes('classification') ? 'rgba(139, 92, 246, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                                color: result.task_type.includes('classification') ? '#a78bfa' : '#22c55e'
                            }}>
                                {result.task_type.includes('classification') ? '📊 Classification' : '📈 Regression'}
                            </span>
                        </div>

                        {result.charts && Object.keys(result.charts).length > 0 ? (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Render all charts as images */}
                                {Object.entries(result.charts).map(([chartKey, chartData]) => {
                                    // Skip if no data or not a valid base64 string
                                    if (!chartData || typeof chartData !== 'string') return null;

                                    // Get nice title for chart
                                    const chartTitles: Record<string, string> = {
                                        'confusion_matrix': '📊 Confusion Matrix',
                                        'class_distribution': '📈 Class Distribution',
                                        'classification_metrics': '📋 Classification Metrics',
                                        'prediction_accuracy_pie': '✅ Prediction Accuracy',
                                        'roc_curve': '📈 ROC Curve',
                                        'probability_histogram': '🎲 Confidence Distribution',
                                        'confidence_gauge': '🎯 Confidence Level',
                                        'actual_vs_predicted': '📉 Actual vs Predicted',
                                        'residual_plot': '📊 Residual Analysis',
                                        'error_histogram': '📊 Error Distribution',
                                        'prediction_error': '🎯 Prediction Error',
                                        'qq_plot': '📐 Q-Q Plot',
                                        'regression_metrics': '📋 Regression Metrics',
                                        'error_boxplot': '📦 Error Box Plot',
                                        'feature_importance': '🔑 Feature Importance',
                                        'model_comparison': '🏆 Model Comparison',
                                        'training_time': '⏱️ Training Time',
                                        'cluster_scatter': '🔮 Cluster Analysis',
                                    };

                                    const title = chartTitles[chartKey] || chartKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                                    return (
                                        <motion.div
                                            key={chartKey}
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="p-4 rounded-2xl border overflow-hidden"
                                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                                        >
                                            <h4 className="text-sm font-semibold mb-3" style={{ color: theme.textPrimary }}>
                                                {title}
                                            </h4>
                                            <img
                                                src={chartData}
                                                alt={title}
                                                className="w-full h-auto rounded-lg"
                                                style={{ maxHeight: '350px', objectFit: 'contain' }}
                                            />
                                        </motion.div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div
                                className="p-12 rounded-2xl border text-center"
                                style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                            >
                                <Activity className="w-16 h-16 mx-auto mb-4 text-gray-500" />
                                <h4 className="text-lg font-semibold mb-2" style={{ color: theme.textPrimary }}>
                                    No Charts Available
                                </h4>
                                <p style={{ color: theme.textMuted }}>
                                    Charts will appear here after training completes
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'features' && featureImportance && (
                    <div
                        className="p-6 rounded-2xl border"
                        style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                    >
                        <Plot
                            data={featureImportance.data}
                            layout={featureImportance.layout as any}
                            config={{ displayModeBar: false, responsive: true }}
                            style={{ width: '100%' }}
                        />
                        <div className="mt-6">
                            <h4 className="font-semibold mb-4" style={{ color: theme.textPrimary }}>Feature Details</h4>
                            <div className="space-y-2">
                                {result.feature_importance.slice(0, 10).map((f, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center gap-4 p-3 rounded-xl"
                                        style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                    >
                                        <span className="w-8 h-8 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold">
                                            {f.rank}
                                        </span>
                                        <div className="flex-1">
                                            <span className="font-medium" style={{ color: theme.textPrimary }}>{f.feature}</span>
                                            <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                                                <div
                                                    className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500"
                                                    style={{ width: `${f.importance * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                        <span className="font-bold text-emerald-400">{(f.importance * 100).toFixed(1)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Clustering Tab - Unsupervised Learning */}
                {activeTab === 'clustering' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div
                            className="p-6 rounded-2xl border bg-gradient-to-br from-purple-500/10 to-blue-500/10"
                            style={{ borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Layers className="w-5 h-5 text-purple-400" />
                                Unsupervised Learning
                                {result.clustering && (
                                    <span className="ml-auto px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs">✓ Complete</span>
                                )}
                            </h3>
                            <div className="space-y-4">
                                <div className="p-4 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Algorithm</span>
                                        <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-sm font-medium">
                                            {result.clustering?.algorithm?.toUpperCase() || 'K-Means'}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Clusters Found</span>
                                        <span className="text-emerald-400 font-bold text-xl">
                                            {result.clustering?.n_clusters || 'N/A'}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium" style={{ color: theme.textMuted }}>Silhouette Score</span>
                                        <span className="text-blue-400 font-bold">
                                            {result.clustering?.silhouette_score?.toFixed(3) || 'N/A'}
                                        </span>
                                    </div>
                                </div>

                                {/* Cluster Distribution */}
                                {result.clustering?.cluster_distribution && (
                                    <div className="p-4 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                                        <h4 className="text-sm font-medium mb-3" style={{ color: theme.textPrimary }}>Cluster Distribution</h4>
                                        <div className="space-y-2">
                                            {Object.entries(result.clustering.cluster_distribution).map(([cluster, count]) => (
                                                <div key={cluster} className="flex items-center gap-3">
                                                    <span className="text-sm" style={{ color: theme.textMuted }}>{cluster}</span>
                                                    <div className="flex-1 bg-gray-700 rounded-full h-2">
                                                        <div
                                                            className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-blue-500"
                                                            style={{ width: `${(count as number / result.data_summary.rows) * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-sm font-medium text-purple-400">{count as number}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <p className="text-sm" style={{ color: theme.textMuted }}>
                                    {result.clustering
                                        ? `✅ Automatically identified ${result.clustering.n_clusters} distinct segments in your data.`
                                        : 'Clustering analysis groups similar data points together.'}
                                </p>
                            </div>
                        </div>

                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Activity className="w-5 h-5 text-blue-400" />
                                Cluster Visualization
                            </h3>
                            {result.charts?.cluster_scatter ? (
                                <Plot
                                    data={result.charts.cluster_scatter.data}
                                    layout={{
                                        ...result.charts.cluster_scatter.layout,
                                        paper_bgcolor: 'rgba(0,0,0,0)',
                                        plot_bgcolor: 'rgba(0,0,0,0)',
                                    } as any}
                                    config={{ displayModeBar: false, responsive: true }}
                                    style={{ width: '100%', height: '300px' }}
                                />
                            ) : (
                                <div className="h-64 flex items-center justify-center rounded-xl" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                    <div className="text-center">
                                        <Layers className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                                        <p style={{ color: theme.textMuted }}>Cluster visualization will appear here</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Predictions Tab - Production-Level Interactive Prediction */}
                {activeTab === 'predictions' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Prediction Form */}
                        <div
                            className="p-6 rounded-2xl border bg-gradient-to-br from-emerald-500/10 to-teal-500/10"
                            style={{ borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Target className="w-5 h-5 text-emerald-400" />
                                Make Prediction
                                <span className="ml-auto px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs">
                                    {result.best_model.name}
                                </span>
                            </h3>
                            <div className="space-y-4">
                                <p className="text-sm" style={{ color: theme.textMuted }}>
                                    Enter feature values to predict <span className="text-emerald-400 font-medium">{result.target_column}</span>
                                </p>

                                {/* Feature Inputs - Use feature_columns for ALL features */}
                                <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                                    {(result.feature_columns || result.feature_importance.map(f => f.feature)).map((feature, i) => {
                                        const importance = result.feature_importance.find(f => f.feature === feature);
                                        const isImportant = importance && importance.rank <= 3;

                                        return (
                                            <div key={i}>
                                                <label className="text-sm font-medium mb-1 flex items-center gap-2" style={{ color: theme.textMuted }}>
                                                    {feature}
                                                    {isImportant && (
                                                        <span className="px-1.5 py-0.5 text-xs rounded bg-amber-500/20 text-amber-400">
                                                            Top Feature
                                                        </span>
                                                    )}
                                                </label>
                                                <input
                                                    type="text"
                                                    value={predictionInputs[feature] || ''}
                                                    onChange={(e) => handleInputChange(feature, e.target.value)}
                                                    placeholder={`Enter ${feature}...`}
                                                    className="w-full px-4 py-2.5 rounded-xl border bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition"
                                                    style={{ borderColor: theme.borderColor, color: theme.textPrimary }}
                                                />
                                            </div>
                                        );
                                    })}
                                </div>

                                {/* Prediction Error */}
                                {predictionError && (
                                    <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                                        ⚠️ {predictionError}
                                    </div>
                                )}

                                {/* Predict Button */}
                                <button
                                    onClick={handlePredict}
                                    disabled={isPredicting || Object.keys(predictionInputs).length === 0}
                                    className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold hover:opacity-90 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isPredicting ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            Predicting...
                                        </>
                                    ) : (
                                        <>
                                            <Zap className="w-4 h-4" />
                                            Generate Prediction
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Prediction Result Panel */}
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Activity className="w-5 h-5 text-blue-400" />
                                Prediction Result
                            </h3>

                            {predictionResult ? (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="space-y-6"
                                >
                                    {/* Main Prediction */}
                                    <div className="p-6 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 text-center">
                                        <p className="text-sm mb-2" style={{ color: theme.textMuted }}>
                                            Predicted {result.target_column}
                                        </p>
                                        <p className="text-4xl font-bold text-emerald-400">
                                            {typeof predictionResult.prediction === 'number'
                                                ? predictionResult.prediction.toFixed(2)
                                                : predictionResult.prediction}
                                        </p>
                                    </div>

                                    {/* Confidence/Probability */}
                                    {predictionResult.probability !== undefined && (
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm" style={{ color: theme.textMuted }}>Confidence</span>
                                                <span className="font-bold" style={{ color: getMetricColor(predictionResult.probability) }}>
                                                    {(predictionResult.probability * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                            <div className="w-full bg-gray-700 rounded-full h-3">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${predictionResult.probability * 100}%` }}
                                                    className="h-3 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {/* Model Info */}
                                    <div className="p-3 rounded-xl" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                        <p className="text-xs" style={{ color: theme.textMuted }}>
                                            Model: <span className="text-blue-400">{predictionResult.model || result.best_model.name}</span>
                                        </p>
                                    </div>
                                </motion.div>
                            ) : (
                                <div className="h-64 flex items-center justify-center rounded-xl" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                    <div className="text-center">
                                        <Target className="w-12 h-12 mx-auto mb-3 text-gray-500" />
                                        <p style={{ color: theme.textMuted }}>Enter values and click predict</p>
                                        <p className="text-sm mt-1" style={{ color: theme.textMuted }}>to see the result here</p>
                                    </div>
                                </div>
                            )}

                            {/* Quick Stats */}
                            <div className="mt-6 grid grid-cols-2 gap-3">
                                <div className="p-3 rounded-xl text-center" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                    <p className="text-xs" style={{ color: theme.textMuted }}>Task Type</p>
                                    <p className="font-semibold text-sm mt-1" style={{ color: theme.textPrimary }}>
                                        {result.task_type.includes('classification') ? '📊 Classification' : '📈 Regression'}
                                    </p>
                                </div>
                                <div className="p-3 rounded-xl text-center" style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                    <p className="text-xs" style={{ color: theme.textMuted }}>Model Score</p>
                                    <p className="font-semibold text-sm mt-1" style={{ color: getMetricColor(getBestMetric().value) }}>
                                        {(getBestMetric().value * 100).toFixed(1)}%
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'insights' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                                {result.insights.map((insight, i) => (
                                    <div
                                        key={i}
                                        className="p-4 rounded-xl border-l-4 border-l-emerald-500"
                                        style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                    >
                                        <p style={{ color: theme.textPrimary }}>{insight}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Recommendations */}
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <TrendingUp className="w-5 h-5 text-blue-400" />
                                Recommendations
                            </h3>
                            <div className="space-y-3">
                                {result.recommendations.map((rec, i) => (
                                    <div
                                        key={i}
                                        className="flex items-start gap-3 p-4 rounded-xl"
                                        style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                    >
                                        <div className="p-1.5 rounded-lg bg-blue-500/20">
                                            <ChevronRight className="w-4 h-4 text-blue-400" />
                                        </div>
                                        <p style={{ color: theme.textPrimary }}>{rec}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* API Endpoint */}
                        {result.api_endpoint && (
                            <div
                                className="lg:col-span-2 p-6 rounded-2xl border bg-gradient-to-r from-emerald-500/10 to-teal-500/10"
                                style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}
                            >
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                    <Zap className="w-5 h-5 text-emerald-400" />
                                    Deployed API Endpoint
                                </h3>
                                <div className="flex items-center gap-4">
                                    <code className="flex-1 p-4 rounded-xl bg-black/30 text-emerald-400 font-mono">
                                        POST {result.api_endpoint}
                                    </code>
                                    <button
                                        className="px-4 py-3 bg-emerald-500 rounded-xl text-white font-medium hover:bg-emerald-600 transition-colors"
                                        onClick={() => {
                                            navigator.clipboard.writeText(`${window.location.origin}${result.api_endpoint}`);
                                            alert('Copied to clipboard!');
                                        }}
                                    >
                                        Copy URL
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </motion.div>

            {/* Data Summary Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="p-4 rounded-xl flex items-center justify-between"
                style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
            >
                <div className="flex items-center gap-6 text-sm" style={{ color: theme.textMuted }}>
                    <span>📊 {result.data_summary.rows.toLocaleString()} rows</span>
                    <span>📁 {result.data_summary.columns} columns</span>
                    <span>⚙️ {result.data_summary.features_engineered} features engineered</span>
                </div>
                {result.data_summary.business_context && (
                    <p className="text-sm max-w-lg truncate" style={{ color: theme.textMuted }}>
                        {result.data_summary.business_context}
                    </p>
                )}
            </motion.div>
        </div>
    );
};

export default AutoML;
