import React, { useState } from 'react';
import { useCVStore } from '@/store/cvStore';
import { GitBranch, Target, Clock, ArrowRight, Activity, FlaskConical, Trophy, BarChart3, Eye, Download, CheckCircle2 } from 'lucide-react';
import { useUserStore } from '@/store/userStore';

const CVExperimentTracker: React.FC = () => {
  const { isDark } = useUserStore();
  const { trainingJobs, activeDatasetId, setActiveJobId, setActiveTab } = useCVStore();
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  const bgCard = isDark ? 'bg-white/[0.03]' : 'bg-white';
  const border = isDark ? 'border-white/[0.06]' : 'border-slate-200';
  const textH = isDark ? 'text-white' : 'text-slate-900';
  const textM = isDark ? 'text-slate-400' : 'text-slate-600';
  const textS = isDark ? 'text-slate-500' : 'text-slate-500';

  const datasetJobs = trainingJobs.filter(j => j.datasetId === activeDatasetId);
  const completedJobs = datasetJobs.filter(j => j.status === 'completed');

  const toggleSelect = (id: string) => {
    setSelectedJobs(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const bestJob = completedJobs.length > 0 
    ? completedJobs.reduce((best, j) => (j.metrics?.mAP50 || 0) > (best.metrics?.mAP50 || 0) ? j : best, completedJobs[0])
    : null;

  if (completedJobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <FlaskConical className={`w-14 h-14 mb-4 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
        <h3 className={`text-lg font-bold ${textH}`}>No Experiments Yet</h3>
        <p className={`mt-1.5 text-xs max-w-md ${textM}`}>
          Run your first training job to start tracking experiments and comparing models side-by-side.
        </p>
      </div>
    );
  }

  const selectedForComparison = completedJobs.filter(j => selectedJobs.includes(j.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={`font-bold text-lg ${textH}`}>Experiment History</h3>
          <p className={`text-xs ${textM} mt-0.5`}>{completedJobs.length} completed runs · {datasetJobs.filter(j => j.status === 'running').length} running</p>
        </div>
        <div className="flex gap-2">
          {selectedJobs.length >= 2 && (
            <button onClick={() => setShowComparison(!showComparison)}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-bold flex items-center gap-2 transition-colors shadow-lg shadow-emerald-500/20">
              <BarChart3 className="w-3.5 h-3.5" /> Compare ({selectedJobs.length})
            </button>
          )}
        </div>
      </div>

      {/* Comparison Panel */}
      {showComparison && selectedForComparison.length >= 2 && (
        <div className={`p-5 rounded-2xl border ${bgCard} ${border}`}>
          <h4 className={`text-sm font-bold ${textH} mb-4 flex items-center gap-2`}>
            <BarChart3 className="w-4 h-4 text-emerald-500" /> Side-by-Side Comparison
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className={`border-b ${border}`}>
                  <th className={`text-left p-2 font-bold ${textS}`}>Metric</th>
                  {selectedForComparison.map(j => (
                    <th key={j.id} className={`text-center p-2 font-bold ${textH}`}>
                      {j.config.model.toUpperCase()}
                      {j.id === bestJob?.id && <Trophy className="w-3 h-3 text-amber-500 inline ml-1" />}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'mAP@50', key: 'mAP50', fmt: (v: number) => `${(v * 100).toFixed(1)}%` },
                  { label: 'Precision', key: 'precision', fmt: (v: number) => `${(v * 100).toFixed(1)}%` },
                  { label: 'Recall', key: 'recall', fmt: (v: number) => `${(v * 100).toFixed(1)}%` },
                  { label: 'F1 Score', key: 'f1', fmt: (v: number) => v.toFixed(4) },
                  { label: 'Inference', key: 'inferenceTime', fmt: (v: number) => `${v}ms` },
                  { label: 'Model Size', key: 'modelSizeMB', fmt: (v: number) => `${v}MB` },
                ].map((metric, i) => {
                  const values = selectedForComparison.map(j => (j.metrics as any)?.[metric.key] || 0);
                  const maxVal = Math.max(...values);
                  return (
                    <tr key={i} className={`border-b last:border-0 ${border}`}>
                      <td className={`p-2 font-medium ${textM}`}>{metric.label}</td>
                      {selectedForComparison.map((j, idx) => {
                        const val = (j.metrics as any)?.[metric.key] || 0;
                        const isBest = val === maxVal && metric.key !== 'inferenceTime' && metric.key !== 'modelSizeMB';
                        return (
                          <td key={j.id} className={`p-2 text-center font-mono font-bold ${isBest ? 'text-emerald-500' : textH}`}>
                            {metric.fmt(val)}
                            {isBest && <span className="ml-1 text-[9px]">🏆</span>}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
                <tr className={`border-b last:border-0 ${border}`}>
                  <td className={`p-2 font-medium ${textM}`}>Epochs</td>
                  {selectedForComparison.map(j => (
                    <td key={j.id} className={`p-2 text-center font-mono ${textH}`}>{j.progress.totalEpochs}</td>
                  ))}
                </tr>
                <tr>
                  <td className={`p-2 font-medium ${textM}`}>Mode</td>
                  {selectedForComparison.map(j => (
                    <td key={j.id} className="p-2 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        j.mode === 'ultra' ? 'bg-purple-500/10 text-purple-500' :
                        j.mode === 'expert' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-emerald-500/10 text-emerald-500'
                      }`}>{j.mode}</span>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Experiments Table */}
      <div className={`rounded-2xl border overflow-hidden ${bgCard} ${border}`}>
        <table className="w-full text-left text-xs">
          <thead className={`border-b ${border} ${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}`}>
            <tr>
              <th className={`p-3 font-bold ${textS} w-10`}>
                <input type="checkbox" className="rounded text-emerald-500 focus:ring-emerald-500 bg-transparent"
                  onChange={(e) => { if (e.target.checked) setSelectedJobs(completedJobs.map(j => j.id)); else setSelectedJobs([]); }} />
              </th>
              <th className={`p-3 font-bold ${textS}`}>Run ID</th>
              <th className={`p-3 font-bold ${textS}`}>Architecture</th>
              <th className={`p-3 font-bold ${textS}`}>Mode</th>
              <th className={`p-3 font-bold ${textS}`}>Epochs</th>
              <th className={`p-3 font-bold text-emerald-500`}>mAP@50</th>
              <th className={`p-3 font-bold ${textS}`}>Precision</th>
              <th className={`p-3 font-bold ${textS}`}>Recall</th>
              <th className={`p-3 font-bold ${textS}`}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {completedJobs.map((job) => (
              <tr key={job.id} className={`border-b last:border-0 ${border} ${isDark ? 'hover:bg-white/[0.02]' : 'hover:bg-slate-50'} transition-colors ${
                job.id === bestJob?.id ? (isDark ? 'bg-emerald-500/[0.03]' : 'bg-emerald-50/50') : ''
              }`}>
                <td className="p-3">
                  <input type="checkbox" checked={selectedJobs.includes(job.id)} onChange={() => toggleSelect(job.id)}
                    className="rounded text-emerald-500 focus:ring-emerald-500 bg-transparent" />
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <div className={`font-mono font-bold ${textH}`}>{job.id.substring(0, 10)}</div>
                    {job.id === bestJob?.id && <Trophy className="w-3.5 h-3.5 text-amber-500" />}
                  </div>
                  <div className={`text-[10px] mt-0.5 ${textS}`}>{new Date(job.startedAt).toLocaleString()}</div>
                </td>
                <td className="p-3">
                  <div className={`font-bold ${textH}`}>{job.config.model.toUpperCase()}</div>
                  <div className={`text-[10px] ${textS}`}>img: {job.config.imageSize}px</div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    job.mode === 'ultra' ? 'bg-purple-500/10 text-purple-500' :
                    job.mode === 'expert' ? 'bg-amber-500/10 text-amber-500' :
                    'bg-emerald-500/10 text-emerald-500'
                  }`}>{job.mode}</span>
                </td>
                <td className={`p-3 ${textH}`}>{job.progress.totalEpochs}</td>
                <td className="p-3 font-mono font-extrabold text-emerald-500">{((job.metrics?.mAP50 || 0) * 100).toFixed(1)}%</td>
                <td className={`p-3 font-mono ${textH}`}>{((job.metrics?.precision || 0) * 100).toFixed(1)}%</td>
                <td className={`p-3 font-mono ${textH}`}>{((job.metrics?.recall || 0) * 100).toFixed(1)}%</td>
                <td className="p-3">
                  <button onClick={() => { setActiveJobId(job.id); setActiveTab('results'); }}
                    className="flex items-center gap-1 text-xs font-bold text-emerald-500 hover:text-emerald-400 transition-colors">
                    View <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CVExperimentTracker;
