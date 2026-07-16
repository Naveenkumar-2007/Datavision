import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Lock, Database, Server, Key, ShieldCheck, Loader2 } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { useUserStore } from '@/store/userStore';
import { api } from '@/services/api';

interface Props {
  source: string;
  onClose: () => void;
  onConnect: (connectionId: string) => void;
}

export const ConnectionSetupModal: React.FC<Props> = ({ source, onClose, onConnect }) => {
  const { isDark } = useUserStore();
  const [step, setStep] = useState(1);
  const [isConnecting, setIsConnecting] = useState(false);
  const toast = useToast();

  const [host, setHost] = useState('');
  const [databaseName, setDatabaseName] = useState('');
  const [targetTable, setTargetTable] = useState('');
  const [credentials, setCredentials] = useState('');
  
  const handleConnect = async () => {
    if (!host || !credentials) {
      toast.error('Host and Credentials are required');
      return;
    }
    
    setIsConnecting(true);
    try {
      // POST credentials to backend using the configured axios instance
      const response = await api.post('/api/v1/connections', {
        source_type: source.toLowerCase(),
        host,
        database_name: databaseName,
        target_table: targetTable,
        credentials
      });
      
      const connectionId = response.data.connection_id;
      
      // Persist guest connections
      if (response.data.is_guest && response.data.connection) {
        const stored = JSON.parse(localStorage.getItem('guest_live_connections') || '[]');
        stored.unshift(response.data.connection); // Add to top
        localStorage.setItem('guest_live_connections', JSON.stringify(stored));
      }
      
      setStep(2);
      
      // After success step, trigger connect with the real connectionId
      setTimeout(() => {
        onConnect(connectionId);
      }, 1500);
      
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className={`fixed inset-0 z-[60] flex items-center justify-center p-4 backdrop-blur-md ${isDark ? 'bg-black/60' : 'bg-white/40'}`}>
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`w-full max-w-md border rounded-2xl overflow-hidden shadow-2xl flex flex-col ${isDark ? 'bg-[#111] border-gray-800' : 'bg-white border-gray-200'}`}
      >
        <div className={`p-4 border-b flex items-center justify-between ${isDark ? 'bg-[#1a1a1a] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isDark ? 'bg-blue-500/20 text-blue-400' : 'bg-blue-100 text-blue-600'}`}>
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h2 className={`font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Secure Connection
              </h2>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                End-to-end encrypted link to {source}
              </p>
            </div>
          </div>
          <button onClick={onClose} className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10 text-gray-400 hover:text-white' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-900'}`} disabled={isConnecting}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          {step === 1 ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className={`text-sm flex items-center gap-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <Server className="w-4 h-4" /> Host / Endpoint URL
                </label>
                <input 
                  type="text" 
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder={`e.g. ${source.toLowerCase()}.enterprise.net`}
                  className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 transition-colors ${isDark ? 'bg-[#1a1a1a] border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                />
              </div>
              
              <div className="space-y-2">
                <label className={`text-sm flex items-center gap-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <Database className="w-4 h-4" /> Database / Warehouse Name
                </label>
                <input 
                  type="text" 
                  value={databaseName}
                  onChange={(e) => setDatabaseName(e.target.value)}
                  placeholder="e.g. production_analytics"
                  className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 transition-colors ${isDark ? 'bg-[#1a1a1a] border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                />
              </div>

              <div className="space-y-2">
                <label className={`text-sm flex items-center gap-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <Database className="w-4 h-4" /> Target Table / Stream
                </label>
                <input 
                  type="text" 
                  value={targetTable}
                  onChange={(e) => setTargetTable(e.target.value)}
                  placeholder="e.g. weather_data"
                  className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 transition-colors ${isDark ? 'bg-[#1a1a1a] border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                />
              </div>

              <div className="space-y-2">
                <label className={`text-sm flex items-center gap-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <Key className="w-4 h-4" /> Secure API Key / Token
                </label>
                <input 
                  type="password" 
                  value={credentials}
                  onChange={(e) => setCredentials(e.target.value)}
                  placeholder="••••••••••••••••••••••••"
                  className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 transition-colors font-mono tracking-widest ${isDark ? 'bg-[#1a1a1a] border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                />
              </div>

              <button 
                onClick={handleConnect}
                disabled={isConnecting}
                className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-70"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Negotiating Secure Handshake...
                  </>
                ) : (
                  <>
                    <Lock className="w-5 h-5" />
                    Establish Secure Connection
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <motion.div 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center"
              >
                <ShieldCheck className="w-10 h-10 text-green-500" />
              </motion.div>
              <h3 className={`text-xl font-bold text-center ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Established</h3>
              <p className={`text-center text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Secure tunnel to {source} verified.<br/>
                Launching Agentic Live Dashboard...
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};
