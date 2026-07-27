import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Camera, LayoutDashboard, Database, Image as ImageIcon, Crosshair, 
  Settings, Play, BarChart2, Eye, GitBranch, Box, Upload,
  AlertCircle, Sparkles, Network, Target, Activity, Layout,
  Rocket, Download, Cpu, TrendingUp, Zap, Clock, Layers,
  Shield, Server, HardDrive, CheckCircle2, XCircle
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useCVStore } from '@/store/cvStore';
import { useToast } from '@/contexts/ToastContext';
import apiService, { api } from '@/services/api';
import { TrainingMode, CVTrainingConfig } from '@/types/cv';

// Components
import CVDatasetUpload from '@/components/cv/CVDatasetUpload';
import CVDatasetGallery from '@/components/cv/CVDatasetGallery';
import CVTrainingConfigPanel from '@/components/cv/CVTrainingConfig';
import CVTrainingMonitor from '@/components/cv/CVTrainingMonitor';
import CVResultsDashboard from '@/components/cv/CVResultsDashboard';
import CVPredictionPanel from '@/components/cv/CVPredictionPanel';
import CVExperimentTracker from '@/components/cv/CVExperimentTracker';
import CVDeployPanel from '@/components/cv/CVDeployPanel';
import CVModelHub from '@/components/cv/CVModelHub';

const ComputerVision: React.FC = () => {
  const { isDark } = useUserStore();
  const toast = useToast();
  const { 
    activeTab, setActiveTab, 
    datasets, setDatasets, addDataset, activeDatasetId, setActiveDatasetId,
    activeJobId, setActiveJobId, trainingJobs, addTrainingJob, updateTrainingJob
  } = useCVStore();
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Theme classes
  const bg = isDark ? 'bg-[#0a0b10]' : 'bg-slate-50';
  const bgCard = isDark ? 'bg-white/[0.03]' : 'bg-white';
  const border = isDark ? 'border-white/[0.06]' : 'border-slate-200';
  const textH = isDark ? 'text-white' : 'text-slate-900';
  const textM = isDark ? 'text-slate-400' : 'text-slate-600';
  const textS = isDark ? 'text-slate-500' : 'text-slate-500';

  useEffect(() => { fetchDatasets(); }, []);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    const activeJob = trainingJobs.find(j => j.id === activeJobId);
    if (activeJob && (activeJob.status === 'running' || activeJob.status === 'starting')) {
       eventSource = new EventSource(`${api.defaults.baseURL || ''}/api/v1/cv/train/${activeJobId}/progress`);
       eventSource.onmessage = (event) => {
         try {
           const data = JSON.parse(event.data);
           if (data.error) { eventSource?.close(); return; }
           if (activeJobId) {
             updateTrainingJob(activeJobId, {
               status: data.status, progress: data.progress,
               metrics: data.metrics, modelPath: data.model_path,
               completedAt: data.completed_at
             });
           }
           if (['completed', 'failed', 'cancelled'].includes(data.status)) {
             eventSource?.close();
             if (data.status === 'completed') { toast.success('Training completed!'); setActiveTab('results'); }
             else if (data.status === 'failed') { toast.error('Training failed.'); }
           }
         } catch(e) {}
       };
       eventSource.onerror = () => { eventSource?.close(); };
    }
    return () => { if (eventSource) eventSource.close(); };
  }, [activeJobId]);

  const fetchDatasets = async () => {
    try {
      const res = await api.get('/api/v1/cv/datasets');
      if (res.data.datasets) {
        setDatasets(res.data.datasets);
        if (res.data.datasets.length > 0 && !activeDatasetId) setActiveDatasetId(res.data.datasets[0].id);
      }
    } catch (e) { console.error("Failed to fetch datasets", e); }
  };

  const [selectedTaskType, setSelectedTaskType] = useState<string | null>(null);

  const handleDatasetUploadComplete = (dataset: any) => {
    addDataset(dataset);
    setActiveDatasetId(dataset.id);
    if (dataset.taskType) setSelectedTaskType(dataset.taskType);
    setActiveTab('vision_tasks');
  };

  const handleStartTraining = async (mode: TrainingMode, config: CVTrainingConfig, chosenTaskType?: string) => {
    if (!activeDatasetId) return;
    try {
      const activeDs = datasets.find(d => d.id === activeDatasetId);
      const taskType = chosenTaskType || selectedTaskType || activeDs?.taskType || 'classification';
      const res = await api.post('/api/v1/cv/train', { 
        dataset_id: activeDatasetId, 
        mode, 
        config,
        task_type: taskType 
      });
      if (res.data.success) {
        const jobId = res.data.job_id;
        addTrainingJob({
          id: jobId, datasetId: activeDatasetId, userId: 'current', mode, config, status: 'starting',
          progress: { status: 'starting', epoch: 0, totalEpochs: config.epochs, loss: 0, valLoss: 0, metrics: {},
            logs: [`Initializing ${mode.toUpperCase()} training job for task: ${taskType.toUpperCase()}...`], systemStats: { gpuUsage: 0, vramUsage: '0GB', cpuUsage: 0, ramUsage: '0GB' }, startedAt: new Date().toISOString() },
          startedAt: new Date().toISOString()
        });
        setActiveJobId(jobId);
        setActiveTab('live_training');
        toast.success(`Started ${mode} training for ${taskType.replace(/_/g, ' ')}`);
      }
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed to start training'); }
  };

  const handleStopTraining = async () => { if (!activeJobId) return; try { await api.post(`/api/v1/cv/train/${activeJobId}/stop`); toast.success('Training stopped'); } catch (e) {} };
  const handlePauseTraining = async () => { if (!activeJobId) return; try { await api.post(`/api/v1/cv/train/${activeJobId}/pause`); } catch (e) {} };
  const handleResumeTraining = async () => { if (!activeJobId) return; try { await api.post(`/api/v1/cv/train/${activeJobId}/resume`); } catch (e) {} };

  // Computed stats
  const completedJobs = trainingJobs.filter(j => j.status === 'completed');
  const bestModel = useMemo(() => {
    if (completedJobs.length === 0) return null;
    return completedJobs.reduce((best, j) => (j.metrics?.mAP50 || 0) > (best.metrics?.mAP50 || 0) ? j : best, completedJobs[0]);
  }, [completedJobs]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'data', label: 'Dataset', icon: Database },
    { id: 'vision_tasks', label: 'Vision Tasks', icon: Crosshair },
    { id: 'training', label: 'Training', icon: Settings },
    { id: 'live_training', label: 'Live Training', icon: Activity },
    { id: 'results', label: 'Results', icon: BarChart2 },
    { id: 'prediction', label: 'Prediction', icon: Eye },
    { id: 'experiments', label: 'Experiments', icon: GitBranch },
    { id: 'model_hub', label: 'Model Hub', icon: Layers },
    { id: 'deploy', label: 'Deploy & Export', icon: Rocket },
  ];

  const activeJob = trainingJobs.find(j => j.id === activeJobId);

  return (
    <div className={`flex flex-col h-full overflow-hidden ${bg}`}>
      {/* Header */}
      <div className={`flex items-center justify-between p-4 border-b shrink-0 z-10 ${bgCard} ${border}`}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20">
            <Camera className="w-5 h-5" />
          </div>
          <div>
            <h1 className={`text-lg font-bold ${textH}`}>Computer Vision Studio</h1>
            <p className={`text-xs ${textM}`}>Zero-code, end-to-end vision AI pipelines</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {activeDatasetId && (
            <div className={`hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium ${border} ${isDark ? 'bg-white/[0.03]' : 'bg-slate-50'}`}>
              <Database className="w-3.5 h-3.5 text-emerald-500" />
              <span className={`truncate max-w-[140px] ${textH}`}>
                {datasets.find(d => d.id === activeDatasetId)?.name || 'Unknown'}
              </span>
            </div>
          )}
          {completedJobs.length > 0 && (
            <div className={`hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium ${border} ${isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'}`}>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-emerald-600 dark:text-emerald-400">{completedJobs.length} trained</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          {/* Navigation Tabs */}
          <div className={`flex border-b overflow-x-auto no-scrollbar ${border} ${bgCard}`}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-5 py-3.5 font-medium text-xs transition-all border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-emerald-500 text-emerald-500'
                    : `border-transparent ${textM} hover:text-emerald-400`
                }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
                {tab.id === 'live_training' && activeJob?.status === 'running' && (
                  <div className="ml-1 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                )}
              </button>
            ))}
          </div>

          <div className="p-4 md:p-6 lg:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="max-w-7xl mx-auto"
              >
              
              {/* ════════ OVERVIEW ════════ */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Quick Stats Row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className={`p-5 rounded-2xl border ${bgCard} ${border} transition-all hover:border-emerald-500/30`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className={`p-2 rounded-lg ${isDark ? 'bg-blue-500/10' : 'bg-blue-50'}`}>
                          <Database className="w-4 h-4 text-blue-500" />
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Datasets</span>
                      </div>
                      <p className={`text-3xl font-extrabold ${textH}`}>{datasets.length}</p>
                      <p className={`text-xs ${textM} mt-1`}>{datasets.reduce((s, d) => s + d.numImages, 0)} total images</p>
                    </div>

                    <div className={`p-5 rounded-2xl border ${bgCard} ${border} transition-all hover:border-emerald-500/30`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className={`p-2 rounded-lg ${isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'}`}>
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Models</span>
                      </div>
                      <p className={`text-3xl font-extrabold ${textH}`}>{completedJobs.length}</p>
                      <p className={`text-xs ${textM} mt-1`}>{trainingJobs.filter(j => j.status === 'running').length} training now</p>
                    </div>

                    <div className={`p-5 rounded-2xl border ${bgCard} ${border} transition-all hover:border-emerald-500/30`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className={`p-2 rounded-lg ${isDark ? 'bg-purple-500/10' : 'bg-purple-50'}`}>
                          <Target className="w-4 h-4 text-purple-500" />
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Best mAP50</span>
                      </div>
                      <p className={`text-3xl font-extrabold ${textH}`}>
                        {bestModel ? `${((bestModel.metrics?.mAP50 || 0) * 100).toFixed(1)}%` : '—'}
                      </p>
                      <p className={`text-xs ${textM} mt-1`}>{bestModel ? bestModel.config.model.toUpperCase() : 'No models yet'}</p>
                    </div>

                    <div className={`p-5 rounded-2xl border bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20 cursor-pointer hover:shadow-xl hover:scale-[1.02] transition-all`}
                         onClick={() => setActiveTab('data')}>
                      <Upload className="w-7 h-7 mb-3 opacity-80" />
                      <p className="font-bold text-base">New Project</p>
                      <p className="text-xs opacity-80 mt-0.5">Upload Dataset</p>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { icon: Crosshair, title: 'Object Detection', desc: 'YOLOv8 · RT-DETR · YOLO-World', badge: 'Most Popular', onClick: () => setActiveTab('vision_tasks') },
                      { icon: ImageIcon, title: 'Image Classification', desc: 'ResNet · EfficientNet · ViT', badge: 'Fast Training', onClick: () => setActiveTab('vision_tasks') },
                      { icon: Network, title: 'Instance Segmentation', desc: 'YOLO-Seg · Mask R-CNN · SAM 2', badge: 'Pixel-Perfect', onClick: () => setActiveTab('vision_tasks') },
                    ].map((action, i) => (
                      <button key={i} onClick={action.onClick}
                        className={`p-5 rounded-2xl border text-left transition-all hover:-translate-y-1 hover:shadow-lg group ${bgCard} ${border} hover:border-emerald-500/40`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className={`p-2 rounded-xl ${isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'} group-hover:bg-emerald-500/20 transition-colors`}>
                            <action.icon className="w-5 h-5 text-emerald-500" />
                          </div>
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 tracking-wider">
                            {action.badge}
                          </span>
                        </div>
                        <h3 className={`text-sm font-bold ${textH} group-hover:text-emerald-500 transition-colors`}>{action.title}</h3>
                        <p className={`text-xs ${textM} mt-0.5`}>{action.desc}</p>
                      </button>
                    ))}
                  </div>
                  
                  {/* Recent Datasets */}
                  <div className={`p-6 rounded-2xl border ${bgCard} ${border}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className={`text-sm font-bold ${textH}`}>Recent Datasets</h3>
                      <button onClick={() => setActiveTab('data')} className="text-xs font-medium text-emerald-500 hover:text-emerald-400">
                        View All →
                      </button>
                    </div>
                    {datasets.length === 0 ? (
                      <div className={`text-center py-8 ${textS} text-sm`}>No datasets uploaded yet. Upload your first dataset to get started.</div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {datasets.slice(0, 6).map(d => (
                          <div key={d.id} onClick={() => { setActiveDatasetId(d.id); setActiveTab('data'); }}
                            className={`p-4 rounded-xl border cursor-pointer transition-all hover:border-emerald-500/40 hover:-translate-y-0.5 ${border} ${isDark ? 'hover:bg-white/[0.02]' : 'hover:bg-slate-50'} ${
                              activeDatasetId === d.id ? 'border-emerald-500/50 ring-1 ring-emerald-500/20' : ''
                            }`}>
                            <div className={`font-bold text-sm mb-1.5 truncate ${textH}`}>{d.name}</div>
                            <div className={`text-xs flex gap-3 ${textM}`}>
                              <span className="flex items-center gap-1"><ImageIcon className="w-3 h-3" /> {d.numImages} imgs</span>
                              <span className="flex items-center gap-1"><Target className="w-3 h-3" /> {d.numClasses} cls</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Recent Training Runs */}
                  {trainingJobs.length > 0 && (
                    <div className={`p-6 rounded-2xl border ${bgCard} ${border}`}>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className={`text-sm font-bold ${textH}`}>Training History</h3>
                        <button onClick={() => setActiveTab('experiments')} className="text-xs font-medium text-emerald-500 hover:text-emerald-400">
                          All Experiments →
                        </button>
                      </div>
                      <div className="space-y-2">
                        {trainingJobs.slice(0, 5).map(job => (
                          <div key={job.id} className={`flex items-center justify-between p-3 rounded-xl border ${border} ${isDark ? 'hover:bg-white/[0.02]' : 'hover:bg-slate-50'} transition-colors`}>
                            <div className="flex items-center gap-3">
                              <div className={`w-2 h-2 rounded-full ${
                                job.status === 'completed' ? 'bg-emerald-500' :
                                job.status === 'running' ? 'bg-blue-500 animate-pulse' :
                                job.status === 'failed' ? 'bg-red-500' : 'bg-slate-400'
                              }`} />
                              <div>
                                <span className={`text-xs font-bold ${textH}`}>{job.config.model.toUpperCase()}</span>
                                <span className={`text-xs ${textS} ml-2`}>{job.mode} · {job.progress.totalEpochs} epochs</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              {job.metrics?.mAP50 && (
                                <span className="text-xs font-bold text-emerald-500 font-mono">
                                  mAP: {((job.metrics.mAP50) * 100).toFixed(1)}%
                                </span>
                              )}
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                                job.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' :
                                job.status === 'running' ? 'bg-blue-500/10 text-blue-500' :
                                job.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                                'bg-slate-500/10 text-slate-500'
                              }`}>{job.status}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ════════ DATASET ════════ */}
              {activeTab === 'data' && (
                <div className="space-y-6">
                  <CVDatasetUpload onUploadComplete={handleDatasetUploadComplete} />
                  <CVDatasetGallery />
                </div>
              )}

              {/* ════════ VISION TASKS ════════ */}
              {activeTab === 'vision_tasks' && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-xl bg-emerald-500/10">
                      <Sparkles className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div>
                      <h2 className={`text-lg font-bold ${textH}`}>Vision Tasks</h2>
                      <p className={`text-xs ${textM}`}>Auto-detected from your dataset. Override if needed.</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { type: 'object_detection', icon: Crosshair, title: 'Object Detection', desc: 'Find and locate multiple objects using bounding boxes.', format: 'YOLO, COCO', models: 'YOLOv8, RT-DETR' },
                      { type: 'classification', icon: ImageIcon, title: 'Image Classification', desc: 'Categorize images into predefined classes.', format: 'Folder Structure', models: 'ResNet, EfficientNet' },
                      { type: ['semantic_segmentation', 'instance_segmentation'], icon: Network, title: 'Instance Segmentation', desc: 'Pixel-perfect masks for object boundaries.', format: 'YOLO, COCO', models: 'YOLO-Seg, Mask R-CNN' },
                      { type: 'pose_estimation', icon: Activity, title: 'Keypoint Detection', desc: 'Detect and track specific points on objects.', format: 'COCO Keypoints', models: 'YOLO-Pose, HRNet' },
                      { type: 'ocr', icon: Layout, title: 'OCR', desc: 'Extract text from images.', format: 'JSON/TXT', models: 'TrOCR, PaddleOCR' },
                    ].map((task, i) => {
                      const currentTaskType = datasets.find(d => d.id === activeDatasetId)?.taskType;
                      const isActive = Array.isArray(task.type) ? task.type.includes(currentTaskType || '') : currentTaskType === task.type;
                      return (
                        <div key={i} className={`p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden ${bgCard} ${
                          isActive ? 'border-emerald-500 shadow-lg shadow-emerald-500/10' : `${border} hover:border-emerald-500/40 hover:-translate-y-0.5`
                        }`}>
                          {isActive && <div className="absolute top-0 right-0 px-2.5 py-0.5 bg-emerald-500 text-white text-[9px] font-bold rounded-bl-lg tracking-wider">AUTO-DETECTED</div>}
                          <task.icon className={`w-8 h-8 mb-3 ${isActive ? 'text-emerald-500' : textM}`} />
                          <h3 className={`text-sm font-bold mb-1.5 ${textH}`}>{task.title}</h3>
                          <p className={`text-xs ${textM} mb-3 leading-relaxed`}>{task.desc}</p>
                          <div className={`space-y-1.5 text-xs ${textM} mb-4`}>
                            <div className="flex justify-between"><span className={textS}>Format:</span><span className="text-emerald-500 font-medium">{task.format}</span></div>
                            <div className="flex justify-between"><span className={textS}>Models:</span><span className={`font-medium ${textH}`}>{task.models}</span></div>
                          </div>
                          <button onClick={() => {
                            const chosenType = Array.isArray(task.type) ? task.type[0] : task.type;
                            setSelectedTaskType(chosenType);
                            setActiveTab('training');
                            toast.info(`Selected task: ${task.title}`);
                          }}
                            className={`w-full py-2 rounded-xl text-sm font-bold transition-colors ${
                              isActive ? 'bg-emerald-500 text-white hover:bg-emerald-600' : `border ${border} text-emerald-500 hover:bg-emerald-500 hover:text-white`
                            }`}>
                            Proceed to Training
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* ════════ TRAINING CONFIG ════════ */}
              {activeTab === 'training' && (
                <CVTrainingConfigPanel 
                  onStartTraining={handleStartTraining} 
                  selectedTaskType={selectedTaskType || undefined}
                  disabled={!activeDatasetId || (activeJob && activeJob.status === 'running')} 
                />
              )}

              {/* ════════ LIVE TRAINING ════════ */}
              {activeTab === 'live_training' && (
                activeJob ? (
                  <CVTrainingMonitor 
                    job={activeJob} 
                    onPause={handlePauseTraining}
                    onResume={handleResumeTraining}
                    onStop={handleStopTraining}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Play className={`w-14 h-14 mb-4 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
                    <h3 className={`text-lg font-bold ${textH}`}>No Active Training</h3>
                    <p className={`text-xs ${textM} mt-1`}>Start a training job to monitor it live.</p>
                    <button onClick={() => setActiveTab('training')} className="mt-4 px-5 py-2 rounded-xl bg-emerald-500 text-white font-medium text-sm hover:bg-emerald-400 transition-colors">
                      Go to Training Config
                    </button>
                  </div>
                )
              )}

              {/* ════════ RESULTS ════════ */}
              {activeTab === 'results' && (
                activeJob?.status === 'completed' ? (
                  <CVResultsDashboard job={activeJob} />
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <BarChart2 className={`w-14 h-14 mb-4 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
                    <h3 className={`text-lg font-bold ${textH}`}>No Results Yet</h3>
                    <p className={`text-xs ${textM} mt-1`}>Complete a training job to view results.</p>
                  </div>
                )
              )}

              {/* ════════ PREDICTION ════════ */}
              {activeTab === 'prediction' && <CVPredictionPanel />}
              
              {/* ════════ EXPERIMENTS ════════ */}
              {activeTab === 'experiments' && <CVExperimentTracker />}

              {/* ════════ MODEL HUB ════════ */}
              {activeTab === 'model_hub' && <CVModelHub />}

              {/* ════════ DEPLOY & EXPORT ════════ */}
              {activeTab === 'deploy' && <CVDeployPanel />}

            </motion.div>
          </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComputerVision;
