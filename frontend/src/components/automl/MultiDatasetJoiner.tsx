import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, FileText, ArrowRight, X, Play, Loader2, CheckCircle, Database } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import apiService from '@/services/api';
import { useToast } from '@/contexts/ToastContext';

interface MultiDatasetJoinerProps {
    isOpen: boolean;
    onClose: () => void;
    files: Array<{ name: string; size: number }>;
    onSuccess: (newFileName: string) => void;
}

const MultiDatasetJoiner: React.FC<MultiDatasetJoinerProps> = ({ isOpen, onClose, files, onSuccess }) => {
    const isDark = useUserStore((state) => state.isDark);
    const { addToast } = useToast();
    const [file1, setFile1] = useState('');
    const [file2, setFile2] = useState('');
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [suggestions, setSuggestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    
    // Join configurations
    const [selectedJoin, setSelectedJoin] = useState<any>(null);
    const [joinType, setJoinType] = useState('left');
    const [outputName, setOutputName] = useState('');

    useEffect(() => {
        if (!isOpen) {
            setStep(1);
            setFile1('');
            setFile2('');
            setSuggestions([]);
            setSelectedJoin(null);
            setOutputName('');
        }
    }, [isOpen]);

    const handleAnalyze = async () => {
        if (!file1 || !file2) return;
        setLoading(true);
        try {
            const res = await apiService.getJoinSuggestions(file1, file2);
            setSuggestions(res.suggestions || []);
            if (res.suggestions && res.suggestions.length > 0) {
                setSelectedJoin(res.suggestions[0]);
                setOutputName(`joined_${file1.replace('.csv', '')}_${file2}`);
            }
            setStep(2);
        } catch (err: any) {
            addToast('error', 'Analysis Failed', err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleJoin = async () => {
        if (!selectedJoin || !outputName) return;
        setLoading(true);
        try {
            const res = await apiService.joinDatasets({
                file1,
                file2,
                left_on: selectedJoin.left_key,
                right_on: selectedJoin.right_key,
                how: joinType,
                output_filename: outputName
            });
            addToast('success', 'Datasets Joined!', `Created ${res.filename} with ${res.rows} rows.`);
            onSuccess(res.filename);
            onClose();
        } catch (err: any) {
            addToast('error', 'Join Failed', err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="w-full max-w-3xl rounded-2xl overflow-hidden border shadow-2xl flex flex-col"
                    style={{
                        backgroundColor: 'var(--bg-surface)',
                        borderColor: 'var(--border-color)',
                        color: 'var(--text-primary)',
                        maxHeight: '90vh'
                    }}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                                <Network className="w-5 h-5 text-purple-500" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">Multi-Dataset Intelligence</h2>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Automatically discover relationships and merge datasets</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 rounded-xl transition-colors hover:bg-white/5">
                            <X className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6 overflow-y-auto flex-1">
                        {/* Step 1: Select Files */}
                        {step === 1 && (
                            <div className="space-y-6">
                                <div className="grid grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-sm font-semibold">Primary Dataset (Left)</label>
                                        <select
                                            value={file1}
                                            onChange={e => setFile1(e.target.value)}
                                            className="w-full p-3 rounded-xl border appearance-none outline-none focus:ring-2 focus:ring-purple-500/50"
                                            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                        >
                                            <option value="">Select a dataset...</option>
                                            {files.map(f => (
                                                <option key={f.name} value={f.name}>{f.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-semibold">Secondary Dataset (Right)</label>
                                        <select
                                            value={file2}
                                            onChange={e => setFile2(e.target.value)}
                                            className="w-full p-3 rounded-xl border appearance-none outline-none focus:ring-2 focus:ring-purple-500/50"
                                            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                        >
                                            <option value="">Select a dataset...</option>
                                            {files.filter(f => f.name !== file1).map(f => (
                                                <option key={f.name} value={f.name}>{f.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                
                                <div className="flex justify-center mt-8">
                                    <button
                                        onClick={handleAnalyze}
                                        disabled={!file1 || !file2 || loading}
                                        className="px-8 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                                        Analyze Relationships
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 2: Confirm Join */}
                        {step === 2 && (
                            <div className="space-y-6">
                                {suggestions.length > 0 ? (
                                    <div className="p-4 rounded-xl border border-green-500/20 bg-green-500/5 flex items-start gap-4">
                                        <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
                                        <div>
                                            <h4 className="font-semibold text-green-500 mb-1">Relationships Discovered</h4>
                                            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                                Found {suggestions.length} possible join configuration(s) between <strong>{file1}</strong> and <strong>{file2}</strong>.
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-4 rounded-xl border border-yellow-500/20 bg-yellow-500/5">
                                        <h4 className="font-semibold text-yellow-500 mb-1">No confident relationships found</h4>
                                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                            You can still manually configure the join below.
                                        </p>
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Configuration</h3>
                                    
                                    <div className="grid grid-cols-3 gap-4 items-center">
                                        <div>
                                            <label className="text-xs mb-1 block" style={{ color: 'var(--text-muted)' }}>Left Key ({file1})</label>
                                            <input 
                                                type="text" 
                                                value={selectedJoin?.left_key || ''} 
                                                onChange={e => setSelectedJoin({...selectedJoin, left_key: e.target.value})}
                                                className="w-full p-2.5 text-sm rounded-lg border outline-none"
                                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                            />
                                        </div>
                                        <div className="flex flex-col items-center justify-center pt-5">
                                            <ArrowRight className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                                            <span className="text-[10px] uppercase font-bold text-purple-500 mt-1">{joinType} join</span>
                                        </div>
                                        <div>
                                            <label className="text-xs mb-1 block" style={{ color: 'var(--text-muted)' }}>Right Key ({file2})</label>
                                            <input 
                                                type="text" 
                                                value={selectedJoin?.right_key || ''} 
                                                onChange={e => setSelectedJoin({...selectedJoin, right_key: e.target.value})}
                                                className="w-full p-2.5 text-sm rounded-lg border outline-none"
                                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mt-4">
                                        <div>
                                            <label className="text-xs mb-1 block" style={{ color: 'var(--text-muted)' }}>Join Type</label>
                                            <select
                                                value={joinType}
                                                onChange={e => setJoinType(e.target.value)}
                                                className="w-full p-2.5 text-sm rounded-lg border outline-none appearance-none"
                                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                            >
                                                <option value="left">Left Join (Keep all from {file1})</option>
                                                <option value="inner">Inner Join (Keep only matches)</option>
                                                <option value="outer">Outer Join (Keep all from both)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs mb-1 block" style={{ color: 'var(--text-muted)' }}>Output Filename</label>
                                            <input 
                                                type="text" 
                                                value={outputName} 
                                                onChange={e => setOutputName(e.target.value)}
                                                className="w-full p-2.5 text-sm rounded-lg border outline-none"
                                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                            />
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="flex justify-end gap-3 mt-8 border-t pt-6" style={{ borderColor: 'var(--border-color)' }}>
                                    <button
                                        onClick={() => setStep(1)}
                                        className="px-6 py-2.5 rounded-xl font-medium transition-colors hover:bg-white/5"
                                    >
                                        Back
                                    </button>
                                    <button
                                        onClick={handleJoin}
                                        disabled={!selectedJoin?.left_key || !selectedJoin?.right_key || !outputName || loading}
                                        className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2"
                                    >
                                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
                                        Execute Join
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default MultiDatasetJoiner;

