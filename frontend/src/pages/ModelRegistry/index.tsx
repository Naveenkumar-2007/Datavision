import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Database, Rocket, Activity, Box, Search, Filter,
    ChevronDown, ChevronRight, Archive, Download, Play
} from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/services/api';

interface ModelVersion {
    id: string;
    version: number;
    algorithm: string;
    status: 'Draft' | 'Staging' | 'Production' | 'Archived';
    created_at: string;
}

interface MLModel {
    id: string;
    name: string;
    task_type: string;
    target_column: string;
    created_at: string;
    versions: ModelVersion[];
}

const ModelRegistry = () => {
    const [models, setModels] = useState<MLModel[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedModels, setExpandedModels] = useState<Set<string>>(new Set());
    const toast = useToast();
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    const [selectedPredictModel, setSelectedPredictModel] = useState<{id: string, name: string} | null>(null);
    
    useEffect(() => {
        fetchModels();
    }, []);
    
    const fetchModels = async () => {
        try {
            const res = await api.get('/api/v1/mlops/registry/models');
            if (res.data.success) {
                setModels(res.data.data);
            }
        } catch (err) {
            console.error("Failed to fetch models", err);
        } finally {
            setLoading(false);
        }
    };
    
    const toggleExpand = (id: string) => {
        const newSet = new Set(expandedModels);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setExpandedModels(newSet);
    };

    const promoteVersion = async (versionId: string, status: string) => {
        try {
            const res = await api.post('/api/v1/mlops/registry/promote', {
                version_id: versionId,
                status: status
            });
            if (res.data.success) {
                fetchModels();
            }
        } catch (err) {
            console.error("Promotion failed", err);
        }
    };
    
    const handleDownloadJoblib = async (versionId: string) => {
        try {
            toast.info("Preparing model file...");
            const res = await api.get(`/api/v1/automl/download-model/${versionId}`, {
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const a = document.createElement('a');
            a.href = url;
            a.download = `model_${versionId}.joblib`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success("Model downloaded successfully");
        } catch (err) {
            toast.error("Failed to download model");
        }
    };
    
    const triggerBatchPredict = (modelId: string, modelName: string) => {
        setSelectedPredictModel({ id: modelId, name: modelName });
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };
    
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !selectedPredictModel) return;
        
        try {
            toast.info(`Running batch prediction on ${file.name}...`);
            const formData = new FormData();
            formData.append('file', file);
            formData.append('model_name', selectedPredictModel.id);
            
            // We use native fetch here for raw blob response handling
            const authHeaders = api.defaults.headers.common;
            const res = await fetch('/api/v1/automl/batch-predict', {
                method: 'POST',
                headers: {
                    'Authorization': authHeaders['Authorization'] as string
                },
                body: formData
            });
            
            if (!res.ok) throw new Error("Batch prediction failed");
            
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `predictions_${file.name}`;
            a.click();
            toast.success('Batch predictions complete!');
        } catch (err: any) {
            toast.error(err.message || 'Prediction failed');
        } finally {
            if (e.target) e.target.value = '';
            setSelectedPredictModel(null);
        }
    };
    
    const getStatusStyle = (status: string) => {
        switch (status) {
            case 'Production': return 'bg-green-500/10 text-green-400 border-green-500/20';
            case 'Staging': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            case 'Archived': return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
            default: return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
        }
    };

    return (
        <div className="flex-1 overflow-auto bg-[var(--bg-primary)] p-8 relative">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
                        <Box className="w-8 h-8 text-blue-500" />
                        Model Registry
                    </h1>
                    <p className="text-[var(--text-muted)] text-lg">Central hub for tracking model lineage, versioning, and lifecycle management.</p>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-2xl p-6">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-blue-500/10 rounded-xl">
                            <Database className="w-6 h-6 text-blue-500" />
                        </div>
                        <span className="text-xs font-semibold text-blue-500 bg-blue-500/10 px-2 py-1 rounded-full">+12% this week</span>
                    </div>
                    <p className="text-[var(--text-muted)] text-sm font-medium mb-1">Total Models</p>
                    <h3 className="text-3xl font-bold">{models.length}</h3>
                </div>

                <div className="bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-2xl p-6">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-green-500/10 rounded-xl">
                            <Rocket className="w-6 h-6 text-green-500" />
                        </div>
                    </div>
                    <p className="text-[var(--text-muted)] text-sm font-medium mb-1">Production Deployments</p>
                    <h3 className="text-3xl font-bold">
                        {models.flatMap(m => m.versions).filter(v => v.status === 'Production').length}
                    </h3>
                </div>

                <div className="bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-2xl p-6">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-purple-500/10 rounded-xl">
                            <Activity className="w-6 h-6 text-purple-500" />
                        </div>
                    </div>
                    <p className="text-[var(--text-muted)] text-sm font-medium mb-1">Total Predictions (24h)</p>
                    <h3 className="text-3xl font-bold">0</h3>
                </div>
            </div>

            {/* Main Content */}
            <div className="bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-2xl overflow-hidden shadow-lg shadow-black/5">
                {/* Search/Filter Bar */}
                <div className="p-4 border-b border-[var(--border-color)] flex gap-4">
                    <div className="relative flex-1">
                        <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                        <input 
                            type="text" 
                            placeholder="Search models by name or task..." 
                            className="w-full bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl pl-10 pr-4 py-2.5 focus:outline-none focus:border-blue-500 transition-colors"
                        />
                    </div>
                    <button className="px-4 py-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl hover:bg-black/5 transition-colors flex items-center gap-2">
                        <Filter className="w-5 h-5" />
                        <span>Filter</span>
                    </button>
                </div>

                {/* Model List */}
                <div className="divide-y divide-[var(--border-color)]">
                    {loading ? (
                        <div className="p-12 text-center text-[var(--text-muted)]">Loading registry...</div>
                    ) : models.length === 0 ? (
                        <div className="p-12 text-center">
                            <Box className="w-16 h-16 mx-auto mb-4 text-[var(--text-muted)] opacity-50" />
                            <h3 className="text-xl font-semibold mb-2">No models found</h3>
                            <p className="text-[var(--text-muted)] max-w-md mx-auto">Models trained in AutoML will automatically appear in this registry.</p>
                        </div>
                    ) : (
                        models.map(model => (
                            <div key={model.id} className="group">
                                {/* Model Row */}
                                <div 
                                    className="p-4 hover:bg-[var(--bg-card)] transition-colors cursor-pointer flex items-center gap-4"
                                    onClick={() => toggleExpand(model.id)}
                                >
                                    <button className="p-1 rounded hover:bg-black/5 transition-colors">
                                        {expandedModels.has(model.id) ? 
                                            <ChevronDown className="w-5 h-5 text-[var(--text-muted)]" /> : 
                                            <ChevronRight className="w-5 h-5 text-[var(--text-muted)]" />
                                        }
                                    </button>
                                    
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="font-semibold text-lg">{model.name}</h3>
                                            <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-secondary)]">
                                                {model.task_type}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-6 text-sm text-[var(--text-muted)]">
                                            <span>ID: <span className="font-mono">{model.id.split('-')[0]}</span></span>
                                            <span>Target: <span className="text-blue-500">{model.target_column || 'N/A'}</span></span>
                                            <span>{model.versions.length} version{model.versions.length !== 1 ? 's' : ''}</span>
                                        </div>
                                    </div>
                                    
                                    <div className="text-right">
                                        <div className="text-sm text-[var(--text-muted)] mb-1">Latest Version</div>
                                        {model.versions.length > 0 ? (
                                            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${getStatusStyle(model.versions[0].status)}`}>
                                                {model.versions[0].status}
                                            </span>
                                        ) : (
                                            <span className="text-[var(--text-muted)]">None</span>
                                        )}
                                    </div>
                                </div>

                                {/* Versions Expandable Area */}
                                <AnimatePresence>
                                    {expandedModels.has(model.id) && (
                                        <motion.div 
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="overflow-hidden bg-[var(--bg-card)] border-t border-[var(--border-color)]"
                                        >
                                            <div className="p-4 pl-12 space-y-3">
                                                {model.versions.map(v => (
                                                    <div key={v.id} className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-surface)] hover:border-gray-400 transition-colors">
                                                        <div className="flex items-center gap-4">
                                                            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                                                                <span className="font-bold text-blue-500">v{v.version}</span>
                                                            </div>
                                                            <div>
                                                                <div className="flex items-center gap-2 mb-0.5">
                                                                    <span className="font-medium">{v.algorithm}</span>
                                                                    <span className={`text-[10px] px-2 py-0.5 font-bold rounded-full border ${getStatusStyle(v.status)}`}>
                                                                        {v.status}
                                                                    </span>
                                                                </div>
                                                                <div className="text-xs text-[var(--text-muted)]">
                                                                    Created on {new Date(v.created_at).toLocaleDateString()}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Actions */}
                                                        <div className="flex items-center gap-2">
                                                            {v.status === 'Draft' && (
                                                                <button onClick={() => promoteVersion(v.id, 'Staging')} className="px-3 py-1.5 text-xs font-medium bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 rounded-lg transition-colors border border-blue-500/20">
                                                                    Move to Staging
                                                                </button>
                                                            )}
                                                            {v.status === 'Staging' && (
                                                                <button onClick={() => promoteVersion(v.id, 'Production')} className="px-3 py-1.5 text-xs font-medium bg-green-500/10 text-green-500 hover:bg-green-500/20 rounded-lg transition-colors border border-green-500/20 flex items-center gap-1">
                                                                    <Rocket className="w-3 h-3" />
                                                                    Promote to Prod
                                                                </button>
                                                            )}
                                                            {v.status === 'Production' && (
                                                                <button onClick={() => promoteVersion(v.id, 'Archived')} className="px-3 py-1.5 text-xs font-medium hover:bg-black/5 rounded-lg transition-colors flex items-center gap-1 text-[var(--text-secondary)] border border-[var(--border-color)]">
                                                                    <Archive className="w-3 h-3" />
                                                                    Archive
                                                                </button>
                                                            )}
                                                            <button 
                                                                onClick={() => handleDownloadJoblib(v.id)}
                                                                className="px-3 py-1.5 text-xs font-medium hover:bg-black/5 rounded-lg transition-colors flex items-center gap-1 text-[var(--text-secondary)] border border-[var(--border-color)]"
                                                            >
                                                                <Download className="w-3 h-3" />
                                                                Download .joblib
                                                            </button>
                                                            <button 
                                                                onClick={() => triggerBatchPredict(v.id, model.name)}
                                                                className="px-3 py-1.5 text-xs font-medium bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:opacity-90 rounded-lg transition-colors flex items-center gap-1 shadow-sm"
                                                            >
                                                                <Play className="w-3 h-3" />
                                                                Batch Predict
                                                            </button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        ))
                    )}
                </div>
            </div>
            <input 
                type="file" 
                ref={fileInputRef} 
                accept=".csv" 
                className="hidden" 
                onChange={handleFileUpload} 
            />
        </div>
    );
};

export default ModelRegistry;
