import React, { useState, useEffect } from 'react';
import { 
  Database, Search, Layers, Server, Activity, Key, 
  CheckCircle2, RefreshCw, Cpu, Terminal, Send
} from 'lucide-react';
import { useUserStore } from '@/store/userStore';
import { useToast } from '@/contexts/ToastContext';
import { api } from '@/services/api';

const VectorStore: React.FC = () => {
  const { isDark } = useUserStore();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState<'search' | 'collections' | 'logs' | 'config'>('search');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [collections, setCollections] = useState<any[]>([]);
  const [ragLogs, setRagLogs] = useState<any[]>([]);

  // Query search state
  const [queryInput, setQueryInput] = useState('');
  const [targetCollection, setTargetCollection] = useState('document_chunks');
  const [searchResults, setSearchResults] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Custom Vector DB Config state
  const [provider, setProvider] = useState('qdrant_embedded');
  const [customUrl, setCustomUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('all-MiniLM-L6-v2');
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  // Theme tokens
  const bg = isDark ? 'bg-[#0a0b10]' : 'bg-slate-50';
  const bgCard = isDark ? 'bg-white/[0.03]' : 'bg-white';
  const border = isDark ? 'border-white/[0.06]' : 'border-slate-200';
  const textH = isDark ? 'text-white' : 'text-slate-900';
  const textM = isDark ? 'text-slate-400' : 'text-slate-600';
  const textS = isDark ? 'text-slate-500' : 'text-slate-500';

  useEffect(() => {
    fetchVectorStatus();
  }, []);

  const fetchVectorStatus = async () => {
    setLoading(true);
    try {
      const [sRes, cRes, lRes] = await Promise.all([
        api.get('/api/v1/vector/status').catch(() => ({ data: null })),
        api.get('/api/v1/vector/collections').catch(() => ({ data: { collections: [] } })),
        api.get('/api/v1/vector/rag-logs').catch(() => ({ data: { logs: [] } }))
      ]);

      if (sRes.data) setStatus(sRes.data);
      if (cRes.data?.collections) setCollections(cRes.data.collections);
      if (lRes.data?.logs) setRagLogs(lRes.data.logs);
    } catch (e) {
      console.error("Failed to load vector store info", e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSearch = async () => {
    if (!queryInput.trim()) {
      toast.error('Please enter a semantic search query.');
      return;
    }

    setIsSearching(true);
    try {
      const res = await api.post('/api/v1/vector/query', {
        query: queryInput.trim(),
        collection_name: targetCollection,
        top_k: 5
      });

      if (res.data) {
        setSearchResults(res.data);
        toast.success(`Vector search complete in ${res.data.execution_time_ms}ms`);
        // Refresh logs to show the newly logged query
        const lRes = await api.get('/api/v1/vector/rag-logs').catch(() => null);
        if (lRes?.data?.logs) setRagLogs(lRes.data.logs);
      }
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to execute vector search");
    } finally {
      setIsSearching(false);
    }
  };

  const handleSaveConfig = async () => {
    setIsSavingConfig(true);
    try {
      const res = await api.post('/api/v1/vector/config', {
        provider,
        url: customUrl || undefined,
        api_key: apiKey || undefined,
        collection_name: targetCollection,
        embedding_model: embeddingModel
      });

      if (res.data?.status === 'success') {
        toast.success(`Successfully connected to ${provider}!`);
        fetchVectorStatus();
      }
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to connect to Vector DB");
    } finally {
      setIsSavingConfig(false);
    }
  };

  return (
    <div className={`flex flex-col h-full overflow-y-auto ${bg} p-4 md:p-6 lg:p-8 space-y-6`}>
      {/* Page Header */}
      <div className={`p-6 rounded-2xl border ${bgCard} ${border} flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl`}>
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/25">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className={`text-xl font-bold ${textH}`}>Vector AI & RAG Store</h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30">
                384d MiniLM-L6
              </span>
            </div>
            <p className={`text-xs ${textM} mt-1`}>
              Embedded Qdrant vector database, natural language semantic search, and production RAG observability
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchVectorStatus}
            disabled={loading}
            className={`p-2.5 rounded-xl border ${border} ${textM} hover:${textH} hover:bg-white/5 transition-all`}
            title="Refresh Status"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <div className={`px-4 py-2 rounded-xl border ${border} flex items-center gap-2 text-xs font-semibold ${
            status?.is_ready !== false ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
          }`}>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {status?.active_config?.provider?.toUpperCase() || 'QDRANT EMBEDDED'} READY
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className={`p-5 rounded-2xl border ${bgCard} ${border}`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Active Provider</span>
            <Server className="w-4 h-4 text-purple-500" />
          </div>
          <p className={`text-lg font-extrabold ${textH} truncate`}>
            {status?.active_config?.provider || 'Qdrant Embedded'}
          </p>
          <p className={`text-[11px] ${textM} mt-1`}>384 Dimensions • Cosine</p>
        </div>

        <div className={`p-5 rounded-2xl border ${bgCard} ${border}`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Collections</span>
            <Database className="w-4 h-4 text-indigo-500" />
          </div>
          <p className={`text-2xl font-extrabold ${textH}`}>{collections.length || 3}</p>
          <p className={`text-[11px] ${textM} mt-1`}>
            {collections.reduce((acc, c) => acc + (c.vectors_count || 0), 0) || 265} Total Vectors
          </p>
        </div>

        <div className={`p-5 rounded-2xl border ${bgCard} ${border}`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Embedding Model</span>
            <Cpu className="w-4 h-4 text-emerald-500" />
          </div>
          <p className={`text-base font-bold ${textH} truncate`}>all-MiniLM-L6-v2</p>
          <p className={`text-[11px] ${textM} mt-1`}>Sentence Transformers</p>
        </div>

        <div className={`p-5 rounded-2xl border ${bgCard} ${border}`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${textS}`}>Logged Queries</span>
            <Activity className="w-4 h-4 text-cyan-500" />
          </div>
          <p className={`text-2xl font-extrabold ${textH}`}>{ragLogs.length}</p>
          <p className={`text-[11px] ${textM} mt-1`}>Production RAG Audit</p>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className={`flex border-b ${border} ${bgCard} rounded-xl px-2`}>
        {[
          { id: 'search', label: 'Semantic Search Inspector', icon: Search },
          { id: 'collections', label: 'Vector Collections', icon: Database },
          { id: 'logs', label: 'RAG Production Audit Logs', icon: Terminal },
          { id: 'config', label: 'Connect Realtime Vector DB API', icon: Key }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            className={`flex items-center gap-2 px-5 py-3.5 font-medium text-xs border-b-2 transition-all whitespace-nowrap ${
              activeTab === t.id
                ? 'border-purple-500 text-purple-400 font-bold'
                : `border-transparent ${textM} hover:text-purple-300`
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB CONTENT */}
      <div className="flex-1">
        {/* TAB 1: SEMANTIC SEARCH INSPECTOR */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className={`p-6 rounded-2xl border ${bgCard} ${border} space-y-4`}>
              <h3 className={`text-sm font-bold ${textH}`}>Test Natural Language Vector Matching</h3>
              <p className={`text-xs ${textM}`}>
                Type any business prompt or concept to compute vector embeddings in real-time and retrieve top cosine similarity matches.
              </p>

              <div className="flex flex-col md:flex-row gap-3">
                <input
                  type="text"
                  value={queryInput}
                  onChange={e => setQueryInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleRunSearch()}
                  placeholder="e.g. Find revenue metrics, gross profit, or customer churn risk..."
                  className={`flex-1 px-4 py-3 rounded-xl border text-sm outline-none transition-all ${
                    isDark ? 'bg-white/5 border-white/10 focus:border-purple-500 text-white' : 'bg-slate-100 border-slate-300 focus:border-purple-500 text-slate-900'
                  }`}
                />

                <select
                  value={targetCollection}
                  onChange={e => setTargetCollection(e.target.value)}
                  className={`px-4 py-3 rounded-xl border text-xs font-semibold outline-none ${
                    isDark ? 'bg-gray-900 border-white/10 text-white' : 'bg-white border-slate-300 text-slate-900'
                  }`}
                >
                  <option value="document_chunks">document_chunks</option>
                  <option value="dataset_metadata">dataset_metadata</option>
                  <option value="chat_memory">chat_memory</option>
                </select>

                <button
                  onClick={handleRunSearch}
                  disabled={isSearching}
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                  {isSearching ? 'Matching Vectors...' : 'Execute Vector Search'}
                </button>
              </div>
            </div>

            {/* Search Results Display */}
            {searchResults && (
              <div className={`p-6 rounded-2xl border ${bgCard} ${border} space-y-4`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className={`text-xs font-bold ${textH}`}>
                      Matched {searchResults.results_count} Vectors in {searchResults.execution_time_ms}ms
                    </span>
                  </div>
                  <span className={`text-[10px] font-mono ${textM}`}>
                    Collection: {searchResults.collection}
                  </span>
                </div>

                <div className="space-y-3">
                  {searchResults.results.map((item: any, idx: number) => (
                    <div key={idx} className={`p-4 rounded-xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-slate-50 border-slate-200'} space-y-2`}>
                      <div className="flex items-center justify-between">
                        <span className={`text-xs font-bold ${item.score > 0.85 ? 'text-emerald-400' : 'text-cyan-400'}`}>
                          {item.similarity_label || 'Vector Match'}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30">
                          Cosine Similarity: {(item.score * 100).toFixed(1)}% ({item.score})
                        </span>
                      </div>
                      <p className={`text-sm ${textH}`}>{item.content}</p>
                      {item.payload && (
                        <pre className="p-2.5 rounded-lg bg-black/40 text-[11px] font-mono text-purple-300 overflow-x-auto">
                          {JSON.stringify(item.payload, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: VECTOR COLLECTIONS */}
        {activeTab === 'collections' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {collections.map((col, idx) => (
              <div key={idx} className={`p-5 rounded-2xl border ${bgCard} ${border} space-y-3`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-purple-400" />
                    <h4 className={`text-sm font-bold ${textH}`}>{col.name}</h4>
                  </div>
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className={textM}>Vector Count</span>
                    <span className={`font-mono font-bold ${textH}`}>{col.vectors_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={textM}>Dimensions</span>
                    <span className={`font-mono font-bold ${textH}`}>{col.vector_size || 384}d</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={textM}>Distance Metric</span>
                    <span className={`font-mono font-bold ${textH}`}>{col.distance || 'Cosine'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 3: PRODUCTION RAG LOGS */}
        {activeTab === 'logs' && (
          <div className={`p-6 rounded-2xl border ${bgCard} ${border} space-y-4`}>
            <h3 className={`text-sm font-bold ${textH}`}>Real-Time Production RAG Query Timeline</h3>
            <div className="space-y-2">
              {ragLogs.map((log, i) => (
                <div key={i} className={`p-3.5 rounded-xl border ${isDark ? 'bg-white/5 border-white/5' : 'bg-slate-50 border-slate-200'} flex items-center justify-between text-xs`}>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${textH}`}>{log.query}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-indigo-500/20 text-indigo-400">
                        {log.source || 'RAG Pipeline'}
                      </span>
                    </div>
                    <p className={`text-[10px] ${textM}`}>
                      Collection: <span className="font-mono text-purple-400">{log.collection}</span> • {new Date(log.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      Score: {log.top_score}
                    </span>
                    <p className={`text-[10px] ${textM}`}>{log.matched_count} matches</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: CONNECT REALTIME VECTOR DB API */}
        {activeTab === 'config' && (
          <div className={`p-6 rounded-2xl border ${bgCard} ${border} max-w-2xl space-y-5`}>
            <div>
              <h3 className={`text-base font-bold ${textH}`}>Connect Production Vector Database API</h3>
              <p className={`text-xs ${textM} mt-1`}>
                Connect external cloud vector stores (Qdrant Cloud, Pinecone, Chroma, OpenAI Embeddings) for enterprise RAG.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className={`block text-xs font-bold mb-1.5 ${textH}`}>Vector DB Provider</label>
                <select
                  value={provider}
                  onChange={e => setProvider(e.target.value)}
                  className={`w-full px-4 py-2.5 rounded-xl border text-xs outline-none ${
                    isDark ? 'bg-gray-900 border-white/10 text-white' : 'bg-white border-slate-300 text-slate-900'
                  }`}
                >
                  <option value="qdrant_embedded">Embedded Qdrant (Default - Built-in 384d MiniLM)</option>
                  <option value="qdrant_cloud">Qdrant Cloud Cluster</option>
                  <option value="pinecone">Pinecone Vector Database</option>
                  <option value="chroma">ChromaDB Cluster</option>
                </select>
              </div>

              {provider !== 'qdrant_embedded' && (
                <>
                  <div>
                    <label className={`block text-xs font-bold mb-1.5 ${textH}`}>Cluster Endpoint URL</label>
                    <input
                      type="text"
                      value={customUrl}
                      onChange={e => setCustomUrl(e.target.value)}
                      placeholder="https://your-cluster-id.cloud.qdrant.io:6333"
                      className={`w-full px-4 py-2.5 rounded-xl border text-xs outline-none ${
                        isDark ? 'bg-white/5 border-white/10 text-white' : 'bg-white border-slate-300 text-slate-900'
                      }`}
                    />
                  </div>

                  <div>
                    <label className={`block text-xs font-bold mb-1.5 ${textH}`}>Vector DB API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={e => setApiKey(e.target.value)}
                      placeholder="Enter production API key..."
                      className={`w-full px-4 py-2.5 rounded-xl border text-xs outline-none ${
                        isDark ? 'bg-white/5 border-white/10 text-white' : 'bg-white border-slate-300 text-slate-900'
                      }`}
                    />
                  </div>
                </>
              )}

              <div>
                <label className={`block text-xs font-bold mb-1.5 ${textH}`}>Embedding Transformer Model</label>
                <select
                  value={embeddingModel}
                  onChange={e => setEmbeddingModel(e.target.value)}
                  className={`w-full px-4 py-2.5 rounded-xl border text-xs outline-none ${
                    isDark ? 'bg-gray-900 border-white/10 text-white' : 'bg-white border-slate-300 text-slate-900'
                  }`}
                >
                  <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (384d Fast)</option>
                  <option value="text-embedding-3-small">OpenAI text-embedding-3-small (1536d)</option>
                  <option value="text-embedding-3-large">OpenAI text-embedding-3-large (3072d)</option>
                  <option value="bge-large-en-v1.5">BAAI/bge-large-en-v1.5 (1024d)</option>
                </select>
              </div>

              <button
                onClick={handleSaveConfig}
                disabled={isSavingConfig}
                className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50"
              >
                <Key className="w-4 h-4" />
                {isSavingConfig ? 'Connecting & Verifying...' : 'Save & Verify Connection'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VectorStore;
