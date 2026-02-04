import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Boxes, Database, Play, Settings as SettingsIcon,
  PieChart, Info, Download, RefreshCw, ChevronDown,
  AlertCircle, CheckCircle, HelpCircle
} from 'lucide-react';
import { api } from '@/services/api';
import { getUserIdSync } from '@/utils/userId';

interface ClusterResult {
  success: boolean;
  algorithm: string;
  n_clusters: number;
  silhouette_score: number;
  cluster_distribution: Record<string, number>;
  charts: Record<string, string>;
  insights: string[];
  pca_variance_explained?: number;
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
  const [algorithm, setAlgorithm] = useState<string>('kmeans');
  const [nClusters, setNClusters] = useState<number | null>(null);
  const [autoDetect, setAutoDetect] = useState<boolean>(true);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<ClusterResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(true);

  // Load user files and saved clustering result on mount
  useEffect(() => {
    loadFiles();
    loadSavedClusteringModel();
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

            {/* Cluster Visualization */}
            {result.charts?.cluster_scatter && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold flex items-center gap-2 text-gray-900 dark:text-white">
                    <PieChart className="w-5 h-5 text-purple-500" />
                    Cluster Visualization (PCA 2D)
                  </h3>
                  <button 
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = result.charts.cluster_scatter;
                      link.download = 'clusters.png';
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
                  <img
                    src={result.charts.cluster_scatter}
                    alt="Cluster visualization"
                    className="max-w-full max-h-[500px] rounded-lg"
                  />
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
                    <div
                      key={cluster}
                      className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-center"
                    >
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{cluster}</p>
                      <p className="text-xs text-purple-500 mt-1">{percentage}%</p>
                    </div>
                  );
                })}
              </div>
            </div>
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
