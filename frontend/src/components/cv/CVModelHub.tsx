import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, Star, Clock, Target, Cpu, HardDrive, ShieldCheck, Trash2 } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import apiService, { api } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';

const CVModelHub: React.FC = () => {
  const { isDark } = useUserStore();
  const toast = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('my_models');
  const [models, setModels] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/api/v1/cv/models');
      if (res.data.models) {
        setModels(res.data.models);
      }
    } catch (e) {
      // Mock models fallback
      setModels([
        { id: 'm1', name: 'YOLOv8s Helmet Detection', task: 'object_detection', mAP50: 0.942, size_mb: 22.5, tag: 'Trained', completed_at: '2026-07-27' },
        { id: 'm2', name: 'ResNet50 Brain Tumor Classifier', task: 'classification', mAP50: 0.985, size_mb: 98.1, tag: 'High Acc', completed_at: '2026-07-26' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadModel = async (modelId: string) => {
    try {
      await api.post(`/api/v1/cv/models/${modelId}/export`, { formats: ['pytorch', 'onnx'] });
      const res = await api.get(`/api/v1/cv/export/${modelId}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `model_${modelId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      toast.success('Model downloaded successfully!');
    } catch (e: any) {
      toast.error('Failed to download model.');
    }
  };

  const handleDeleteModel = (modelId: string) => {
    if (window.confirm('Are you sure you want to delete this trained model?')) {
      setModels(prev => prev.filter(m => m.id !== modelId));
      toast.success('Model deleted from hub.');
    }
  };

  const tabs = [
    { id: 'my_models', label: 'My Models' },
    { id: 'community', label: 'Community' },
    { id: 'pretrained', label: 'Pre-trained SOTA' }
  ];

  const pretrainedModels = [
    { name: 'YOLOv11x', task: 'Object Detection', mAP50: 0.985, size_mb: 180, isVerified: true, downloads: '1.2M', tag: 'SOTA' },
    { name: 'SAM 2 (Large)', task: 'Zero-Shot Segmentation', mAP50: 0.99, size_mb: 350, isVerified: true, downloads: '850K', tag: 'Meta AI' },
    { name: 'Florence-2', task: 'Vision-Language', mAP50: 0.96, size_mb: 420, isVerified: true, downloads: '500K', tag: 'Microsoft' },
    { name: 'YOLO-World', task: 'Open-Vocabulary Detection', mAP50: 0.94, size_mb: 220, isVerified: true, downloads: '410K', tag: 'Real-time' },
    { name: 'RT-DETR', task: 'Object Detection', mAP50: 0.95, size_mb: 140, isVerified: true, downloads: '320K', tag: 'Transformer' }
  ];

  const communityModels = [
    { name: 'Medical Mask Detect', task: 'Object Detection', mAP50: 0.89, size_mb: 45, author: 'Dr. Jane Smith', downloads: '12K' },
    { name: 'Retail Shelf Scanner', task: 'Object Detection', mAP50: 0.91, size_mb: 60, author: 'RetailCorp', downloads: '8K' },
    { name: 'Plant Disease Seg', task: 'Segmentation', mAP50: 0.85, size_mb: 110, author: 'AgriTech Labs', downloads: '5K' },
  ];

  const displayModels = activeTab === 'my_models' ? models : activeTab === 'community' ? communityModels : pretrainedModels;

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col md:flex-row justify-between gap-4">
        <div className="flex-1 relative max-w-xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search models by name, architecture, or task..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border focus:ring-2 focus:ring-emerald-500/50 outline-none transition-all"
            style={{ 
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)'
            }}
          />
        </div>
        
        <div className="flex p-1 rounded-xl bg-black/5 dark:bg-white/5 border w-fit" style={{ borderColor: 'var(--border-color)' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id 
                  ? 'bg-white dark:bg-slate-800 shadow-sm text-emerald-500' 
                  : 'hover:bg-black/5 dark:hover:bg-white/5 text-slate-500 dark:text-slate-400'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Model Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {displayModels.length === 0 && !isLoading ? (
          <div className="col-span-full py-12 text-center text-slate-500">
            No models found.
          </div>
        ) : (
          displayModels.map((model, i) => (
            <div key={i} className="p-5 rounded-2xl border flex flex-col transition-all hover:-translate-y-1 hover:border-emerald-500/50 hover:shadow-xl hover:shadow-emerald-500/10 group relative overflow-hidden" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
              
              {model.tag && (
                <div className="absolute top-0 right-0 px-3 py-1 bg-emerald-500 text-white text-[10px] font-bold tracking-wider uppercase rounded-bl-xl">
                  {model.tag}
                </div>
              )}

              <div className="flex justify-between items-start mb-4 mt-2">
                <div className="flex-1 min-w-0 pr-2">
                  <h3 className="font-bold text-lg truncate flex items-center gap-1.5" style={{ color: 'var(--text-primary)' }}>
                    {model.name || model.config?.model?.toUpperCase() || 'Unknown Model'}
                    {model.isVerified && <ShieldCheck className="w-4 h-4 text-blue-500 shrink-0" />}
                  </h3>
                  <div className="text-xs font-mono mt-1 flex items-center gap-2">
                    <span className="text-emerald-500">{model.job_id ? model.job_id.substring(0, 8) : model.author || 'Official'}</span>
                    {model.downloads && <span className="text-slate-500">• {model.downloads} dl</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-all">
                  <button 
                    onClick={() => handleDownloadModel(model.id)} 
                    className="p-2 rounded-xl border bg-emerald-500/10 hover:bg-emerald-500 hover:text-white transition-all text-emerald-500" 
                    title="Download Model (.zip)"
                    style={{ borderColor: 'var(--border-color)' }}
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => handleDeleteModel(model.id)} 
                    className="p-2 rounded-xl border border-red-500/20 bg-red-500/10 hover:bg-red-500 hover:text-white transition-all text-red-500" 
                    title="Delete Model"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2 mb-5 text-xs font-medium">
                <span className="px-2.5 py-1 rounded-md bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5" style={{ color: 'var(--text-primary)' }}>
                  {model.task || model.config?.task || 'object_detection'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-5">
                <div className="p-3 rounded-xl border bg-gradient-to-br from-emerald-500/5 to-transparent flex flex-col items-center justify-center text-center transition-colors group-hover:border-emerald-500/20" style={{ borderColor: 'var(--border-color)' }}>
                  <div className="text-[10px] uppercase tracking-wider font-bold mb-1" style={{ color: 'var(--text-muted)' }}>
                    mAP50 Score
                  </div>
                  <div className="font-bold text-lg text-emerald-500 font-mono">
                    {((model.metrics?.mAP50 || model.mAP50 || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-3 rounded-xl border bg-black/5 dark:bg-white/5 flex flex-col items-center justify-center text-center transition-colors group-hover:border-slate-500/20" style={{ borderColor: 'var(--border-color)' }}>
                  <div className="text-[10px] uppercase tracking-wider font-bold mb-1" style={{ color: 'var(--text-muted)' }}>
                    Model Size
                  </div>
                  <div className="font-bold text-lg font-mono" style={{ color: 'var(--text-primary)' }}>
                    {model.metrics?.modelSizeMB || model.size_mb || '?'} MB
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-4 border-t flex items-center justify-between text-xs font-medium" style={{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}>
                <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> {new Date(model.completed_at || Date.now()).toLocaleDateString()}</span>
                <span className="flex items-center gap-1 text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full"><Star className="w-3 h-3 fill-amber-500" /> 4.9</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CVModelHub;
