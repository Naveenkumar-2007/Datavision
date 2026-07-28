import React, { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { motion } from 'framer-motion';
import { 
  GitBranch, Database, FileText, Cpu, Share2, ShieldAlert,
  Search, Check, Brain, Layout, RefreshCw, Download, 
  ArrowDown, Shield, Lock, Zap, HelpCircle, Network,
  CheckCircle2, AlertTriangle, Server
} from 'lucide-react';
import { api } from '@/services/api';

import { VectorInspectorModal } from '@/components/vector/VectorInspectorModal';

const iconMap: Record<string, React.ReactNode> = {
  database: <Database className="w-6 h-6 text-blue-500" />,
  cpu: <Cpu className="w-6 h-6 text-indigo-500" />,
  brain: <Brain className="w-6 h-6 text-amber-500" />,
  layout: <FileText className="w-6 h-6 text-emerald-500" />
};

const DataLineage: React.FC = () => {
  const { isDark } = useUserStore();
  const [lineageData, setLineageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rescanning, setRescanning] = useState(false);
  const [isVectorModalOpen, setIsVectorModalOpen] = useState(false);

  // Theme classes
  const bgCard = isDark ? 'bg-white/[0.03]' : 'bg-white';
  const border = isDark ? 'border-white/[0.06]' : 'border-slate-200';
  const textH = isDark ? 'text-white' : 'text-slate-900';
  const textM = isDark ? 'text-slate-400' : 'text-slate-600';
  const textS = isDark ? 'text-slate-500' : 'text-slate-500';

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

  useEffect(() => { fetchData(); }, []);

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

  return (
    <div className={`p-4 md:p-6 lg:p-8 max-w-7xl mx-auto min-h-screen ${isDark ? 'bg-[#0a0b10]' : 'bg-slate-50'}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h2 className={`text-xl font-bold tracking-tight ${textH}`}>Data Lineage & Governance</h2>
            <p className={`text-xs ${textM}`}>Visual audit trails, data flow compliance, and semantic indexing.</p>
          </div>
        </div>
        <button onClick={handleRescan}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl font-bold text-xs shadow-lg shadow-indigo-500/20 transition-all">
          <RefreshCw className={`w-3.5 h-3.5 ${rescanning ? 'animate-spin' : ''}`} />
          Re-scan Flows
        </button>
      </div>

      {/* Compliance Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[
          { label: 'GDPR Compliance', value: stats.gdpr_status === 'Verified' ? '100% Verified' : 'No Data', icon: Shield,
            color: stats.gdpr_status === 'Verified' ? 'text-emerald-500' : textS,
            bg: stats.gdpr_status === 'Verified' ? (isDark ? 'bg-emerald-500/10' : 'bg-emerald-50') : (isDark ? 'bg-white/[0.02]' : 'bg-slate-50') },
          { label: 'Active Pipelines', value: `${stats.total_pipelines || 0} Streams`, icon: GitBranch,
            color: isDark ? 'text-blue-400' : 'text-blue-600',
            bg: isDark ? 'bg-blue-500/10' : 'bg-blue-50' },
          { label: 'Data Nodes', value: `${stats.total_nodes || 0} Nodes`, icon: Database,
            color: isDark ? 'text-purple-400' : 'text-purple-600',
            bg: isDark ? 'bg-purple-500/10' : 'bg-purple-50' },
          { label: 'Encryption', value: stats.encryption || 'AES-256', icon: Lock,
            color: isDark ? 'text-teal-400' : 'text-teal-600',
            bg: isDark ? 'bg-teal-500/10' : 'bg-teal-50' }
        ].map((stat, i) => (
          <motion.div key={i}
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
            className={`p-4 rounded-2xl border ${bgCard} ${border} transition-all hover:border-indigo-500/30`}>
            <div className="flex items-center justify-between mb-2">
              <div className={`p-1.5 rounded-lg ${stat.bg}`}>
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <span className={`text-[9px] font-bold uppercase tracking-wider ${textS}`}>{stat.label}</span>
            </div>
            <p className={`text-lg font-extrabold ${stat.color}`}>{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Semantic Search / RAG Explanation Card */}
      <div className={`p-5 rounded-2xl border mb-6 ${bgCard} ${border}`}>
        <div className="flex items-start gap-4">
          <div className={`p-2.5 rounded-xl shrink-0 ${isDark ? 'bg-amber-500/10' : 'bg-amber-50'}`}>
            <Brain className={`w-5 h-5 ${isDark ? 'text-amber-400' : 'text-amber-600'}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between gap-2 mb-1.5 flex-wrap">
              <div className="flex items-center gap-2">
                <h3 className={`text-sm font-bold ${textH}`}>Semantic Search & RAG (Qdrant + MiniLM-L6)</h3>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${isDark ? 'bg-amber-500/10 text-amber-400' : 'bg-amber-50 text-amber-600'} tracking-wider`}>
                  VECTOR AI
                </span>
              </div>
              <button 
                onClick={() => setIsVectorModalOpen(true)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm transition-all ${
                  isDark 
                    ? 'bg-gradient-to-r from-amber-500/20 to-indigo-500/20 text-amber-300 border border-amber-500/30 hover:border-amber-400' 
                    : 'bg-amber-500 text-white hover:bg-amber-600'
                }`}
              >
                <Server className="w-3.5 h-3.5" />
                Inspect Vector DB & Test Queries
              </button>
            </div>
            <p className={`text-xs leading-relaxed ${textM} mb-3`}>
              When you upload datasets, DataVision automatically creates <strong className={textH}>vector embeddings</strong> of 
              your column names, data descriptions, and metadata using the <strong className={textH}>MiniLM-L6 transformer</strong>. 
              These embeddings are stored in <strong className={textH}>Qdrant</strong> (a vector database) enabling:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { icon: Search, title: 'Natural Language Search', desc: 'Search datasets by meaning — "find revenue columns" matches total_sales, gross_income, etc.' },
                { icon: Brain, title: 'AI Analyst Memory', desc: 'The Gemini/GPT analyst uses RAG to recall relevant data context when answering your questions.' },
                { icon: Zap, title: 'Smart Column Matching', desc: 'AutoML and Dashboard generators use semantic search to intelligently map and correlate columns.' },
              ].map((feature, i) => (
                <div key={i} className={`p-3 rounded-xl border ${border} ${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}`}>
                  <feature.icon className={`w-4 h-4 mb-1.5 ${isDark ? 'text-amber-400' : 'text-amber-600'}`} />
                  <h4 className={`text-xs font-bold ${textH} mb-0.5`}>{feature.title}</h4>
                  <p className={`text-[10px] leading-relaxed ${textS}`}>{feature.desc}</p>
                </div>
              ))}
            </div>
            <div className={`mt-3 p-3 rounded-lg ${isDark ? 'bg-emerald-500/[0.06] border border-emerald-500/15' : 'bg-emerald-50 border border-emerald-200'}`}>
              <p className={`text-[11px] ${textM} flex items-center gap-2`}>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                <span><strong className={textH}>Auto-connected</strong> — Qdrant indexing runs automatically when you upload data in DataHub. No manual setup required.</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <VectorInspectorModal isOpen={isVectorModalOpen} onClose={() => setIsVectorModalOpen(false)} />

      {/* Data Flow Diagram */}
      <div className={`p-6 rounded-2xl border min-h-[400px] flex flex-col ${bgCard} ${border}`}>
        <div className={`flex justify-between items-center border-b pb-4 mb-6 ${border}`}>
          <div className="flex items-center gap-2">
            <GitBranch className={`w-4 h-4 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
            <span className={`text-sm font-bold ${textH}`}>Interactive Data Flow Diagram</span>
          </div>
          <button onClick={handleExportAuditLog}
            className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center gap-1.5 transition-colors ${
              isDark ? 'border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10' : 'border-indigo-200 text-indigo-600 hover:bg-indigo-50'
            }`}>
            <Download className="w-3.5 h-3.5" /> Export Audit Log
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex justify-center items-center">
            <RefreshCw className="w-6 h-6 text-indigo-500 animate-spin" />
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex-1 flex flex-col justify-center items-center text-center">
            <Database className={`w-10 h-10 mb-3 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
            <h3 className={`text-base font-bold mb-1 ${textH}`}>No Data Pipelines Yet</h3>
            <p className={`text-xs max-w-md ${textS}`}>
              Upload a dataset in the Data Hub to see your data lineage flow appear here automatically.
            </p>
          </div>
        ) : (
          <div className="flex-1 space-y-2">
            {['source', 'transform', 'dashboard'].map((type, groupIdx) => {
              const groupNodes = nodes.filter((n: any) => n.type === type || (type === 'dashboard' && n.type === 'dashboard'));
              if (groupNodes.length === 0) return null;

              const groupLabel = type === 'source' ? '📥 Data Sources' : type === 'transform' ? '⚙️ Processing Pipeline' : '📊 Outputs';

              return (
                <div key={type}>
                  <h4 className={`text-[10px] font-bold uppercase tracking-wider mb-3 ${textS}`}>{groupLabel}</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {groupNodes.map((node: any, nodeIdx: number) => {
                      const statusColors: Record<string, string> = {
                        active: 'text-emerald-500', success: 'text-emerald-500',
                        pending: 'text-amber-500', error: 'text-red-500',
                      };
                      return (
                        <motion.div key={node.id}
                          initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: groupIdx * 0.1 + nodeIdx * 0.04 }}
                          className={`p-4 rounded-xl border transition-all hover:border-indigo-500/30 ${bgCard} ${border}`}>
                          <div className="flex items-start justify-between mb-2.5">
                            {iconMap[node.icon] || <Database className={`w-6 h-6 ${textS}`} />}
                            <span className={`text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded ${
                              isDark ? 'bg-white/[0.05]' : 'bg-slate-100'
                            } ${statusColors[node.status] || textS}`}>
                              ● {node.status}
                            </span>
                          </div>
                          <h5 className={`font-bold text-sm mb-0.5 ${textH}`}>{node.label}</h5>
                          <p className={`text-[10px] uppercase tracking-wider mb-2.5 ${textS}`}>{node.type}</p>
                          {node.metadata && (
                            <div className="space-y-1">
                              {Object.entries(node.metadata).map(([key, value]) => (
                                <div key={key} className="flex justify-between text-[11px]">
                                  <span className={textS}>{key}:</span>
                                  <span className={`font-medium ${textM}`}>{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>

                  {/* Flow arrow */}
                  {type !== 'dashboard' && groupNodes.length > 0 && (
                    <div className="flex justify-center my-4">
                      <div className={`flex flex-col items-center gap-1 ${isDark ? 'text-indigo-400' : 'text-indigo-500'}`}>
                        <div className={`w-px h-6 ${isDark ? 'bg-indigo-500/30' : 'bg-indigo-300'}`} />
                        <ArrowDown className="w-4 h-4" />
                        <div className={`w-px h-6 ${isDark ? 'bg-indigo-500/30' : 'bg-indigo-300'}`} />
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
