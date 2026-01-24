/**
 * 🔍 Explain Modal - Shows SHAP explanation for predictions
 * 
 * Features:
 * - Waterfall chart showing feature contributions
 * - Plain English explanation
 * - Top contributing features list
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    X,
    HelpCircle,
    TrendingUp,
    TrendingDown,
    Lightbulb,
    RefreshCw,
    AlertCircle
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';

interface ContributionItem {
    feature: string;
    value: number;
    shap_value: number;
    direction: string;
}

interface ExplainResponse {
    success: boolean;
    base_value?: number;
    prediction?: any;
    prediction_contribution?: number;
    contributions: ContributionItem[];
    waterfall_chart?: string;
    explanation_text?: string;
}

interface ExplainModalProps {
    isOpen: boolean;
    onClose: () => void;
    inputValues: Record<string, any>;
}

const ExplainModal: React.FC<ExplainModalProps> = ({ isOpen, onClose, inputValues }) => {
    const { isDark } = useUserStore();
    const [loading, setLoading] = useState(true);  // Start with loading=true
    const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchExplanation = async () => {
        try {
            setLoading(true);
            setError(null);

            const userId = localStorage.getItem('userId') || 'default';
            console.log('[ExplainModal] Fetching explanation for:', inputValues);

            const response = await fetch('/api/v1/automl/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    input_values: inputValues,
                    user_id: userId
                })
            });

            const data = await response.json();
            console.log('[ExplainModal] Response:', data);

            if (response.ok && data.success) {
                setExplanation(data);
            } else {
                setError(data.detail || data.error || 'Explanation failed');
            }
        } catch (err: any) {
            console.error('[ExplainModal] Error:', err);
            setError(err.message || 'Failed to get explanation');
        } finally {
            setLoading(false);
        }
    };

    // Fetch when modal opens
    React.useEffect(() => {
        if (isOpen) {
            setLoading(true);
            setExplanation(null);
            setError(null);

            if (Object.keys(inputValues).length > 0) {
                fetchExplanation();
            } else {
                setLoading(false);
                setError('No input values provided. Please fill in the prediction form first.');
            }
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
                style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="w-full max-w-3xl max-h-[85vh] overflow-hidden rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20">
                                <HelpCircle className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                                    🔍 Why This Prediction?
                                </h2>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    SHAP values show how each feature influenced the prediction
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">
                        {loading && (
                            <div className="flex flex-col items-center justify-center py-12">
                                <RefreshCw className="w-12 h-12 animate-spin text-primary-400 mb-4" />
                                <p style={{ color: 'var(--text-muted)' }}>Calculating SHAP values...</p>
                                <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>This may take a few seconds...</p>
                            </div>
                        )}

                        {error && !loading && (
                            <div className="text-center py-12">
                                <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
                                <p className="text-red-400 mb-2">{error}</p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    Make sure SHAP is installed: pip install shap
                                </p>
                            </div>
                        )}

                        {explanation && !loading && (
                            <div className="space-y-6">
                                {/* Plain English Explanation */}
                                {explanation.explanation_text && (
                                    <div
                                        className="p-4 rounded-xl border-l-4 border-l-blue-500"
                                        style={{ backgroundColor: isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.05)' }}
                                    >
                                        <div className="flex items-start gap-3">
                                            <Lightbulb className="w-5 h-5 text-blue-400 mt-0.5" />
                                            <div>
                                                <p className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                                                    Quick Explanation
                                                </p>
                                                <p style={{ color: 'var(--text-muted)' }}>
                                                    {explanation.explanation_text}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Waterfall Chart */}
                                {explanation.waterfall_chart && (
                                    <div>
                                        <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                                            📊 Feature Impact (Waterfall Chart)
                                        </h3>
                                        <div
                                            className="rounded-xl overflow-hidden"
                                            style={{ backgroundColor: isDark ? '#0f172a' : '#f8fafc' }}
                                        >
                                            <img
                                                src={explanation.waterfall_chart}
                                                alt="SHAP Waterfall Chart"
                                                className="w-full"
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Feature Contributions List */}
                                <div>
                                    <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                                        🎯 Top Contributing Features
                                    </h3>
                                    <div className="space-y-2">
                                        {explanation.contributions.slice(0, 10).map((contrib, i) => (
                                            <div
                                                key={i}
                                                className="flex items-center gap-3 p-3 rounded-xl"
                                                style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                            >
                                                <div className={`p-1.5 rounded-lg ${contrib.direction === 'positive' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                                                    {contrib.direction === 'positive' ? (
                                                        <TrendingUp className="w-4 h-4 text-green-400" />
                                                    ) : (
                                                        <TrendingDown className="w-4 h-4 text-red-400" />
                                                    )}
                                                </div>
                                                <div className="flex-1">
                                                    <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                                                        {contrib.feature}
                                                    </p>
                                                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                                        Value: {typeof contrib.value === 'number' ? contrib.value.toFixed(2) : contrib.value}
                                                    </p>
                                                </div>
                                                <div className="text-right">
                                                    <span
                                                        className={`font-bold text-sm ${contrib.direction === 'positive' ? 'text-green-400' : 'text-red-400'}`}
                                                    >
                                                        {contrib.shap_value > 0 ? '+' : ''}{contrib.shap_value.toFixed(3)}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Base Value */}
                                {explanation.base_value !== undefined && (
                                    <div className="text-center pt-4 border-t" style={{ borderColor: 'var(--border-color)' }}>
                                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                            Base value: <span className="font-mono">{explanation.base_value.toFixed(4)}</span>
                                            {explanation.prediction !== undefined && (
                                                <> → Prediction: <span className="font-bold text-primary-400">{explanation.prediction}</span></>
                                            )}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

export default ExplainModal;
