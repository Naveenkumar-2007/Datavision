/**
 * 🔧 Auto-Fix Component
 * 
 * Autonomous data quality fixes:
 * - Missing value imputation
 * - Outlier detection & handling
 * - Duplicate removal
 * - Data type corrections
 * - Date feature enrichment
 */

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
    Wrench,
    Upload,
    FileSpreadsheet,
    CheckCircle,
    AlertCircle,
    Loader,
    Download,
    Trash2,
    TrendingUp,
    AlertTriangle,
    Zap,
    Sparkles,
    RotateCcw,
    Settings,
} from 'lucide-react';

interface AutoFixReport {
    original_shape: { rows: number; cols: number };
    final_shape: { rows: number; cols: number };
    fixes_applied: Array<{
        operation: string;
        column: string | null;
        rows_affected: number;
        description: string;
    }>;
    enrichments_added: string[];
    quality_improvement: {
        before: number;
        after: number;
        improvement: number;
    };
    processing_time_ms: number;
}

interface AutoFixProps {
    theme: {
        isDark: boolean;
        bgColor: string;
        cardBg: string;
        textPrimary: string;
        textMuted: string;
        borderColor: string;
    };
    userId?: string;
    onFixComplete?: (fixedFile: string, report: AutoFixReport) => void;
}

const AutoFix: React.FC<AutoFixProps> = ({ theme, userId = 'default', onFixComplete }) => {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [detecting, setDetecting] = useState(false);
    const [report, setReport] = useState<AutoFixReport | null>(null);
    const [detectedIssues, setDetectedIssues] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [showOptions, setShowOptions] = useState(false);

    // Fix options
    const [options, setOptions] = useState({
        fix_missing: true,
        fix_outliers: true,
        fix_duplicates: true,
        fix_types: true,
        enrich_dates: true,
        aggressive: false,
    });

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            setFile(acceptedFiles[0]);
            setReport(null);
            setDetectedIssues(null);
            setError(null);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls'],
        },
        maxFiles: 1,
    });

    const handleDetectIssues = async () => {
        if (!file) return;

        setDetecting(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/v2/autonomous/detect-issues', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                setDetectedIssues(data);
            } else {
                setError(data.detail || 'Detection failed');
            }
        } catch (err) {
            setError('Failed to detect issues');
            console.error('Detect error:', err);
        } finally {
            setDetecting(false);
        }
    };

    const handleAutoFix = async () => {
        if (!file) return;

        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', userId);

            // Add options
            Object.entries(options).forEach(([key, value]) => {
                formData.append(key, String(value));
            });

            const response = await fetch('/api/v2/autonomous/auto-fix', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                setReport(data.report);
                if (onFixComplete) {
                    onFixComplete(data.fixed_file, data.report);
                }
            } else {
                setError(data.detail || 'Auto-fix failed');
            }
        } catch (err) {
            setError('Failed to process file');
            console.error('Auto-fix error:', err);
        } finally {
            setLoading(false);
        }
    };

    const getOperationIcon = (operation: string) => {
        switch (operation) {
            case 'remove_duplicates': return Trash2;
            case 'impute_missing': return Wrench;
            case 'cap_outliers': return AlertTriangle;
            case 'convert_to_numeric': return TrendingUp;
            case 'convert_to_datetime': return Sparkles;
            default: return CheckCircle;
        }
    };

    const reset = () => {
        setFile(null);
        setReport(null);
        setDetectedIssues(null);
        setError(null);
    };

    return (
        <div className="space-y-6">
            {/* File Upload */}
            {!file && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div
                        {...getRootProps()}
                        className={`p-8 rounded-2xl border-2 border-dashed cursor-pointer transition-all ${isDragActive ? 'border-emerald-500 bg-emerald-500/10' : ''
                            }`}
                        style={{
                            borderColor: isDragActive ? '#10b981' : theme.borderColor,
                            backgroundColor: isDragActive ? 'rgba(16, 185, 129, 0.1)' : theme.cardBg
                        }}
                    >
                        <input {...getInputProps()} />
                        <div className="text-center">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                                <Wrench className="w-8 h-8 text-amber-400" />
                            </div>
                            <h3 className="text-lg font-semibold mb-2" style={{ color: theme.textPrimary }}>
                                Auto-Fix Your Data
                            </h3>
                            <p style={{ color: theme.textMuted }}>
                                Drop a CSV or Excel file to automatically fix data quality issues
                            </p>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* File Selected */}
            {file && !report && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                >
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                            <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
                        </div>
                        <div className="flex-1">
                            <p className="font-medium" style={{ color: theme.textPrimary }}>{file.name}</p>
                            <p className="text-sm" style={{ color: theme.textMuted }}>
                                {(file.size / 1024).toFixed(1)} KB
                            </p>
                        </div>
                        <button
                            onClick={reset}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                            style={{ color: theme.textMuted }}
                        >
                            <RotateCcw className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Options Toggle */}
                    <button
                        onClick={() => setShowOptions(!showOptions)}
                        className="flex items-center gap-2 text-sm mb-4 hover:opacity-80 transition-opacity"
                        style={{ color: theme.textMuted }}
                    >
                        <Settings className="w-4 h-4" />
                        {showOptions ? 'Hide' : 'Show'} Options
                    </button>

                    {/* Options Panel */}
                    <AnimatePresence>
                        {showOptions && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4 overflow-hidden"
                            >
                                {Object.entries(options).map(([key, value]) => (
                                    <label
                                        key={key}
                                        className="flex items-center gap-2 cursor-pointer p-2 rounded-lg hover:bg-white/5"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={value}
                                            onChange={(e) => setOptions(prev => ({ ...prev, [key]: e.target.checked }))}
                                            className="rounded border-gray-600 bg-gray-700 text-emerald-500 focus:ring-emerald-500"
                                        />
                                        <span className="text-sm" style={{ color: theme.textPrimary }}>
                                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        </span>
                                    </label>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Detected Issues */}
                    {detectedIssues && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="p-4 rounded-xl mb-4"
                            style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)' }}
                        >
                            <h4 className="font-medium mb-2" style={{ color: theme.textPrimary }}>Issues Detected:</h4>
                            <ul className="space-y-1 text-sm">
                                {detectedIssues.issues.missing_values?.length > 0 && (
                                    <li className="flex items-center gap-2 text-amber-400">
                                        <AlertTriangle className="w-4 h-4" />
                                        {detectedIssues.issues.missing_values.length} columns with missing values
                                    </li>
                                )}
                                {detectedIssues.issues.duplicates?.length > 0 && (
                                    <li className="flex items-center gap-2 text-amber-400">
                                        <Trash2 className="w-4 h-4" />
                                        Duplicate rows detected
                                    </li>
                                )}
                                {detectedIssues.issues.outliers?.length > 0 && (
                                    <li className="flex items-center gap-2 text-amber-400">
                                        <TrendingUp className="w-4 h-4" />
                                        {detectedIssues.issues.outliers.length} columns with outliers
                                    </li>
                                )}
                            </ul>
                            <p className="mt-2 text-sm" style={{ color: theme.textMuted }}>
                                {detectedIssues.recommendation}
                            </p>
                        </motion.div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/20 border border-red-500/30 mb-4 flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400" />
                            <span className="text-red-400">{error}</span>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button
                            onClick={handleDetectIssues}
                            disabled={detecting || loading}
                            className="flex-1 px-4 py-3 rounded-xl border transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                            style={{ borderColor: theme.borderColor, color: theme.textPrimary }}
                        >
                            {detecting ? (
                                <Loader className="w-5 h-5 animate-spin" />
                            ) : (
                                <AlertTriangle className="w-5 h-5" />
                            )}
                            Detect Issues
                        </button>
                        <button
                            onClick={handleAutoFix}
                            disabled={loading || detecting}
                            className="flex-1 px-4 py-3 bg-gradient-to-r from-emerald-500 to-green-500 rounded-xl text-white font-semibold transition-opacity hover:opacity-90 flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {loading ? (
                                <Loader className="w-5 h-5 animate-spin" />
                            ) : (
                                <Zap className="w-5 h-5" />
                            )}
                            Auto-Fix Now
                        </button>
                    </div>
                </motion.div>
            )}

            {/* Fix Report */}
            {report && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                >
                    {/* Success Header */}
                    <div
                        className="p-6 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30"
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 rounded-2xl bg-emerald-500 flex items-center justify-center">
                                <CheckCircle className="w-8 h-8 text-white" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-emerald-400">Data Fixed!</h3>
                                <p style={{ color: theme.textMuted }}>
                                    Quality improved from {(report.quality_improvement.before * 100).toFixed(0)}% to{' '}
                                    <span className="text-emerald-400 font-bold">
                                        {(report.quality_improvement.after * 100).toFixed(0)}%
                                    </span>
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                            <p className="text-sm" style={{ color: theme.textMuted }}>Original Rows</p>
                            <p className="text-xl font-bold" style={{ color: theme.textPrimary }}>
                                {report.original_shape.rows.toLocaleString()}
                            </p>
                        </div>
                        <div className="p-4 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                            <p className="text-sm" style={{ color: theme.textMuted }}>Final Rows</p>
                            <p className="text-xl font-bold text-emerald-400">
                                {report.final_shape.rows.toLocaleString()}
                            </p>
                        </div>
                        <div className="p-4 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                            <p className="text-sm" style={{ color: theme.textMuted }}>Fixes Applied</p>
                            <p className="text-xl font-bold text-amber-400">
                                {report.fixes_applied.length}
                            </p>
                        </div>
                        <div className="p-4 rounded-xl" style={{ backgroundColor: theme.cardBg }}>
                            <p className="text-sm" style={{ color: theme.textMuted }}>Processing Time</p>
                            <p className="text-xl font-bold text-blue-400">
                                {report.processing_time_ms}ms
                            </p>
                        </div>
                    </div>

                    {/* Fixes Applied */}
                    {report.fixes_applied.length > 0 && (
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h4 className="font-semibold mb-4" style={{ color: theme.textPrimary }}>Fixes Applied:</h4>
                            <div className="space-y-2">
                                {report.fixes_applied.map((fix, index) => {
                                    const Icon = getOperationIcon(fix.operation);
                                    return (
                                        <div
                                            key={index}
                                            className="flex items-center gap-3 p-3 rounded-xl"
                                            style={{ backgroundColor: theme.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                        >
                                            <Icon className="w-5 h-5 text-emerald-400" />
                                            <span className="flex-1" style={{ color: theme.textPrimary }}>
                                                {fix.description}
                                            </span>
                                            {fix.rows_affected > 0 && (
                                                <span className="text-sm px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-400">
                                                    {fix.rows_affected} rows
                                                </span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Enrichments */}
                    {report.enrichments_added.length > 0 && (
                        <div
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: theme.cardBg, borderColor: theme.borderColor }}
                        >
                            <h4 className="font-semibold mb-4 flex items-center gap-2" style={{ color: theme.textPrimary }}>
                                <Sparkles className="w-5 h-5 text-purple-400" />
                                New Features Added:
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {report.enrichments_added.map((feature, index) => (
                                    <span
                                        key={index}
                                        className="px-3 py-1 rounded-lg bg-purple-500/20 text-purple-400 text-sm"
                                    >
                                        {feature}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button
                            onClick={reset}
                            className="px-4 py-3 rounded-xl border transition-colors flex items-center gap-2"
                            style={{ borderColor: theme.borderColor, color: theme.textMuted }}
                        >
                            <RotateCcw className="w-5 h-5" />
                            Fix Another File
                        </button>
                    </div>
                </motion.div>
            )}
        </div>
    );
};

export default AutoFix;
