import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Bell,
  Clock,
  ArrowRight,
  Search,
  Shield
} from 'lucide-react';

import apiService from '@/services/api';
import { useToast } from '@/contexts/ToastContext';
import { useLiveStore } from '@/store/liveStore';

const AnomalyMonitor: React.FC = () => {
  const { isDark } = useUserStore();
  const navigate = useNavigate();
  const toast = useToast();
  const { anomalyCache, setAnomalyCache } = useLiveStore();
  
  const [activeTab, setActiveTab] = useState<'all' | 'unresolved'>('unresolved');
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [showAlertRules, setShowAlertRules] = useState(false);
  const [summary, setSummary] = useState<any>(() => {
    return anomalyCache['latest_anomalies'] || {
      critical_count: 0,
      scanned_metrics: 0,
      mean_resolution_time: "—",
      anomalies: []
    };
  });
  
  const fetchAnomalies = async () => {
    if (!anomalyCache['latest_anomalies']) {
        setLoading(true);
    }
    try {
      const response = await apiService.getAnomaliesOverview();
      if (response.data) {
        setSummary(response.data);
        setAnomalyCache('latest_anomalies', response.data);
      }
    } catch (error) {
      console.error("Error fetching anomalies", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      await apiService.triggerAnomalyScan();
      await fetchAnomalies();
    } catch (error) {
      console.error("Error triggering scan", error);
    } finally {
      setScanning(false);
    }
  };

  const handleAnalyzeRootCause = (anomaly: any) => {
    // Navigate to AI Analyst with the anomaly question pre-filled
    const question = `Analyze the root cause of this anomaly: ${anomaly.metric}. ${anomaly.description}`;
    navigate('/chat', { state: { prefillMessage: question } });
  };

  const handleAutoFix = async (anomaly: any) => {
    toast.success(`Agentic Swarm initiated for anomaly: ${anomaly.metric}. Fixing data...`);
    try {
      const response = await apiService.triggerAutoFix();
      if (response.data?.status === 'success') {
        toast.success(response.data.message || `${anomaly.metric} anomaly successfully resolved!`);
        // Refresh anomalies to reflect the cleaned dataset
        await fetchAnomalies();
      } else {
        toast.error(`Auto-fix failed: ${response.data?.message}`);
      }
    } catch (error) {
      toast.error('Failed to communicate with Agentic Swarm.');
      console.error(error);
    }
  };

  const anomalies = summary.anomalies || [];
  const unresolvedCount = anomalies.filter((a: any) => !a.resolved).length;
  const resolvedCount = anomalies.filter((a: any) => a.resolved).length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
            📈 Anomaly Monitor
          </h2>
          <p className="text-sm mt-1" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            Proactive 24/7 metric scanning powered by DataVision Autonomous Intelligence.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleScan} className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 text-sm font-medium transition-all ${
            isDark ? 'border-white/10 hover:bg-white/5 text-gray-200' : 'border-gray-200 hover:bg-gray-50 text-gray-700'
          }`}>
            <RefreshCw className={`w-4 h-4 ${scanning || loading ? 'animate-spin' : ''}`} /> Scan Data
          </button>
          <button 
            onClick={() => setShowAlertRules(!showAlertRules)}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/20"
          >
            <Bell className="w-4 h-4" /> Alert Rules
          </button>
        </div>
      </div>

      {/* Alert Rules Panel */}
      {showAlertRules && (
        <div className={`p-6 rounded-2xl border ${isDark ? 'bg-indigo-500/10 border-indigo-500/20' : 'bg-indigo-50 border-indigo-100'}`}>
          <h3 className="font-semibold mb-3 flex items-center gap-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
            <Shield className="w-5 h-5 text-indigo-400" /> Alert Configuration
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div className={`p-4 rounded-xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-white border-gray-200'}`}>
              <p className="text-xs text-gray-500 mb-1">Z-Score Threshold</p>
              <p className="font-bold text-lg" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>2.5σ</p>
              <p className="text-xs text-gray-500 mt-1">Values beyond 2.5 standard deviations are flagged</p>
            </div>
            <div className={`p-4 rounded-xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-white border-gray-200'}`}>
              <p className="text-xs text-gray-500 mb-1">IQR Multiplier</p>
              <p className="font-bold text-lg" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>1.5×</p>
              <p className="text-xs text-gray-500 mt-1">Interquartile range multiplier for outlier detection</p>
            </div>
            <div className={`p-4 rounded-xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-white border-gray-200'}`}>
              <p className="text-xs text-gray-500 mb-1">Missing Data Alert</p>
              <p className="font-bold text-lg" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>&gt;20%</p>
              <p className="text-xs text-gray-500 mt-1">Columns with &gt;20% null values are flagged</p>
            </div>
          </div>
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`p-5 rounded-2xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>Critical Anomalies</span>
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <p className="text-3xl font-bold mt-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>{loading ? '-' : summary.critical_count}</p>
          <div className="mt-2 text-xs flex items-center gap-1 text-red-400">
            <span>{summary.critical_count > 0 ? 'Needs immediate review' : 'All clear'}</span>
          </div>
        </div>

        <div className={`p-5 rounded-2xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>Total Scanned Metrics</span>
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          </div>
          <p className="text-3xl font-bold mt-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>{loading ? '-' : summary.scanned_metrics}</p>
          <div className="mt-2 text-xs flex items-center gap-1 text-emerald-400">
            <span>{anomalies.length === 0 ? '100% metrics healthy' : `${anomalies.length} anomalies detected`}</span>
          </div>
        </div>

        <div className={`p-5 rounded-2xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>Scan Mode</span>
            <Clock className="w-5 h-5 text-indigo-500" />
          </div>
          <p className="text-3xl font-bold mt-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>{loading ? '-' : summary.mean_resolution_time}</p>
          <div className="mt-2 text-xs flex items-center gap-1 text-indigo-400">
            <span>Statistical: Z-Score + IQR</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b" style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
        <button 
          onClick={() => setActiveTab('unresolved')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition-all ${
            activeTab === 'unresolved' 
              ? 'border-indigo-500 text-indigo-400' 
              : 'border-transparent text-gray-500 hover:text-gray-400'
          }`}
        >
          Unresolved ({unresolvedCount})
        </button>
        <button 
          onClick={() => setActiveTab('all')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition-all ${
            activeTab === 'all' 
              ? 'border-indigo-500 text-indigo-400' 
              : 'border-transparent text-gray-500 hover:text-gray-400'
          }`}
        >
          All Scans ({anomalies.length})
        </button>
      </div>

      {/* Empty State */}
      {!loading && anomalies.length === 0 && (
        <div className={`p-12 rounded-2xl border text-center ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100'}`}>
          <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
          <h3 className="text-lg font-bold mb-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>All Clear!</h3>
          <p className="text-sm text-gray-500">No anomalies detected in your uploaded data. Your metrics look healthy.</p>
          <p className="text-xs text-gray-500 mt-2">Upload data in the Data Hub, then click "Scan Data" to analyze.</p>
        </div>
      )}

      {/* Anomalies List */}
      <div className="space-y-4">
        {anomalies
          .filter((a: any) => activeTab === 'all' || (activeTab === 'unresolved' ? !a.resolved : a.resolved))
          .map((anom: any) => (
            <div 
              key={anom.id}
              className={`p-6 rounded-2xl border transition-all ${
                isDark 
                  ? 'bg-white/5 border-white/5 hover:bg-white/[0.08]' 
                  : 'bg-white border-gray-100 shadow-sm hover:shadow-md'
              }`}
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${
                      anom.importance === 'high' ? 'bg-red-500/10 text-red-400' : 
                      anom.importance === 'medium' ? 'bg-amber-500/10 text-amber-400' :
                      'bg-blue-500/10 text-blue-400'
                    }`}>
                      {anom.importance} Risk
                    </span>
                    <h3 className="text-base font-semibold" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
                      {anom.metric}
                    </h3>
                  </div>
                  <p className="text-sm" style={{ color: isDark ? '#cbd5e1' : '#475569' }}>
                    {anom.description}
                  </p>
                  <div className="flex items-center gap-4 text-xs mt-2" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
                    <span>Dataset: <strong>{anom.dataset}</strong></span>
                    <span>•</span>
                    <span>Detected: <strong>{anom.detectedAt}</strong></span>
                  </div>
                </div>

                <div className="text-right flex flex-col items-end gap-2 shrink-0">
                  <span className="text-sm font-bold" style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}>
                    {anom.value}
                  </span>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleAutoFix(anom)}
                      className="px-3 py-1.5 rounded-lg bg-green-500/10 hover:bg-green-500/20 text-green-500 text-xs font-semibold flex items-center gap-1.5 transition-all"
                    >
                      <Shield className="w-3.5 h-3.5" /> Auto-Fix
                    </button>
                    <button 
                      onClick={() => handleAnalyzeRootCause(anom)}
                      className="px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-xs font-semibold flex items-center gap-1.5 transition-all"
                    >
                      Analyze Root Cause <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};

export default AnomalyMonitor;
