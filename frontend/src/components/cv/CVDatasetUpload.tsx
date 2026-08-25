import React, { useRef, useState } from 'react';
import { Upload, File, Image as ImageIcon, Database, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import { CVDatasetHealth } from '@/types/cv';
import apiService, { api } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';

interface Props {
  onUploadComplete: (dataset: any) => void;
}

const CVDatasetUpload: React.FC<Props> = ({ onUploadComplete }) => {
  const { isDark } = useUserStore();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files[0]);
    }
  };

  const handleFiles = async (file: File) => {
    const validExts = ['.zip', '.tar', '.tar.gz', '.tgz'];
    if (!validExts.some(ext => file.name.toLowerCase().endsWith(ext))) {
      toast.error('Please upload your dataset as a compressed folder (.zip, .tar, .tar.gz, .tgz) so we can preserve your directory structure.');
      return;
    }
    if (file.size > 20 * 1024 * 1024 * 1024) {
      toast.error('Vision datasets can be up to 20 GB. Please choose a smaller archive.');
      return;
    }

    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Simulate upload progress
      const interval = setInterval(() => {
        setProgress(p => Math.min(p + 10, 90));
      }, 500);

      const res = await api.post('/api/v1/cv/datasets', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      clearInterval(interval);
      setProgress(100);
      
      setTimeout(() => {
        setUploading(false);
        const datasetObj = res.data.dataset || (res.data.id ? res.data : null);
        if (datasetObj) {
          toast.success('Dataset uploaded and analyzed successfully!');
          onUploadComplete(datasetObj);
        } else {
          toast.error(res.data.error || 'Failed to process dataset.');
        }
      }, 500);

    } catch (err: any) {
      setUploading(false);
      toast.error(err.response?.data?.detail || 'Upload failed');
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>Upload Vision Dataset</h2>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Drop a compressed archive of your images and annotations. We'll automatically detect the format.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div 
            className={`relative overflow-hidden border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300 ${
              isDragging 
                ? 'border-emerald-500 bg-emerald-500/10 scale-[1.02]' 
                : isDark ? 'border-white/20 hover:border-emerald-500/50 hover:bg-white/5' : 'border-slate-300 hover:border-emerald-500/50 hover:bg-slate-50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !uploading && fileInputRef.current?.click()}
            style={{ cursor: uploading ? 'wait' : 'pointer', minHeight: '320px' }}
          >
            {isDragging && (
              <div className="absolute inset-0 bg-emerald-500/20 backdrop-blur-sm z-10 flex items-center justify-center">
                <Upload className="w-16 h-16 text-emerald-500 animate-bounce" />
              </div>
            )}
            
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept=".zip,.tar,.tar.gz,.tgz" 
            />
            
            <AnimatePresence mode="wait">
              {uploading ? (
                <motion.div 
                  key="uploading"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center space-y-6 h-full"
                >
                  <div className="relative">
                    <Loader2 className="w-16 h-16 text-emerald-500 animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-bold text-emerald-500">{progress}%</span>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Processing Dataset...
                    </h3>
                    <p className="text-sm max-w-xs mx-auto" style={{ color: 'var(--text-muted)' }}>
                      Extracting images, analyzing structure, and calculating health score.
                    </p>
                  </div>
                  <div className="w-full max-w-sm bg-black/10 dark:bg-white/10 rounded-full h-2 overflow-hidden">
                    <motion.div 
                      className="bg-emerald-500 h-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ ease: "linear", duration: 0.5 }}
                    />
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center justify-center h-full gap-6"
                >
                  <div className={`p-5 rounded-full shadow-lg ${isDark ? 'bg-emerald-500/20 text-emerald-400 shadow-emerald-500/20' : 'bg-emerald-50 text-emerald-600 shadow-emerald-500/20'}`}>
                    <Upload className="w-10 h-10" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                      Click or drag archive here
                    </h3>
                    <p className="text-sm px-4 max-w-md mx-auto" style={{ color: 'var(--text-muted)' }}>
                      Supports .zip, .tar, .tar.gz, and .tgz formats up to 20 GB.
                    </p>
                  </div>
                  
                  <div className="flex flex-wrap items-center justify-center gap-3 mt-4">
                    <div className="flex items-center gap-2 text-xs font-medium px-4 py-2 rounded-xl transition-colors hover:bg-emerald-500/10 hover:text-emerald-500" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-muted)' }}>
                      <ImageIcon className="w-4 h-4" /> Classification
                    </div>
                    <div className="flex items-center gap-2 text-xs font-medium px-4 py-2 rounded-xl transition-colors hover:bg-emerald-500/10 hover:text-emerald-500" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-muted)' }}>
                      <File className="w-4 h-4" /> YOLOv8
                    </div>
                    <div className="flex items-center gap-2 text-xs font-medium px-4 py-2 rounded-xl transition-colors hover:bg-emerald-500/10 hover:text-emerald-500" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-muted)' }}>
                      <Database className="w-4 h-4" /> COCO
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Info Panel */}
        <div className="space-y-6">
          <div className="p-6 rounded-3xl border bg-gradient-to-b from-transparent to-black/5 dark:to-white/5" style={{ borderColor: 'var(--border-color)' }}>
            <h4 className="font-bold flex items-center gap-2 mb-4" style={{ color: 'var(--text-primary)' }}>
              <CheckCircle2 className="w-5 h-5 text-emerald-500" /> Auto-Detection
            </h4>
            <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--text-muted)' }}>
              Datavision will automatically scan your folder structure and annotations to figure out the task type (Detection, Classification, Segmentation).
            </p>

            <h4 className="font-bold text-sm mb-3" style={{ color: 'var(--text-primary)' }}>Expected YOLO Structure:</h4>
            <div className="p-4 rounded-xl font-mono text-xs space-y-2 border" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-muted)', borderColor: 'var(--border-color)' }}>
              <div className="text-emerald-500 font-bold">dataset.zip</div>
              <div className="pl-4 border-l border-white/10">
                <div>├── images/</div>
                <div className="pl-4 border-l border-white/10 text-slate-500">
                  <div>├── train/ (img1.jpg...)</div>
                  <div>└── val/</div>
                </div>
                <div>├── labels/</div>
                <div className="pl-4 border-l border-white/10 text-slate-500">
                  <div>├── train/ (img1.txt...)</div>
                  <div>└── val/</div>
                </div>
                <div>└── data.yaml</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CVDatasetUpload;
