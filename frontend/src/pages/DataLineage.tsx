import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserStore } from '@/store/userStore';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitBranch, Database, FileText, Cpu, Share2, ShieldAlert,
  Search, Check, Brain, Layout, RefreshCw, Download, 
  ArrowDown, Shield, Lock, Zap, HelpCircle, Network,
  CheckCircle2, AlertTriangle, Server, BarChart3, Table2,
  ChevronDown, ChevronRight, Activity, Columns, Clock,
  PieChart, Hash, Type
} from 'lucide-react';
import { api } from '@/services/api';

const iconMap: Record<string, React.ReactNode> = {
  database: <Database className="w-6 h-6 text-blue-500" />,
  cpu: <Cpu className="w-6 h-6 text-indigo-500" />,
  brain: <Brain className="w-6 h-6 text-amber-500" />,
  layout: <FileText className="w-6 h-6 text-emerald-500" />
};

const DataLineage: React.FC = () => {
  const navigate = useNavigate();
  const { isDark } = useUserStore();
  const [lineageData, setLineageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rescanning, setRescanning] = useState(false);
  const [expandedNode, setExpandedNode] = useState<string | null>(null);
  const [showAuditLog, setShowAuditLog] = useState(false);

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
  const auditLog = lineageData?.audit_log || [];
  const dataQuality = stats?.data_quality || {};

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
            <p className={`text-xs ${textM}`}>Data flow tracking, column-level lineage, quality metrics, and audit trail.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowAuditLog(!showAuditLog)}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl font-bold text-xs border transition-all ${
              showAuditLog 
                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' 
                : `${isDark ? 'border-white/10 text-slate-400 hover:bg-white/5' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`
            }`}>
            <Clock className="w-3.5 h-3.5" />
            Audit Log ({auditLog.length})
          </button>
          <button onClick={handleRescan}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl font-bold text-xs shadow-lg shadow-indigo-500/20 transition-all">
            <RefreshCw className={`w-3.5 h-3.5 ${rescanning ? 'animate-spin' : ''}`} />
            Re-scan Flows
          </button>
        </div>
      </div>

      {/* Compliance & Quality Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
        {[
          { label: 'Data Completeness', value: dataQuality.completeness ? `${dataQuality.completeness}%` : (stats.gdpr_status === 'Verified' ? '100%' : 'No Data'), icon: CheckCircle2,
            color: (dataQuality.completeness || 0) > 90 ? 'text-emerald-500' : (dataQuality.completeness || 0) > 70 ? 'text-amber-500' : 'text-red-500',
            bg: isDark ? 'bg-emerald-500/10' : 'bg-emerald-50' },
          { label: 'Active Pipelines', value: `${stats.total_pipelines || 0} Streams`, icon: GitBranch,
            color: isDark ? 'text-blue-400' : 'text-blue-600',
            bg: isDark ? 'bg-blue-500/10' : 'bg-blue-50' },
          { label: 'Data Nodes', value: `${stats.total_nodes || 0} Nodes`, icon: Database,
            color: isDark ? 'text-purple-400' : 'text-purple-600',
            bg: isDark ? 'bg-purple-500/10' : 'bg-purple-50' },
          { label: 'Total Columns', value: `${stats.total_columns || dataQuality.total_columns || 0}`, icon: Columns,
            color: isDark ? 'text-cyan-400' : 'text-cyan-600',
            bg: isDark ? 'bg-cyan-500/10' : 'bg-cyan-50' },
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

      {/* Data Quality Breakdown — only show if we have column data */}
      {dataQuality.total_columns > 0 && (
        <div className={`p-5 rounded-2xl border mb-6 ${bgCard} ${border}`}>
          <div className="flex items-center gap-2 mb-4">
            <Activity className={`w-4 h-4 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
            <h3 className={`text-sm font-bold ${textH}`}>Data Quality Profile</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Completeness Bar */}
            <div className={`p-4 rounded-xl border ${border} ${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs font-semibold ${textM}`}>Completeness</span>
                <span className={`text-sm font-bold ${
                  dataQuality.completeness >= 90 ? 'text-emerald-500' : dataQuality.completeness >= 70 ? 'text-amber-500' : 'text-red-500'
                }`}>{dataQuality.completeness}%</span>
              </div>
              <div className={`w-full h-2 rounded-full ${isDark ? 'bg-white/10' : 'bg-slate-200'}`}>
                <div 
                  className={`h-full rounded-full transition-all ${
                    dataQuality.completeness >= 90 ? 'bg-emerald-500' : dataQuality.completeness >= 70 ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(100, dataQuality.completeness)}%` }}
                />
              </div>
            </div>
            {/* Numeric vs Categorical */}
            <div className={`p-4 rounded-xl border ${border} ${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}`}>
              <span className={`text-xs font-semibold ${textM} block mb-2`}>Column Types</span>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <Hash className="w-3.5 h-3.5 text-blue-500" />
                  <span className={`text-xs ${textH}`}><strong>{dataQuality.numeric_columns}</strong> Numeric</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Type className="w-3.5 h-3.5 text-purple-500" />
                  <span className={`text-xs ${textH}`}><strong>{dataQuality.categorical_columns}</strong> Categorical</span>
                </div>
              </div>
            </div>
            {/* Total Stats */}
            <div className={`p-4 rounded-xl border ${border} ${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}`}>
              <span className={`text-xs font-semibold ${textM} block mb-2`}>Dataset Overview</span>
              <div className="flex items-center gap-4">
                <span className={`text-xs ${textH}`}><strong>{stats.total_files}</strong> files</span>
                <span className={`text-xs ${textH}`}><strong>{(stats.total_rows || 0).toLocaleString()}</strong> rows</span>
                <span className={`text-xs ${textH}`}><strong>{dataQuality.total_columns}</strong> columns</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Log Table — toggleable */}
      <AnimatePresence>
        {showAuditLog && auditLog.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            exit={{ opacity: 0, height: 0 }}
            className={`rounded-2xl border mb-6 overflow-hidden ${bgCard} ${border}`}
          >
            <div className={`px-5 py-3 flex items-center justify-between border-b ${border}`}>
              <div className="flex items-center gap-2">
                <Clock className={`w-4 h-4 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
                <span className={`text-sm font-bold ${textH}`}>Audit Trail</span>
              </div>
              <button onClick={handleExportAuditLog}
                className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center gap-1.5 transition-colors ${
                  isDark ? 'border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/10' : 'border-indigo-200 text-indigo-600 hover:bg-indigo-50'
                }`}>
                <Download className="w-3.5 h-3.5" /> Export CSV
              </button>
            </div>
            <div className="max-h-[300px] overflow-y-auto">
              <table className="w-full">
                <thead>
                  <tr className={`text-[10px] uppercase tracking-wider ${textS} border-b ${border}`}>
                    <th className="px-5 py-2 text-left font-bold">Timestamp</th>
                    <th className="px-3 py-2 text-left font-bold">Action</th>
                    <th className="px-3 py-2 text-left font-bold">Entity</th>
                    <th className="px-3 py-2 text-left font-bold">Details</th>
                    <th className="px-3 py-2 text-left font-bold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.map((entry: any, i: number) => (
                    <tr key={i} className={`border-b ${border} last:border-b-0 hover:${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'} transition-colors`}>
                      <td className={`px-5 py-2.5 text-xs ${textM} whitespace-nowrap`}>
                        {new Date(entry.timestamp).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                      </td>
                      <td className={`px-3 py-2.5 text-xs font-semibold ${textH}`}>{entry.action}</td>
                      <td className={`px-3 py-2.5 text-xs ${textM}`}>{entry.entity}</td>
                      <td className={`px-3 py-2.5 text-xs ${textS} max-w-[200px] truncate`}>{entry.details}</td>
                      <td className="px-3 py-2.5">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          entry.status === 'Success' 
                            ? (isDark ? 'bg-emerald-500/10 text-emerald-400' : 'bg-emerald-50 text-emerald-600')
                            : (isDark ? 'bg-red-500/10 text-red-400' : 'bg-red-50 text-red-600')
                        }`}>{entry.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Data Flow Diagram */}
      <div className={`p-6 rounded-2xl border min-h-[400px] flex flex-col ${bgCard} ${border}`}>
        <div className={`flex justify-between items-center border-b pb-4 mb-6 ${border}`}>
          <div className="flex items-center gap-2">
            <GitBranch className={`w-4 h-4 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`} />
            <span className={`text-sm font-bold ${textH}`}>Interactive Data Flow Diagram</span>
          </div>
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
            <button onClick={() => navigate('/datahub')}
              className="mt-4 px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl text-xs font-bold transition-all">
              Go to Data Hub
            </button>
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
                      const isExpanded = expandedNode === node.id;
                      const hasColumns = node.column_details && node.column_details.length > 0;
                      
                      return (
                        <motion.div key={node.id}
                          initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: groupIdx * 0.1 + nodeIdx * 0.04 }}
                          className={`rounded-xl border transition-all hover:border-indigo-500/30 ${bgCard} ${border} ${hasColumns ? 'cursor-pointer' : ''}`}
                          onClick={() => hasColumns && setExpandedNode(isExpanded ? null : node.id)}
                        >
                          <div className="p-4">
                            <div className="flex items-start justify-between mb-2.5">
                              {iconMap[node.icon] || <Database className={`w-6 h-6 ${textS}`} />}
                              <div className="flex items-center gap-1.5">
                                <span className={`text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded ${
                                  isDark ? 'bg-white/[0.05]' : 'bg-slate-100'
                                } ${statusColors[node.status] || textS}`}>
                                  ● {node.status}
                                </span>
                                {hasColumns && (
                                  isExpanded 
                                    ? <ChevronDown className={`w-3.5 h-3.5 ${textS}`} />
                                    : <ChevronRight className={`w-3.5 h-3.5 ${textS}`} />
                                )}
                              </div>
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
                          </div>

                          {/* Column-Level Lineage Details (expandable) */}
                          <AnimatePresence>
                            {isExpanded && hasColumns && (
                              <motion.div 
                                initial={{ height: 0, opacity: 0 }} 
                                animate={{ height: 'auto', opacity: 1 }} 
                                exit={{ height: 0, opacity: 0 }}
                                className={`border-t ${border} overflow-hidden`}
                              >
                                <div className="px-4 py-3">
                                  <div className="flex items-center gap-1.5 mb-2">
                                    <Table2 className={`w-3.5 h-3.5 ${isDark ? 'text-cyan-400' : 'text-cyan-600'}`} />
                                    <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>
                                      Column Details ({node.column_details.length})
                                    </span>
                                  </div>
                                  <div className="max-h-[200px] overflow-y-auto space-y-1">
                                    {node.column_details.map((col: any, ci: number) => (
                                      <div key={ci} className={`flex items-center justify-between text-[11px] px-2 py-1.5 rounded-lg ${
                                        isDark ? 'bg-white/[0.02] hover:bg-white/[0.04]' : 'bg-slate-50 hover:bg-slate-100'
                                      } transition-colors`}>
                                        <div className="flex items-center gap-2 flex-1 min-w-0">
                                          {col.type.includes('int') || col.type.includes('float') 
                                            ? <Hash className="w-3 h-3 text-blue-500 shrink-0" />
                                            : <Type className="w-3 h-3 text-purple-500 shrink-0" />
                                          }
                                          <span className={`font-semibold truncate ${textH}`}>{col.name}</span>
                                        </div>
                                        <div className="flex items-center gap-3 shrink-0">
                                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${isDark ? 'bg-white/[0.05]' : 'bg-slate-200'} ${textS}`}>
                                            {col.type}
                                          </span>
                                          <span className={`text-[10px] ${col.null_pct > 10 ? 'text-amber-500' : col.null_pct > 0 ? 'text-slate-400' : 'text-emerald-500'}`}>
                                            {col.null_pct}% null
                                          </span>
                                          <span className={`text-[10px] ${textS}`}>
                                            {col.unique} unique
                                          </span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
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
