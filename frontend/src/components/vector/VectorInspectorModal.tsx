import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, Search, Database, Cpu, Zap, CheckCircle2, AlertTriangle, 
  X, RefreshCw, Server, ArrowRight, Shield, Layers, Key, Check
} from 'lucide-react';
import { api } from '@/services/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const VectorInspectorModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'search' | 'collections' | 'rag_logs' | 'config'>('search');
  
  // State
  const [status, setStatus] = useState<any>(null);
  const [collections, setCollections] = useState<any[]>([]);
  const [ragLogs, setRagLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollection, setSelectedCollection] = useState('document_chunks');
  const [topK, setTopK] = useState(5);
  const [searchResults, setSearchResults] = useState<any>(null);
  const [searching, setSearching] = useState(false);

  // Config State
  const [provider, setProvider] = useState<'qdrant_embedded' | 'qdrant_cloud' | 'pinecone' | 'chroma'>('qdrant_cloud');
  const [qdrantUrl, setQdrantUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [collectionName, setCollectionName] = useState('dataset_metadata');
  const [testingConn, setTestingConn] = useState(false);
  const [connFeedback, setConnFeedback] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadVectorData();
    }
  }, [isOpen]);

  const loadVectorData = async () => {
    setLoading(true);
    try {
      const [statusRes, colsRes, logsRes] = await Promise.all([
        api.get('/api/v1/vector/status').catch(() => ({ data: null })),
        api.get('/api/v1/vector/collections').catch(() => ({ data: { collections: [] } })),
        api.get('/api/v1/vector/rag-logs').catch(() => ({ data: { logs: [] } }))
      ]);
      
      setStatus(statusRes.data);
      setCollections(colsRes.data?.collections || []);
      setRagLogs(logsRes.data?.logs || []);
    } catch (e) {
      console.error("Failed to load vector store info", e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.post('/api/v1/vector/query', {
        query: searchQuery,
        collection_name: selectedCollection,
        top_k: topK
      });
      setSearchResults(res.data);
    } catch (e: any) {
      setSearchResults({
        query: searchQuery,
        results_count: 0,
        results: [],
        error: e.response?.data?.detail || "Failed to execute vector search"
      });
    } finally {
      setSearching(false);
    }
  };

  const handleSaveConfig = async () => {
    setTestingConn(true);
    setConnFeedback(null);
    try {
      const res = await api.post('/api/v1/vector/config', {
        provider,
        url: qdrantUrl,
        api_key: apiKey,
        collection_name: collectionName
      });
      setConnFeedback({ msg: res.data.message || 'Connected successfully!', type: 'success' });
      loadVectorData();
    } catch (e: any) {
      setConnFeedback({ 
        msg: e.response?.data?.detail || 'Connection test failed. Check URL & API Key.', 
        type: 'error' 
      });
    } finally {
      setTestingConn(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="w-full max-w-5xl bg-[#0A0A12] border border-gray-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col h-[85vh]"
        >
          {/* Header */}
          <div className="px-6 py-5 border-b border-gray-800/80 bg-[#10101A] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 shadow-[0_0_20px_rgba(99,102,241,0.4)]">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white tracking-wide">Vector AI & RAG Store</h2>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    Qdrant + MiniLM-L6 (384d)
                  </span>
                </div>
                <p className="text-xs text-gray-400">Natural language search, semantic index, and custom Vector DB configuration</p>
              </div>
            </div>

            <button 
              onClick={onClose}
              className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-gray-800/60 bg-[#0C0C14] px-6 gap-2 pt-2">
            {[
              { id: 'search', label: 'Semantic Search Tester', icon: Search },
              { id: 'collections', label: 'Vector Collections', icon: Database },
              { id: 'rag_logs', label: 'RAG Activity Feed', icon: Zap },
              { id: 'config', label: 'Connect Custom Vector DB', icon: Server },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold rounded-t-xl transition-all border-b-2 ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 bg-[#07070D] space-y-6">
            
            {/* TAB 1: SEMANTIC SEARCH TESTER */}
            {activeTab === 'search' && (
              <div className="space-y-6">
                <div className="p-5 rounded-2xl bg-[#11111E] border border-gray-800/80 space-y-4">
                  <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <Search className="w-4 h-4 text-indigo-400" />
                    Test Natural Language Vector Matching
                  </h3>

                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="relative flex-1">
                      <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-gray-500" />
                      <input 
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleRunSearch()}
                        placeholder="Search by meaning: e.g. 'find revenue and profit growth columns'..."
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-black/40 border border-gray-800 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-500 transition-all"
                      />
                    </div>

                    <select
                      value={selectedCollection}
                      onChange={(e) => setSelectedCollection(e.target.value)}
                      className="px-3 py-2.5 rounded-xl bg-black/40 border border-gray-800 text-gray-300 text-xs focus:outline-none"
                    >
                      <option value="document_chunks">Document Chunks</option>
                      <option value="dataset_metadata">Dataset Metadata</option>
                      <option value="chat_memory">Chat Memory</option>
                    </select>

                    <button
                      onClick={handleRunSearch}
                      disabled={searching || !searchQuery.trim()}
                      className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-50 hover:opacity-90 transition-all"
                    >
                      {searching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                      Query Vectors
                    </button>
                  </div>

                  {/* Sample Query Pills */}
                  <div className="flex items-center gap-2 pt-1 flex-wrap">
                    <span className="text-[11px] text-gray-500">Quick prompts:</span>
                    {[
                      "find revenue & financial metrics",
                      "customer retention & churn rate",
                      "sales volume per region"
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => { setSearchQuery(q); }}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/20 transition-all"
                      >
                        "{q}"
                      </button>
                    ))}
                  </div>
                </div>

                {/* Search Results Display */}
                {searchResults && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>Found <strong className="text-white">{searchResults.results_count}</strong> matches for "{searchResults.query}"</span>
                      {searchResults.execution_time_ms && (
                        <span className="text-indigo-400 font-mono">⚡ {searchResults.execution_time_ms} ms</span>
                      )}
                    </div>

                    <div className="space-y-3">
                      {searchResults.results.map((res: any, idx: number) => (
                        <motion.div 
                          key={res.id || idx}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="p-4 rounded-2xl bg-[#10101B] border border-gray-800/80 hover:border-indigo-500/40 transition-all space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Similarity Score: {(res.score * 100).toFixed(1)}%
                            </span>
                            <span className="text-[11px] text-gray-500 font-mono">Point ID: {res.id}</span>
                          </div>

                          <p className="text-sm text-gray-200 leading-relaxed font-medium">{res.content}</p>

                          {res.payload && (
                            <div className="p-3 rounded-xl bg-black/40 border border-gray-800/60 font-mono text-[11px] text-gray-400 overflow-x-auto">
                              {JSON.stringify(res.payload, null, 2)}
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: COLLECTIONS EXPLORER */}
            {activeTab === 'collections' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {collections.map((col) => (
                    <div key={col.name} className="p-5 rounded-2xl bg-[#11111E] border border-gray-800/80 hover:border-indigo-500/30 transition-all space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
                          <Database className="w-5 h-5" />
                        </div>
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                      </div>

                      <div>
                        <h4 className="font-bold text-white text-base">{col.name}</h4>
                        <p className="text-xs text-gray-400 mt-1">Cosine Distance Vector Index</p>
                      </div>

                      <div className="pt-3 border-t border-gray-800/60 grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-500 text-[10px] uppercase font-semibold block">Vectors</span>
                          <span className="font-bold text-white text-sm">{col.vectors_count}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 text-[10px] uppercase font-semibold block">Dimensions</span>
                          <span className="font-bold text-indigo-400 text-sm">{col.vector_size}d</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: RAG ACTIVITY FEED */}
            {activeTab === 'rag_logs' && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-indigo-400" />
                  Real-time AI Analyst Vector Memory Telemetry
                </h3>

                <div className="space-y-2">
                  {ragLogs.map((log) => (
                    <div key={log.id} className="p-4 rounded-xl bg-[#10101A] border border-gray-800/60 flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white">"{log.query}"</span>
                          <span className="px-2 py-0.5 rounded text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            {log.source}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-500">Collection: {log.collection} • Matched {log.matched_count} points</p>
                      </div>

                      <div className="text-right">
                        <span className="text-xs font-bold text-emerald-400 font-mono">{(log.top_score * 100).toFixed(1)}% match</span>
                        <span className="text-[10px] text-gray-500 block">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 4: CUSTOM VECTOR DB CONFIG */}
            {activeTab === 'config' && (
              <div className="p-6 rounded-2xl bg-[#11111E] border border-gray-800/80 space-y-6 max-w-2xl mx-auto">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Server className="w-5 h-5 text-indigo-400" />
                    Connect Your Custom Vector Database
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">Connect your enterprise Qdrant Cloud or self-hosted instance to inspect vectors in real-time.</p>
                </div>

                {connFeedback && (
                  <div className={`p-4 rounded-xl border text-xs font-semibold flex items-center gap-3 ${
                    connFeedback.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'
                  }`}>
                    {connFeedback.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                    {connFeedback.msg}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300 block mb-2">Vector Provider</label>
                    <select
                      value={provider}
                      onChange={(e: any) => setProvider(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-gray-800 text-white text-xs focus:outline-none focus:border-indigo-500"
                    >
                      <option value="qdrant_cloud">Qdrant Cloud / Self-Hosted</option>
                      <option value="qdrant_embedded">Embedded Local Qdrant (Default)</option>
                      <option value="pinecone">Pinecone Vector Database</option>
                      <option value="chroma">ChromaDB Store</option>
                    </select>
                  </div>

                  {provider === 'qdrant_cloud' && (
                    <>
                      <div>
                        <label className="text-xs font-semibold text-gray-300 block mb-1">Qdrant Cloud URL</label>
                        <input
                          type="text"
                          value={qdrantUrl}
                          onChange={(e) => setQdrantUrl(e.target.value)}
                          placeholder="https://xyz.cloud.qdrant.io:6333"
                          className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-gray-800 text-white text-xs focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-300 block mb-1">API Key</label>
                        <input
                          type="password"
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="qdrant_api_key_..."
                          className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-gray-800 text-white text-xs focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-300 block mb-1">Target Collection Name</label>
                        <input
                          type="text"
                          value={collectionName}
                          onChange={(e) => setCollectionName(e.target.value)}
                          placeholder="dataset_metadata"
                          className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-gray-800 text-white text-xs focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </>
                  )}

                  <button
                    onClick={handleSaveConfig}
                    disabled={testingConn}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-50 hover:opacity-90 transition-all mt-4"
                  >
                    {testingConn ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                    Test Connection & Connect Vector DB
                  </button>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
