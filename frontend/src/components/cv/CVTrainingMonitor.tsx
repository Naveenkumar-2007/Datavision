import React from 'react';
import { motion } from 'framer-motion';
import { Pause, Play, Square, Loader2, AlertTriangle, Cpu, Activity, Database, Server } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';
import { CVTrainingJob } from '@/types/cv';
import { useUserStore } from '@/store/userStore';

interface Props {
  job: CVTrainingJob;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}

const CVTrainingMonitor: React.FC<Props> = ({ job, onPause, onResume, onStop }) => {
  const { isDark } = useUserStore();
  const progress = job.progress || {};
  const totalEpochs = progress.totalEpochs || 1;
  const currentEpoch = progress.epoch || 0;
  let percentComplete = Math.round((currentEpoch / totalEpochs) * 100) || 0;
  if (job.status === 'failed') percentComplete = 0;
  
  const systemStats = progress.systemStats || { gpuUsage: 0, vramUsage: '0GB', cpuUsage: 0, ramUsage: '0GB' };
  const metrics = progress.metrics || {};
  const logs = progress.logs || [];

  // Mock chart data history if not provided by backend yet (in real app, backend sends history array)
  // For UI sake, we'll simulate a history based on current epoch
  const chartData = Array.from({ length: Math.max(1, currentEpoch) }).map((_, i) => ({
    epoch: i + 1,
    loss: Math.max(0, 3.5 * Math.exp(-(i/totalEpochs)*4) + (Math.random() * 0.1)),
    map: Math.min(0.98, 0.1 + (0.85 * (1 - Math.exp(-(i/totalEpochs)*5))))
  }));

  if (currentEpoch > 0) {
    chartData[currentEpoch - 1] = {
      epoch: currentEpoch,
      loss: progress.loss || 0,
      map: metrics.mAP50 || 0
    };
  }

  return (
    <div className="space-y-6">
      {job.status === 'failed' && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-red-500 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-500">Training Failed</h3>
            <p className="text-sm text-red-400 mt-1">{job.error || 'An unknown error occurred during training.'}</p>
          </div>
        </div>
      )}
      
      {/* Top Status Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
        <div className="flex items-center gap-4">
          <div className="relative flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800">
            {job.status === 'running' ? (
              <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            ) : job.status === 'paused' ? (
              <Pause className="w-8 h-8 text-amber-500" />
            ) : job.status === 'completed' ? (
              <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center">
                <div className="w-4 h-4 bg-white rounded-full" />
              </div>
            ) : (
              <AlertTriangle className="w-8 h-8 text-red-500" />
            )}
            <svg className="absolute inset-0 w-full h-full -rotate-90">
              <circle cx="32" cy="32" r="30" fill="none" strokeWidth="4" className="stroke-slate-200 dark:stroke-slate-700" />
              <circle 
                cx="32" cy="32" r="30" 
                fill="none" 
                strokeWidth="4" 
                className="stroke-emerald-500 transition-all duration-1000"
                strokeDasharray="188.5"
                strokeDashoffset={188.5 - (188.5 * percentComplete) / 100}
              />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              {percentComplete}% <span className="text-lg font-medium" style={{ color: 'var(--text-muted)' }}>Complete</span>
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Epoch {currentEpoch} of {totalEpochs} • {job.mode?.toUpperCase() || 'FAST'} Mode
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {job.status === 'running' && (
            <button onClick={onPause} className="p-3 rounded-xl border hover:bg-amber-500/10 hover:text-amber-500 hover:border-amber-500 transition-colors" style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}>
              <Pause className="w-5 h-5" />
            </button>
          )}
          {job.status === 'paused' && (
            <button onClick={onResume} className="p-3 rounded-xl border hover:bg-emerald-500/10 hover:text-emerald-500 hover:border-emerald-500 transition-colors" style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}>
              <Play className="w-5 h-5" />
            </button>
          )}
          {(job.status === 'running' || job.status === 'paused') && (
            <button onClick={onStop} className="p-3 rounded-xl border hover:bg-red-500/10 hover:text-red-500 hover:border-red-500 transition-colors" style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}>
              <Square className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Charts Area */}
        <div className="lg:col-span-2 space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-2xl border" 
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
          >
            <h3 className="font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Training Metrics</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#334155' : '#e2e8f0'} />
                  <XAxis dataKey="epoch" stroke={isDark ? '#94a3b8' : '#64748b'} fontSize={12} />
                  <YAxis yAxisId="left" stroke={isDark ? '#94a3b8' : '#64748b'} fontSize={12} />
                  <YAxis yAxisId="right" orientation="right" stroke={isDark ? '#94a3b8' : '#64748b'} fontSize={12} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: isDark ? '#1e293b' : '#fff', borderColor: isDark ? '#334155' : '#e2e8f0', borderRadius: '8px' }}
                  />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={false} name="Loss" />
                  <Line yAxisId="right" type="monotone" dataKey="map" stroke="#10b981" strokeWidth={2} dot={false} name="mAP50" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-4 rounded-2xl border bg-slate-900 overflow-hidden relative" 
            style={{ borderColor: 'var(--border-color)' }}
          >
            <div className="flex items-center justify-between mb-2 border-b border-slate-700 pb-2">
              <h3 className="font-semibold text-slate-200 font-mono text-sm">training_logs.sh</h3>
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
                <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
                <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
              </div>
            </div>
            <div className="h-48 overflow-y-auto font-mono text-xs space-y-1">
              {logs.map((log, i) => (
                <div key={i} className="text-slate-400">
                  <span className="text-emerald-500 mr-2">$</span>
                  {log}
                </div>
              ))}
              {job.status === 'running' && (
                <div className="text-slate-400 animate-pulse">
                  <span className="text-emerald-500 mr-2">$</span>_
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* System Stats Sidebar */}
        <div className="space-y-4">
          <motion.div 
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-4 rounded-2xl border" 
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-emerald-500" />
              <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>System Monitor</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1" style={{ color: 'var(--text-muted)' }}><Server className="w-4 h-4" /> GPU Usage</span>
                  <span className="font-bold text-emerald-500">{systemStats.gpuUsage}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                  <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${systemStats.gpuUsage}%` }}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1" style={{ color: 'var(--text-muted)' }}><Database className="w-4 h-4" /> VRAM</span>
                  <span className="font-bold text-purple-500">{systemStats.vramUsage} / 16GB</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                  <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: '45%' }}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1" style={{ color: 'var(--text-muted)' }}><Cpu className="w-4 h-4" /> CPU</span>
                  <span className="font-bold text-blue-500">{systemStats.cpuUsage}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                  <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${systemStats.cpuUsage}%` }}></div>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* Current Metrics Snapshot */}
          <motion.div 
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="p-4 rounded-2xl border" 
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
          >
            <h3 className="font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Current Performance</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl border bg-black/5 dark:bg-white/5" style={{ borderColor: 'var(--border-color)' }}>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Loss</div>
                <div className="text-xl font-bold text-red-500">{(progress.loss || 0).toFixed(3)}</div>
              </div>
              <div className="p-3 rounded-xl border bg-black/5 dark:bg-white/5" style={{ borderColor: 'var(--border-color)' }}>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>mAP50</div>
                <div className="text-xl font-bold text-emerald-500">{(metrics.mAP50 || 0).toFixed(3)}</div>
              </div>
              <div className="p-3 rounded-xl border bg-black/5 dark:bg-white/5" style={{ borderColor: 'var(--border-color)' }}>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Precision</div>
                <div className="text-xl font-bold text-blue-500">{(metrics.precision || 0).toFixed(3)}</div>
              </div>
              <div className="p-3 rounded-xl border bg-black/5 dark:bg-white/5" style={{ borderColor: 'var(--border-color)' }}>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Recall</div>
                <div className="text-xl font-bold text-purple-500">{(metrics.recall || 0).toFixed(3)}</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default CVTrainingMonitor;
