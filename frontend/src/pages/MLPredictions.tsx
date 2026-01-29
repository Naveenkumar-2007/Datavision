/**
 * 🤖 ML Predictions - Complete Training & Results Page
 * 
 * SAME AS DATAHUB:
 * - Select from existing files uploaded in DataHub
 * - Smart target column detection with auto-select
 * - Fast Mode (7 algorithms, 30-60s) vs Ultra Mode (20+ algorithms, 2-10min)
 * - Same training overlay with animated spinning icon
 * - Full dark/light mode support
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Brain,
    TrendingUp,
    BarChart3,
    AlertTriangle,
    CheckCircle,
    Target,
    Zap,
    RefreshCw,
    Sparkles,
    Award,
    Layers,
    PieChart,
    Activity,
    Play,
    History,
    Database,
    Download,
    FileText,
    XCircle,
    HeartPulse,
    Sliders,
    HelpCircle,
} from 'lucide-react';
import ModelHistory from '@/components/automl/ModelHistory';
import DataHealthCard from '@/components/automl/DataHealthCard';
import PlaygroundTab from '@/components/automl/PlaygroundTab';
import ExplainModal from '@/components/automl/ExplainModal';
import apiService from '@/services/api';
import { useUserStore } from '@/store/userStore';
import { useToast } from '@/contexts/ToastContext';
import { getUserIdSync } from '@/utils/userId';


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
    charts: Record<string, string>;
    data_summary: {
        rows: number;
        columns: number;
        features_engineered: number;
        features_used?: number;
    };
    processing_time_seconds: number;
    is_nlp_task?: boolean;
    primary_text_col?: string;
    feature_columns?: string[];
    cleaned_file?: string;
}

interface FileItem {
    id: string;
    name: string;
    size: number;
    type: string;
    uploadedAt: string;
    status: 'processing' | 'completed' | 'failed';
}

const MLPredictions: React.FC = () => {
    const { isDark } = useUserStore();
    const toast = useToast();
    const navigate = useNavigate();
    const location = useLocation();

    // Results state
    const [result, setResult] = useState<MLResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'features' | 'predict' | 'playground' | 'history' | 'data'>('overview');
    const [showExplainModal, setShowExplainModal] = useState(false);
    const [explainInputValues, setExplainInputValues] = useState<Record<string, any>>({});
    const [predictionInput, setPredictionInput] = useState<Record<string, string>>({});
    const [predictionResult, setPredictionResult] = useState<any>(null);
    const [chartsLoading, setChartsLoading] = useState(false);

    // File & Training state - SAME AS DATAHUB
    const [existingFiles, setExistingFiles] = useState<FileItem[]>([]);
    const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
    const [training, setTraining] = useState(false);
    const [ultraMode, setUltraMode] = useState(true); // Ultra AutoML (maximum accuracy) is default
    const [targetColumn, setTargetColumn] = useState('');
    const [availableColumns, setAvailableColumns] = useState<string[]>([]);
    const [progressMessage, setProgressMessage] = useState('Initializing...');
    const [abortController, setAbortController] = useState<AbortController | null>(null);

    // Smart target column detection - SAME AS DATAHUB
    const detectTargetColumn = (columns: string[]): string => {
        const targetPatterns = [
            'target', 'label', 'class', 'y', 'output', 'result', 'prediction',
            'price_range', 'price', 'category', 'status', 'type', 'outcome',
            'fraud', 'churn', 'default', 'survived', 'approved', 'purchased'
        ];

        // Check for exact/partial matches
        for (const pattern of targetPatterns) {
            for (const col of columns) {
                if (col.toLowerCase().includes(pattern)) {
                    return col;
                }
            }
        }

        // Default: last column (common ML convention)
        return columns[columns.length - 1];
    };

    // Load existing files from DataHub
    const loadExistingFiles = async () => {
        try {
            const response = await apiService.listFiles();
            const dataFiles = (response.data.files || []).filter((f: FileItem) =>
                f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
            );
            setExistingFiles(dataFiles);
        } catch (error) {
            console.error('Failed to load files:', error);
        }
    };

    // Fetch charts from API
    const fetchChartsFromAPI = async (userId: string): Promise<Record<string, string>> => {
        try {
            const response = await fetch(`/api/v2/automl/charts/${userId}`);
            const data = await response.json();
            if (data.success && data.charts && Object.keys(data.charts).length > 0) {
                try {
                    sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(data.charts));
                } catch (e) {
                    console.warn('[MLPredictions] Failed to cache charts');
                }
                return data.charts;
            }
            return {};
        } catch (error) {
            console.warn('[MLPredictions] Failed to fetch charts:', error);
            return {};
        }
    };

    // Load results on mount
    useEffect(() => {
        const loadResults = async () => {
            const userId = localStorage.getItem('userId') || 'default';

            const addChartsFromStorage = async (result: MLResult): Promise<MLResult> => {
                if (!result.charts || Object.keys(result.charts).length === 0) {
                    const savedCharts = sessionStorage.getItem(`mlCharts_${userId}`);
                    if (savedCharts) {
                        try {
                            result.charts = JSON.parse(savedCharts);
                            return result;
                        } catch (e) { }
                    }
                    setChartsLoading(true);
                    const apiCharts = await fetchChartsFromAPI(userId);
                    setChartsLoading(false);
                    if (Object.keys(apiCharts).length > 0) {
                        result.charts = apiCharts;
                    }
                }
                return result;
            };

            // 🔄 Sync result with active model from backend to ensure consistency
            const syncWithActiveModel = async (result: MLResult): Promise<MLResult> => {
                try {
                    const response = await fetch(`/api/v2/autonomous/models/${userId}`);
                    const data = await response.json();
                    
                    if (data.success && data.models && data.models.length > 0) {
                        const activeModel = data.models.find((m: any) => m.is_active);
                        if (activeModel) {
                            // Update result.best_model to match the active model
                            result.best_model = {
                                name: activeModel.model_name,
                                metrics: activeModel.metrics || {}
                            };
                            result.target_column = activeModel.target_column;
                            result.task_type = activeModel.task_type;
                            result.feature_columns = activeModel.feature_columns || result.feature_columns;
                            console.log('[MLPredictions] Synced with active model:', activeModel.model_name);
                        }
                    }
                } catch (err) {
                    console.warn('[MLPredictions] Could not sync with active model:', err);
                }
                return result;
            };

            // Priority 1: Location state (fresh training - skip sync)
            if (location.state?.automlResult) {
                const navResult = location.state.automlResult;
                const resultWithCharts = await addChartsFromStorage(navResult);
                setResult(resultWithCharts);
                try {
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(navResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                } catch (storageErr) {
                    const { charts, ...lightResult } = navResult;
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(lightResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                }
                if (resultWithCharts.charts && Object.keys(resultWithCharts.charts).length > 0) {
                    try {
                        sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(resultWithCharts.charts));
                    } catch (e) { }
                }
                setLoading(false);
                return;
            }

            // Priority 2: User-specific localStorage (sync with active model)
            const saved = localStorage.getItem(`mlResults_${userId}`);
            if (saved) {
                try {
                    let parsedSaved = JSON.parse(saved);
                    parsedSaved = await syncWithActiveModel(parsedSaved);
                    const resultWithCharts = await addChartsFromStorage(parsedSaved);
                    setResult(resultWithCharts);
                    setLoading(false);
                    return;
                } catch (e) { }
            }

            // Priority 3: Legacy migration (sync with active model)
            const legacySaved = localStorage.getItem('mlResults');
            if (legacySaved) {
                try {
                    let parsed = JSON.parse(legacySaved);
                    parsed = await syncWithActiveModel(parsed);
                    const resultWithCharts = await addChartsFromStorage(parsed);
                    setResult(resultWithCharts);
                    localStorage.setItem(`mlResults_${userId}`, legacySaved);
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                    setLoading(false);
                    return;
                } catch (e) { }
            }

            // No results - load existing files
            await loadExistingFiles();
            setLoading(false);
        };

        loadResults();

        if (location.state?.activeTab) {
            setActiveTab(location.state.activeTab);
        }
    }, [location.state, location.key]);

    // 🔄 Refresh overview when model changes (rollback/delete)
    const handleModelChange = async () => {
        const userId = localStorage.getItem('userId') || 'default';
        try {
            const response = await fetch(`/api/v2/autonomous/models/${userId}`);
            const data = await response.json();
            
            if (data.success && data.models && data.models.length > 0) {
                const activeModel = data.models.find((m: any) => m.is_active);
                if (activeModel && result) {
                    setResult({
                        ...result,
                        best_model: {
                            name: activeModel.model_name,
                            metrics: activeModel.metrics || {}
                        },
                        target_column: activeModel.target_column,
                        task_type: activeModel.task_type,
                        feature_columns: activeModel.feature_columns || result.feature_columns
                    });
                }
            }
        } catch (err) {
            console.warn('[MLPredictions] Could not refresh after model change:', err);
        }
    };

    const getMetricColor = (value: number) => {
        if (value >= 0.9) return '#10b981';
        if (value >= 0.7) return '#f59e0b';
        return '#ef4444';
    };

    // Fetch columns from existing file - SAME AS DATAHUB
    const fetchColumnsFromFile = async (fileName: string) => {
        try {
            const userId = localStorage.getItem('userId') || 'default';
            // Download file and parse columns
            const fileResponse = await fetch(`/api/v1/files/${userId}/${fileName}/download`);
            if (!fileResponse.ok) return;
            
            const blob = await fileResponse.blob();
            const text = await blob.text();
            const firstLine = text.split('\n')[0];
            const columns = firstLine.split(',').map(col => col.trim().replace(/"/g, ''));
            
            setAvailableColumns(columns);
            const detected = detectTargetColumn(columns);
            setTargetColumn(detected);
            console.log(`📊 Detected columns: ${columns.length}, Target: ${detected}`);
        } catch (error) {
            console.error('Failed to fetch columns:', error);
        }
    };

    // Select existing file
    const handleSelectFile = async (file: FileItem) => {
        setSelectedFile(file);
        await fetchColumnsFromFile(file.name);
    };

    // Training handler - EXACT SAME AS DATAHUB
    const handleRunAutoML = async () => {
        if (!selectedFile) {
            toast.error('Please select a data file first.');
            return;
        }

        setTraining(true);

        // Create abort controller for "Stop" functionality
        const controller = new AbortController();
        setAbortController(controller);

        try {
            // Get the file from server and send to AutoML - SAME AS DATAHUB
            const userId = localStorage.getItem('userId') || 'default';
            const fileResponse = await fetch(`/api/v1/files/${userId}/${selectedFile.name}/download`, {
                signal: controller.signal
            });

            if (!fileResponse.ok) throw new Error('Failed to get file');

            const fileBlob = await fileResponse.blob();
            const formData = new FormData();
            formData.append('file', fileBlob, selectedFile.name);
            formData.append('user_id', userId);

            // Add target column if selected/detected
            if (targetColumn) {
                formData.append('target_column', targetColumn);
            }

            // Send to Training API with abort signal
            // Use Ultra AutoML endpoint for maximum accuracy
            const endpoint = ultraMode ? '/api/v2/automl/ultra_train' : '/api/v2/automl/train';
            if (ultraMode) {
                formData.append('mode', 'maximum_accuracy');
            }
            const automlResponse = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            const automlResult = await automlResponse.json();

            if (automlResult.success) {
                // Save to localStorage with USER-SPECIFIC key for data isolation
                try {
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(automlResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');

                    if (automlResult.charts) {
                        try {
                            sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(automlResult.charts));
                        } catch (chartErr) {
                            console.warn("Charts too large for sessionStorage");
                        }
                    }
                } catch (e) {
                    console.warn("Storage quota full, saving result without charts");
                    const { charts, ...lightResult } = automlResult;
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(lightResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                }

                window.dispatchEvent(new CustomEvent('filesUpdated'));
                setResult(automlResult);
            } else {
                toast.error(`AutoML failed: ${automlResult.detail || automlResult.error || 'Unknown error'}`);
            }
        } catch (error: any) {
            // Handle User Stop
            if (error.name === 'AbortError') {
                return; // Silent exit on stop
            }
            console.error('AutoML error:', error);
            toast.error(`AutoML error: ${error.message}`);
        } finally {
            setTraining(false);
            setAbortController(null);
        }
    };

    // Stop Training - SAME AS DATAHUB
    const handleStopTraining = async () => {
        if (abortController) abortController.abort();
        setTraining(false);

        // Signal Backend to Stop Permanently
        try {
            const userId = localStorage.getItem('userId') || 'default';
            const formData = new FormData();
            formData.append('user_id', userId);
            await fetch('/api/v2/automl/stop_training', {
                method: 'POST',
                body: formData
            });
        } catch (e) {
            console.error("Failed to signal stop to backend", e);
        }
    };

    // Animation loop for training messages - SAME AS DATAHUB
    useEffect(() => {
        if (!training) return;
        const messages = ultraMode ? [
            '🎼 Initializing Ultra AutoML...',
            '📊 Analyzing Dataset Profile...',
            '🎯 Meta-Learning Recommendations...',
            '🔬 Synthesizing 50+ Features...',
            '🤖 Training Classical Models...',
            '🧠 Training Neural Networks...',
            '📈 Optimizing Hyperparameters...',
            '⚖️ Building Ultra Ensemble...',
            '🔮 Generating Explainability...',
        ] : [
            '🧹 Cleaning Data (Phase 1/4)...',
            '🛠️ Engineering Features (Phase 2/4)...',
            '🤖 Training 15+ Models (Phase 3/4)...',
            '📈 Optimizing Hyperparameters...',
            '⚖️ Building Ensembles...',
            '📊 Generating High-Res Charts...'
        ];
        let i = 0;
        const interval = setInterval(() => {
            setProgressMessage(messages[i % messages.length]);
            i++;
        }, 3500);
        return () => clearInterval(interval);
    }, [training, ultraMode]);

    // Check if data files exist
    const hasDataFiles = existingFiles.length > 0;

    // Show loading spinner
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
                    <RefreshCw className="w-16 h-16 mx-auto mb-4 animate-spin" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                    <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>Loading ML Results...</h2>
                </motion.div>
            </div>
        );
    }

    // ========================================================================
    // NO RESULTS - SHOW TRAINING INTERFACE (SAME AS DATAHUB)
    // ========================================================================
    if (!result) {
        return (
            <div className="space-y-6">
                {/* TRAINING OVERLAY - EXACT COPY FROM DATAHUB */}
                {training && (
                    <div
                        className="fixed inset-0 z-[100] flex items-center justify-center transition-all duration-500"
                        style={{ backgroundColor: 'var(--glass-overlay)' }}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0, y: 20 }}
                            animate={{ scale: 1, opacity: 1, y: 0 }}
                            className="flex flex-col items-center max-w-lg w-full p-8 text-center"
                        >
                            {/* Big Animated Icon - Mode Aware Colors */}
                            <div className="relative w-40 h-40 mb-8 flex items-center justify-center">
                                <div className={`absolute inset-0 blur-2xl rounded-full animate-pulse ${ultraMode ? 'bg-purple-500/20' : 'bg-green-500/20'}`}></div>
                                <div className={`absolute inset-0 border-4 rounded-full animate-spin ${ultraMode
                                    ? 'border-t-purple-400 border-r-purple-400/50 border-b-purple-400/20 border-l-purple-400/50'
                                    : 'border-t-green-400 border-r-green-400/50 border-b-green-400/20 border-l-green-400/50'
                                    }`}></div>
                                <div className={`absolute inset-4 border-4 rounded-full animate-spin ${ultraMode
                                    ? 'border-b-pink-400 border-l-pink-400/50 border-t-pink-400/20 border-r-pink-400/50'
                                    : 'border-b-blue-400 border-l-blue-400/50 border-t-blue-400/20 border-r-blue-400/50'
                                    }`} style={{ animationDirection: 'reverse', animationDuration: '3s' }}></div>
                                <Brain className="w-16 h-16 relative z-10 animate-pulse" style={{ color: 'var(--text-primary)' }} />
                            </div>

                            {/* Title - Mode Aware */}
                            <h2 className={`text-4xl font-bold bg-clip-text text-transparent mb-4 ${ultraMode
                                ? 'bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400'
                                : 'bg-gradient-to-r from-emerald-400 via-green-400 to-cyan-400'
                                }`}>
                                {ultraMode ? '🎼 Ultra AutoML Training' : '🚀 Fast ML Training'}
                            </h2>

                            {/* Mode Details */}
                            <div className={`flex items-center gap-2 mb-4 px-4 py-2 rounded-full ${ultraMode ? 'bg-purple-500/20 text-purple-300' : 'bg-green-500/20 text-green-300'
                                }`}>
                                {ultraMode ? (
                                    <>
                                        <span className="text-sm font-medium">20+ Algorithms</span>
                                        <span className="opacity-50">•</span>
                                        <span className="text-sm font-medium">Ensembles</span>
                                        <span className="opacity-50">•</span>
                                        <span className="text-sm font-medium">Deep Learning</span>
                                    </>
                                ) : (
                                    <>
                                        <span className="text-sm font-medium">7 Core Algorithms</span>
                                        <span className="opacity-50">•</span>
                                        <span className="text-sm font-medium">Quick Training</span>
                                    </>
                                )}
                            </div>

                            {/* Progress Card */}
                            <div
                                className={`backdrop-blur border rounded-2xl p-6 w-full mb-8 shadow-2xl ${ultraMode ? 'border-purple-500/30' : 'border-green-500/30'
                                    }`}
                                style={{ backgroundColor: 'var(--bg-card)' }}
                            >
                                <p className="text-xl font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                                    {progressMessage}
                                </p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    {ultraMode
                                        ? '⏱️ Ultra mode: 2-10 minutes for maximum accuracy.'
                                        : '⏱️ Fast mode: 30-60 seconds for quick results.'
                                    }
                                </p>
                            </div>

                            <button
                                onClick={handleStopTraining}
                                className="group px-8 py-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 font-bold hover:bg-red-500/20 hover:border-red-500/50 transition-all flex items-center gap-3"
                            >
                                <XCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
                                STOP TRAINING
                            </button>
                        </motion.div>
                    </div>
                )}

                {/* Header - SAME STYLE AS DATAHUB */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>ML Predictions</h1>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Train ML models on your data files</p>
                    </div>

                    {/* 🤖 ML Train Button - Shows when data files exist - SAME AS DATAHUB */}
                    {hasDataFiles && selectedFile && (
                        <div className="flex items-center gap-2 w-full md:w-auto">
                            {/* Fast/Ultra Mode Toggle - Pill Style (SAME AS DATAHUB) */}
                            <div className="inline-flex p-1 rounded-xl border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }}>
                                <button
                                    onClick={() => setUltraMode(false)}
                                    disabled={training}
                                    className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${!ultraMode
                                        ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg'
                                        : ''
                                        }`}
                                    style={ultraMode ? { color: 'var(--text-muted)' } : undefined}
                                    title="Fast Mode: 10 models, ~5-10min training (up to 500k rows)"
                                >
                                    <Zap className="w-4 h-4" />
                                    Fast
                                </button>
                                <button
                                    onClick={() => setUltraMode(true)}
                                    disabled={training}
                                    className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${ultraMode
                                        ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
                                        : ''
                                        }`}
                                    style={!ultraMode ? { color: 'var(--text-muted)' } : undefined}
                                    title="Ultra Mode: 25+ models with ensembles, ~15-30min training (up to 1M rows)"
                                >
                                    <Sparkles className="w-4 h-4" />
                                    Ultra
                                </button>
                            </div>

                            {/* Train Button - Mode Aware (SAME AS DATAHUB) */}
                            <button
                                onClick={handleRunAutoML}
                                disabled={training}
                                className={`btn-primary flex-1 md:flex-none rounded-full flex items-center justify-center gap-2 px-6 py-2.5 ${ultraMode
                                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500'
                                    : 'bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500'
                                    } text-white font-medium ${training ? 'opacity-60 cursor-wait' : ''}`}
                            >
                                {training ? (
                                    <>
                                        <div className="loading-spinner" />
                                        <span className="whitespace-nowrap">{ultraMode ? 'Ultra Training...' : 'Training...'}</span>
                                    </>
                                ) : (
                                    <>
                                        <Brain className="w-5 h-5" />
                                        <span className="whitespace-nowrap">{ultraMode ? '🧠 Ultra ML' : '🚀 Fast ML'}</span>
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </motion.div>

                {/* File Selection Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-xl bg-blue-500/20">
                            <Database className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Your Data Files</h2>
                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                {existingFiles.length > 0
                                    ? `${existingFiles.length} file(s) available from DataHub`
                                    : 'No files found - Upload files in DataHub first'}
                            </p>
                        </div>
                    </div>

                    {existingFiles.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {existingFiles.map((file) => (
                                <button
                                    key={file.id}
                                    onClick={() => handleSelectFile(file)}
                                    disabled={training}
                                    className="p-4 rounded-xl border text-left transition-all flex items-center gap-3 hover:border-emerald-500/50"
                                    style={{
                                        backgroundColor: selectedFile?.id === file.id
                                            ? (isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(16, 185, 129, 0.1)')
                                            : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                        borderColor: selectedFile?.id === file.id ? '#10b981' : 'var(--border-color)'
                                    }}
                                >
                                    <FileText className="w-6 h-6 flex-shrink-0" style={{ color: selectedFile?.id === file.id ? '#10b981' : 'var(--text-muted)' }} />
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>{file.name}</p>
                                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</p>
                                    </div>
                                    {selectedFile?.id === file.id && <CheckCircle className="w-5 h-5 flex-shrink-0" style={{ color: '#10b981' }} />}
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <Database className="w-12 h-12 mx-auto mb-3 opacity-50" style={{ color: 'var(--text-muted)' }} />
                            <p style={{ color: 'var(--text-muted)' }}>No data files found</p>
                            <button
                                onClick={() => navigate('/data-hub')}
                                className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                            >
                                Go to DataHub to upload files
                            </button>
                        </div>
                    )}
                </motion.div>

                {/* 🎯 Target Column Selection - SAME AS DATAHUB */}
                {availableColumns.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="p-4 rounded-2xl border"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2 rounded-xl bg-purple-500/20">
                                <Sparkles className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                    🎯 Target Column (What to predict)
                                </p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    Auto-detected: <span className="text-purple-400">{targetColumn}</span> • Change if needed
                                </p>
                            </div>
                        </div>

                        <select
                            value={targetColumn}
                            onChange={(e) => setTargetColumn(e.target.value)}
                            disabled={training}
                            className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
                            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                        >
                            {availableColumns.map((col) => (
                                <option key={col} value={col} style={{ backgroundColor: isDark ? '#1f2937' : '#ffffff', color: isDark ? '#ffffff' : '#000000' }}>
                                    {col}
                                </option>
                            ))}
                        </select>

                        <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                            💡 Tip: Select the column you want the model to predict (e.g., price, category, fraud)
                        </p>
                    </motion.div>
                )}

                {/* 🏥 Data Health Card - Shows before training */}
                {selectedFile && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <DataHealthCard
                            fileName={selectedFile.name}
                            targetColumn={targetColumn}
                        />
                    </motion.div>
                )}

                {/* Instructions when no file selected */}
                {!selectedFile && existingFiles.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-6"
                    >
                        <p style={{ color: 'var(--text-muted)' }}>
                            👆 Select a file above to start training
                        </p>
                    </motion.div>
                )}
            </div>
        );
    }

    // ========================================================================
    // RESULTS VIEW - Showing trained model results
    // ========================================================================
    const metrics = result.best_model?.metrics || {};
    let bestMetric: [string, number] = ['accuracy', 0];

    if (metrics.accuracy !== undefined) {
        bestMetric = ['accuracy', metrics.accuracy];
    } else if (metrics.f1 !== undefined) {
        bestMetric = ['f1', metrics.f1];
    } else if (metrics.r2 !== undefined) {
        bestMetric = ['r2', metrics.r2];
    } else {
        const entries = Object.entries(metrics);
        if (entries.length > 0) {
            bestMetric = entries[0] as [string, number];
        }
    }

    const rankedFeatures = (result.feature_importance && result.feature_importance.length > 0)
        ? result.feature_importance
        : (result.feature_columns || []).map((f, i) => ({
            feature: f,
            importance: 1 / (result.feature_columns?.length || 1),
            rank: i + 1
        }));

    const inputFeatures = (result.feature_metadata && result.feature_metadata.length > 0)
        ? result.feature_metadata
        : rankedFeatures.map(f => ({
            name: f.feature,
            type: 'numeric' as const,
            min: 0,
            max: 100,
            mean: 50,
            options: undefined as string[] | undefined
        }));

    return (
        <div className="space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
                <div className="flex items-center gap-4 w-full md:w-auto">
                    <div className="min-w-0">
                        <h1 className="text-2xl font-bold flex items-center gap-3 truncate" style={{ color: 'var(--text-primary)' }}>
                            <Brain className="w-8 h-8 flex-shrink-0" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                            <span className="truncate">ML Predictions</span>
                        </h1>
                        <p className="text-sm truncate" style={{ color: 'var(--text-muted)' }}>
                            Target: <span className="font-medium" style={{ color: isDark ? '#4ade80' : '#16a34a' }}>{result.target_column}</span>
                            {' • '}
                            Task: <span className="text-blue-400 font-medium">{result.task_type}</span>
                            {' • '}
                            <span className="text-amber-400 font-medium">{result.processing_time_seconds?.toFixed(1)}s</span>
                        </p>
                    </div>
                </div>
                <button
                    onClick={() => {
                        setResult(null);
                        loadExistingFiles();
                    }}
                    className="w-full md:w-auto px-4 py-2 rounded-xl border transition-colors flex items-center justify-center gap-2"
                    style={{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}
                >
                    <RefreshCw className="w-4 h-4" />
                    <span>New Training</span>
                </button>
            </motion.div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-primary-500/20">
                            <Award className="w-5 h-5" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Best Model</span>
                    </div>
                    <p className="text-2xl font-bold text-primary-500">{result.best_model.name}</p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Target className="w-5 h-5 text-blue-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>{bestMetric[0]?.toUpperCase()}</span>
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
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-emerald-500/20">
                            <Layers className="w-5 h-5 text-emerald-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Models Trained</span>
                    </div>
                    <p className="text-2xl font-bold text-emerald-400">{result.all_models?.length || 0}</p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-amber-500/20">
                            <Sparkles className="w-5 h-5 text-amber-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Columns</span>
                    </div>
                    <p className="text-2xl font-bold text-amber-400">{result.data_summary?.columns || result.feature_importance?.length || 0}</p>
                </motion.div>
            </div>

            {/* Tabs */}
            <div className="overflow-x-auto no-scrollbar pb-2 md:pb-0">
                <div
                    className="flex gap-2 p-1.5 rounded-xl min-w-max md:min-w-0 border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    {[
                        { id: 'overview', label: 'Overview', icon: PieChart },
                        { id: 'charts', label: 'ML Charts', icon: BarChart3 },
                        { id: 'features', label: 'Features', icon: TrendingUp },
                        { id: 'predict', label: 'Predict', icon: Play },
                        { id: 'playground', label: 'Playground', icon: Sliders },
                        { id: 'history', label: 'History', icon: History },
                        { id: 'data', label: 'Data', icon: Database },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex-1 flex flex-shrink-0 items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                                ? 'bg-gradient-to-r from-primary-500 to-emerald-500 text-white shadow-lg'
                                : ''
                                }`}
                            style={activeTab !== tab.id ? { color: 'var(--text-muted)' } : undefined}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>
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
                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Activity className="w-5 h-5 text-blue-400" />
                                All Models Performance
                            </h3>
                            <div className="space-y-3">
                                {result.all_models?.slice(0, 8).map((model, i) => {
                                    const mainMetric = Object.values(model.metrics)[0] || 0;
                                    return (
                                        <div key={i} className="flex items-center gap-3">
                                            <span className="w-24 text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                                                {model.name}
                                            </span>
                                            <div className="flex-1 rounded-full h-3" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}>
                                                <div
                                                    className={`h-3 rounded-full ${model.name === result.best_model.name ? 'bg-gradient-to-r from-primary-500 to-emerald-500' : 'bg-blue-500'}`}
                                                    style={{ width: `${mainMetric * 100}%` }}
                                                />
                                            </div>
                                            <span className="w-16 text-sm font-bold text-right" style={{ color: 'var(--text-primary)' }}>
                                                {(mainMetric * 100).toFixed(1)}%
                                            </span>
                                            {model.name === result.best_model.name && (
                                                <span className="text-xs px-2 py-0.5 bg-primary-500 text-white rounded">BEST</span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Insights */}
                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Sparkles className="w-5 h-5 text-amber-400" />
                                AI Insights
                            </h3>
                            <div className="space-y-3">
                                {result.insights?.slice(0, 5).map((insight, i) => (
                                    <div
                                        key={i}
                                        className="p-4 rounded-xl border-l-4 border-l-green-500"
                                        style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                    >
                                        <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{insight}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'playground' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                            <Sliders className="w-5 h-5 text-violet-400" />
                            Interactive Prediction Playground
                        </h3>
                        <PlaygroundTab 
                            onPredictionMade={(pred) => {
                                setPredictionResult(pred);
                                setExplainInputValues(pred.input_values || {});
                            }}
                        />
                    </div>
                )}

                {activeTab === 'charts' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {chartsLoading && (
                            <div className="col-span-2 text-center p-12 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                <RefreshCw className="w-16 h-16 mx-auto mb-4 animate-spin" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                                <p className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Loading Charts...</p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Fetching ML visualizations from server</p>
                            </div>
                        )}

                        {!chartsLoading && result.charts && Object.entries(result.charts).map(([chartName, chartBase64]) => (
                            <div
                                key={chartName}
                                className="rounded-2xl border overflow-hidden transition-all hover:shadow-lg"
                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                            >
                                <div className="flex items-center gap-3 px-5 py-4 border-b" style={{ borderColor: 'var(--border-color)' }}>
                                    <div className="p-2 rounded-lg bg-gradient-to-r from-primary-500/20 to-emerald-500/20">
                                        <BarChart3 className="w-4 h-4" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                                    </div>
                                    <h3 className="text-base font-semibold capitalize" style={{ color: 'var(--text-primary)' }}>
                                        {chartName.replace(/_/g, ' ')}
                                    </h3>
                                </div>
                                <div className="p-4" style={{ backgroundColor: isDark ? '#0f172a' : '#f8fafc' }}>
                                    <img src={chartBase64} alt={chartName} className="w-full rounded-lg" style={{ maxHeight: '350px', objectFit: 'contain' }} />
                                </div>
                            </div>
                        ))}

                        {!chartsLoading && (!result.charts || Object.keys(result.charts).length === 0) && (
                            <div className="col-span-2 text-center p-12 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                <BarChart3 className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
                                <p className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>No Charts Available</p>
                                <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>Charts may not have been generated during training.</p>
                                <button
                                    onClick={async () => {
                                        const userId = localStorage.getItem('userId') || 'default';
                                        setChartsLoading(true);
                                        const charts = await fetchChartsFromAPI(userId);
                                        if (Object.keys(charts).length > 0) {
                                            setResult(prev => prev ? { ...prev, charts } : prev);
                                        }
                                        setChartsLoading(false);
                                    }}
                                    className="px-4 py-2 rounded-lg bg-primary-500 text-white hover:bg-primary-600 transition-colors flex items-center gap-2 mx-auto"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Refresh Charts
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'features' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h3 className="text-lg font-semibold mb-6 flex items-center justify-between" style={{ color: 'var(--text-primary)' }}>
                            <span>Feature Importance Ranking</span>
                            <span className="text-sm font-normal px-3 py-1 rounded-full bg-primary-500/20" style={{ color: isDark ? '#4ade80' : '#16a34a' }}>
                                {rankedFeatures.length} features
                            </span>
                        </h3>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                            {rankedFeatures.map((f, i) => (
                                <div
                                    key={i}
                                    className="flex items-center gap-4 p-3 rounded-xl"
                                    style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                >
                                    <span className="w-8 h-8 rounded-lg bg-gradient-to-r from-primary-500 to-emerald-500 flex items-center justify-center text-white font-bold">
                                        {f.rank || i + 1}
                                    </span>
                                    <div className="flex-1">
                                        <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{f.feature}</span>
                                        <div className="w-full rounded-full h-2 mt-1" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}>
                                            <div className="h-2 rounded-full bg-gradient-to-r from-primary-500 to-emerald-500" style={{ width: `${f.importance * 100}%` }} />
                                        </div>
                                    </div>
                                    <span className="font-bold" style={{ color: isDark ? '#4ade80' : '#16a34a' }}>{(f.importance * 100).toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'predict' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h3 className="text-lg font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>
                            Make a Prediction with {result.best_model.name}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                            {inputFeatures.map((meta) => {
                                const featureName = meta.name;
                                const isNumeric = meta.type === 'numeric';
                                const isExplicitText = (result as any).is_nlp_task && (result as any).primary_text_col === featureName;
                                const lowerName = featureName.toLowerCase();
                                const isHeuristicText = lowerName.includes('text') || lowerName.includes('content') || lowerName.includes('body') ||
                                    lowerName.includes('email') || lowerName.includes('review') || lowerName.includes('description') ||
                                    lowerName.includes('summary') || lowerName.includes('message');
                                const isText = isExplicitText || isHeuristicText;

                                return (
                                    <div key={featureName} className={isText ? "col-span-full" : ""}>
                                        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                                            {featureName}
                                            <span className="ml-2 text-xs opacity-60">({isNumeric ? 'numeric' : isText ? 'text input' : 'select'})</span>
                                            {isText && <span className="ml-2 text-xs bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">NLP Content</span>}
                                        </label>

                                        {isNumeric ? (
                                            <input
                                                type="number"
                                                placeholder={meta.mean !== undefined ? `e.g. ${meta.mean.toFixed(1)}` : `Enter ${featureName}`}
                                                value={predictionInput[featureName] || ''}
                                                onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors"
                                                style={{
                                                    backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                    borderColor: 'var(--border-color)',
                                                    color: 'var(--text-primary)',
                                                }}
                                            />
                                        ) : isText ? (
                                            <textarea
                                                placeholder={`Enter text for ${featureName}...`}
                                                value={predictionInput[featureName] || ''}
                                                onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                rows={5}
                                                className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors resize-none"
                                                style={{
                                                    backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                    borderColor: 'var(--border-color)',
                                                    color: 'var(--text-primary)',
                                                }}
                                            />
                                        ) : (
                                            <input
                                                type="text"
                                                placeholder={`Enter ${featureName}`}
                                                value={predictionInput[featureName] || ''}
                                                onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors"
                                                style={{
                                                    backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                    borderColor: 'var(--border-color)',
                                                    color: 'var(--text-primary)',
                                                }}
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    const dataToSend = {
                                        user_id: getUserIdSync(),
                                        model_name: result.best_model.name,
                                        data: Object.fromEntries(
                                            Object.entries(predictionInput).map(([k, v]) => [k, parseFloat(v) || v])
                                        )
                                    };
                                    const response = await fetch('/api/v2/automl/predict', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify(dataToSend)
                                    });
                                    const data = await response.json();
                                    setPredictionResult(data);
                                } catch (e: any) {
                                    toast.error(`Prediction failed: ${e.message}`);
                                }
                            }}
                            className="px-6 py-3 bg-gradient-to-r from-primary-500 to-emerald-500 rounded-xl text-white font-semibold hover:opacity-90 transition-opacity flex items-center gap-2"
                        >
                            <Play className="w-5 h-5" />
                            Get Prediction
                        </button>

                        {predictionResult && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mt-6 p-4 sm:p-6 rounded-xl border-2"
                                style={{
                                    backgroundColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.05)',
                                    borderColor: isDark ? '#22c55e' : '#16a34a',
                                }}
                            >
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <div>
                                        <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                                            Predicted label
                                        </p>
                                        <p 
                                            className="text-3xl sm:text-4xl font-bold"
                                            style={{ color: isDark ? '#4ade80' : '#15803d' }}
                                        >
                                            {predictionResult.prediction}
                                        </p>
                                    </div>
                                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
                                        {predictionResult.probability && (
                                            <div className="sm:text-right">
                                                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>Confidence</p>
                                                <div className="flex items-center gap-2">
                                                    <div
                                                        className="w-20 sm:w-24 h-3 rounded-full overflow-hidden"
                                                        style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}
                                                    >
                                                        <div
                                                            className="h-full rounded-full bg-gradient-to-r from-green-500 to-amber-500 transition-all duration-300"
                                                            style={{ width: `${Math.max(...predictionResult.probability) * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="font-bold" style={{ color: isDark ? '#4ade80' : '#15803d' }}>
                                                        {(Math.max(...predictionResult.probability) * 100).toFixed(1)}%
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => {
                                                setExplainInputValues(predictionInput);
                                                setShowExplainModal(true);
                                            }}
                                            className="w-full sm:w-auto px-3 py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 text-sm font-medium"
                                            style={{
                                                backgroundColor: isDark ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)',
                                                color: isDark ? '#fbbf24' : '#b45309',
                                            }}
                                        >
                                            <HelpCircle className="w-4 h-4" />
                                            Why this prediction?
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </div>
                )}

                {activeTab === 'history' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <ModelHistory 
                            userId={localStorage.getItem('userId') || 'default'} 
                            onModelChange={handleModelChange}
                        />
                    </div>
                )}

                {activeTab === 'data' && (
                    <div className="p-12 text-center rounded-2xl border border-dashed" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="max-w-md mx-auto">
                            <div className="w-20 h-20 mx-auto bg-primary-500/20 rounded-full flex items-center justify-center mb-6">
                                <Database className="w-10 h-10" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                            </div>
                            <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                                Production Cleaned Dataset
                            </h2>
                            <p className="mb-8 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                Download the exact dataset used for training. This data has been processed by our
                                Silicon Valley Grade pipeline (Imputed, Encoded, Scaled, and Cleaned).
                            </p>

                            {result.cleaned_file ? (
                                <div className="space-y-4">
                                    <a
                                        href={`/api/v1/files/${localStorage.getItem('userId') || 'default'}/${result.cleaned_file}/download`}
                                        className="inline-flex items-center gap-3 px-8 py-4 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-bold text-lg shadow-lg shadow-primary-500/20 transition-all hover:scale-105"
                                    >
                                        <Download className="w-6 h-6" />
                                        Download Cleaned CSV
                                    </a>
                                    <p className="text-xs flex items-center justify-center gap-2" style={{ color: 'var(--text-muted)' }}>
                                        <CheckCircle className="w-3 h-3 text-emerald-400" />
                                        Ready for Production Deployment
                                    </p>
                                </div>
                            ) : (
                                <div className="p-4 bg-amber-500/10 text-amber-500 rounded-lg inline-flex items-center gap-2">
                                    <AlertTriangle className="w-5 h-5" />
                                    <span>Cleaned dataset not available for this session.</span>
                                </div>
                            )}
                        </motion.div>
                    </div>
                )}
            </motion.div>

            {/* Explain Modal */}
            <ExplainModal
                isOpen={showExplainModal}
                onClose={() => setShowExplainModal(false)}
                inputValues={explainInputValues}
            />

            {/* Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="p-4 rounded-xl flex items-center justify-between"
                style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
            >
                <div className="flex items-center gap-6 text-sm" style={{ color: 'var(--text-muted)' }}>
                    <span>📊 {result.data_summary?.rows?.toLocaleString() || 0} rows</span>
                    <span>📁 {result.data_summary?.columns || 0} columns</span>
                    <span>⚙️ {result.data_summary?.features_engineered || 0} features engineered</span>
                </div>
            </motion.div>
        </div>
    );
};

export default MLPredictions;
