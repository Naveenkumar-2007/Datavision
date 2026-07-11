import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { motion } from 'framer-motion';
import { 
  GitBranch, 
  Database, 
  FileText, 
  Cpu, 
  Share2, 
  ShieldAlert,
  Search,
  Check,
  Brain,
  Layout,
  RefreshCw,
  Download
} from 'lucide-react';

import { api } from '@/services/api';

const iconMap: Record<string, React.ReactNode> = {
  database: <Database className="w-8 h-8 text-blue-400 mb-2" />,
  cpu: <Cpu className="w-8 h-8 text-indigo-400 mb-2" />,
  brain: <Brain className="w-8 h-8 text-amber-400 mb-2" />,
  layout: <FileText className="w-8 h-8 text-emerald-400 mb-2" />
};

const DataLineage: React.FC = () => {
  const { isDark } = useUserStore();
  const [lineageData, setLineageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rescanning, setRescanning] = useState(false);

  const fetchData = async () => {
    try {
      const response = await api.get('/api/v1/lineage/');
      setLineageData(response.data);
    } catch (err) {
      console.error("Failed to load lineage", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRescan = async () => {
    setRescanning(true);
    await fetchData();
    setRescanning(false);
  };

  const handleExportAuditLog = async () => {
    try {
      const response = await api.get('/api/v1/lineage/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'datavision_audit_log.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export audit log", err);
    }
  };

  const stats = lineageData?.stats || {};
  const nodes = lineageData?.nodes || [];
  const edges = lineageData?.edges || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto min-h-screen">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
            🗺️ Data Lineage & Governance
          </h2>
          <p className="text-sm mt-1" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            Visual audit trails and data flow compliance center.
          </p>
        </div>
        <button 
          onClick={handleRescan}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-lg shadow-indigo-500/20 transition-all font-medium text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${rescanning ? 'animate-spin' : ''}`} />
          Re-scan Flows
        </button>
      </div>

      {/* Audit stats — Dynamic from real data */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'GDPR COMPLIANCE', value: stats.gdpr_status === 'Verified' ? '100% Verified' : 'No Data', color: stats.gdpr_status === 'Verified' ? 'text-emerald-400' : 'text-gray-500' },
          { label: 'ACTIVE PIPELINES', value: `${stats.total_pipelines || 0} Streams`, color: isDark ? 'text-white' : 'text-gray-900' },
          { label: 'DATA NODES', value: `${stats.total_nodes || 0} Nodes`, color: isDark ? 'text-white' : 'text-gray-900' },
          { label: 'ENCRYPTION STANDARD', value: stats.encryption || 'AES-256', color: 'text-teal-400' }
        ].map((stat, i) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            key={i}
            className={`p-5 rounded-2xl border backdrop-blur-xl ${isDark ? 'bg-white/5 border-white/5' : 'bg-white border-gray-100 shadow-sm'}`}
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">{stat.label}</p>
            <p className={`text-xl font-bold mt-2 ${stat.color}`}>{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Visual Flow Chart */}
      <div className={`p-6 rounded-3xl border min-h-[500px] flex flex-col relative overflow-hidden ${
        isDark ? 'bg-zinc-900/50 border-white/5' : 'bg-white border-gray-200/60 shadow-sm'
      }`}>
        <div className="flex justify-between items-center border-b pb-4 mb-8" style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
          <span className="font-semibold text-sm">Interactive Data Flow Diagram</span>
          <button 
            onClick={handleExportAuditLog}
            className="px-4 py-1.5 rounded-lg border border-indigo-500/30 text-indigo-400 text-xs font-medium hover:bg-indigo-500/10 transition-colors flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" /> Export Audit Log (.csv)
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex justify-center items-center">
            <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex-1 flex flex-col justify-center items-center text-center">
            <Database className="w-12 h-12 text-gray-500 mb-4" />
            <h3 className="text-lg font-bold mb-2" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>No Data Pipelines Yet</h3>
            <p className="text-sm text-gray-500 max-w-md">Upload a dataset in the Data Hub to see your data lineage flow appear here automatically.</p>
          </div>
        ) : (
          <div className="flex-1">
            {/* Group nodes by type for visual flow */}
            {['source', 'transform', 'dashboard'].map((type, groupIdx) => {
              const groupNodes = nodes.filter((n: any) => n.type === type || (type === 'dashboard' && n.type === 'dashboard'));
              if (groupNodes.length === 0) return null;

              const groupLabel = type === 'source' ? '📥 Data Sources' : type === 'transform' ? '⚙️ Processing Pipeline' : '📊 Outputs';

              return (
                <div key={type} className="mb-8">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">{groupLabel}</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {groupNodes.map((node: any, nodeIdx: number) => {
                      const statusColors: Record<string, string> = {
                        active: 'text-emerald-400',
                        success: 'text-emerald-400',
                        pending: 'text-amber-400',
                        error: 'text-red-400',
                      };

                      return (
                        <motion.div
                          key={node.id}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: groupIdx * 0.15 + nodeIdx * 0.05 }}
                          className={`p-5 rounded-2xl border relative ${
                            isDark ? 'bg-white/5 border-white/10 hover:bg-white/[0.08]' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                          } transition-all`}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              {iconMap[node.icon] || <Database className="w-8 h-8 text-gray-400 mb-2" />}
                            </div>
                            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded ${
                              isDark ? 'bg-white/10' : 'bg-gray-100'
                            } ${statusColors[node.status] || 'text-gray-400'}`}>
                              ● {node.status}
                            </span>
                          </div>

                          <h5 className="font-bold text-sm mb-1" style={{ color: isDark ? '#f8fafc' : '#0f172a' }}>
                            {node.label}
                          </h5>
                          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-3">{node.type}</p>

                          {node.metadata && (
                            <div className="space-y-1.5">
                              {Object.entries(node.metadata).map(([key, value]) => (
                                <div key={key} className="flex justify-between text-xs">
                                  <span className="text-gray-500">{key}:</span>
                                  <span className="font-medium" style={{ color: isDark ? '#e2e8f0' : '#334155' }}>{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>

                  {/* Flow arrow between groups */}
                  {type !== 'dashboard' && groupNodes.length > 0 && (
                    <div className="flex justify-center my-4">
                      <div className="flex items-center gap-2 text-indigo-400">
                        <div className="w-px h-8 bg-indigo-500/30"></div>
                        <span className="text-xs font-medium">▼ flows to</span>
                        <div className="w-px h-8 bg-indigo-500/30"></div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default DataLineage;
