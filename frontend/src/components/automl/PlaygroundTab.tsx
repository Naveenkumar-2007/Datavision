/**
 * 🎮 Playground Tab - Interactive Prediction with Sliders
 * 
 * Features:
 * - Sliders for numeric features
 * - Dropdowns for categorical features
 * - Real-time prediction updates
 * - Confidence display
 * - SHAP explanation button
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Sliders, RefreshCw, Sparkles, AlertCircle, Activity, ChevronDown, HelpCircle } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import debounce from 'lodash/debounce';
import ExplainModal from './ExplainModal';

interface SliderConfig {
    name: string;
    type: 'numeric' | 'categorical';
    min?: number;
    max?: number;
    step?: number;
    default?: any;
    options?: string[];
}

interface PlaygroundConfig {
    model_name: string;
    task_type: string;
    target_column: string;
    sliders: SliderConfig[];
    class_names?: string[];
}

interface PlaygroundProps {
    onPredictionMade?: (prediction: any) => void;
}

const PlaygroundTab: React.FC<PlaygroundProps> = ({ onPredictionMade }) => {
    const { isDark } = useUserStore();
    const [config, setConfig] = useState<PlaygroundConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [values, setValues] = useState<Record<string, any>>({});
    const [prediction, setPrediction] = useState<any>(null);
    const [predicting, setPredicting] = useState(false);
    const [confidence, setConfidence] = useState<number | null>(null);
    const [showExplainModal, setShowExplainModal] = useState(false);

    // Load playground config
    useEffect(() => {
        const loadConfig = async () => {
            try {
                setLoading(true);
                const userId = localStorage.getItem('userId') || 'default';
                const response = await fetch(`/api/v1/automl/playground/config?user_id=${userId}`);
                const data = await response.json();

                if (response.ok) {
                    setConfig(data);
                    // Initialize values with defaults
                    const initialValues: Record<string, any> = {};
                    data.sliders.forEach((slider: SliderConfig) => {
                        initialValues[slider.name] = slider.default ??
                            (slider.type === 'numeric' ? slider.min : slider.options?.[0]);
                    });
                    setValues(initialValues);
                    setError(null);
                } else {
                    setError(data.detail || 'Failed to load playground');
                }
            } catch (err) {
                setError('Failed to connect to server');
            } finally {
                setLoading(false);
            }
        };
        loadConfig();
    }, []);

    // Debounced prediction
    const debouncedPredict = useCallback(
        debounce(async (vals: Record<string, any>) => {
            try {
                setPredicting(true);
                const userId = localStorage.getItem('userId') || 'default';
                const response = await fetch('/api/v1/automl/playground/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ values: vals, user_id: userId })
                });
                const data = await response.json();

                if (data.success) {
                    setPrediction(data.prediction_label || data.prediction);
                    setConfidence(data.confidence);
                    onPredictionMade?.(data);
                }
            } catch (err) {
                console.error('Prediction error:', err);
            } finally {
                setPredicting(false);
            }
        }, 300),
        []
    );

    // Handle value change
    const handleValueChange = (name: string, value: any) => {
        const newValues = { ...values, [name]: value };
        setValues(newValues);
        debouncedPredict(newValues);
    };

    // Manual predict
    const handlePredict = async () => {
        debouncedPredict.cancel();
        debouncedPredict(values);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <RefreshCw className="w-8 h-8 animate-spin text-primary-400" />
                <span className="ml-3 text-lg" style={{ color: 'var(--text-muted)' }}>Loading Playground...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-16">
                <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-400" />
                <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Playground Not Available</h3>
                <p style={{ color: 'var(--text-muted)' }}>{error}</p>
            </div>
        );
    }

    if (!config) return null;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-gradient-to-r from-green-500/20 to-amber-500/20">
                        <Sliders className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                            🎮 Interactive Playground
                        </h3>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            Adjust sliders to see predictions change in real-time
                        </p>
                    </div>
                </div>
                <button
                    onClick={handlePredict}
                    disabled={predicting}
                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-green-500 to-amber-500 text-white font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                >
                    {predicting ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                        <Sparkles className="w-4 h-4" />
                    )}
                    Predict
                </button>
            </div>

            {/* Prediction Result */}
            <motion.div
                initial={false}
                animate={{
                    scale: prediction ? [1, 1.02, 1] : 1,
                    borderColor: prediction ? '#22c55e' : 'var(--border-color)'
                }}
                className="p-4 sm:p-6 rounded-2xl border-2"
                style={{
                    backgroundColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.05)',
                    borderColor: isDark ? '#22c55e' : '#16a34a'
                }}
            >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                            Predicted {config.target_column}
                        </p>
                        <p className="text-3xl sm:text-4xl font-bold" style={{ color: isDark ? '#4ade80' : '#15803d' }}>
                            {prediction !== null ? String(prediction) : '—'}
                        </p>
                    </div>
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
                        {confidence !== null && (
                            <div className="sm:text-right">
                                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>Confidence</p>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-20 sm:w-24 h-3 rounded-full overflow-hidden"
                                        style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}
                                    >
                                        <div
                                            className="h-full rounded-full bg-gradient-to-r from-green-500 to-amber-500 transition-all duration-300"
                                            style={{ width: `${confidence * 100}%` }}
                                        />
                                    </div>
                                    <span className="font-bold" style={{ color: isDark ? '#4ade80' : '#15803d' }}>{(confidence * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        )}
                        {prediction !== null && (
                            <button
                                onClick={() => setShowExplainModal(true)}
                                className="w-full sm:w-auto px-3 py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 text-sm font-medium"
                                style={{
                                    backgroundColor: isDark ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)',
                                    color: isDark ? '#fbbf24' : '#b45309',
                                }}
                            >
                                <HelpCircle className="w-4 h-4" />
                                Why this prediction?
                            </button>
                        )}
                    </div>
                </div>
            </motion.div>

            {/* Sliders Grid */}
            <div
                className="p-6 rounded-2xl border"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
            >
                <h4 className="font-semibold mb-6 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                    <Activity className="w-5 h-5 text-green-400" />
                    Adjust Feature Values
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400 ml-2">
                        {config.sliders.length} features
                    </span>
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {config.sliders.map((slider) => (
                        <div key={slider.name} className="space-y-2">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                                    {slider.name}
                                </label>
                                <span className="text-xs font-mono px-2 py-0.5 rounded"
                                    style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb', color: 'var(--text-primary)' }}>
                                    {slider.type === 'numeric'
                                        ? Number(values[slider.name])?.toFixed(2)
                                        : values[slider.name]}
                                </span>
                            </div>

                            {slider.type === 'numeric' ? (
                                <div className="space-y-1">
                                    <input
                                        type="range"
                                        min={slider.min}
                                        max={slider.max}
                                        step={slider.step}
                                        value={values[slider.name] ?? slider.min}
                                        onChange={(e) => handleValueChange(slider.name, parseFloat(e.target.value))}
                                        className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-green-500"
                                        style={{
                                            background: `linear-gradient(to right, #14b8a6 0%, #14b8a6 ${((values[slider.name] - (slider.min || 0)) / ((slider.max || 100) - (slider.min || 0))) * 100}%, ${isDark ? '#374151' : '#e5e7eb'} ${((values[slider.name] - (slider.min || 0)) / ((slider.max || 100) - (slider.min || 0))) * 100}%, ${isDark ? '#374151' : '#e5e7eb'} 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
                                        <span>{slider.min}</span>
                                        <span>{slider.max}</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="relative">
                                    <select
                                        value={values[slider.name] ?? ''}
                                        onChange={(e) => handleValueChange(slider.name, e.target.value)}
                                        className="w-full p-3 rounded-xl border appearance-none cursor-pointer pr-10"
                                        style={{
                                            backgroundColor: 'var(--bg-secondary)',
                                            borderColor: 'var(--border-color)',
                                            color: 'var(--text-primary)'
                                        }}
                                    >
                                        {slider.options?.map((opt) => (
                                            <option key={opt} value={opt}>{opt}</option>
                                        ))}
                                    </select>
                                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                                        style={{ color: 'var(--text-muted)' }} />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Tips */}
            <div className="text-sm text-center" style={{ color: 'var(--text-muted)' }}>
                💡 Predictions update automatically as you adjust the sliders
            </div>

            {/* SHAP Explain Modal */}
            <ExplainModal
                isOpen={showExplainModal}
                onClose={() => setShowExplainModal(false)}
                inputValues={values}
            />
        </div>
    );
};

export default PlaygroundTab;

