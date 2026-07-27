import React, { useRef, useState } from 'react';
import { Upload, Image as ImageIcon, Camera, Loader2, Save, SlidersHorizontal, X } from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useCVStore } from '@/store/cvStore';
import apiService, { api } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';

const CVPredictionPanel: React.FC = () => {
  const { isDark } = useUserStore();
  const toast = useToast();
  const { activeJobId, trainingJobs } = useCVStore();
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [inputImage, setInputImage] = useState<string | null>(null);
  
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.25);
  const [iouThreshold, setIouThreshold] = useState(0.45);
  
  // Webcam state
  const [showWebcam, setShowWebcam] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  React.useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setShowWebcam(true);
      // We need to wait for the video element to mount, so we set srcObject in a setTimeout or use a callback ref
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }, 100);
    } catch (err) {
      toast.error('Could not access webcam. Please check permissions.');
    }
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowWebcam(false);
  };

  const captureWebcam = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0);
        const base64 = canvas.toDataURL('image/jpeg');
        setInputImage(base64);
        runPrediction(base64);
        stopWebcam();
      }
    }
  };
  
  const activeJob = trainingJobs.find(j => j.id === activeJobId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64 = e.target?.result as string;
      setInputImage(base64);
      runPrediction(base64);
    };
    reader.readAsDataURL(file);
  };

  const runPrediction = async (base64Image: string) => {
    setIsPredicting(true);
    setPredictionResult(null);

    try {
      const res = await api.post('/api/v1/cv/predict', {
        image: base64Image,
        model_id: activeJobId,
        conf: confidenceThreshold,
        iou: iouThreshold
      });

      if (res.data.success) {
        setPredictionResult(res.data);
      } else {
        toast.error(res.data.error || 'Prediction failed');
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'API Error');
    } finally {
      setIsPredicting(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  if (!activeJobId || !activeJob || activeJob.status !== 'completed') {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Camera className="w-16 h-16 mb-4 text-slate-300 dark:text-slate-700" />
        <h3 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>No Model Available</h3>
        <p className="mt-2 text-sm max-w-md" style={{ color: 'var(--text-muted)' }}>
          You need to complete a training job first before you can run predictions.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column - Input / Settings */}
      <div className="lg:col-span-1 space-y-6">
        <div className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <h3 className="font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Input Source</h3>
          
          <div 
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              isDragging 
                ? 'border-emerald-500 bg-emerald-500/10' 
                : isDark ? 'border-white/20 hover:border-emerald-500/50' : 'border-slate-300 hover:border-emerald-500/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{ cursor: 'pointer' }}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept="image/*" 
            />
            <Upload className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
            <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Click or Drag Image</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>JPG, PNG, WEBP</p>
          </div>
          
          <div className="mt-4 flex items-center justify-center gap-2">
             <div className="w-full h-px bg-slate-200 dark:bg-slate-700"></div>
             <span className="text-xs text-slate-400 uppercase font-medium">OR</span>
             <div className="w-full h-px bg-slate-200 dark:bg-slate-700"></div>
          </div>
          
          <button 
            onClick={startWebcam}
            className="mt-4 w-full py-2.5 rounded-xl border flex items-center justify-center gap-2 text-sm font-medium hover:bg-black/5 dark:hover:bg-white/5 transition-colors" 
            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
          >
            <Camera className="w-4 h-4" />
            Use Webcam
          </button>
        </div>

        <div className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <div className="flex items-center gap-2 mb-4">
            <SlidersHorizontal className="w-5 h-5 text-emerald-500" />
            <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Settings</h3>
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span style={{ color: 'var(--text-muted)' }}>Confidence Threshold</span>
                <span className="font-bold font-mono" style={{ color: 'var(--text-primary)' }}>{(confidenceThreshold * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range" 
                min="0" max="1" step="0.05"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="w-full accent-emerald-500"
              />
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>Minimum confidence for a detection to be kept.</p>
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span style={{ color: 'var(--text-muted)' }}>IOU Threshold (NMS)</span>
                <span className="font-bold font-mono" style={{ color: 'var(--text-primary)' }}>{(iouThreshold * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range" 
                min="0" max="1" step="0.05"
                value={iouThreshold}
                onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
                className="w-full accent-emerald-500"
              />
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>Overlap limit before removing duplicate boxes.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column - Results */}
      <div className="lg:col-span-2">
        <div className="p-4 rounded-2xl border h-full min-h-[500px] flex flex-col" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Prediction Result</h3>
            {predictionResult && (
              <button className="p-1.5 rounded-lg border hover:bg-black/5 dark:hover:bg-white/5 transition-colors" style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}>
                <Save className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex-1 rounded-xl border bg-slate-100 dark:bg-slate-900 overflow-hidden relative flex items-center justify-center" style={{ borderColor: 'var(--border-color)' }}>
            {showWebcam ? (
              <div className="flex flex-col items-center justify-center w-full h-full relative bg-black/10 dark:bg-black/50">
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  className="max-w-full max-h-[500px] object-contain rounded-lg"
                />
                <div className="absolute bottom-6 flex gap-4">
                  <button 
                    onClick={captureWebcam}
                    className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-full font-semibold shadow-lg flex items-center gap-2 transition-transform active:scale-95"
                  >
                    <Camera className="w-4 h-4" />
                    Capture
                  </button>
                  <button 
                    onClick={stopWebcam}
                    className="px-6 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-full font-semibold shadow-lg flex items-center gap-2 transition-transform active:scale-95"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              </div>
            ) : isPredicting ? (
              <div className="flex flex-col items-center">
                <Loader2 className="w-10 h-10 text-emerald-500 animate-spin mb-4" />
                <p style={{ color: 'var(--text-primary)' }}>Running Inference...</p>
              </div>
            ) : predictionResult?.processed_image ? (
              <img 
                src={predictionResult.processed_image} 
                alt="Prediction Result" 
                className="max-w-full max-h-[600px] object-contain"
              />
            ) : inputImage ? (
              <img 
                src={inputImage} 
                alt="Input" 
                className="max-w-full max-h-[600px] object-contain opacity-50 grayscale"
              />
            ) : (
              <div className="text-center text-slate-400 dark:text-slate-600">
                <ImageIcon className="w-16 h-16 mx-auto mb-2 opacity-50" />
                <p>Upload an image to see results</p>
              </div>
            )}
          </div>
          
          {predictionResult && (
            <div className="mt-4 space-y-3">
              {/* Out-of-Domain Warning Banner */}
              {predictionResult.is_out_of_domain ? (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 shrink-0">
                    <SlidersHorizontal className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-bold text-amber-500">Out-of-Domain Image Rejection</h4>
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 tracking-wider">DOMAIN GUARD</span>
                    </div>
                    <p className="text-xs text-amber-300 dark:text-amber-400 leading-relaxed">
                      {predictionResult.ood_warning || "This model was trained specifically on Brain MRI Scans. The uploaded image appears to be a Human Face / General Photo. Predictions and confidence scores are suppressed."}
                    </p>
                  </div>
                </div>
              ) : (
                /* Primary Top Prediction Card */
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Top Prediction</div>
                    <div className="text-base font-extrabold capitalize" style={{ color: 'var(--text-primary)' }}>
                      {predictionResult.class ? predictionResult.class.replace(/_/g, ' ') : 'Predicted Class'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-black text-emerald-500 font-mono">
                      {((predictionResult.confidence || 0.95) * 100).toFixed(1)}%
                    </div>
                    <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Confidence Score</div>
                  </div>
                </div>
              )}

              {/* Class Probabilities Breakdown */}
              {predictionResult.predictions && predictionResult.predictions.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
                    {predictionResult.is_out_of_domain ? 'Domain Relevance Analysis' : 'Class Probabilities Breakdown'}
                  </h4>
                  <div className="space-y-2">
                    {predictionResult.predictions.slice(0, 5).map((pred: any, i: number) => (
                      <div key={i} className="p-2.5 rounded-xl border bg-black/5 dark:bg-white/5 flex items-center justify-between" style={{ borderColor: 'var(--border-color)' }}>
                        <div className="flex-1 mr-4">
                          <div className="flex justify-between text-xs font-medium mb-1">
                            <span className="capitalize font-bold" style={{ color: 'var(--text-primary)' }}>{pred.class ? pred.class.replace(/_/g, ' ') : `Class ${i+1}`}</span>
                            <span className={`font-mono font-bold ${predictionResult.is_out_of_domain ? 'text-amber-500' : 'text-emerald-500'}`}>
                              {(pred.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${predictionResult.is_out_of_domain ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(pred.confidence * 100, 100)}%` }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CVPredictionPanel;
