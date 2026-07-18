import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Activity, X, Server, Database, TrendingUp, AlertTriangle } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { useUserStore } from '@/store/userStore';

interface LiveData {
  timestamp: string;
  total_rows?: number;
  rows_per_sec?: number;
  cpu_usage?: number;
  error_rate?: number;
  connector_source: string;
  status: string;
}

interface Props {
  source: string;
  connectionId: string;
  onClose: () => void;
}

export const LiveStreamingDashboard: React.FC<Props> = ({ source, connectionId, onClose }) => {
  const { isDark } = useUserStore();
  const [dataStream, setDataStream] = useState<LiveData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const toast = useToast();

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/live-data/${connectionId}`;
    
    const connectWs = () => {
      try {
        ws.current = new WebSocket(wsUrl);
        
        ws.current.onopen = () => {
          setIsConnected(true);
          toast.success(`Connected to ${source} Live Stream`);
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const entry: LiveData = {
              timestamp: new Date().toISOString(),
              total_rows: data.total_rows,
              rows_per_sec: data.rows_per_sec,
              cpu_usage: data.cpu_usage,
              error_rate: data.error_rate,
              connector_source: source,
              status: data.status || 'OK'
            };
            setDataStream(prev => [...prev.slice(-99), entry]);
          } catch (e) {
            console.error('Failed to parse WS data', e);
          }
        };

        ws.current.onerror = () => {
          setConnectionError('Connection error. Retrying...');
        };

        ws.current.onclose = () => {
          setIsConnected(false);
          setTimeout(connectWs, 3000);
        };
      } catch (e) {
        setConnectionError('Failed to establish WebSocket');
      }
    };

    connectWs();
    return () => { ws.current?.close(); };
  }, [source, connectionId]);

  const latestData = dataStream.length > 0 ? dataStream[dataStream.length - 1] : null;

  // Theme
  const bg = isDark ? 'bg-[#111]' : 'bg-white';
  const bgHeader = isDark ? 'bg-[#1a1a1a]' : 'bg-gray-50';
  const border = isDark ? 'border-gray-800' : 'border-gray-200';
  const textPrimary = isDark ? 'text-white' : 'text-gray-900';
  const textSecondary = isDark ? 'text-gray-400' : 'text-gray-600';
  const textMuted = isDark ? 'text-gray-500' : 'text-gray-400';
  const cardBg = isDark ? 'bg-[#1a1a1a]' : 'bg-gray-50';
  const logBg = isDark ? 'bg-black' : 'bg-gray-900';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`w-full max-w-4xl ${bg} border ${border} rounded-2xl overflow-hidden shadow-2xl flex flex-col h-[80vh]`}
      >
        {/* Header */}
        <div className={`p-4 border-b ${border} flex items-center justify-between ${bgHeader}`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isConnected ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'}`}>
              <Activity className={`w-5 h-5 ${isConnected ? 'animate-pulse' : ''}`} />
            </div>
            <div>
              <h2 className={`font-bold ${textPrimary} flex items-center gap-2`}>
                {source} Live Stream
                {isConnected && <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>}
              </h2>
              <p className={`text-xs ${textSecondary}`}>
                {isConnected ? 'Receiving real-time telemetry' : connectionError ? connectionError : 'Connecting...'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10 text-gray-400 hover:text-white' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-900'}`}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {source === 'DataVision API Push' && (
            <div className={`p-4 rounded-xl border ${isDark ? 'bg-green-500/5 border-green-500/30' : 'bg-green-50 border-green-200'} text-left`}>
              <h3 className={`text-sm font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-green-400' : 'text-green-700'}`}>
                <Activity className="w-4 h-4" /> API Push is Active!
              </h3>
              <p className={`text-xs mb-2 ${textSecondary}`}>Your unique Push URL:</p>
              <code className={`text-xs p-2 rounded block overflow-x-auto font-mono ${isDark ? 'bg-black/60 text-green-300 border border-gray-800' : 'bg-gray-100 text-green-700 border border-gray-200'}`}>
                {`${window.location.protocol}//${window.location.host}/api/v1/push/${connectionId}`}
              </code>
              <p className={`text-xs mt-2 ${textMuted}`}>Run your generated Python script locally. Data will appear here in real-time.</p>
            </div>
          )}

          {/* Top KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { icon: Database, label: 'Total Rows', value: latestData?.total_rows?.toLocaleString() ?? '--' },
              { icon: TrendingUp, label: 'Rows Added/sec', value: latestData?.rows_per_sec?.toLocaleString() ?? '--' },
              { icon: Server, label: 'CPU Usage (Est)', value: latestData?.cpu_usage !== undefined ? `${latestData.cpu_usage.toFixed(1)}%` : '--' },
              { icon: AlertTriangle, label: 'Error Rate', value: latestData?.error_rate !== undefined ? `${latestData.error_rate.toFixed(2)}%` : '--', isError: latestData && (latestData.error_rate ?? 0) > 1.5 }
            ].map((kpi, i) => (
              <div key={i} className={`${cardBg} border ${border} p-4 rounded-xl`}>
                <div className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2 ${textSecondary}`}>
                  <kpi.icon className="w-4 h-4" /> {kpi.label}
                </div>
                <div className={`text-3xl font-bold font-mono ${kpi.isError ? 'text-red-500' : (i === 3 ? (isDark ? 'text-green-400' : 'text-green-600') : textPrimary)}`}>
                  {kpi.value}
                </div>
              </div>
            ))}
          </div>

          {/* Terminal / Log View — always dark for terminal feel */}
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 h-64 overflow-hidden flex flex-col">
            <div className="text-xs text-gray-500 font-mono mb-2 uppercase border-b border-gray-700 pb-2">
              Live Event Log (Agentic Feed)
            </div>
            <div className="flex-1 overflow-y-auto space-y-1 font-mono text-sm flex flex-col-reverse">
              {[...dataStream].reverse().map((data, idx) => (
                <div key={idx} className={`flex items-start gap-3 py-1 ${data.status === 'Anomaly Detected' ? 'text-red-400' : 'text-green-400/80'}`}>
                  <span className="text-gray-600">[{new Date(data.timestamp).toLocaleTimeString()}]</span>
                  <span className="flex-1">
                    {data.status === 'Anomaly Detected' 
                      ? `CRITICAL: Anomaly detected! CPU: ${data.cpu_usage}%, Errors: ${data.error_rate}%. Agent Swarm deployed for auto-remediation.` 
                      : `INFO: Telemetry OK. Rows: ${data.total_rows ?? '--'}, Velocity: ${data.rows_per_sec ?? '--'}/s`}
                  </span>
                </div>
              ))}
              {dataStream.length === 0 && (
                <div className="text-gray-600 animate-pulse">Waiting for telemetry data...</div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
