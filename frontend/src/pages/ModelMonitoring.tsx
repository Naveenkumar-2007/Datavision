import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, CheckCircle, Clock, Server, ArrowUpRight, Zap, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import apiService from '@/services/api';
import { api } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';
import { useUserStore } from '@/store/userStore';

export const ModelMonitoring: React.FC = () => {
    const isDark = useUserStore((state) => state.isDark);
    const { addToast } = useToast();
    
    const [deployments, setDeployments] = useState<any[]>([]);
    const [selectedDeployId, setSelectedDeployId] = useState<string>('');
    
    const [metrics, setMetrics] = useState<any>(null);
    const [driftAlerts, setDriftAlerts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDeployments();
    }, []);

    useEffect(() => {
        if (selectedDeployId) {
            fetchMonitoringData(selectedDeployId);
            // Setup polling
            const interval = setInterval(() => {
                fetchMonitoringData(selectedDeployId, true);
            }, 5000);
            return () => clearInterval(interval);
        }
    }, [selectedDeployId]);

    const fetchDeployments = async () => {
        try {
            const userId = useUserStore.getState().user?.id || 'default';
            // We use standard axios GET with X-User-ID for now
            const res = await api.get('/api/v1/deploy/list', {
                headers: { 'X-User-ID': userId }
            });
            const deps = res.data.deployments || [];
            setDeployments(deps);
            if (deps.length > 0) {
                setSelectedDeployId(deps[0].deploy_id);
            } else {
                setLoading(false);
            }
        } catch (e) {
            console.error("Failed to load deployments", e);
            setLoading(false);
        }
    };

    const fetchMonitoringData = async (deployId: string, background = false) => {
        if (!background) setLoading(true);
        try {
            // Fetch Metrics
            const metricsRes = await api.get(`/api/v1/monitoring/${deployId}/metrics`);
            setMetrics(metricsRes.data.data);
            
            // Fetch Drift
            const driftRes = await api.get(`/api/v1/monitoring/${deployId}/drift`);
            setDriftAlerts(driftRes.data.alerts || []);
            
        } catch (e: any) {
            if (!background) {
                addToast('error', 'Failed to load telemetry', e.response?.data?.detail || e.message);
            }
        } finally {
            if (!background) setLoading(false);
        }
    };

    if (loading && !metrics) {
        return (
            <div className="flex h-full items-center justify-center">
                <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
            </div>
        );
    }

    if (deployments.length === 0) {
        return (
            <div className="flex flex-col h-full items-center justify-center p-8 text-center">
                <Server className="w-16 h-16 text-gray-400 mb-4" />
                <h2 className="text-2xl font-bold mb-2">No Active Deployments</h2>
                <p className="text-gray-500 mb-6 max-w-md">
                    You haven't deployed any models yet. Go to ML Predictions, select a model, and click "Deploy as API".
                </p>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto h-full p-6 md:p-8" style={{ backgroundColor: 'var(--bg-main)' }}>
            <div className="max-w-7xl mx-auto space-y-8">
                
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-500">
                                <Activity className="w-6 h-6" />
                            </div>
                            <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                                Model Monitoring
                            </h1>
                        </div>
                        <p className="text-gray-500">Real-time telemetry and data drift detection for deployed APIs.</p>
                    </div>
                    
                    <div className="min-w-[250px]">
                        <select
                            value={selectedDeployId}
                            onChange={(e) => setSelectedDeployId(e.target.value)}
                            className="w-full p-3 rounded-xl border font-semibold outline-none focus:ring-2 focus:ring-purple-500/50"
                            style={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                        >
                            {deployments.map(d => (
                                <option key={d.deploy_id} value={d.deploy_id}>
                                    {d.model_name} ({d.deploy_id.slice(-6)})
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {metrics && (
                    <>
                        {/* KPI Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            {[
                                { title: 'Status', value: 'Active', icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500/10' },
                                { title: 'Total Predictions', value: metrics.total_requests.toLocaleString(), icon: Zap, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
                                { title: 'Avg Latency', value: `${metrics.avg_latency_ms} ms`, icon: Clock, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                                { title: 'Drift Alerts', value: driftAlerts.length, icon: AlertTriangle, color: driftAlerts.length > 0 ? 'text-red-500' : 'text-gray-500', bg: driftAlerts.length > 0 ? 'bg-red-500/10' : 'bg-gray-500/10' },
                            ].map((kpi, i) => (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    key={kpi.title}
                                    className="p-6 rounded-2xl border shadow-sm flex items-center justify-between"
                                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                >
                                    <div>
                                        <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>{kpi.title}</p>
                                        <h3 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{kpi.value}</h3>
                                    </div>
                                    <div className={`p-3 rounded-xl ${kpi.bg}`}>
                                        <kpi.icon className={`w-6 h-6 ${kpi.color}`} />
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            
                            {/* Latency Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="lg:col-span-2 p-6 rounded-2xl border shadow-sm"
                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                            >
                                <h3 className="text-lg font-bold mb-6" style={{ color: 'var(--text-primary)' }}>Inference Latency (Live)</h3>
                                <div className="h-[300px]">
                                    {metrics.timeseries && metrics.timeseries.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={metrics.timeseries}>
                                                <defs>
                                                    <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#333' : '#eee'} vertical={false} />
                                                <XAxis 
                                                    dataKey="timestamp" 
                                                    tickFormatter={(timeStr) => new Date(timeStr).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
                                                    stroke={isDark ? '#888' : '#666'} 
                                                />
                                                <YAxis stroke={isDark ? '#888' : '#666'} />
                                                <Tooltip 
                                                    contentStyle={{ backgroundColor: isDark ? '#1e1e1e' : '#fff', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                                    labelFormatter={(label) => new Date(label).toLocaleTimeString()}
                                                />
                                                <Area type="monotone" dataKey="latency_ms" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorLatency)" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center border-2 border-dashed rounded-xl" style={{ borderColor: 'var(--border-color)' }}>
                                            <Activity className="w-8 h-8 text-gray-400 mb-2" />
                                            <span className="text-gray-500">Waiting for API requests...</span>
                                        </div>
                                    )}
                                </div>
                            </motion.div>

                            {/* Data Drift Panel */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 }}
                                className="p-6 rounded-2xl border shadow-sm flex flex-col"
                                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                            >
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>Data Drift Monitor</h3>
                                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-500">
                                        KS Test
                                    </span>
                                </div>
                                
                                <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                                    {driftAlerts.length > 0 ? (
                                        driftAlerts.map((alert, i) => (
                                            <div key={i} className={`p-4 rounded-xl border ${alert.severity === 'high' ? 'border-red-500/30 bg-red-500/5' : 'border-yellow-500/30 bg-yellow-500/5'}`}>
                                                <div className="flex items-start justify-between mb-2">
                                                    <span className={`font-semibold ${alert.severity === 'high' ? 'text-red-500' : 'text-yellow-500'}`}>
                                                        {alert.feature}
                                                    </span>
                                                    <span className={`text-xs font-bold px-2 py-1 rounded-md ${alert.severity === 'high' ? 'bg-red-500/10 text-red-500' : 'bg-yellow-500/10 text-yellow-500'}`}>
                                                        {alert.shift_percentage.toFixed(1)}% Shift
                                                    </span>
                                                </div>
                                                <div className="flex justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
                                                    <span>Train Mean: <strong>{alert.training_mean.toFixed(2)}</strong></span>
                                                    <span>Live Mean: <strong>{alert.inference_mean.toFixed(2)}</strong></span>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-center p-4">
                                            <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mb-4">
                                                <CheckCircle className="w-8 h-8 text-green-500" />
                                            </div>
                                            <h4 className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>No Drift Detected</h4>
                                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                                Live inference data matches the training distribution perfectly.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default ModelMonitoring;

