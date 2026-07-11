/**
 * 🧠 AUTOPILOT — Agentic Autonomous Data Science
 * ================================================
 * 
 * Cinematic full-experience page where the AI autonomously analyzes data.
 * User uploads a file, optionally sets a goal, and watches the AI work.
 * 
 * Features:
 * - Real-time SSE streaming of agent progress
 * - Step-by-step visualization of the pipeline
 * - Live insights appearing as they're discovered
 * - Charts generated inline
 * - Final report compilation
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Brain, Upload, Sparkles, CheckCircle2, XCircle, Loader2,
    FileText, BarChart3, Wand2, Zap, Target, TrendingUp,
    Code2, FileBarChart, ArrowRight, StopCircle, RefreshCw,
    ChevronDown, ChevronUp, Clock, AlertTriangle, Rocket
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { api } from '@/services/api';

// Helper to get user ID
const getUserIdSync = (): string => {
    try {
        const raw = localStorage.getItem('datavision_user');
        if (raw) {
            const parsed = JSON.parse(raw);
            return parsed?.id || parsed?.user_id || 'default';
        }
    } catch {}
    return 'default';
};

interface AutopilotStep {
    id: string;
    phase: string;
    title: string;
    description: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
    result?: any;
    error?: string;
    duration_ms?: number;
    progress: number;
}

interface AutopilotEvent {
    type: string;
    timestamp: string;
    data: any;
}

const PHASE_ICONS: Record<string, React.ReactNode> = {
    planning: <Brain className="w-5 h-5" />,
    data_profiling: <Target className="w-5 h-5" />,
    data_cleaning: <Wand2 className="w-5 h-5" />,
    feature_discovery: <Zap className="w-5 h-5" />,
    insight_extraction: <Sparkles className="w-5 h-5" />,
    visualization: <BarChart3 className="w-5 h-5" />,
    model_training: <TrendingUp className="w-5 h-5" />,
    model_evaluation: <CheckCircle2 className="w-5 h-5" />,
    code_generation: <Code2 className="w-5 h-5" />,
    report_generation: <FileBarChart className="w-5 h-5" />,
};

const Autopilot: React.FC = () => {
    const { isDark } = useUserStore();

    // State
    const [isRunning, setIsRunning] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [goal, setGoal] = useState('');
    const [targetColumn, setTargetColumn] = useState('');
    const [steps, setSteps] = useState<AutopilotStep[]>([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(-1);
    const [insights, setInsights] = useState<string[]>([]);
    const [sessionInfo, setSessionInfo] = useState<any>(null);
    const [finalSummary, setFinalSummary] = useState('');
    const [finalData, setFinalData] = useState<any>(null);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [error, setError] = useState('');
    const [showInsights, setShowInsights] = useState(true);
    const [dragOver, setDragOver] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const insightsEndRef = useRef<HTMLDivElement>(null);
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const abortRef = useRef<AbortController | null>(null);

    // Timer
    useEffect(() => {
        if (isRunning) {
            const start = Date.now();
            timerRef.current = setInterval(() => setElapsedTime(Math.floor((Date.now() - start) / 1000)), 1000);
        } else {
            if (timerRef.current) clearInterval(timerRef.current);
        }
        return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }, [isRunning]);

    // Auto-scroll insights
    useEffect(() => {
        insightsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [insights]);

    const handleFileSelect = useCallback((selectedFile: File) => {
        setFile(selectedFile);
        setIsComplete(false);
        setSteps([]);
        setInsights([]);
        setError('');
        setFinalSummary('');
        setFinalData(null);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && (droppedFile.name.endsWith('.csv') || droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
            handleFileSelect(droppedFile);
        }
    }, [handleFileSelect]);

    const startAutopilot = async () => {
        if (!file) return;

        setIsRunning(true);
        setIsComplete(false);
        setSteps([]);
        setInsights([]);
        setError('');
        setFinalSummary('');
        setFinalData(null);
        setCurrentStepIndex(-1);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('goal', goal || 'Perform comprehensive autonomous data analysis');
        formData.append('user_id', getUserIdSync());
        if (targetColumn.trim()) formData.append('target_column', targetColumn);

        try {
            abortRef.current = new AbortController();
            
            const baseUrl = api.defaults.baseURL || '';
            const response = await fetch(`${baseUrl}/api/v1/autopilot/run`, {
                method: 'POST',
                body: formData,
                signal: abortRef.current.signal,
                headers: {
                    'X-User-ID': getUserIdSync(),
                },
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errData.detail || 'Failed to start autopilot');
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No response stream');

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6).trim();
                        if (data === '[DONE]') {
                            setIsRunning(false);
                            setIsComplete(true);
                            continue;
                        }
                        try {
                            const event: AutopilotEvent = JSON.parse(data);
                            handleEvent(event);
                        } catch {}
                    }
                }
            }
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                setError(err.message || 'Autopilot failed');
            }
        } finally {
            setIsRunning(false);
        }
    };

    const handleEvent = (event: AutopilotEvent) => {
        switch (event.type) {
            case 'session_start':
                setSessionInfo(event.data);
                break;

            case 'step_start':
                setCurrentStepIndex(event.data.step_index);
                setSteps(prev => {
                    const updated = [...prev];
                    // Add step if not already present
                    if (!updated.find(s => s.id === event.data.step.id)) {
                        updated.push(event.data.step);
                    } else {
                        const idx = updated.findIndex(s => s.id === event.data.step.id);
                        updated[idx] = event.data.step;
                    }
                    return updated;
                });
                break;

            case 'step_complete':
                setSteps(prev => {
                    const updated = [...prev];
                    const idx = updated.findIndex(s => s.id === event.data.step.id);
                    if (idx >= 0) updated[idx] = event.data.step;
                    return updated;
                });
                // Extract insights from step results
                if (event.data.step.result?.plan) {
                    setInsights(prev => [...prev, event.data.step.result.plan]);
                }
                break;

            case 'step_error':
                setSteps(prev => {
                    const updated = [...prev];
                    const idx = updated.findIndex(s => s.id === event.data.step.id);
                    if (idx >= 0) updated[idx] = event.data.step;
                    return updated;
                });
                break;

            case 'session_complete':
                setIsComplete(true);
                setIsRunning(false);
                if (event.data.insights) setInsights(event.data.insights);
                if (event.data.summary) setFinalSummary(event.data.summary);
                setFinalData(event.data);
                break;

            case 'error':
                setError(event.data.error);
                setIsRunning(false);
                break;
        }
    };

    const cancelAutopilot = () => {
        abortRef.current?.abort();
        setIsRunning(false);
    };

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return m > 0 ? `${m}m ${s}s` : `${s}s`;
    };

    // =========================================================================
    // RENDER
    // =========================================================================

    return (
        <div className="min-h-screen p-4 md:p-8" style={{ color: 'var(--text-primary)' }}>
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <div className="flex items-center gap-4 mb-2">
                    <div className="relative">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                            <Brain className="w-7 h-7 text-white" />
                        </div>
                        {isRunning && (
                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full animate-pulse border-2" style={{ borderColor: 'var(--bg-primary)' }} />
                        )}
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 via-purple-400 to-fuchsia-400 bg-clip-text text-transparent">
                            Agentic Autopilot
                        </h1>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            Autonomous AI Data Scientist — Upload data, set a goal, watch the magic
                        </p>
                    </div>
                    {isRunning && (
                        <div className="ml-auto flex items-center gap-3">
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                                <Clock className="w-4 h-4 text-emerald-400 animate-pulse" />
                                <span className="text-sm font-mono text-emerald-400">{formatTime(elapsedTime)}</span>
                            </div>
                            <button onClick={cancelAutopilot} className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded-xl transition-colors text-sm font-semibold">
                                <StopCircle className="w-4 h-4" /> Stop
                            </button>
                        </div>
                    )}
                </div>
            </motion.div>

            {/* Upload & Config Zone — shown when NOT running */}
            {!isRunning && !isComplete && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-3xl mx-auto space-y-6">
                    {/* Drop Zone */}
                    <div
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                        className={`relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 ${
                            dragOver ? 'border-purple-400 bg-purple-500/10 scale-[1.02]' :
                            file ? 'border-emerald-500/50 bg-emerald-500/5' :
                            'border-white/10 hover:border-purple-400/50 hover:bg-white/[0.02]'
                        }`}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".csv,.xlsx,.xls"
                            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                            className="hidden"
                        />
                        {file ? (
                            <div className="space-y-2">
                                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
                                <p className="text-lg font-bold text-emerald-400">{file.name}</p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    {(file.size / 1024).toFixed(1)} KB — Click to change
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <Upload className="w-16 h-16 mx-auto" style={{ color: 'var(--text-muted)', opacity: 0.5 }} />
                                <p className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Drop your data file here</p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>CSV, Excel — up to 50K rows</p>
                            </div>
                        )}
                    </div>

                    {/* Goal & Config */}
                    {file && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
                                    🎯 Goal (optional)
                                </label>
                                <input
                                    type="text"
                                    value={goal}
                                    onChange={(e) => setGoal(e.target.value)}
                                    placeholder="e.g., Predict customer churn, Find sales patterns, Forecast revenue..."
                                    className="w-full px-4 py-3 rounded-xl border text-base focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
                                    style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
                                    🎯 Target column (optional — AI will auto-detect)
                                </label>
                                <input
                                    type="text"
                                    value={targetColumn}
                                    onChange={(e) => setTargetColumn(e.target.value)}
                                    placeholder="e.g., price, churn, revenue (leave blank for auto-detect)"
                                    className="w-full px-4 py-3 rounded-xl border text-base focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
                                    style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                />
                            </div>

                            {/* Launch Button */}
                            <button
                                onClick={startAutopilot}
                                className="w-full py-4 rounded-2xl bg-gradient-to-r from-violet-600 via-purple-600 to-fuchsia-600 hover:from-violet-500 hover:via-purple-500 hover:to-fuchsia-500 text-white font-bold text-lg shadow-xl shadow-purple-500/30 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-3"
                            >
                                <Rocket className="w-6 h-6" />
                                Launch Autopilot
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        </motion.div>
                    )}
                </motion.div>
            )}

            {/* Pipeline Execution View */}
            {(isRunning || isComplete) && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* LEFT: Pipeline Steps */}
                    <div className="lg:col-span-1 space-y-3">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                            <Sparkles className="w-5 h-5 text-purple-400" /> Pipeline
                        </h3>
                        {steps.map((step, i) => (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className={`flex items-start gap-3 p-3 rounded-xl border transition-all ${
                                    step.status === 'running' ? 'border-purple-500/50 bg-purple-500/10 shadow-lg shadow-purple-500/10' :
                                    step.status === 'completed' ? 'border-emerald-500/30 bg-emerald-500/5' :
                                    step.status === 'failed' ? 'border-red-500/30 bg-red-500/5' :
                                    'border-white/5 bg-white/[0.02]'
                                }`}
                            >
                                <div className={`mt-0.5 shrink-0 ${
                                    step.status === 'running' ? 'text-purple-400 animate-pulse' :
                                    step.status === 'completed' ? 'text-emerald-400' :
                                    step.status === 'failed' ? 'text-red-400' :
                                    'text-white/30'
                                }`}>
                                    {step.status === 'running' ? <Loader2 className="w-5 h-5 animate-spin" /> :
                                     step.status === 'completed' ? <CheckCircle2 className="w-5 h-5" /> :
                                     step.status === 'failed' ? <XCircle className="w-5 h-5" /> :
                                     PHASE_ICONS[step.phase] || <div className="w-5 h-5 rounded-full border-2 border-current" />}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className={`text-sm font-semibold ${
                                        step.status === 'running' ? 'text-purple-300' :
                                        step.status === 'completed' ? 'text-emerald-300' :
                                        step.status === 'failed' ? 'text-red-300' :
                                        ''
                                    }`} style={{ color: step.status === 'pending' ? 'var(--text-muted)' : undefined }}>
                                        {step.title}
                                    </p>
                                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                                        {step.status === 'completed' && step.duration_ms
                                            ? `Done in ${(step.duration_ms / 1000).toFixed(1)}s`
                                            : step.description}
                                    </p>
                                    {step.error && (
                                        <p className="text-xs text-red-400 mt-1 flex items-center gap-1">
                                            <AlertTriangle className="w-3 h-3" /> {step.error.slice(0, 100)}
                                        </p>
                                    )}
                                </div>
                            </motion.div>
                        ))}

                        {/* Pending steps placeholder */}
                        {isRunning && steps.length < 10 && (
                            <div className="space-y-2">
                                {Array.from({ length: 10 - steps.length }).map((_, i) => (
                                    <div key={`pending-${i}`} className="flex items-center gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.01]">
                                        <div className="w-5 h-5 rounded-full border-2 border-white/10" />
                                        <div className="h-3 rounded-full bg-white/5 flex-1" />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* RIGHT: Insights & Results */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* Session Info Banner */}
                        {sessionInfo && (
                            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                                className="p-4 rounded-xl border border-purple-500/20 bg-purple-500/5">
                                <div className="flex items-center justify-between flex-wrap gap-2">
                                    <div className="flex items-center gap-3">
                                        <FileText className="w-5 h-5 text-purple-400" />
                                        <span className="font-semibold text-sm">{sessionInfo.filename}</span>
                                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                                            {sessionInfo.rows?.toLocaleString()} rows × {sessionInfo.cols} cols
                                        </span>
                                    </div>
                                    {isRunning && (
                                        <div className="flex items-center gap-2 text-emerald-400">
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span className="text-sm font-mono">{formatTime(elapsedTime)}</span>
                                        </div>
                                    )}
                                    {isComplete && (
                                        <span className="text-sm font-bold text-emerald-400 flex items-center gap-1">
                                            <CheckCircle2 className="w-4 h-4" /> Complete — {formatTime(elapsedTime)}
                                        </span>
                                    )}
                                </div>
                            </motion.div>
                        )}

                        {/* Insights Stream */}
                        <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border-color)', background: 'var(--bg-secondary)' }}>
                            <button
                                onClick={() => setShowInsights(!showInsights)}
                                className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/[0.03] transition-colors"
                            >
                                <span className="font-bold text-sm flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-amber-400" />
                                    Live Insights ({insights.length})
                                </span>
                                {showInsights ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                            <AnimatePresence>
                                {showInsights && (
                                    <motion.div
                                        initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="px-4 pb-4 space-y-2 max-h-[400px] overflow-y-auto">
                                            {insights.length === 0 && isRunning && (
                                                <p className="text-sm italic py-4" style={{ color: 'var(--text-muted)' }}>
                                                    Analyzing your data... insights will appear here in real-time
                                                </p>
                                            )}
                                            {insights.map((insight, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: 20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    className="text-sm p-3 rounded-lg border border-white/5 bg-white/[0.02] leading-relaxed whitespace-pre-wrap"
                                                    style={{ color: 'var(--text-primary)' }}
                                                >
                                                    {insight}
                                                </motion.div>
                                            ))}
                                            <div ref={insightsEndRef} />
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Mission Accomplished Dashboard */}
                        {isComplete && finalSummary && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                                className="p-6 rounded-2xl border bg-gradient-to-br from-emerald-500/10 to-teal-500/5 shadow-xl shadow-emerald-500/5"
                                style={{ borderColor: isDark ? 'rgba(16, 185, 129, 0.3)' : 'rgba(16, 185, 129, 0.4)' }}
                            >
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-2xl font-black text-emerald-500 flex items-center gap-3">
                                        <Rocket className="w-8 h-8" />
                                        Mission Accomplished
                                    </h3>
                                    <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 font-bold rounded-full text-sm">
                                        Pipeline 100%
                                    </span>
                                </div>

                                {/* Metric Cards */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                    <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-center">
                                        <p className="text-xs text-emerald-600/80 uppercase font-bold mb-1">Rows Cleaned</p>
                                        <p className="text-xl font-black text-emerald-400">{sessionInfo?.rows?.toLocaleString() || 'N/A'}</p>
                                    </div>
                                    <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-center">
                                        <p className="text-xs text-emerald-600/80 uppercase font-bold mb-1">Insights Found</p>
                                        <p className="text-xl font-black text-emerald-400">{finalData?.insights_count || 0}</p>
                                    </div>
                                    <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-center">
                                        <p className="text-xs text-emerald-600/80 uppercase font-bold mb-1">Model Trained</p>
                                        <p className="text-xl font-black text-emerald-400">{finalData?.model_trained ? 'YES' : 'NO'}</p>
                                    </div>
                                    <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-center">
                                        <p className="text-xs text-emerald-600/80 uppercase font-bold mb-1">Duration</p>
                                        <p className="text-xl font-black text-emerald-400">{formatTime(finalData?.elapsed_seconds || elapsedTime)}</p>
                                    </div>
                                </div>

                                {finalData?.model_result && (
                                    <div className="mb-6 p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 flex items-center gap-4">
                                        <div className="p-3 bg-emerald-500/20 rounded-lg text-emerald-400">
                                            <Brain className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-emerald-300">AI Model Deployed to DataHub</h4>
                                            <p className="text-sm text-emerald-400/80">
                                                {finalData.model_result.model_type === 'classification' 
                                                    ? `Accuracy: ${(finalData.model_result.metrics?.accuracy * 100 || 0).toFixed(1)}%` 
                                                    : `R² Score: ${(finalData.model_result.metrics?.r2 || 0).toFixed(3)}`} 
                                                {' '}— Ready for API consumption.
                                            </p>
                                        </div>
                                    </div>
                                )}

                                <div className="p-4 rounded-xl border border-white/10 bg-black/20">
                                    <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                        <FileText className="w-4 h-4 text-purple-400" /> Executive Summary
                                    </h4>
                                    <div className="prose prose-sm prose-invert max-w-none whitespace-pre-wrap leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                        {finalSummary}
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {/* Restart Button */}
                        {isComplete && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-center pt-4">
                                <button
                                    onClick={() => { setIsComplete(false); setFile(null); setSteps([]); setInsights([]); setFinalSummary(''); }}
                                    className="flex items-center gap-2 px-6 py-3 rounded-xl border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 font-semibold transition-colors"
                                >
                                    <RefreshCw className="w-4 h-4" /> Analyze Another Dataset
                                </button>
                            </motion.div>
                        )}

                        {/* Error */}
                        {error && (
                            <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm">
                                <strong>Error:</strong> {error}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Autopilot;
