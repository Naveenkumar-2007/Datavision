import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Boxes, Database, Play, Settings as SettingsIcon,
  PieChart, Info, Download, RefreshCw, ChevronDown,
  AlertCircle, CheckCircle, HelpCircle, Brain, Code2,
  BarChart3, FileText
} from 'lucide-react';
import { api } from '@/services/api';
import { getUserIdSync } from '@/utils/userId';

interface ClusterResult {
  success: boolean;
  algorithm: string;
  n_clusters: number;
  n_samples?: number;
  n_features?: number;
  silhouette_score: number;
  calinski_harabasz_score?: number;
  davies_bouldin_score?: number;
  cluster_distribution: Record<string, number>;
  charts: Record<string, string>;
  insights: string[];
  pca_variance_explained?: number;
  reliability_score?: number;
  cleaned_file?: string;
  model_pkl_file?: string;
  model_id?: string;
  k_scores?: Record<number, number>;
}

interface FileInfo {
  id: string;
  name: string;
  filename: string;
  rows?: number;
  columns?: number;
}

const ALGORITHMS = [
  { 
    id: 'auto', 
    name: '🚀 Auto (Smart Selection)', 
    description: 'Automatically selects the best algorithm for your data',
    requiresClusters: false,
    speed: 'Fast'
  },
  { 
    id: 'kmeans', 
    name: 'K-Means', 
    description: 'Best for spherical clusters of similar size',
    requiresClusters: true,
    speed: 'Fast'
  },
  { 
    id: 'dbscan', 
    name: 'DBSCAN', 
    description: 'Detects outliers, finds arbitrary shaped clusters',
    requiresClusters: false,
    speed: 'Medium'
  },
  { 
    id: 'hierarchical', 
    name: 'Hierarchical', 
    description: 'Shows cluster relationships (dendrogram)',
    requiresClusters: true,
    speed: 'Slow'
  },
  { 
    id: 'gmm', 
    name: 'Gaussian Mixture', 
    description: 'Soft clustering with probability assignments',
    requiresClusters: true,
    speed: 'Medium'
  },
  { 
    id: 'spectral', 
    name: 'Spectral', 
    description: 'Complex non-convex cluster structures',
    requiresClusters: true,
    speed: 'Slow'
  },
];

export default function Clustering() {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [algorithm, setAlgorithm] = useState<string>('auto');
  const [nClusters, setNClusters] = useState<number | null>(null);
  const [autoDetect, setAutoDetect] = useState<boolean>(true);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<ClusterResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'data'>('overview');

  // Load user files on mount - DO NOT auto-load results
  // Results should ONLY show after user clicks "Run Clustering"
  useEffect(() => {
    loadFiles();
    // Removed loadSavedClusteringModel() - results show only after user action
  }, []);

  const loadSavedClusteringModel = async () => {
    try {
      const userId = getUserIdSync();
      
      // First try to load from backend (persisted model)
      try {
        const response = await api.get(`/api/v1/ml/clustering/models/${userId}/active`);
        if (response.data?.success && response.data?.has_model) {
          console.log('✅ Loaded clustering model from backend');
          // We have a saved model - try to load full result from localStorage
          const savedResult = localStorage.getItem(`clusteringResult_${userId}`);
          if (savedResult) {
            setResult(JSON.parse(savedResult));
            return;
          }
        }
      } catch (backendErr) {
        console.log('No saved clustering model in backend, checking localStorage...');
      }
      
      // Fallback to localStorage
      const savedResult = localStorage.getItem(`clusteringResult_${userId}`);
      if (savedResult) {
        try {
          setResult(JSON.parse(savedResult));
        } catch (e) {
          console.error('Failed to parse saved clustering result:', e);
        }
      }
    } catch (e) {
      console.error('Failed to load saved clustering model:', e);
    }
  };

  const loadFiles = async () => {
    try {
      setIsLoadingFiles(true);
      const userId = getUserIdSync();
      const response = await api.get(`/api/v1/files/user/${userId}`);
      const fileList = response.data?.files || response.data || [];
      setFiles(fileList);
    } catch (err) {
      console.error('Failed to load files:', err);
      setError('Failed to load your files. Please try again.');
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const runClustering = async () => {
    if (!selectedFile) {
      setError('Please select a data file first.');
      return;
    }

    setIsRunning(true);
    setError(null);
    setResult(null);

    try {
      const userId = getUserIdSync();
      const response = await api.post('/api/v1/ml/clustering', {
        file_id: selectedFile,
        user_id: userId,
        algorithm,
        n_clusters: autoDetect ? null : nClusters,
      });

      if (response.data?.success) {
        setResult(response.data);
        // Save to localStorage for persistence (model is also saved to backend)
        localStorage.setItem(`clusteringResult_${userId}`, JSON.stringify(response.data));
        console.log('✅ Clustering complete - model saved to backend and localStorage');
      } else {
        throw new Error(response.data?.error || 'Clustering analysis failed');
      }
    } catch (err: any) {
      console.error('Clustering failed:', err);
      setError(err.response?.data?.detail || err.message || 'Clustering analysis failed. Please try again.');
    } finally {
      setIsRunning(false);
    }
  };

  const selectedAlgo = ALGORITHMS.find(a => a.id === algorithm);

  const getSilhouetteColor = (score: number) => {
    if (score >= 0.7) return 'text-green-500';
    if (score >= 0.5) return 'text-blue-500';
    if (score >= 0.25) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getSilhouetteLabel = (score: number) => {
    if (score >= 0.7) return 'Excellent';
    if (score >= 0.5) return 'Good';
    if (score >= 0.25) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 mb-8"
        >
          <div className="p-3 bg-purple-500/10 rounded-xl">
            <Boxes className="w-8 h-8 text-purple-500" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Clustering Analysis
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Discover natural groups and patterns in your data using unsupervised learning
            </p>
          </div>
        </motion.div>

        {/* Configuration Panel */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 mb-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-white">
            <SettingsIcon className="w-5 h-5 text-gray-500" />
            Configuration
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* File Selection */}
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                <Database className="w-4 h-4 inline mr-1" />
                Select Data
              </label>
              {isLoadingFiles ? (
                <div className="w-full p-3 border rounded-lg bg-gray-50 dark:bg-gray-700 animate-pulse">
                  <span className="text-gray-400">Loading files...</span>
                </div>
              ) : (
                <div className="relative">
                  <select
                    value={selectedFile}
                    onChange={(e) => setSelectedFile(e.target.value)}
                    className="w-full p-3 border rounded-lg dark:bg-gray-700 dark:border-gray-600 
                             text-gray-900 dark:text-white appearance-none cursor-pointer
                             focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value="">Choose a file...</option>
                    {files.map((file) => (
                      <option key={file.id} value={file.id}>
                        {file.filename || file.name}
                        {file.rows ? ` (${file.rows} rows)` : ''}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                </div>
              )}
              {files.length === 0 && !isLoadingFiles && (
                <p className="text-xs text-gray-500 mt-1">
                  No files found. Upload data in Data Hub first.
                </p>
              )}
            </div>

            {/* Algorithm Selection */}
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                <PieChart className="w-4 h-4 inline mr-1" />
                Algorithm
              </label>
              <div className="relative">
                <select
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full p-3 border rounded-lg dark:bg-gray-700 dark:border-gray-600 
                           text-gray-900 dark:text-white appearance-none cursor-pointer
                           focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  {ALGORITHMS.map((algo) => (
                    <option key={algo.id} value={algo.id}>
                      {algo.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {selectedAlgo?.description}
              </p>
              <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                Speed: {selectedAlgo?.speed}
              </span>
            </div>

            {/* Number of Clusters */}
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                <HelpCircle className="w-4 h-4 inline mr-1" />
                Number of Clusters
              </label>
              
              {/* Auto-detect toggle */}
              <label className="flex items-center gap-2 mb-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoDetect}
                  onChange={(e) => setAutoDetect(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-purple-600 
                           focus:ring-purple-500 dark:border-gray-600"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Auto-detect optimal clusters
                </span>
              </label>

              {!autoDetect && selectedAlgo?.requiresClusters && (
                <input
                  type="number"
                  value={nClusters || ''}
                  onChange={(e) => setNClusters(e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="e.g., 3"
                  min={2}
                  max={20}
                  className="w-full p-3 border rounded-lg dark:bg-gray-700 dark:border-gray-600
                           text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              )}

              {!selectedAlgo?.requiresClusters && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  DBSCAN automatically determines cluster count
                </p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 
                       rounded-lg flex items-center gap-2 text-red-700 dark:text-red-400"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Run Button */}
          <button
            onClick={runClustering}
            disabled={!selectedFile || isRunning}
            className="mt-6 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium
                     hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-2 transition-colors"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Analyzing Clusters...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Run Clustering
              </>
            )}
          </button>
        </motion.div>

        {/* Results */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Tab Navigation */}
            <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-4">
              <button
                onClick={() => setActiveTab('overview')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'overview'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                Overview
              </button>
              <button
                onClick={() => setActiveTab('charts')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'charts'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <PieChart className="w-4 h-4" />
                Charts ({Object.keys(result.charts || {}).length})
              </button>
              <button
                onClick={() => setActiveTab('data')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'data'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <Database className="w-4 h-4" />
                Data & Model
              </button>
            </div>

            {/* ============================================= */}
            {/* OVERVIEW TAB */}
            {/* ============================================= */}
            {activeTab === 'overview' && (
              <>
                {/* Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">Clusters Found</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {result.n_clusters}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">Silhouette Score</p>
                    <p className={`text-3xl font-bold ${getSilhouetteColor(result.silhouette_score)}`}>
                      {result.silhouette_score.toFixed(3)}
                    </p>
                    <span className={`text-xs ${getSilhouetteColor(result.silhouette_score)}`}>
                      {getSilhouetteLabel(result.silhouette_score)}
                    </span>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">Algorithm</p>
                    <p className="text-xl font-bold text-blue-600">
                      {ALGORITHMS.find(a => a.id === result.algorithm)?.name || result.algorithm}
                    </p>
                  </div>
                  {result.pca_variance_explained !== undefined && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">PCA Variance</p>
                      <p className="text-3xl font-bold text-green-600">
                        {(result.pca_variance_explained * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                </div>

                {/* Additional Metrics */}
                {(result.calinski_harabasz_score || result.davies_bouldin_score || result.reliability_score) && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {result.calinski_harabasz_score !== undefined && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                        <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">Calinski-Harabasz</p>
                        <p className="text-2xl font-bold text-cyan-600">{result.calinski_harabasz_score.toFixed(1)}</p>
                        <p className="text-xs text-gray-500">Higher is better</p>
                      </div>
                    )}
                    {result.davies_bouldin_score !== undefined && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                        <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">Davies-Bouldin</p>
                        <p className="text-2xl font-bold text-amber-600">{result.davies_bouldin_score.toFixed(3)}</p>
                        <p className="text-xs text-gray-500">Lower is better</p>
                      </div>
                    )}
                    {result.reliability_score !== undefined && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                        <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">Reliability Score</p>
                        <p className="text-2xl font-bold text-emerald-600">{result.reliability_score}%</p>
                        <p className="text-xs text-gray-500">Production confidence</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Main Scatter Plot */}
                {result.charts?.cluster_scatter && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold flex items-center gap-2 text-gray-900 dark:text-white">
                        <PieChart className="w-5 h-5 text-purple-500" />
                        🔮 Cluster Scatter (PCA 2D)
                      </h3>
                      <button
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = result.charts.cluster_scatter;
                          link.download = 'cluster_scatter.png';
                          link.click();
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>
                    <div className="flex justify-center">
                      <img src={result.charts.cluster_scatter} alt="Cluster scatter" className="max-w-full max-h-[500px] rounded-lg" />
                    </div>
                  </div>
                )}

                {/* Cluster Distribution */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">
                    Cluster Distribution
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {Object.entries(result.cluster_distribution).map(([cluster, count]) => {
                      const total = Object.values(result.cluster_distribution).reduce((a, b) => a + b, 0);
                      const percentage = ((count / total) * 100).toFixed(1);
                      return (
                        <div key={cluster} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-center">
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">{cluster}</p>
                          <p className="text-xs text-purple-500 mt-1">{percentage}%</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Insights */}
                {result.insights && result.insights.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-white">
                      <Info className="w-5 h-5 text-blue-500" />
                      Insights
                    </h3>
                    <ul className="space-y-3">
                      {result.insights.map((insight, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                          <span>{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}

            {/* ============================================= */}
            {/* CHARTS TAB */}
            {/* ============================================= */}
            {activeTab === 'charts' && result.charts && Object.keys(result.charts).length > 0 && (
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  📊 Visualizations ({Object.keys(result.charts).length} Charts)
                </h3>
                
                {/* Primary Visualization - Cluster Scatter */}
                {result.charts.cluster_scatter && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold flex items-center gap-2 text-gray-900 dark:text-white">
                        <PieChart className="w-5 h-5 text-purple-500" />
                        🔮 Cluster Scatter (PCA 2D)
                      </h3>
                      <button 
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = result.charts.cluster_scatter;
                          link.download = 'cluster_scatter.png';
                          link.click();
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 
                                 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600
                                 text-gray-700 dark:text-gray-300 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>
                    <div className="flex justify-center">
                      <img src={result.charts.cluster_scatter} alt="Cluster scatter" className="max-w-full max-h-[500px] rounded-lg" />
                    </div>
                  </div>
                )}

                {/* 3D Visualization if available */}
                {result.charts.cluster_3d && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-gray-900 dark:text-white">🌐 3D Cluster Visualization</h3>
                      <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.cluster_3d; l.download = 'cluster_3d.png'; l.click(); }}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                        <Download className="w-4 h-4" /> Download
                      </button>
                    </div>
                    <div className="flex justify-center">
                      <img src={result.charts.cluster_3d} alt="3D Clusters" className="max-w-full max-h-[500px] rounded-lg" />
                    </div>
                  </div>
                )}

                {/* Grid Layout for Secondary Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  
                  {/* Elbow Method */}
                  {result.charts.elbow_method && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📈 Elbow Method</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.elbow_method; l.download = 'elbow_method.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.elbow_method} alt="Elbow Method" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Silhouette Plot */}
                  {result.charts.silhouette_plot && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📊 Silhouette Analysis</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.silhouette_plot; l.download = 'silhouette.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.silhouette_plot} alt="Silhouette" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* PCA Variance */}
                  {result.charts.pca_variance && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📊 PCA Explained Variance</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.pca_variance; l.download = 'pca_variance.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.pca_variance} alt="PCA Variance" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Cluster Heatmap */}
                  {result.charts.cluster_heatmap && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🔥 Cluster Profile Heatmap</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.cluster_heatmap; l.download = 'cluster_heatmap.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.cluster_heatmap} alt="Cluster Heatmap" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Dendrogram (Hierarchical) */}
                  {result.charts.dendrogram && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 lg:col-span-2">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🌳 Hierarchical Dendrogram</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.dendrogram; l.download = 'dendrogram.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.dendrogram} alt="Dendrogram" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* GMM BIC/AIC Chart */}
                  {result.charts.gmm_bic_aic && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📊 GMM BIC/AIC Scores</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.gmm_bic_aic; l.download = 'gmm_bic_aic.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.gmm_bic_aic} alt="GMM BIC/AIC" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* DBSCAN K-Distance Chart */}
                  {result.charts.dbscan_kdist && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📈 DBSCAN K-Distance</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.dbscan_kdist; l.download = 'dbscan_kdist.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.dbscan_kdist} alt="DBSCAN K-Distance" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Spectral Affinity Matrix */}
                  {result.charts.spectral_affinity && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🔗 Spectral Affinity</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.spectral_affinity; l.download = 'spectral_affinity.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.spectral_affinity} alt="Spectral Affinity" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* t-SNE */}
                  {result.charts.tsne && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🔬 t-SNE Visualization</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.tsne; l.download = 'tsne.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.tsne} alt="t-SNE" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* UMAP */}
                  {result.charts.umap && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🗺️ UMAP Visualization</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.umap; l.download = 'umap.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.umap} alt="UMAP" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Pairplot */}
                  {result.charts.pairplot && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 lg:col-span-2">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🔍 Feature Pairplot</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.pairplot; l.download = 'pairplot.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.pairplot} alt="Pairplot" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Boxplots */}
                  {result.charts.boxplots && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 lg:col-span-2">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📦 Feature Boxplots by Cluster</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.boxplots; l.download = 'boxplots.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.boxplots} alt="Boxplots" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Violin Plots */}
                  {result.charts.violin_plots && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 lg:col-span-2">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🎻 Violin Plots by Cluster</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.violin_plots; l.download = 'violin_plots.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.violin_plots} alt="Violin Plots" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Correlation Heatmap */}
                  {result.charts.correlation_heatmap && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🔗 Correlation Heatmap</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.correlation_heatmap; l.download = 'correlation_heatmap.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.correlation_heatmap} alt="Correlation" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Radar Chart */}
                  {result.charts.radar_chart && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">🎯 Radar Chart Comparison</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.radar_chart; l.download = 'radar_chart.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.radar_chart} alt="Radar Chart" className="w-full rounded-lg" />
                    </div>
                  )}

                  {/* Distribution Bar */}
                  {result.charts.cluster_distribution && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold text-gray-900 dark:text-white">📊 Cluster Size Distribution</h4>
                        <button onClick={() => { const l = document.createElement('a'); l.href = result.charts.cluster_distribution; l.download = 'distribution.png'; l.click(); }}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300">
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                      <img src={result.charts.cluster_distribution} alt="Distribution" className="w-full rounded-lg" />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ============================================= */}
            {/* DATA TAB - Download PKL Model & Cleaned Data */}
            {/* ============================================= */}
            {activeTab === 'data' && (
              <div className="text-center py-8">
                <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="max-w-2xl mx-auto">
                  <div className="w-20 h-20 mx-auto bg-purple-500/20 rounded-full flex items-center justify-center mb-6">
                    <Database className="w-10 h-10 text-purple-500" />
                  </div>
                  <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
                    Production Assets
                  </h2>
                  <p className="mb-8 leading-relaxed text-gray-600 dark:text-gray-400">
                    Download trained clustering model and cleaned dataset with cluster assignments for deployment in production environments.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Trained Model Download */}
                    <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="w-14 h-14 mx-auto bg-purple-500/20 rounded-full flex items-center justify-center mb-4">
                        <Brain className="w-7 h-7 text-purple-500" />
                      </div>
                      <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                        Clustering Model
                      </h3>
                      <p className="text-sm mb-4 text-gray-600 dark:text-gray-400">
                        Download the trained clustering model (.pkl) with scaler and centroids for new predictions.
                      </p>
                      <a
                        href={`/api/v1/ml/clustering/download-model/${getUserIdSync()}`}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-xl font-semibold transition-all hover:scale-105"
                      >
                        <Download className="w-5 h-5" />
                        Download Model (.pkl)
                      </a>
                      <p className="text-xs mt-3 flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
                        <CheckCircle className="w-3 h-3 text-purple-400" />
                        {result.algorithm?.toUpperCase() || 'Clustering'} Model
                      </p>
                    </div>

                    {/* Cleaned Dataset Download */}
                    <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="w-14 h-14 mx-auto bg-emerald-500/20 rounded-full flex items-center justify-center mb-4">
                        <FileText className="w-7 h-7 text-emerald-500" />
                      </div>
                      <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                        Clustered Dataset
                      </h3>
                      <p className="text-sm mb-4 text-gray-600 dark:text-gray-400">
                        Original data with Cluster assignments, Cluster names, and PCA coordinates.
                      </p>
                      <a
                        href={`/api/v1/ml/clustering/download-data/${getUserIdSync()}`}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold transition-all hover:scale-105"
                      >
                        <Download className="w-5 h-5" />
                        Download CSV
                      </a>
                      <p className="text-xs mt-3 flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
                        <CheckCircle className="w-3 h-3 text-emerald-400" />
                        {result.n_clusters} Cluster Assignments
                      </p>
                    </div>
                  </div>

                  {/* Usage Instructions */}
                  <div className="mt-8 p-4 rounded-xl text-left bg-gray-50 dark:bg-gray-800/50">
                    <h4 className="font-semibold mb-2 flex items-center gap-2 text-gray-900 dark:text-white">
                      <Code2 className="w-4 h-4" />
                      Usage Example
                    </h4>
                    <pre className="text-xs p-3 rounded-lg overflow-x-auto bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300">
{`import pickle
import pandas as pd

# Load the trained clustering model
with open('clustering_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

# Access components
scaler = model_data['scaler']
centroids = model_data['centroids_scaled']
feature_cols = model_data['feature_columns']

# Predict cluster for new data
new_data = pd.read_csv('new_data.csv')
X_new = scaler.transform(new_data[feature_cols])

# Find nearest centroid
import numpy as np
distances = np.linalg.norm(X_new[:, np.newaxis] - centroids, axis=2)
predictions = np.argmin(distances, axis=1)`}
                    </pre>
                  </div>

                  {/* Data Summary */}
                  <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
                    <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
                      <p className="text-gray-500 dark:text-gray-400">Samples</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{result.n_samples || '—'}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
                      <p className="text-gray-500 dark:text-gray-400">Features</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{result.n_features || '—'}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
                      <p className="text-gray-500 dark:text-gray-400">Clusters</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{result.n_clusters}</p>
                    </div>
                  </div>
                </motion.div>
              </div>
            )}
          </motion.div>
        )}

        {/* Empty State */}
        {!result && !isRunning && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center py-16"
          >
            <Boxes className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
              Ready to Discover Patterns
            </h3>
            <p className="text-gray-500 dark:text-gray-500 max-w-md mx-auto">
              Select a data file and run clustering to automatically find natural groups 
              and segments in your data. Great for customer segmentation, product grouping, and more.
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
