import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Activity, X, Server, Database, TrendingUp, AlertTriangle } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';

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
  const [dataStream, setDataStream] = useState<LiveData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const toast = useToast();

  useEffect(() => {
    // Determine WS URL based on current host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // Append the connectionId to the URL path
    const wsUrl = `${protocol}//${host}/api/v1/ws/live-data/${connectionId}`;
    
    const connectWs = () => {
      try {
        // Use relative path via Vite proxy for local dev, or current host for prod
        const finalWsUrl = wsUrl;
        
        ws.current = new WebSocket(finalWsUrl);
        
        ws.current.onopen = () => {
          setIsConnected(true);
          toast.success(`Connected to ${source} Live Stream`);
        };

        ws.current.onmessage = (event) => {
          try {
            const parsedData = JSON.parse(event.data);
            
            // Check if backend sent an error message
            if (parsedData.error) {
              setConnectionError(parsedData.error);
              setIsConnected(false);
              return;
            }
            
            // Override source with the one requested
            parsedData.connector_source = source;
            
            setDataStream((prev) => {
              const newStream = [...prev, parsedData];
              // Keep only last 20 data points
              if (newStream.length > 20) {
                newStream.shift();
              }
              return newStream;
            });
          } catch (e) {
            console.error('Error parsing live data', e);
          }
        };

        ws.current.onerror = (error) => {
          console.error('WebSocket Error:', error);
          setConnectionError('Failed to connect to streaming server.');
          setIsConnected(false);
        };

        ws.current.onclose = () => {
          setIsConnected(false);
        };
      } catch (e: any) {
        setConnectionError(e.message);
      }
    };

    connectWs();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [source, connectionId]);

  const latestData = dataStream.length > 0 ? dataStream[dataStream.length - 1] : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-4xl bg-[#111] border border-gray-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col h-[80vh]"
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-[#1a1a1a]">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isConnected ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
              <Activity className={`w-5 h-5 ${isConnected ? 'animate-pulse' : ''}`} />
            </div>
            <div>
              <h2 className="font-bold text-white flex items-center gap-2">
                {source} Live Stream
                {isConnected && <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>}
              </h2>
              <p className="text-xs text-gray-400">
                {isConnected ? 'Receiving real-time telemetry' : connectionError ? connectionError : 'Connecting...'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {source === 'DataVision API Push' && (
            <div className="p-4 rounded-xl border bg-black/40 border-green-500/30 text-left">
              <h3 className="text-sm font-bold text-green-400 mb-2 flex items-center gap-2">
                <Activity className="w-4 h-4" /> API Push is Active!
              </h3>
              <p className="text-xs text-gray-300 mb-2">Your unique Push URL:</p>
              <code className="text-xs bg-black/60 p-2 rounded text-green-300 block overflow-x-auto border border-gray-800 font-mono">
                {`${window.location.protocol}//${window.location.host}/api/v1/push/${connectionId}`}
              </code>
              <p className="text-xs text-gray-500 mt-2">Run your generated Python script locally. Data will appear here in real-time.</p>
            </div>
          )}

          {/* Top KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-dark-card border border-gray-800 p-4 rounded-xl">
              <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
                <Database className="w-4 h-4" /> Total Rows
              </div>
              <div className="text-3xl font-bold text-white font-mono">
                {latestData && latestData.total_rows !== undefined ? latestData.total_rows.toLocaleString() : '--'}
              </div>
            </div>
            
            <div className="bg-dark-card border border-gray-800 p-4 rounded-xl">
              <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" /> Rows Added/sec
              </div>
              <div className="text-3xl font-bold text-white font-mono">
                {latestData && latestData.rows_per_sec !== undefined ? latestData.rows_per_sec.toLocaleString() : '--'}
              </div>
            </div>

            <div className="bg-dark-card border border-gray-800 p-4 rounded-xl">
              <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
                <Server className="w-4 h-4" /> CPU Usage (Est)
              </div>
              <div className="text-3xl font-bold text-white font-mono">
                {latestData && latestData.cpu_usage !== undefined ? `${latestData.cpu_usage.toFixed(1)}%` : '--'}
              </div>
            </div>

            <div className="bg-dark-card border border-gray-800 p-4 rounded-xl">
              <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Error Rate
              </div>
              <div className={`text-3xl font-bold font-mono ${latestData && (latestData.error_rate ?? 0) > 1.5 ? 'text-red-400' : 'text-green-400'}`}>
                {latestData && latestData.error_rate !== undefined ? `${latestData.error_rate.toFixed(2)}%` : '--'}
              </div>
            </div>
          </div>

          {/* Terminal / Log View */}
          <div className="bg-black border border-gray-800 rounded-xl p-4 h-64 overflow-hidden flex flex-col">
            <div className="text-xs text-gray-500 font-mono mb-2 uppercase border-b border-gray-800 pb-2">
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
