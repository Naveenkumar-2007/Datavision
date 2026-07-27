import React, { useState } from 'react';
import { Download, Box, Server, Smartphone, Cpu, CheckCircle2, Loader2, Code2, Terminal, Copy, Check, ShieldCheck, Zap, FileCode } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useCVStore } from '@/store/cvStore';
import { api } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';

const CVDeployPanel: React.FC = () => {
  const { isDark } = useUserStore();
  const toast = useToast();
  const { activeJobId, trainingJobs } = useCVStore();
  
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['pytorch', 'onnx']);
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<any>(null);
  const [copiedCode, setCopiedCode] = useState(false);

  const activeJob = trainingJobs.find(j => j.id === activeJobId);

  const exportOptions = [
    { id: 'pytorch', name: 'PyTorch (.pt)', icon: Box, desc: 'Original weights, best for Python.' },
    { id: 'onnx', name: 'ONNX', icon: Cpu, desc: 'Universal format for C++/C#/Python.' },
    { id: 'fastapi', name: 'FastAPI Server (app.py)', icon: Server, desc: 'Ready-to-deploy REST API server.' },
    { id: 'docker', name: 'Docker Container', icon: Box, desc: 'Dockerfile & container setup.' },
    { id: 'tensorrt', name: 'TensorRT', icon: Zap, desc: 'NVIDIA GPU optimized engine.' },
    { id: 'tflite', name: 'TFLite', icon: Smartphone, desc: 'Android / iOS mobile format.' }
  ];

  const toggleFormat = (id: string) => {
    setSelectedFormats(prev => 
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  const handleExport = async () => {
    if (!activeJobId) return;
    
    setIsExporting(true);
    setExportResult(null);

    try {
      const res = await api.post(`/api/v1/cv/models/${activeJobId}/export`, {
        formats: selectedFormats
      });

      if (res.data.success) {
        setExportResult(res.data);
        toast.success('Export ZIP package generated successfully!');
      } else {
        toast.error(res.data.error || 'Export failed');
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'API Error');
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownload = async () => {
    const jobId = activeJobId || (trainingJobs.length > 0 ? trainingJobs[0].id : null);
    if (!jobId) {
      toast.error('No trained model available to download. Please train a model first.');
      return;
    }
    
    setIsExporting(true);
    try {
      // 1. Auto-generate export package
      await api.post(`/api/v1/cv/models/${jobId}/export`, {
        formats: selectedFormats
      });

      // 2. Download generated ZIP file
      const res = await api.get(`/api/v1/cv/export/${jobId}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `datavision_cv_model_${jobId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      toast.success('Model ZIP package downloaded successfully!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Download failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const pyCodeSnippet = `import cv2
from ultralytics import YOLO

# Load the trained model weights
model = YOLO('models/best.pt')

# Run inference on any image
def predict(image_path):
    results = model(image_path)
    for r in results:
        # Print predictions
        if hasattr(r, 'probs') and r.probs is not None:
            top1_id = int(r.probs.top1)
            print(f"Prediction: {r.names[top1_id]} ({float(r.probs.top1conf)*100:.1f}%)")
        else:
            for box in r.boxes:
                print(f"Detected: {r.names[int(box.cls[0])]} ({float(box.conf[0]):.2f})")

if __name__ == '__main__':
    predict('test_image.jpg')`;

  const copyCode = () => {
    navigator.clipboard.writeText(pyCodeSnippet);
    setCopiedCode(true);
    toast.success('Python code copied!');
    setTimeout(() => setCopiedCode(false), 2000);
  };

  if (!activeJobId || !activeJob || activeJob.status !== 'completed') {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Server className="w-16 h-16 mb-4 text-slate-300 dark:text-slate-700" />
        <h3 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>No Model Available</h3>
        <p className="mt-2 text-sm max-w-md" style={{ color: 'var(--text-muted)' }}>
          You need to complete a training job first before you can export model code & weights.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-6">
        {/* Export Formats Selector */}
        <div className="p-5 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--text-primary)' }}>Model Export & Package Generator</h3>
          <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>
            Select output formats to package into a standalone, runnable ZIP bundle.
          </p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {exportOptions.map((opt) => {
              const isSelected = selectedFormats.includes(opt.id);
              return (
                <div 
                  key={opt.id}
                  onClick={() => toggleFormat(opt.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col gap-2 ${
                    isSelected 
                      ? 'border-emerald-500 bg-emerald-500/10 shadow-sm' 
                      : 'hover:border-emerald-500/50'
                  }`}
                  style={{ borderColor: isSelected ? '' : 'var(--border-color)' }}
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-2 rounded-lg ${isSelected ? 'bg-emerald-500 text-white' : 'bg-black/5 dark:bg-white/5 text-slate-500'}`}>
                      <opt.icon className="w-4 h-4" />
                    </div>
                    {isSelected && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                  </div>
                  <div className="font-bold mt-1" style={{ color: 'var(--text-primary)' }}>{opt.name}</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{opt.desc}</div>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleExport}
            disabled={isExporting || selectedFormats.length === 0}
            className="mt-6 w-full py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Packaging Model & Code...
              </>
            ) : (
              <>
                <Box className="w-5 h-5" />
                Generate Model ZIP Package
              </>
            )}
          </button>
        </div>

        {/* Python Runnable Code Snippet */}
        <div className="p-5 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-emerald-500" />
              <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>Runnable Inference Code (inference.py)</h3>
            </div>
            <button onClick={copyCode} className="text-xs font-medium text-emerald-500 flex items-center gap-1">
              {copiedCode ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedCode ? 'Copied' : 'Copy Code'}
            </button>
          </div>
          <pre className="p-4 rounded-xl border text-[11px] font-mono overflow-x-auto text-slate-300 bg-slate-950 border-slate-800 leading-relaxed">
            {pyCodeSnippet}
          </pre>
        </div>
      </div>

      <div className="space-y-6">
        <div className="p-5 rounded-2xl border min-h-[400px] flex flex-col" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Package Download Manifest</h3>
          
          {!exportResult ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50">
              <Box className="w-16 h-16 mb-4 text-slate-400" />
              <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Click "Generate Model ZIP Package" to prepare downloadable code & model</p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col space-y-6">
              <div className="p-4 rounded-xl border bg-emerald-500/10 border-emerald-500/30 flex items-center gap-4">
                <div className="p-3 bg-emerald-500 rounded-full text-white shrink-0">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-bold text-emerald-500 text-base">Model ZIP Ready</h4>
                  <p className="text-xs font-mono font-medium" style={{ color: 'var(--text-primary)' }}>{exportResult.filename} ({exportResult.size_mb?.toFixed(2)} MB)</p>
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>ZIP Package Includes:</h4>
                <ul className="space-y-2.5">
                  <li className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> Trained Model Checkpoint Weights (`models/best.pt`)
                  </li>
                  {selectedFormats.map(fmt => (
                    <li key={fmt} className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> {exportOptions.find(o => o.id === fmt)?.name} exported format
                    </li>
                  ))}
                  <li className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> Python Inference Script (`inference.py`)
                  </li>
                  <li className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> FastAPI REST Server (`app.py`)
                  </li>
                  <li className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> `requirements.txt` & `README.md` Setup Instructions
                  </li>
                </ul>
              </div>

              <div className="flex-1"></div>

              <button
                onClick={handleDownload}
                className="w-full py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 border-2 border-emerald-500 text-emerald-500 hover:bg-emerald-500 hover:text-white transition-all shadow-lg shadow-emerald-500/10"
              >
                <Download className="w-5 h-5" />
                Download Model ZIP Archive
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CVDeployPanel;
