/**
 * 🗂️ Multi-File Training Component
 * 
 * Allows users to upload separate train and test files for ML training.
 * Connects to the /api/v1/automl/train_with_test endpoint.
 */

import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
    Upload,
    FileSpreadsheet,
    CheckCircle,
    XCircle,
    Loader,
    ArrowRight,
    Info,
    AlertTriangle,
    Zap,
    Brain,
} from 'lucide-react';
import apiService from '@/services/api';

// Theme interface removed


interface MultiFileUploadProps {
    onTrainingComplete: (result: any) => void;
    ultraMode?: boolean;
    onUltraModeChange?: (mode: boolean) => void;
}

interface FileInfo {
    file: File | null;
    name: string;
    rows: number | null;
    columns: number | null;
    error: string | null;
}

const MultiFileUpload: React.FC<MultiFileUploadProps> = ({ onTrainingComplete, ultraMode: parentUltraMode, onUltraModeChange }) => {
    const [trainFile, setTrainFile] = useState<FileInfo>({ file: null, name: '', rows: null, columns: null, error: null });
    const [testFile, setTestFile] = useState<FileInfo>({ file: null, name: '', rows: null, columns: null, error: null });
    const [targetColumn, setTargetColumn] = useState<string>('');
    const [columns, setColumns] = useState<string[]>([]);
    const [isTraining, setIsTraining] = useState(false);
    const [trainingProgress, setTrainingProgress] = useState('');
    const [error, setError] = useState<string | null>(null);

    // Use parent's ultraMode if provided, otherwise use local state
    const [localUltraMode, setLocalUltraMode] = useState(false);
    const ultraMode = parentUltraMode !== undefined ? parentUltraMode : localUltraMode;
    const setUltraMode = (mode: boolean) => {
        if (onUltraModeChange) {
            onUltraModeChange(mode);
        } else {
            setLocalUltraMode(mode);
        }
    };

    // AbortController for stopping training
    const [abortController, setAbortController] = useState<AbortController | null>(null);

    const trainInputRef = useRef<HTMLInputElement>(null);
    const testInputRef = useRef<HTMLInputElement>(null);

    // Parse CSV to get row/column count
    const parseCSV = (file: File): Promise<{ rows: number; columns: string[] }> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const lines = text.split('\n').filter(line => line.trim());
                const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
                resolve({ rows: lines.length - 1, columns: headers });
            };
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    };

    const handleFileSelect = async (type: 'train' | 'test', file: File | null) => {
        if (!file) return;

        const setter = type === 'train' ? setTrainFile : setTestFile;

        try {
            const parsed = await parseCSV(file);
            setter({
                file,
                name: file.name,
                rows: parsed.rows,
                columns: parsed.columns.length,
                error: null
            });

            // Set columns from train file for target selection
            if (type === 'train') {
                setColumns(parsed.columns);
                // Auto-select last column as target
                setTargetColumn(parsed.columns[parsed.columns.length - 1]);
            }

            // Validate test file has same columns
            if (type === 'test' && trainFile.file) {
                const trainParsed = await parseCSV(trainFile.file);
                if (parsed.columns.length !== trainParsed.columns.length) {
                    setter(prev => ({
                        ...prev,
                        error: `Column count mismatch: Train=${trainParsed.columns.length}, Test=${parsed.columns.length}`
                    }));
                }
            }

            // Immediately upload file to DataHub for persistence
            try {
                await apiService.uploadFiles([file]);
                // Notify DataHub to refresh file list
                window.dispatchEvent(new CustomEvent('filesUpdated'));
                console.log(`✅ ${file.name} uploaded to DataHub`);
            } catch (uploadErr) {
                console.warn('File upload to DataHub failed:', uploadErr);
            }

        } catch (err) {
            setter({
                file: null,
                name: file.name,
                rows: null,
                columns: null,
                error: 'Failed to parse file'
            });
        }
    };

    const handleTrain = async () => {
        if (!trainFile.file || !testFile.file) {
            setError('Please upload both train and test files');
            return;
        }

        setIsTraining(true);
        setError(null);
        setTrainingProgress('Starting training...');

        try {
            const userId = localStorage.getItem('userId') || 'default';

            // Files are already uploaded to DataHub on selection
            // Just proceed to training

            // Step 2: Train with the training file
            const trainFormData = new FormData();
            trainFormData.append('file', trainFile.file);
            trainFormData.append('user_id', userId);
            if (targetColumn) {
                trainFormData.append('target_column', targetColumn);
            }

            // Use Ultra or Fast endpoint based on mode
            const endpoint = ultraMode ? '/api/v2/automl/ultra_train' : '/api/v2/automl/train';
            const modeLabel = ultraMode ? 'Ultra' : 'Fast';

            if (ultraMode) {
                trainFormData.append('mode', 'maximum_accuracy');
                setTrainingProgress(`🚀 ${modeLabel} Training (5-10 minutes)...`);
            } else {
                setTrainingProgress(`⚡ ${modeLabel} Training (1-2 minutes)...`);
            }

            // Create AbortController for this request
            const controller = new AbortController();
            setAbortController(controller);

            const response = await fetch(endpoint, {
                method: 'POST',
                body: trainFormData,
                signal: controller.signal,
            });

            setTrainingProgress('Processing results...');

            // Check response status first
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText.slice(0, 100)}`);
            }

            let result;
            try {
                result = await response.json();
            } catch (parseErr) {
                throw new Error('Failed to parse server response');
            }

            if (result.success) {
                setTrainingProgress(`Complete! ✅ (${modeLabel} Mode)`);

                // Save to localStorage like DataHub does (for dashboard/charts)
                try {
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(result));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                } catch (e) {
                    console.warn('Results too large for localStorage, saving without charts');
                    const { charts, ...lightResult } = result;
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(lightResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                }

                // Save charts if available
                if (result.charts) {
                    try {
                        sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(result.charts));
                    } catch (e) {
                        console.warn('Charts too large for sessionStorage');
                    }
                }

                // Dispatch event so dashboard updates
                window.dispatchEvent(new CustomEvent('filesUpdated'));

                // Small delay to show success before navigating
                setTimeout(() => {
                    onTrainingComplete(result);
                }, 500);
            } else {
                setError(result.detail || result.error || 'Training failed');
            }
        } catch (err: any) {
            if (err.name === 'AbortError') {
                setError('Training stopped by user');
            } else {
                console.error('Training error:', err);
                setError(err.message || 'Failed to connect to server');
            }
        } finally {
            setIsTraining(false);
            setAbortController(null);
        }
    };

    // Stop training handler
    const handleStopTraining = async () => {
        if (abortController) {
            abortController.abort();
        }
        setIsTraining(false);
        setAbortController(null);
        setTrainingProgress('');

        // Signal backend to stop
        try {
            const userId = localStorage.getItem('userId') || 'default';
            const formData = new FormData();
            formData.append('user_id', userId);
            await fetch('/api/v2/automl/stop_training', {
                method: 'POST',
                body: formData
            });
        } catch (e) {
            console.error('Failed to signal stop to backend', e);
        }
    };

    const [trainDragActive, setTrainDragActive] = useState(false);
    const [testDragActive, setTestDragActive] = useState(false);

    const handleDrop = (type: 'train' | 'test', e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (type === 'train') setTrainDragActive(false);
        else setTestDragActive(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelect(type, files[0]);
        }
    };

    const handleDragOver = (type: 'train' | 'test', e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (type === 'train') setTrainDragActive(true);
        else setTestDragActive(true);
    };

    const handleDragLeave = (type: 'train' | 'test', e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (type === 'train') setTrainDragActive(false);
        else setTestDragActive(false);
    };

    const FileDropZone = ({
        type,
        fileInfo,
        inputRef
    }: {
        type: 'train' | 'test';
        fileInfo: FileInfo;
        inputRef: React.RefObject<HTMLInputElement>;
    }) => {
        const isDragActive = type === 'train' ? trainDragActive : testDragActive;

        return (
            <div
                onClick={() => inputRef.current?.click()}
                onDrop={(e) => handleDrop(type, e)}
                onDragOver={(e) => handleDragOver(type, e)}
                onDragLeave={(e) => handleDragLeave(type, e)}
                className={`relative p-6 border-2 border-dashed rounded-2xl cursor-pointer transition-all ${isDragActive ? 'border-emerald-500 bg-emerald-500/10 scale-105' :
                    fileInfo.file ? 'border-emerald-500/30 bg-emerald-500/5' : 'hover:border-emerald-500/50'
                    }`}
                style={{
                    borderColor: isDragActive ? '#10b981' : fileInfo.file ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-color)',
                    transform: isDragActive ? 'scale(1.02)' : 'scale(1)'
                }}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="hidden"
                    onChange={(e) => handleFileSelect(type, e.target.files?.[0] || null)}
                />

                <div className="flex flex-col items-center gap-3">
                    {fileInfo.file ? (
                        <>
                            <div className="p-3 rounded-xl bg-emerald-500/20">
                                <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
                            </div>
                            <div className="text-center">
                                <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{fileInfo.name}</p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    {fileInfo.rows?.toLocaleString()} rows × {fileInfo.columns} columns
                                </p>
                            </div>
                            {fileInfo.error && (
                                <div className="flex items-center gap-2 text-red-400 text-sm">
                                    <AlertTriangle className="w-4 h-4" />
                                    {fileInfo.error}
                                </div>
                            )}
                        </>
                    ) : (
                        <>
                            <div className={`p-3 rounded-xl transition-all ${isDragActive ? 'bg-emerald-500/20' : ''}`} style={{ backgroundColor: !isDragActive ? 'var(--bg-secondary)' : undefined }}>
                                <Upload className={`w-8 h-8 ${isDragActive ? 'text-emerald-400' : ''}`} style={{ color: isDragActive ? '#10b981' : 'var(--text-muted)' }} />
                            </div>
                            <div className="text-center">
                                <p className="font-medium" style={{ color: isDragActive ? '#10b981' : 'var(--text-primary)' }}>
                                    {isDragActive ? 'Drop here!' : `Drop ${type === 'train' ? 'Training' : 'Test'} File`}
                                </p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    CSV or Excel
                                </p>
                            </div>
                        </>
                    )}
                </div>

                {/* Label Badge */}
                <div className={`absolute top-3 left-3 px-2 py-1 rounded-full text-xs font-medium ${type === 'train' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                    }`}>
                    {type === 'train' ? '📚 Train' : '🧪 Test'}
                </div>
            </div>
        );
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 rounded-2xl border"
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                Multi-File Training
                <span className="ml-2 px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-xs">
                    Separate Train/Test
                </span>
            </h3>

            <div className="flex items-center gap-2 mb-6 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                <Info className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Use separate train and test files for unbiased model evaluation. The test set will NOT be used for training.
                </p>
            </div>

            {/* File Upload Areas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <FileDropZone type="train" fileInfo={trainFile} inputRef={trainInputRef} />
                <FileDropZone type="test" fileInfo={testFile} inputRef={testInputRef} />
            </div>

            {/* Arrow indicator */}
            {trainFile.file && testFile.file && (
                <div className="flex items-center justify-center gap-4 mb-6">
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-500 to-transparent" />
                    <ArrowRight className="w-6 h-6 text-emerald-400" />
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-500 to-transparent" />
                </div>
            )}

            {/* Target Column Selection */}
            {columns.length > 0 && (
                <div className="mb-6">
                    <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                        Target Column
                    </label>
                    <select
                        value={targetColumn}
                        onChange={(e) => setTargetColumn(e.target.value)}
                        className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-emerald-500"
                        style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                    >
                        {columns.map((col) => (
                            <option key={col} value={col} style={{ backgroundColor: 'var(--bg-card)' }}>
                                {col}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Fast/Ultra Mode Toggle */}
            {columns.length > 0 && (
                <div className="mb-6 flex items-center gap-4">
                    <button
                        onClick={() => setUltraMode(false)}
                        disabled={isTraining}
                        className={`flex-1 p-4 rounded-xl border-2 transition-all ${!ultraMode
                            ? 'border-emerald-500 bg-emerald-500/10'
                            : 'border-transparent hover:border-gray-500/30'
                            }`}
                        style={{ backgroundColor: !ultraMode ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-card)' }}
                    >
                        <div className="flex items-center gap-3">
                            <Zap className={`w-6 h-6 ${!ultraMode ? 'text-emerald-400' : 'text-gray-500'}`} />
                            <div className="text-left">
                                <p className="font-semibold" style={{ color: !ultraMode ? '#10b981' : 'var(--text-primary)' }}>
                                    ⚡ Fast Mode
                                </p>
                                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                    1-2 min • 7 models
                                </p>
                            </div>
                        </div>
                    </button>

                    <button
                        onClick={() => setUltraMode(true)}
                        disabled={isTraining}
                        className={`flex-1 p-4 rounded-xl border-2 transition-all ${ultraMode
                            ? 'border-purple-500 bg-purple-500/10'
                            : 'border-transparent hover:border-gray-500/30'
                            }`}
                        style={{ backgroundColor: ultraMode ? 'rgba(139, 92, 246, 0.1)' : 'var(--bg-card)' }}
                    >
                        <div className="flex items-center gap-3">
                            <Brain className={`w-6 h-6 ${ultraMode ? 'text-purple-400' : 'text-gray-500'}`} />
                            <div className="text-left">
                                <p className="font-semibold" style={{ color: ultraMode ? '#a78bfa' : 'var(--text-primary)' }}>
                                    🚀 Ultra Mode
                                </p>
                                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                    5-10 min • 20+ models
                                </p>
                            </div>
                        </div>
                    </button>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="flex items-center gap-2 p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/20">
                    <XCircle className="w-5 h-5 text-red-400" />
                    <p className="text-sm text-red-400">{error}</p>
                </div>
            )}

            {/* Train Button */}
            <div className="flex gap-3">
                <button
                    onClick={handleTrain}
                    disabled={!trainFile.file || !testFile.file || isTraining}
                    className={`flex-1 py-4 rounded-xl font-semibold flex items-center justify-center gap-3 transition-all ${trainFile.file && testFile.file && !isTraining
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:opacity-90'
                        : 'bg-gray-500/20 text-gray-500 cursor-not-allowed'
                        }`}
                >
                    {isTraining ? (
                        <>
                            <Loader className="w-5 h-5 animate-spin" />
                            {trainingProgress}
                        </>
                    ) : (
                        <>
                            <CheckCircle className="w-5 h-5" />
                            Train with Separate Test Set
                        </>
                    )}
                </button>

                {/* Stop Training Button - Only visible during training */}
                {isTraining && (
                    <button
                        onClick={handleStopTraining}
                        className="px-6 py-4 rounded-xl font-semibold bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-all flex items-center gap-2"
                    >
                        <XCircle className="w-5 h-5" />
                        Stop
                    </button>
                )}
            </div>

            {/* Summary Stats */}
            {trainFile.file && testFile.file && (
                <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                    <div>
                        <p className="text-2xl font-bold text-blue-400">{trainFile.rows?.toLocaleString()}</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Training Samples</p>
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-purple-400">{testFile.rows?.toLocaleString()}</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Test Samples</p>
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-emerald-400">{trainFile.columns}</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Features</p>
                    </div>
                </div>
            )}
        </motion.div>
    );
};

export default MultiFileUpload;
