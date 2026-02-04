/**
 * 🤖 ML Predictions - Complete Training & Results Page
 * 
 * SAME AS DATAHUB:
 * - Select from existing files uploaded in DataHub
 * - Smart target column detection with auto-select
 * - Fast Mode (7 algorithms, 30-60s) vs Ultra Mode (20+ algorithms, 2-10min)
 * - Same training overlay with animated spinning icon
 * - Full dark/light mode support
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Brain,
    TrendingUp,
    BarChart3,
    AlertTriangle,
    CheckCircle,
    Target,
    Zap,
    RefreshCw,
    Sparkles,
    Award,
    Layers,
    PieChart,
    Activity,
    Play,
    Square,
    History,
    Database,
    Download,
    FileText,
    XCircle,
    HeartPulse,
    Sliders,
    HelpCircle,
    Boxes,
    GitBranch,
    Code2,
} from 'lucide-react';
import ModelHistory from '@/components/automl/ModelHistory';
import DataHealthCard from '@/components/automl/DataHealthCard';
import PlaygroundTab from '@/components/automl/PlaygroundTab';
import ExplainModal from '@/components/automl/ExplainModal';
import apiService from '@/services/api';
import { useUserStore } from '@/store/userStore';
import { useToast } from '@/contexts/ToastContext';
import { getUserIdSync } from '@/utils/userId';


interface FeatureMetadata {
    name: string;
    type: 'numeric' | 'categorical' | 'text' | 'datetime';
    min?: number | string;  // number for numeric, ISO string for datetime
    max?: number | string;  // number for numeric, ISO string for datetime
    mean?: number;
    options?: string[];
    placeholder?: string;  // For text/datetime inputs
}

interface MLResult {
    success: boolean;
    task_type: string;
    target_column: string;
    best_model: {
        name: string;
        metrics: Record<string, number>;
    };
    all_models: Array<{
        name: string;
        metrics: Record<string, number>;
    }>;
    feature_importance: Array<{
        feature: string;
        importance: number;
        rank: number;
    }>;
    feature_metadata?: FeatureMetadata[];
    bias_reports: Array<{
        type: string;
        description: string;
        severity: string;
        corrected: boolean;
    }>;
    insights: string[];
    recommendations: string[];
    charts: Record<string, string>;
    data_summary: {
        rows: number;
        columns: number;
        features_engineered: number;
        features_used?: number;
    };
    processing_time_seconds: number;
    is_nlp_task?: boolean;
    primary_text_col?: string;
    feature_columns?: string[];
    cleaned_file?: string;
    mode?: 'traditional' | 'nlp' | 'deep_learning';
    modes_trained?: string[];
    modes_requested?: string[];
    results_per_mode?: Record<string, {
        success: boolean;
        best_model?: string;
        algorithm?: string;
        architecture?: string;
        metrics?: Record<string, number>;
        error?: string;
    }>;
    combined_metrics?: Record<string, any>;
    leaderboard?: Array<{
        mode: string;
        model: string;
        score: number;
        metrics?: Record<string, number>;
    }>;
    best_overall?: {
        mode: string;
        name: string;
        metrics?: Record<string, number>;
    };
    pipeline?: string;
    was_stopped?: boolean;
}

interface FileItem {
    id: string;
    name: string;
    size: number;
    type: string;
    uploadedAt: string;
    status: 'processing' | 'completed' | 'failed';
}

const MLPredictions: React.FC = () => {
    const { isDark } = useUserStore();
    const toast = useToast();
    const navigate = useNavigate();
    const location = useLocation();

    // Results state
    const [result, setResult] = useState<MLResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'features' | 'predict' | 'playground' | 'history' | 'data' | 'clustering'>('overview');
    const [showExplainModal, setShowExplainModal] = useState(false);
    const [explainInputValues, setExplainInputValues] = useState<Record<string, any>>({});
    const [predictionInput, setPredictionInput] = useState<Record<string, string>>({});
    const [predictionResult, setPredictionResult] = useState<any>(null);
    const [chartsLoading, setChartsLoading] = useState(false);

    // File & Training state - SAME AS DATAHUB
    const [existingFiles, setExistingFiles] = useState<FileItem[]>([]);
    const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
    const [training, setTraining] = useState(false);
    const [ultraMode, setUltraMode] = useState(true); // Ultra AutoML (maximum accuracy) is default
    const [targetColumn, setTargetColumn] = useState('');
    const [availableColumns, setAvailableColumns] = useState<string[]>([]);
    const [progressMessage, setProgressMessage] = useState('Initializing...');
    const [abortController, setAbortController] = useState<AbortController | null>(null);

    // Learning Type: supervised (classification/regression) or unsupervised (clustering)
    const [learningType, setLearningType] = useState<'supervised' | 'unsupervised'>('supervised');

    // Multi-mode ML selection - users can select multiple modes simultaneously
    const [selectedModes, setSelectedModes] = useState<Set<'traditional' | 'nlp' | 'deep_learning'>>(new Set(['traditional']));

    // Algorithm selection per ML type (multi-select within each mode)
    const [selectedAlgorithms, setSelectedAlgorithms] = useState<{
        traditional: string[];
        nlp: string[];
        deep_learning: string[];
    }>({
        traditional: ['auto'],
        nlp: ['auto'],
        deep_learning: ['auto'],
    });

    // For backward compatibility with existing code
    const mlType = Array.from(selectedModes)[0] || 'traditional';
    const selectedAlgorithm = selectedAlgorithms[mlType]?.[0] || 'auto';
    const setMlType = (type: 'traditional' | 'nlp' | 'deep_learning') => {
        setSelectedModes(new Set([type]));
    };

    // Toggle mode selection (multi-select enabled)
    const toggleMode = (mode: 'traditional' | 'nlp' | 'deep_learning') => {
        const newModes = new Set(selectedModes);
        if (newModes.has(mode)) {
            if (newModes.size > 1) { // Keep at least one mode selected
                newModes.delete(mode);
            }
        } else {
            newModes.add(mode);
        }
        setSelectedModes(newModes);
    };

    // Toggle algorithm selection within a mode
    const toggleAlgorithm = (mode: 'traditional' | 'nlp' | 'deep_learning', algo: string) => {
        setSelectedAlgorithms(prev => {
            const current = prev[mode];
            if (algo === 'auto') {
                return { ...prev, [mode]: ['auto'] };
            }
            const withoutAuto = current.filter(a => a !== 'auto');
            if (current.includes(algo)) {
                const filtered = withoutAuto.filter(a => a !== algo);
                return { ...prev, [mode]: filtered.length > 0 ? filtered : ['auto'] };
            } else {
                return { ...prev, [mode]: [...withoutAuto, algo] };
            }
        });
    };

    // Select all algorithms in a mode
    const selectAllAlgorithms = (mode: 'traditional' | 'nlp' | 'deep_learning') => {
        const allAlgos = algorithmOptions[mode].filter(a => a.value !== 'auto').map(a => a.value);
        setSelectedAlgorithms(prev => ({ ...prev, [mode]: allAlgos }));
    };

    // COMPREHENSIVE Algorithm Options - ALL algorithms for each mode
    const algorithmOptions = {
        traditional: [
            { value: 'auto', label: '🚀 Auto (Best Model)', description: 'Smart selection from all algorithms', category: 'auto' },
            // Tree-based
            { value: 'random_forest', label: 'Random Forest', description: 'Ensemble of decision trees', category: 'Tree' },
            { value: 'xgboost', label: 'XGBoost', description: 'Competition winner', category: 'Tree' },
            { value: 'lightgbm', label: 'LightGBM', description: 'Fast gradient boosting', category: 'Tree' },
            { value: 'catboost', label: 'CatBoost', description: 'Great for categories', category: 'Tree' },
            { value: 'decision_tree', label: 'Decision Tree', description: 'Simple, interpretable', category: 'Tree' },
            { value: 'extra_trees', label: 'Extra Trees', description: 'More random than RF', category: 'Tree' },
            { value: 'gradient_boosting', label: 'Gradient Boosting', description: 'Classic boosting', category: 'Tree' },
            { value: 'hist_gradient_boosting', label: 'Histogram GB', description: 'Fast for large data', category: 'Tree' },
            // Linear
            { value: 'logistic_regression', label: 'Logistic Regression', description: 'Fast baseline', category: 'Linear' },
            { value: 'ridge', label: 'Ridge Regression', description: 'L2 regularization', category: 'Linear' },
            { value: 'lasso', label: 'Lasso Regression', description: 'L1 feature selection', category: 'Linear' },
            { value: 'elastic_net', label: 'Elastic Net', description: 'L1+L2 combined', category: 'Linear' },
            { value: 'sgd', label: 'SGD Classifier', description: 'Online learning', category: 'Linear' },
            // SVM
            { value: 'svm_linear', label: 'SVM (Linear)', description: 'Linear kernel', category: 'SVM' },
            { value: 'svm_rbf', label: 'SVM (RBF)', description: 'Non-linear kernel', category: 'SVM' },
            { value: 'svm_poly', label: 'SVM (Polynomial)', description: 'Polynomial kernel', category: 'SVM' },
            // K-Nearest Neighbors
            { value: 'knn_3', label: 'KNN (k=3)', description: 'Fast, small k', category: 'KNN' },
            { value: 'knn_5', label: 'KNN (k=5)', description: 'Balanced k', category: 'KNN' },
            { value: 'knn_7', label: 'KNN (k=7)', description: 'Smoother', category: 'KNN' },
            { value: 'knn_weighted', label: 'KNN (Weighted)', description: 'Distance weighted', category: 'KNN' },
            // Naive Bayes
            { value: 'gaussian_nb', label: 'Gaussian Naive Bayes', description: 'Continuous features', category: 'Naive Bayes' },
            { value: 'multinomial_nb', label: 'Multinomial NB', description: 'Count data', category: 'Naive Bayes' },
            { value: 'bernoulli_nb', label: 'Bernoulli NB', description: 'Binary features', category: 'Naive Bayes' },
            { value: 'complement_nb', label: 'Complement NB', description: 'Imbalanced data', category: 'Naive Bayes' },
            // Ensemble
            { value: 'adaboost', label: 'AdaBoost', description: 'Adaptive boosting', category: 'Ensemble' },
            { value: 'bagging', label: 'Bagging', description: 'Bootstrap aggregating', category: 'Ensemble' },
            { value: 'voting', label: 'Voting Ensemble', description: 'Multiple models vote', category: 'Ensemble' },
            { value: 'stacking', label: 'Stacking', description: 'Meta-learner', category: 'Ensemble' },
            // Other
            { value: 'lda', label: 'LDA', description: 'Linear Discriminant', category: 'Other' },
            { value: 'qda', label: 'QDA', description: 'Quadratic Discriminant', category: 'Other' },
        ],
        nlp: [
            { value: 'auto', label: '🚀 Auto (Best NLP)', description: 'Smart NLP selection', category: 'auto' },
            // Text Vectorization
            { value: 'tfidf', label: 'TF-IDF', description: 'Term frequency-inverse doc', category: 'Vectorization' },
            { value: 'bow', label: 'Bag of Words', description: 'Word count vectors', category: 'Vectorization' },
            { value: 'count_vectorizer', label: 'Count Vectorizer', description: 'Raw word counts', category: 'Vectorization' },
            { value: 'hashing', label: 'Hashing Vectorizer', description: 'Memory efficient', category: 'Vectorization' },
            // N-grams
            { value: 'unigram', label: 'Unigram', description: 'Single words', category: 'N-gram' },
            { value: 'bigram', label: 'Bigram', description: 'Word pairs', category: 'N-gram' },
            { value: 'trigram', label: 'Trigram', description: 'Three-word sequences', category: 'N-gram' },
            { value: 'char_ngram', label: 'Character N-gram', description: 'Spelling-robust', category: 'N-gram' },
            // Word Embeddings
            { value: 'word2vec_cbow', label: 'Word2Vec (CBOW)', description: 'Context prediction', category: 'Embeddings' },
            { value: 'word2vec_skipgram', label: 'Word2Vec (Skip-gram)', description: 'Word prediction', category: 'Embeddings' },
            { value: 'glove', label: 'GloVe', description: 'Global vectors', category: 'Embeddings' },
            { value: 'fasttext', label: 'FastText', description: 'Subword embeddings', category: 'Embeddings' },
            { value: 'doc2vec', label: 'Doc2Vec', description: 'Document vectors', category: 'Embeddings' },
            // Topic Modeling
            { value: 'lda', label: 'LDA', description: 'Topic discovery', category: 'Topic Model' },
            { value: 'lsa', label: 'LSA/LSI', description: 'Latent semantics', category: 'Topic Model' },
            { value: 'nmf', label: 'NMF', description: 'Non-negative matrix', category: 'Topic Model' },
            // Transformers
            { value: 'bert', label: 'BERT', description: 'Bidirectional encoder', category: 'Transformer' },
            { value: 'distilbert', label: 'DistilBERT', description: 'Lightweight BERT', category: 'Transformer' },
            { value: 'roberta', label: 'RoBERTa', description: 'Robust BERT', category: 'Transformer' },
            { value: 'albert', label: 'ALBERT', description: 'Efficient BERT', category: 'Transformer' },
            { value: 'xlnet', label: 'XLNet', description: 'Permutation LM', category: 'Transformer' },
            { value: 'electra', label: 'ELECTRA', description: 'Efficient pretraining', category: 'Transformer' },
            { value: 'gpt2', label: 'GPT-2', description: 'Generative model', category: 'Transformer' },
            // Sentiment Analysis
            { value: 'vader', label: 'VADER', description: 'Rule-based sentiment', category: 'Sentiment' },
            { value: 'textblob', label: 'TextBlob', description: 'Simple NLP', category: 'Sentiment' },
            // Ensembles
            { value: 'voting_ensemble', label: 'Voting Ensemble', description: 'Multiple classifiers', category: 'Ensemble' },
            { value: 'stacking_ensemble', label: 'Stacking Ensemble', description: 'Meta-learner', category: 'Ensemble' },
            { value: 'blending_ensemble', label: 'Blending Ensemble', description: 'Holdout blend', category: 'Ensemble' },
            { value: 'weighted_ensemble', label: 'Weighted Ensemble', description: 'Weighted voting', category: 'Ensemble' },
        ],
        deep_learning: [
            { value: 'auto', label: '🚀 Auto (Best NN)', description: 'Smart architecture', category: 'auto' },
            // ANN - Artificial Neural Network
            { value: 'ann_shallow', label: 'ANN Shallow (32)', description: 'Single hidden layer', category: 'ANN' },
            { value: 'ann_medium', label: 'ANN Medium (64-32)', description: 'Two layers', category: 'ANN' },
            { value: 'ann_deep', label: 'ANN Deep (128-64-32)', description: 'Three layers', category: 'ANN' },
            { value: 'ann_wide', label: 'ANN Wide (256-128)', description: 'Wide network', category: 'ANN' },
            // MLP - Multi-Layer Perceptron
            { value: 'mlp_small', label: 'MLP Small (64-32)', description: 'Fast, small data', category: 'MLP' },
            { value: 'mlp_medium', label: 'MLP Medium (128-64-32)', description: 'Balanced', category: 'MLP' },
            { value: 'mlp_large', label: 'MLP Large (256-128-64)', description: 'Complex patterns', category: 'MLP' },
            { value: 'mlp_xl', label: 'MLP XL (512-256-128)', description: 'Large scale', category: 'MLP' },
            // RNN - Recurrent Neural Network
            { value: 'rnn_simple', label: 'RNN Simple', description: 'Basic recurrent', category: 'RNN' },
            { value: 'rnn_deep', label: 'RNN Deep', description: 'Stacked RNN', category: 'RNN' },
            { value: 'rnn_bidirectional', label: 'Bidirectional RNN', description: 'Both directions', category: 'RNN' },
            // LSTM - Long Short-Term Memory
            { value: 'lstm_simple', label: 'LSTM', description: 'Long-term memory', category: 'LSTM' },
            { value: 'lstm_stacked', label: 'Stacked LSTM', description: 'Multi-layer LSTM', category: 'LSTM' },
            { value: 'lstm_deep', label: 'Deep LSTM', description: '3+ layer LSTM', category: 'LSTM' },
            { value: 'bilstm', label: 'BiLSTM', description: 'Bidirectional LSTM', category: 'LSTM' },
            { value: 'lstm_attention', label: 'LSTM + Attention', description: 'Attention mechanism', category: 'LSTM' },
            // GRU - Gated Recurrent Unit
            { value: 'gru_simple', label: 'GRU', description: 'Simpler than LSTM', category: 'GRU' },
            { value: 'gru_stacked', label: 'Stacked GRU', description: 'Multi-layer GRU', category: 'GRU' },
            { value: 'bigru', label: 'BiGRU', description: 'Bidirectional GRU', category: 'GRU' },
            // CNN - Convolutional Networks
            { value: 'cnn_1d', label: 'CNN 1D', description: '1D convolutions', category: 'CNN' },
            { value: 'textcnn', label: 'TextCNN', description: 'Text classification', category: 'CNN' },
            { value: 'cnn_multichannel', label: 'Multi-channel CNN', description: 'Multiple filters', category: 'CNN' },
            // Transformer
            { value: 'transformer_encoder', label: 'Transformer Encoder', description: 'Self-attention', category: 'Transformer' },
            { value: 'transformer_decoder', label: 'Transformer Decoder', description: 'Causal attention', category: 'Transformer' },
            { value: 'self_attention', label: 'Self-Attention', description: 'Attention layer', category: 'Transformer' },
            { value: 'multihead_attention', label: 'Multi-Head Attention', description: 'Multiple heads', category: 'Transformer' },
            // Autoencoder
            { value: 'autoencoder', label: 'Autoencoder', description: 'Compression', category: 'Autoencoder' },
            { value: 'vae', label: 'VAE', description: 'Variational', category: 'Autoencoder' },
            { value: 'sparse_autoencoder', label: 'Sparse Autoencoder', description: 'Sparse features', category: 'Autoencoder' },
            { value: 'denoising_autoencoder', label: 'Denoising AE', description: 'Noise robust', category: 'Autoencoder' },
            // Regularization Variants
            { value: 'dropout_nn', label: 'Dropout NN', description: 'Dropout regularization', category: 'Regularized' },
            { value: 'batchnorm_nn', label: 'BatchNorm NN', description: 'Batch normalization', category: 'Regularized' },
            { value: 'layernorm_nn', label: 'LayerNorm NN', description: 'Layer normalization', category: 'Regularized' },
            { value: 'l1_regularized', label: 'L1 Regularized', description: 'Lasso penalty', category: 'Regularized' },
            { value: 'l2_regularized', label: 'L2 Regularized', description: 'Ridge penalty', category: 'Regularized' },
            { value: 'elastic_net_nn', label: 'Elastic Net NN', description: 'L1+L2 penalty', category: 'Regularized' },
            // Activation Variants
            { value: 'relu_nn', label: 'ReLU Network', description: 'ReLU activation', category: 'Activation' },
            { value: 'leaky_relu_nn', label: 'Leaky ReLU Network', description: 'Leaky ReLU', category: 'Activation' },
            { value: 'elu_nn', label: 'ELU Network', description: 'Exponential LU', category: 'Activation' },
            { value: 'selu_nn', label: 'SELU Network', description: 'Self-normalizing', category: 'Activation' },
            { value: 'gelu_nn', label: 'GELU Network', description: 'Gaussian Error LU', category: 'Activation' },
            { value: 'swish_nn', label: 'Swish Network', description: 'Swish activation', category: 'Activation' },
            { value: 'mish_nn', label: 'Mish Network', description: 'Mish activation', category: 'Activation' },
            { value: 'tanh_nn', label: 'Tanh Network', description: 'Tanh activation', category: 'Activation' },
            { value: 'sigmoid_nn', label: 'Sigmoid Network', description: 'Sigmoid activation', category: 'Activation' },
            // Ensemble Neural Networks
            { value: 'bagging_nn', label: 'Bagging NN', description: 'Bootstrap aggregating', category: 'Ensemble' },
            { value: 'boosting_nn', label: 'Boosting NN', description: 'Sequential learning', category: 'Ensemble' },
            { value: 'snapshot_ensemble', label: 'Snapshot Ensemble', description: 'Single training', category: 'Ensemble' },
            { value: 'stacked_nn', label: 'Stacked NN', description: 'Meta-learning', category: 'Ensemble' },
            // Residual Networks
            { value: 'resnet_mlp', label: 'ResNet-MLP', description: 'Skip connections', category: 'Residual' },
            { value: 'densenet_mlp', label: 'DenseNet-MLP', description: 'Dense connections', category: 'Residual' },
            { value: 'highway_network', label: 'Highway Network', description: 'Gated connections', category: 'Residual' },
            { value: 'mlp_bagging', label: 'MLP Bagging', description: 'Bootstrap MLPs', category: 'Ensemble' },
        ],
    };

    const [clusteringAlgorithm, setClusteringAlgorithm] = useState<string>('kmeans');
    const [clusterCount, setClusterCount] = useState<number | null>(null); // null = auto-detect
    const [clusteringResult, setClusteringResult] = useState<any>(null);

    // Clustering UI state
    const [clusterActiveTab, setClusterActiveTab] = useState<'overview' | 'charts' | 'profiles' | 'predict'>('overview');
    const [clusterPredictionInput, setClusterPredictionInput] = useState<Record<string, string>>({});
    const [clusterPredictionResult, setClusterPredictionResult] = useState<any>(null);
    const [clusterPredicting, setClusterPredicting] = useState(false);

    // Smart target column detection - SAME AS DATAHUB
    const detectTargetColumn = (columns: string[]): string => {
        const targetPatterns = [
            'target', 'label', 'class', 'y', 'output', 'result', 'prediction',
            'price_range', 'price', 'category', 'status', 'type', 'outcome',
            'fraud', 'churn', 'default', 'survived', 'approved', 'purchased'
        ];

        // Check for exact/partial matches
        for (const pattern of targetPatterns) {
            for (const col of columns) {
                if (col.toLowerCase().includes(pattern)) {
                    return col;
                }
            }
        }

        // Default: last column (common ML convention)
        return columns[columns.length - 1];
    };

    // Load existing files from DataHub
    const loadExistingFiles = async () => {
        try {
            const response = await apiService.listFiles();
            const dataFiles = (response.data.files || []).filter((f: FileItem) =>
                f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
            );
            setExistingFiles(dataFiles);
        } catch (error) {
            console.error('Failed to load files:', error);
        }
    };

    // Fetch charts from API
    const fetchChartsFromAPI = async (userId: string): Promise<Record<string, string>> => {
        try {
            const response = await fetch(`/api/v2/automl/charts/${userId}`);
            const data = await response.json();
            if (data.success && data.charts && Object.keys(data.charts).length > 0) {
                try {
                    sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(data.charts));
                } catch (e) {
                    console.warn('[MLPredictions] Failed to cache charts');
                }
                return data.charts;
            }
            return {};
        } catch (error) {
            console.warn('[MLPredictions] Failed to fetch charts:', error);
            return {};
        }
    };

    // Load results on mount - with proper cleanup for memory leak prevention
    useEffect(() => {
        let isMounted = true; // Prevent state updates after unmount
        const abortCtrl = new AbortController();

        const loadResults = async () => {
            const userId = getUserIdSync(); // CONSISTENT user ID handling

            const addChartsFromStorage = async (result: MLResult): Promise<MLResult> => {
                if (!result.charts || Object.keys(result.charts).length === 0) {
                    const savedCharts = sessionStorage.getItem(`mlCharts_${userId}`);
                    if (savedCharts) {
                        try {
                            result.charts = JSON.parse(savedCharts);
                            return result;
                        } catch (e) { }
                    }
                    setChartsLoading(true);
                    const apiCharts = await fetchChartsFromAPI(userId);
                    setChartsLoading(false);
                    if (Object.keys(apiCharts).length > 0) {
                        result.charts = apiCharts;
                    }
                }
                return result;
            };

            // 🔄 Sync result with active model from backend to ensure consistency
            const syncWithActiveModel = async (result: MLResult): Promise<MLResult> => {
                try {
                    // First sync basic model info
                    const response = await fetch(`/api/v2/autonomous/models/${userId}`);
                    const data = await response.json();

                    if (data.success && data.models && data.models.length > 0) {
                        const activeModel = data.models.find((m: any) => m.is_active);
                        if (activeModel) {
                            // Update result.best_model to match the active model
                            result.best_model = {
                                name: activeModel.model_name,
                                metrics: activeModel.metrics || {}
                            };
                            result.target_column = activeModel.target_column;
                            result.task_type = activeModel.task_type;
                            result.feature_columns = activeModel.feature_columns || result.feature_columns;
                            // Detect mode from active model
                            result.mode = activeModel.mode || 
                                (activeModel.model_name?.includes('NLP') ? 'nlp' :
                                 activeModel.model_name?.includes('Deep') ? 'deep_learning' : 'traditional');
                            console.log('[MLPredictions] Synced with active model:', activeModel.model_name);
                        }
                    }

                    // CRITICAL: Fetch feature_metadata AND charts from saved model
                    // Use mode=auto to let backend auto-detect the best mode for multi-mode training
                    const savedResultResponse = await fetch(`/api/v1/automl/saved-result?user_id=${userId}&mode=auto`);
                    const savedResult = await savedResultResponse.json();

                    if (savedResult.success) {
                        // Update feature_metadata if missing
                        if ((!result.feature_metadata || result.feature_metadata.length === 0) && savedResult.feature_metadata?.length > 0) {
                            result.feature_metadata = savedResult.feature_metadata;
                            console.log('[MLPredictions] Loaded feature_metadata from saved model:', savedResult.feature_metadata.length, 'features');
                        }
                        
                        // Update charts if missing or empty
                        if ((!result.charts || Object.keys(result.charts).length === 0) && savedResult.charts && Object.keys(savedResult.charts).length > 0) {
                            result.charts = savedResult.charts;
                            console.log('[MLPredictions] Loaded charts from saved model:', Object.keys(savedResult.charts).length, 'charts');
                            // Also save to sessionStorage for faster future access
                            try {
                                sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(savedResult.charts));
                            } catch (e) { }
                        }
                        
                        // Update mode if detected
                        if (savedResult.mode) {
                            result.mode = savedResult.mode as 'traditional' | 'nlp' | 'deep_learning';
                        }
                        
                        // Update multi-mode specific fields
                        if (savedResult.modes_trained) {
                            (result as any).modes_trained = savedResult.modes_trained;
                        }
                        if (savedResult.best_overall) {
                            (result as any).best_overall = savedResult.best_overall;
                        }
                        if (savedResult.results_per_mode) {
                            (result as any).results_per_mode = savedResult.results_per_mode;
                        }
                        if (savedResult.primary_text_col) {
                            (result as any).primary_text_col = savedResult.primary_text_col;
                        }
                        
                        // CRITICAL: Update data_summary if missing (for rows, columns, features display)
                        if ((!result.data_summary || result.data_summary.rows === 0) && savedResult.data_summary) {
                            result.data_summary = savedResult.data_summary;
                            console.log('[MLPredictions] Loaded data_summary from saved model:', savedResult.data_summary);
                        }
                        
                        // Update all_models if missing (for Models Trained count)
                        if ((!result.all_models || result.all_models.length === 0) && savedResult.all_models?.length > 0) {
                            result.all_models = savedResult.all_models;
                            console.log('[MLPredictions] Loaded all_models from saved model:', savedResult.all_models.length, 'models');
                        }
                        
                        // Update leaderboard if missing
                        if ((!result.leaderboard || result.leaderboard?.length === 0) && savedResult.leaderboard?.length > 0) {
                            (result as any).leaderboard = savedResult.leaderboard;
                        }
                    }
                } catch (err) {
                    console.warn('[MLPredictions] Could not sync with active model:', err);
                }
                return result;
            };

            // Priority 1: Location state (fresh training - skip sync)
            if (location.state?.automlResult) {
                const navResult = location.state.automlResult;
                const resultWithCharts = await addChartsFromStorage(navResult);
                if (!isMounted) return; // Prevent state updates if unmounted
                setResult(resultWithCharts);
                setActiveTab('overview'); // Reset to overview when loading results
                try {
                    // Save to BOTH localStorage and sessionStorage
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(navResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                    // SessionStorage for current browser session (persists during navigation)
                    sessionStorage.setItem(`mlResultsSession_${userId}`, JSON.stringify(navResult));
                } catch (storageErr) {
                    const { charts, ...lightResult } = navResult;
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(lightResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                    sessionStorage.setItem(`mlResultsSession_${userId}`, JSON.stringify(lightResult));
                }
                if (resultWithCharts.charts && Object.keys(resultWithCharts.charts).length > 0) {
                    try {
                        sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(resultWithCharts.charts));
                    } catch (e) { }
                }
                if (isMounted) setLoading(false);
                return;
            }

            // Priority 2: Try loading from backend FIRST (persisted across logout/refresh)
            // This ensures data survives logout and browser refresh
            try {
                const backendResponse = await fetch(`/api/v1/automl/saved-result?user_id=${userId}&mode=auto`, {
                    signal: abortCtrl.signal
                });
                const backendResult = await backendResponse.json();
                
                if (backendResult.success && backendResult.best_model) {
                    console.log('[MLPredictions] Loaded from backend API (persisted data)');
                    const resultWithCharts = await addChartsFromStorage(backendResult);
                    if (!isMounted) return;
                    setResult(resultWithCharts);
                    setActiveTab('overview'); // Reset to overview when loading results
                    
                    // Cache to localStorage and sessionStorage
                    try {
                        localStorage.setItem(`mlResults_${userId}`, JSON.stringify(backendResult));
                        localStorage.setItem(`hasMLResults_${userId}`, 'true');
                        sessionStorage.setItem(`mlResultsSession_${userId}`, JSON.stringify(backendResult));
                    } catch (e) {}
                    
                    if (isMounted) setLoading(false);
                    return;
                }
            } catch (err) {
                if ((err as Error).name === 'AbortError') return; // Ignore abort errors
                console.warn('[MLPredictions] Backend API not available, trying localStorage:', err);
            }

            // Priority 3: SessionStorage (current browser session - navigation within app)
            const sessionSaved = sessionStorage.getItem(`mlResultsSession_${userId}`);
            if (sessionSaved) {
                try {
                    let parsedSession = JSON.parse(sessionSaved);
                    // Don't sync - use session results as-is (they're from current session)
                    const resultWithCharts = await addChartsFromStorage(parsedSession);
                    if (!isMounted) return;
                    setResult(resultWithCharts);
                    setActiveTab('overview'); // Reset to overview when loading results
                    setLoading(false);
                    return;
                } catch (e) { }
            }

            // Priority 4: User-specific localStorage (sync with active model)
            const saved = localStorage.getItem(`mlResults_${userId}`);
            if (saved) {
                try {
                    let parsedSaved = JSON.parse(saved);
                    parsedSaved = await syncWithActiveModel(parsedSaved);
                    const resultWithCharts = await addChartsFromStorage(parsedSaved);
                    if (!isMounted) return;
                    setResult(resultWithCharts);
                    setActiveTab('overview'); // Reset to overview when loading results
                    setLoading(false);
                    return;
                } catch (e) { }
            }

            // Priority 5: Legacy migration (sync with active model)
            const legacySaved = localStorage.getItem('mlResults');
            if (legacySaved) {
                try {
                    let parsed = JSON.parse(legacySaved);
                    parsed = await syncWithActiveModel(parsed);
                    const resultWithCharts = await addChartsFromStorage(parsed);
                    if (!isMounted) return;
                    setResult(resultWithCharts);
                    setActiveTab('overview'); // Reset to overview when loading results
                    localStorage.setItem(`mlResults_${userId}`, legacySaved);
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                    setLoading(false);
                    return;
                } catch (e) { }
            }

            // No results - load existing files
            await loadExistingFiles();
            if (isMounted) setLoading(false);
        };

        loadResults();

        // Only override activeTab if explicitly passed in location state
        // Otherwise, keep the 'overview' that was set during loadResults
        if (location.state?.activeTab) {
            setActiveTab(location.state.activeTab);
        } else {
            // Reset to overview when navigating to page without explicit tab
            setActiveTab('overview');
        }

        // Cleanup function to prevent memory leaks
        return () => {
            isMounted = false;
            abortCtrl.abort();
        };
    }, [location.state, location.key]);

    // 🔄 Refresh overview when model changes (rollback/delete)
    const handleModelChange = async () => {
        const userId = getUserIdSync();
        try {
            const response = await fetch(`/api/v2/autonomous/models/${userId}`);
            const data = await response.json();

            if (data.success && data.models && data.models.length > 0) {
                const activeModel = data.models.find((m: any) => m.is_active);
                if (activeModel && result) {
                    setResult({
                        ...result,
                        best_model: {
                            name: activeModel.model_name,
                            metrics: activeModel.metrics || {}
                        },
                        target_column: activeModel.target_column,
                        task_type: activeModel.task_type,
                        feature_columns: activeModel.feature_columns || result.feature_columns
                    });
                }
            }
        } catch (err) {
            console.warn('[MLPredictions] Could not refresh after model change:', err);
        }
    };

    const getMetricColor = (value: number) => {
        if (value >= 0.9) return '#10b981';
        if (value >= 0.7) return '#f59e0b';
        return '#ef4444';
    };

    // Fetch columns from existing file - SAME AS DATAHUB
    const fetchColumnsFromFile = async (fileName: string) => {
        try {
            const userId = getUserIdSync();
            // Download file and parse columns
            const fileResponse = await fetch(`/api/v1/files/${userId}/${fileName}/download`);
            if (!fileResponse.ok) return;

            const blob = await fileResponse.blob();
            const text = await blob.text();
            const firstLine = text.split('\n')[0];
            const columns = firstLine.split(',').map(col => col.trim().replace(/"/g, ''));

            setAvailableColumns(columns);
            const detected = detectTargetColumn(columns);
            setTargetColumn(detected);
            console.log(`📊 Detected columns: ${columns.length}, Target: ${detected}`);
        } catch (error) {
            console.error('Failed to fetch columns:', error);
        }
    };

    // Select existing file
    const handleSelectFile = async (file: FileItem) => {
        setSelectedFile(file);
        await fetchColumnsFromFile(file.name);
    };

    // Training handler - Updated for ML Type support
    const handleRunAutoML = async () => {
        if (!selectedFile) {
            toast.error('Please select a data file first.');
            return;
        }

        setTraining(true);

        // Create abort controller for "Stop" functionality
        const controller = new AbortController();
        setAbortController(controller);

        try {
            // Get the file from server and send to AutoML - SAME AS DATAHUB
            const userId = getUserIdSync();
            const fileResponse = await fetch(`/api/v1/files/${userId}/${selectedFile.name}/download`, {
                signal: controller.signal
            });

            if (!fileResponse.ok) throw new Error('Failed to get file');

            const fileBlob = await fileResponse.blob();
            const formData = new FormData();
            formData.append('file', fileBlob, selectedFile.name);
            formData.append('user_id', userId);

            // Add target column if selected/detected
            if (targetColumn) {
                formData.append('target_column', targetColumn);
            }

            // Multi-mode training support
            const modes = Array.from(selectedModes);
            formData.append('modes', JSON.stringify(modes));
            formData.append('algorithms', JSON.stringify(selectedAlgorithms));

            // ALWAYS use multi_mode/train endpoint - it handles all cases correctly
            // This ensures we train ONLY what user selected, not fast/ultra defaults
            const endpoint = '/api/v2/automl/multi_mode/train';

            // Pass selected algorithms for each mode
            formData.append('selected_traditional', JSON.stringify(selectedAlgorithms.traditional));
            formData.append('selected_nlp', JSON.stringify(selectedAlgorithms.nlp));
            formData.append('selected_deep_learning', JSON.stringify(selectedAlgorithms.deep_learning));

            // Ultra mode is OPTIONAL - only if user explicitly clicked Ultra button
            formData.append('ultra_mode', String(ultraMode && modes.includes('traditional')));

            console.log('🚀 Training with:', {
                modes,
                algorithms: selectedAlgorithms,
                ultraMode: ultraMode && modes.includes('traditional')
            });

            const automlResponse = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            const automlResult = await automlResponse.json();

            if (automlResult.success) {
                // Save to localStorage with USER-SPECIFIC key for data isolation
                try {
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(automlResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');

                    if (automlResult.charts) {
                        try {
                            sessionStorage.setItem(`mlCharts_${userId}`, JSON.stringify(automlResult.charts));
                        } catch (chartErr) {
                            console.warn("Charts too large for sessionStorage");
                        }
                    }
                } catch (e) {
                    console.warn("Storage quota full, saving result without charts");
                    const { charts, ...lightResult } = automlResult;
                    localStorage.setItem(`mlResults_${userId}`, JSON.stringify(lightResult));
                    localStorage.setItem(`hasMLResults_${userId}`, 'true');
                }

                window.dispatchEvent(new CustomEvent('filesUpdated'));
                setResult(automlResult);
            } else {
                toast.error(`AutoML failed: ${automlResult.detail || automlResult.error || 'Unknown error'}`);
            }
        } catch (error: any) {
            // Handle User Stop
            if (error.name === 'AbortError') {
                return; // Silent exit on stop
            }
            console.error('AutoML error:', error);
            toast.error(`AutoML error: ${error.message}`);
        } finally {
            setTraining(false);
            setAbortController(null);
        }
    };

    // Clustering handler - For UNSUPERVISED learning (no target column)
    const handleRunClustering = async () => {
        if (!selectedFile) {
            toast.error('Please select a data file first.');
            return;
        }

        setTraining(true);
        setProgressMessage('🎯 Starting Clustering Analysis...');

        try {
            const userId = getUserIdSync();
            const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');

            const response = await fetch('/api/v1/ml/clustering', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': userId,
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    file_id: selectedFile.id || selectedFile.name,
                    user_id: userId,
                    algorithm: clusteringAlgorithm,
                    n_clusters: clusterCount,
                })
            });

            const clusterResult = await response.json();

            if (!response.ok) {
                // Handle HTTP errors (4xx, 5xx)
                const errorMsg = clusterResult.detail || clusterResult.error || clusterResult.message || 'Server error';
                toast.error(`Clustering failed: ${errorMsg}`);
                return;
            }

            if (clusterResult.success) {
                setClusteringResult(clusterResult);
                setClusterActiveTab('overview'); // Start with overview tab

                // Initialize prediction input with default values
                if (clusterResult.feature_columns && clusterResult.feature_stats) {
                    const defaultInputs: Record<string, string> = {};
                    clusterResult.feature_columns.forEach((col: string) => {
                        const stats = clusterResult.feature_stats[col];
                        if (stats) {
                            defaultInputs[col] = stats.mean?.toFixed(2) || '0';
                        }
                    });
                    setClusterPredictionInput(defaultInputs);
                }

                // Store clustering result WITHOUT charts to avoid localStorage quota exceeded
                try {
                    const { charts, ...resultWithoutCharts } = clusterResult;
                    localStorage.setItem(`clusteringResult_${userId}`, JSON.stringify(resultWithoutCharts));
                } catch (storageErr) {
                    console.warn('Could not cache clustering result:', storageErr);
                }

                toast.success(`Found ${clusterResult.n_clusters} clusters with ${(clusterResult.silhouette_score * 100).toFixed(1)}% separation score!`);
            } else {
                toast.error(`Clustering failed: ${clusterResult.error || clusterResult.detail || 'Unknown error'}`);
            }
        } catch (error: any) {
            console.error('Clustering error:', error);
            toast.error(`Clustering error: ${error.message}`);
        } finally {
            setTraining(false);
        }
    };

    // Predict which cluster a new data point belongs to
    const handlePredictCluster = async () => {
        if (!clusteringResult?.model_id) {
            toast.error('No clustering model available. Please run clustering first.');
            return;
        }

        setClusterPredicting(true);
        setClusterPredictionResult(null);

        try {
            const userId = getUserIdSync();
            const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');

            // Convert string inputs to numbers
            const features: Record<string, number> = {};
            for (const [key, value] of Object.entries(clusterPredictionInput)) {
                features[key] = parseFloat(value) || 0;
            }

            const response = await fetch('/api/v1/ml/clustering/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': userId,
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    user_id: userId,
                    model_id: clusteringResult.model_id,
                    features: features
                })
            });

            const result = await response.json();

            if (result.success) {
                setClusterPredictionResult(result);
                toast.success(`Predicted: ${result.cluster_name}`);
            } else {
                toast.error(`Prediction failed: ${result.error || 'Unknown error'}`);
            }
        } catch (error: any) {
            console.error('Cluster prediction error:', error);
            toast.error(`Prediction error: ${error.message}`);
        } finally {
            setClusterPredicting(false);
        }
    };

    // Combined training handler based on learning type
    const handleStartTraining = () => {
        if (learningType === 'supervised') {
            handleRunAutoML();
        } else {
            handleRunClustering();
        }
    };

    // Stop Training - SAME AS DATAHUB
    const handleStopTraining = async () => {
        if (abortController) abortController.abort();
        setTraining(false);

        // Signal Backend to Stop Permanently
        try {
            const userId = getUserIdSync();
            const formData = new FormData();
            formData.append('user_id', userId);
            await fetch('/api/v2/automl/stop_training', {
                method: 'POST',
                body: formData
            });
        } catch (e) {
            console.error("Failed to signal stop to backend", e);
        }
    };

    // Animation loop for training messages - Mode-aware
    useEffect(() => {
        if (!training) return;

        // Get mode-specific messages
        const modes = Array.from(selectedModes);
        const isMultiMode = modes.length > 1;

        let messages: string[];

        if (isMultiMode) {
            messages = [
                '🚀 Starting Multi-Mode Training...',
                '🌲 Training Traditional ML algorithms...',
                '📝 Running NLP text classification...',
                '🧠 Building Deep Learning models...',
                '📊 Generating mode-specific charts...',
                '⚖️ Comparing cross-mode performance...',
                '🏆 Selecting best overall model...',
            ];
        } else if (modes.includes('nlp')) {
            messages = [
                '📝 Initializing NLP Pipeline...',
                '🧹 Preprocessing text data...',
                '📊 Building TF-IDF/BOW features...',
                '🔤 Training text classifiers...',
                '📈 Evaluating NLP models...',
                '☁️ Generating word clouds...',
                '📊 Creating NLP charts...',
            ];
        } else if (modes.includes('deep_learning')) {
            messages = [
                '🧠 Initializing Deep Learning...',
                '📊 Preprocessing features...',
                '🔧 Building neural network architectures...',
                '⚡ Training ANN/MLP models...',
                '🔄 Testing LSTM/GRU/RNN patterns...',
                '📈 Evaluating network performance...',
                '📊 Generating architecture diagrams...',
            ];
        } else if (ultraMode) {
            messages = [
                '🎼 Initializing Ultra AutoML...',
                '📊 Analyzing Dataset Profile...',
                '🎯 Meta-Learning Recommendations...',
                '🔬 Synthesizing 50+ Features...',
                '🤖 Training Classical Models...',
                '🧠 Training Neural Networks...',
                '📈 Optimizing Hyperparameters...',
                '⚖️ Building Ultra Ensemble...',
                '🔮 Generating Explainability...',
            ];
        } else {
            messages = [
                '🧹 Cleaning Data (Phase 1/4)...',
                '🛠️ Engineering Features (Phase 2/4)...',
                '🤖 Training 15+ Models (Phase 3/4)...',
                '📈 Optimizing Hyperparameters...',
                '⚖️ Building Ensembles...',
                '📊 Generating High-Res Charts...'
            ];
        }

        let i = 0;
        const interval = setInterval(() => {
            setProgressMessage(messages[i % messages.length]);
            i++;
        }, 3500);
        return () => clearInterval(interval);
    }, [training, ultraMode, selectedModes]);

    // Check if data files exist
    const hasDataFiles = existingFiles.length > 0;

    // Show loading spinner
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
                    <RefreshCw className="w-16 h-16 mx-auto mb-4 animate-spin" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                    <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>Loading ML Results...</h2>
                </motion.div>
            </div>
        );
    }

    // ========================================================================
    // NO RESULTS - SHOW TRAINING INTERFACE (SAME AS DATAHUB)
    // ========================================================================
    if (!result && !clusteringResult) {
        return (
            <div className="space-y-6">
                {/* TRAINING OVERLAY - Mode-Aware for Traditional ML, NLP, Deep Learning, Combined */}
                {training && (() => {
                    // Determine training mode display config
                    const modes = Array.from(selectedModes);
                    const isMultiMode = modes.length > 1;
                    const isNlpOnly = modes.length === 1 && modes[0] === 'nlp';
                    const isDlOnly = modes.length === 1 && modes[0] === 'deep_learning';
                    const isTraditionalOnly = modes.length === 1 && modes[0] === 'traditional';
                    const isAutoMode = selectedAlgorithms.traditional.includes('auto');
                    
                    // Get mode-specific colors and labels
                    let gradientClass = 'bg-gradient-to-r from-emerald-400 via-green-400 to-cyan-400';
                    let bgGlow = 'bg-green-500/20';
                    let borderOuter = 'border-t-green-400 border-r-green-400/50 border-b-green-400/20 border-l-green-400/50';
                    let borderInner = 'border-b-blue-400 border-l-blue-400/50 border-t-blue-400/20 border-r-blue-400/50';
                    let badgeBg = 'bg-green-500/20 text-green-300';
                    let borderCard = 'border-green-500/30';
                    let title = '🚀 Fast ML Training';
                    let timeLabel = '⏱️ Fast mode: 1-3 minutes for quick results.';
                    let badges = [{ text: '10 Core Algorithms' }, { text: 'Quick Training' }];
                    
                    // PRIORITY ORDER: Check specific modes FIRST, then Fast/Ultra for traditional auto
                    if (isMultiMode) {
                        // Combined multi-mode training
                        gradientClass = 'bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400';
                        bgGlow = 'bg-indigo-500/20';
                        borderOuter = 'border-t-indigo-400 border-r-indigo-400/50 border-b-indigo-400/20 border-l-indigo-400/50';
                        borderInner = 'border-b-pink-400 border-l-pink-400/50 border-t-pink-400/20 border-r-pink-400/50';
                        badgeBg = 'bg-indigo-500/20 text-indigo-300';
                        borderCard = 'border-indigo-500/30';
                        title = '🔀 Combined ML Training';
                        timeLabel = '⏱️ Multi-mode: 5-15 minutes for comprehensive analysis.';
                        badges = modes.map(m => ({ 
                            text: m === 'traditional' ? 'Traditional ML' : m === 'nlp' ? 'NLP' : 'Deep Learning' 
                        }));
                    } else if (isNlpOnly) {
                        // NLP only mode
                        gradientClass = 'bg-gradient-to-r from-blue-400 via-cyan-400 to-teal-400';
                        bgGlow = 'bg-blue-500/20';
                        borderOuter = 'border-t-blue-400 border-r-blue-400/50 border-b-blue-400/20 border-l-blue-400/50';
                        borderInner = 'border-b-cyan-400 border-l-cyan-400/50 border-t-cyan-400/20 border-r-cyan-400/50';
                        badgeBg = 'bg-blue-500/20 text-blue-300';
                        borderCard = 'border-blue-500/30';
                        title = '📝 NLP Training';
                        timeLabel = '⏱️ NLP mode: 2-5 minutes for text classification.';
                        badges = [{ text: 'TF-IDF/BOW' }, { text: 'Word Embeddings' }, { text: 'Text Classification' }];
                    } else if (isDlOnly) {
                        // Deep Learning only mode
                        gradientClass = 'bg-gradient-to-r from-red-400 via-orange-400 to-amber-400';
                        bgGlow = 'bg-red-500/20';
                        borderOuter = 'border-t-red-400 border-r-red-400/50 border-b-red-400/20 border-l-red-400/50';
                        borderInner = 'border-b-orange-400 border-l-orange-400/50 border-t-orange-400/20 border-r-orange-400/50';
                        badgeBg = 'bg-red-500/20 text-red-300';
                        borderCard = 'border-red-500/30';
                        title = '🧠 Deep Learning Training';
                        timeLabel = '⏱️ Deep Learning: 3-10 minutes for neural networks.';
                        badges = [{ text: 'Neural Networks' }, { text: 'MLP/ANN' }, { text: 'Auto Architecture' }];
                    } else if (isTraditionalOnly && !isAutoMode) {
                        // User selected SPECIFIC algorithms (not auto) - Traditional ML with custom selection
                        gradientClass = 'bg-gradient-to-r from-amber-400 via-yellow-400 to-lime-400';
                        bgGlow = 'bg-amber-500/20';
                        borderOuter = 'border-t-amber-400 border-r-amber-400/50 border-b-amber-400/20 border-l-amber-400/50';
                        borderInner = 'border-b-lime-400 border-l-lime-400/50 border-t-lime-400/20 border-r-lime-400/50';
                        badgeBg = 'bg-amber-500/20 text-amber-300';
                        borderCard = 'border-amber-500/30';
                        title = '🌲 Traditional ML Training';
                        timeLabel = `⏱️ Training ${selectedAlgorithms.traditional.length} selected algorithm(s).`;
                        badges = [{ text: `${selectedAlgorithms.traditional.length} Algorithm(s)` }, { text: 'Custom Selection' }];
                    } else if (isTraditionalOnly && isAutoMode && ultraMode) {
                        // Traditional with AUTO and ULTRA mode explicitly selected
                        gradientClass = 'bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400';
                        bgGlow = 'bg-purple-500/20';
                        borderOuter = 'border-t-purple-400 border-r-purple-400/50 border-b-purple-400/20 border-l-purple-400/50';
                        borderInner = 'border-b-pink-400 border-l-pink-400/50 border-t-pink-400/20 border-r-pink-400/50';
                        badgeBg = 'bg-purple-500/20 text-purple-300';
                        borderCard = 'border-purple-500/30';
                        title = '🎼 Ultra AutoML Training';
                        timeLabel = '⏱️ Ultra mode: 3-8 minutes for maximum accuracy.';
                        badges = [{ text: '15+ Algorithms' }, { text: 'Ensembles' }, { text: 'Auto-Tuning' }];
                    }
                    // else: Default is Fast ML Training (already set above)
                    
                    return (
                        <div
                            className="fixed inset-0 z-[100] flex items-center justify-center transition-all duration-500"
                            style={{ backgroundColor: 'var(--glass-overlay)' }}
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                animate={{ scale: 1, opacity: 1, y: 0 }}
                                className="flex flex-col items-center max-w-lg w-full p-8 text-center"
                            >
                                {/* Big Animated Icon - Mode Aware Colors */}
                                <div className="relative w-40 h-40 mb-8 flex items-center justify-center">
                                    <div className={`absolute inset-0 blur-2xl rounded-full animate-pulse ${bgGlow}`}></div>
                                    <div className={`absolute inset-0 border-4 rounded-full animate-spin ${borderOuter}`}></div>
                                    <div className={`absolute inset-4 border-4 rounded-full animate-spin ${borderInner}`} style={{ animationDirection: 'reverse', animationDuration: '3s' }}></div>
                                    <Brain className="w-16 h-16 relative z-10 animate-pulse" style={{ color: 'var(--text-primary)' }} />
                                </div>

                                {/* Title - Mode Aware */}
                                <h2 className={`text-4xl font-bold bg-clip-text text-transparent mb-4 ${gradientClass}`}>
                                    {title}
                                </h2>

                                {/* Mode Details */}
                                <div className={`flex flex-wrap items-center justify-center gap-2 mb-4 px-4 py-2 rounded-full ${badgeBg}`}>
                                    {badges.map((badge, idx) => (
                                        <React.Fragment key={idx}>
                                            {idx > 0 && <span className="opacity-50">•</span>}
                                            <span className="text-sm font-medium">{badge.text}</span>
                                        </React.Fragment>
                                    ))}
                                </div>

                                {/* Progress Card */}
                                <div
                                    className={`backdrop-blur border rounded-2xl p-6 w-full mb-8 shadow-2xl ${borderCard}`}
                                    style={{ backgroundColor: 'var(--bg-card)' }}
                                >
                                    <p className="text-xl font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                                        {progressMessage}
                                    </p>
                                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                        {timeLabel}
                                    </p>
                                </div>

                                <button
                                    onClick={handleStopTraining}
                                    className="group px-8 py-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 font-bold hover:bg-red-500/20 hover:border-red-500/50 transition-all flex items-center gap-3"
                                >
                                    <XCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
                                    STOP TRAINING
                                </button>
                            </motion.div>
                        </div>
                    );
                })()}

                {/* Header - SAME STYLE AS DATAHUB */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>ML Predictions</h1>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Train ML models on your data files</p>
                    </div>

                    {/* 🤖 ML Train Button - Shows when data files exist - SAME AS DATAHUB */}
                    {hasDataFiles && selectedFile && (
                        <div className="flex items-center gap-2 w-full md:w-auto">
                            {/* For Supervised: Show Fast/Ultra toggle ONLY when 'auto' is selected */}
                            {/* Hide when user has manually selected specific algorithms */}
                            {learningType === 'supervised' && mlType === 'traditional' &&
                                selectedAlgorithms.traditional.includes('auto') && (
                                    <div className="inline-flex p-1 rounded-xl border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }}>
                                        <button
                                            onClick={() => setUltraMode(false)}
                                            disabled={training}
                                            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${!ultraMode
                                                ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg'
                                                : ''
                                                }`}
                                            style={ultraMode ? { color: 'var(--text-muted)' } : undefined}
                                            title="Fast Mode: 10 models, ~5-10min training"
                                        >
                                            <Zap className="w-4 h-4" />
                                            Fast
                                        </button>
                                        <button
                                            onClick={() => setUltraMode(true)}
                                            disabled={training}
                                            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 ${ultraMode
                                                ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
                                                : ''
                                                }`}
                                            style={!ultraMode ? { color: 'var(--text-muted)' } : undefined}
                                            title="Ultra Mode: 25+ models with ensembles"
                                        >
                                            <Sparkles className="w-4 h-4" />
                                            Ultra
                                        </button>
                                    </div>
                                )}

                            {/* Train Button */}
                            <button
                                onClick={handleStartTraining}
                                disabled={training}
                                className={`btn-primary flex-1 md:flex-none rounded-full flex items-center justify-center gap-2 px-6 py-2.5 ${learningType === 'unsupervised'
                                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500'
                                    : mlType === 'nlp'
                                        ? 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500'
                                        : mlType === 'deep_learning'
                                            ? 'bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500'
                                            : ultraMode
                                                ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500'
                                                : 'bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500'
                                    } text-white font-medium ${training ? 'opacity-60 cursor-wait' : ''}`}
                            >
                                {training ? (
                                    <>
                                        <div className="loading-spinner" />
                                        <span className="whitespace-nowrap">
                                            {learningType === 'unsupervised' ? 'Clustering...' :
                                                mlType === 'nlp' ? 'NLP Training...' :
                                                    mlType === 'deep_learning' ? 'Deep Learning...' :
                                                        ultraMode ? 'Ultra Training...' : 'Training...'}
                                        </span>
                                    </>
                                ) : (
                                    <>
                                        {learningType === 'unsupervised' ? (
                                            <>
                                                <Boxes className="w-5 h-5" />
                                                <span className="whitespace-nowrap">🎯 Cluster</span>
                                            </>
                                        ) : mlType === 'nlp' ? (
                                            <>
                                                <FileText className="w-5 h-5" />
                                                <span className="whitespace-nowrap">📝 NLP Train</span>
                                            </>
                                        ) : mlType === 'deep_learning' ? (
                                            <>
                                                <Brain className="w-5 h-5" />
                                                <span className="whitespace-nowrap">🧠 Deep Learning</span>
                                            </>
                                        ) : (
                                            <>
                                                <Brain className="w-5 h-5" />
                                                <span className="whitespace-nowrap">{ultraMode ? '🧠 Ultra ML' : '🚀 Fast ML'}</span>
                                            </>
                                        )}
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </motion.div>

                {/* File Selection Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-xl bg-blue-500/20">
                            <Database className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Your Data Files</h2>
                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                {existingFiles.length > 0
                                    ? `${existingFiles.length} file(s) available from DataHub`
                                    : 'No files found - Upload files in DataHub first'}
                            </p>
                        </div>
                    </div>

                    {existingFiles.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {existingFiles.map((file) => (
                                <button
                                    key={file.id}
                                    onClick={() => handleSelectFile(file)}
                                    disabled={training}
                                    className="p-4 rounded-xl border text-left transition-all flex items-center gap-3 hover:border-emerald-500/50"
                                    style={{
                                        backgroundColor: selectedFile?.id === file.id
                                            ? (isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(16, 185, 129, 0.1)')
                                            : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                        borderColor: selectedFile?.id === file.id ? '#10b981' : 'var(--border-color)'
                                    }}
                                >
                                    <FileText className="w-6 h-6 flex-shrink-0" style={{ color: selectedFile?.id === file.id ? '#10b981' : 'var(--text-muted)' }} />
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>{file.name}</p>
                                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</p>
                                    </div>
                                    {selectedFile?.id === file.id && <CheckCircle className="w-5 h-5 flex-shrink-0" style={{ color: '#10b981' }} />}
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <Database className="w-12 h-12 mx-auto mb-3 opacity-50" style={{ color: 'var(--text-muted)' }} />
                            <p style={{ color: 'var(--text-muted)' }}>No data files found</p>
                            <button
                                onClick={() => navigate('/data-hub')}
                                className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                            >
                                Go to DataHub to upload files
                            </button>
                        </div>
                    )}
                </motion.div>

                {/* � Learning Type Selection - Supervised vs Unsupervised */}
                {availableColumns.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.12 }}
                        className="p-4 rounded-2xl border"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 rounded-xl bg-indigo-500/20">
                                <GitBranch className="w-5 h-5 text-indigo-400" />
                            </div>
                            <div>
                                <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                    Learning Type
                                </p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    Choose how the AI should learn from your data
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {/* Supervised Learning */}
                            <button
                                onClick={() => setLearningType('supervised')}
                                disabled={training}
                                className="p-4 rounded-xl border text-left transition-all"
                                style={{
                                    backgroundColor: learningType === 'supervised'
                                        ? (isDark ? 'rgba(34, 197, 94, 0.15)' : 'rgba(34, 197, 94, 0.1)')
                                        : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                    borderColor: learningType === 'supervised' ? '#22c55e' : 'var(--border-color)'
                                }}
                            >
                                <div className="flex items-center gap-3 mb-2">
                                    <Target className="w-6 h-6" style={{ color: learningType === 'supervised' ? '#22c55e' : 'var(--text-muted)' }} />
                                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                        Supervised Learning
                                    </span>
                                    {learningType === 'supervised' && <CheckCircle className="w-5 h-5 ml-auto" style={{ color: '#22c55e' }} />}
                                </div>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    <strong>Predict a target column</strong> - Train AI to predict outcomes like price, category, churn, fraud.
                                </p>
                                <div className="flex flex-wrap gap-1 mt-2">
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">Classification</span>
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">Regression</span>
                                </div>
                            </button>

                            {/* Unsupervised Learning */}
                            <button
                                onClick={() => setLearningType('unsupervised')}
                                disabled={training}
                                className="p-4 rounded-xl border text-left transition-all"
                                style={{
                                    backgroundColor: learningType === 'unsupervised'
                                        ? (isDark ? 'rgba(168, 85, 247, 0.15)' : 'rgba(168, 85, 247, 0.1)')
                                        : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                    borderColor: learningType === 'unsupervised' ? '#a855f7' : 'var(--border-color)'
                                }}
                            >
                                <div className="flex items-center gap-3 mb-2">
                                    <Boxes className="w-6 h-6" style={{ color: learningType === 'unsupervised' ? '#a855f7' : 'var(--text-muted)' }} />
                                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                        Unsupervised Learning
                                    </span>
                                    {learningType === 'unsupervised' && <CheckCircle className="w-5 h-5 ml-auto" style={{ color: '#a855f7' }} />}
                                </div>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    <strong>Find patterns & groups</strong> - Discover customer segments, product clusters, anomalies automatically.
                                </p>
                                <div className="flex flex-wrap gap-1 mt-2">
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400">Clustering</span>
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-pink-500/20 text-pink-400">Segmentation</span>
                                </div>
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* Supervised: ML Type Selector (Traditional/NLP/Deep Learning) */}
                {learningType === 'supervised' && availableColumns.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.12 }}
                        className="p-4 rounded-2xl border"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20">
                                    <Brain className="w-5 h-5 text-green-400" />
                                </div>
                                <div>
                                    <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                        🤖 Select ML Modes (Multi-Select)
                                    </p>
                                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                        Combine modes for hybrid predictions • Click to toggle
                                    </p>
                                </div>
                            </div>
                            <div className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400">
                                {selectedModes.size} mode{selectedModes.size > 1 ? 's' : ''} selected
                            </div>
                        </div>

                        {/* ML Mode Cards - Multi-Select */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                            {/* Traditional ML */}
                            <button
                                onClick={() => toggleMode('traditional')}
                                disabled={training}
                                className="p-4 rounded-xl border text-left transition-all relative"
                                style={{
                                    backgroundColor: selectedModes.has('traditional')
                                        ? (isDark ? 'rgba(34, 197, 94, 0.15)' : 'rgba(34, 197, 94, 0.1)')
                                        : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                    borderColor: selectedModes.has('traditional') ? '#22c55e' : 'var(--border-color)'
                                }}
                            >
                                {selectedModes.has('traditional') && (
                                    <div className="absolute top-2 right-2">
                                        <CheckCircle className="w-5 h-5 text-green-500" />
                                    </div>
                                )}
                                <div className="flex items-center gap-2 mb-2">
                                    <BarChart3 className="w-5 h-5" style={{ color: selectedModes.has('traditional') ? '#22c55e' : 'var(--text-muted)' }} />
                                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Traditional ML</span>
                                </div>
                                <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                                    {algorithmOptions.traditional.length - 1} algorithms: RF, XGBoost, SVM...
                                </p>
                                <div className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400 inline-block">
                                    {selectedAlgorithms.traditional.includes('auto') ? 'Auto' : `${selectedAlgorithms.traditional.length} selected`}
                                </div>
                            </button>

                            {/* NLP */}
                            <button
                                onClick={() => toggleMode('nlp')}
                                disabled={training}
                                className="p-4 rounded-xl border text-left transition-all relative"
                                style={{
                                    backgroundColor: selectedModes.has('nlp')
                                        ? (isDark ? 'rgba(59, 130, 246, 0.15)' : 'rgba(59, 130, 246, 0.1)')
                                        : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                    borderColor: selectedModes.has('nlp') ? '#3b82f6' : 'var(--border-color)'
                                }}
                            >
                                {selectedModes.has('nlp') && (
                                    <div className="absolute top-2 right-2">
                                        <CheckCircle className="w-5 h-5 text-blue-500" />
                                    </div>
                                )}
                                <div className="flex items-center gap-2 mb-2">
                                    <FileText className="w-5 h-5" style={{ color: selectedModes.has('nlp') ? '#3b82f6' : 'var(--text-muted)' }} />
                                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>NLP</span>
                                </div>
                                <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                                    {algorithmOptions.nlp.length - 1} techniques: TF-IDF, Word2Vec...
                                </p>
                                <div className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 inline-block">
                                    {selectedAlgorithms.nlp.includes('auto') ? 'Auto' : `${selectedAlgorithms.nlp.length} selected`}
                                </div>
                            </button>

                            {/* Deep Learning */}
                            <button
                                onClick={() => toggleMode('deep_learning')}
                                disabled={training}
                                className="p-4 rounded-xl border text-left transition-all relative"
                                style={{
                                    backgroundColor: selectedModes.has('deep_learning')
                                        ? (isDark ? 'rgba(239, 68, 68, 0.15)' : 'rgba(239, 68, 68, 0.1)')
                                        : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                    borderColor: selectedModes.has('deep_learning') ? '#ef4444' : 'var(--border-color)'
                                }}
                            >
                                {selectedModes.has('deep_learning') && (
                                    <div className="absolute top-2 right-2">
                                        <CheckCircle className="w-5 h-5 text-red-500" />
                                    </div>
                                )}
                                <div className="flex items-center gap-2 mb-2">
                                    <Brain className="w-5 h-5" style={{ color: selectedModes.has('deep_learning') ? '#ef4444' : 'var(--text-muted)' }} />
                                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Deep Learning</span>
                                </div>
                                <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                                    {algorithmOptions.deep_learning.length - 1} architectures: MLP, Neural Nets...
                                </p>
                                <div className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 inline-block">
                                    {selectedAlgorithms.deep_learning.includes('auto') ? 'Auto' : `${selectedAlgorithms.deep_learning.length} selected`}
                                </div>
                            </button>
                        </div>

                        {/* Algorithm Selection for Selected Modes */}
                        {Array.from(selectedModes).map((mode) => (
                            <div key={mode} className="mb-4 p-3 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: isDark ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.02)' }}>
                                <div className="flex items-center justify-between mb-3">
                                    <span className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                                        {mode === 'traditional' ? '🌲 Traditional ML Algorithms' :
                                            mode === 'nlp' ? '📝 NLP Techniques' : '🧠 Deep Learning Architectures'}
                                    </span>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setSelectedAlgorithms(prev => ({ ...prev, [mode]: ['auto'] }))}
                                            className={`text-xs px-2 py-1 rounded ${selectedAlgorithms[mode].includes('auto') ? 'bg-green-500 text-white' : 'bg-gray-500/20'}`}
                                            style={{ color: selectedAlgorithms[mode].includes('auto') ? '#fff' : 'var(--text-muted)' }}
                                        >
                                            🚀 Auto
                                        </button>
                                        <button
                                            onClick={() => selectAllAlgorithms(mode)}
                                            className="text-xs px-2 py-1 rounded bg-gray-500/20"
                                            style={{ color: 'var(--text-muted)' }}
                                        >
                                            Select All
                                        </button>
                                    </div>
                                </div>

                                {/* Algorithm Grid */}
                                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2 max-h-48 overflow-y-auto">
                                    {algorithmOptions[mode].filter(a => a.value !== 'auto').map((algo) => {
                                        const isSelected = selectedAlgorithms[mode].includes(algo.value);
                                        return (
                                            <button
                                                key={algo.value}
                                                onClick={() => toggleAlgorithm(mode, algo.value)}
                                                disabled={training}
                                                className={`p-2 rounded-lg border text-left transition-all text-xs ${isSelected ? 'border-green-500' : ''}`}
                                                style={{
                                                    backgroundColor: isSelected
                                                        ? (isDark ? 'rgba(34, 197, 94, 0.15)' : 'rgba(34, 197, 94, 0.1)')
                                                        : (isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'),
                                                    borderColor: isSelected ? '#22c55e' : 'var(--border-color)'
                                                }}
                                                title={algo.description}
                                            >
                                                <div className="flex items-center gap-1">
                                                    {isSelected && <CheckCircle className="w-3 h-3 text-green-500 flex-shrink-0" />}
                                                    <span className="truncate" style={{ color: 'var(--text-primary)' }}>{algo.label}</span>
                                                </div>
                                                <span className="text-[10px] block mt-0.5 opacity-60" style={{ color: 'var(--text-muted)' }}>
                                                    {algo.category}
                                                </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}

                        {/* Training Summary + Start Button */}
                        <div className="p-4 rounded-xl border bg-gradient-to-r from-green-500/10 to-emerald-500/10" style={{ borderColor: '#22c55e' }}>
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div>
                                    <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>📊 Training Summary</p>
                                    <div className="text-xs space-y-1" style={{ color: 'var(--text-muted)' }}>
                                        <p>• <strong>Modes:</strong> {Array.from(selectedModes).map(m =>
                                            m === 'traditional' ? '🌲 Traditional ML' :
                                                m === 'nlp' ? '📝 NLP' : '🧠 Deep Learning'
                                        ).join(', ')}</p>
                                        <p>• <strong>Target:</strong> {targetColumn}</p>
                                        {Array.from(selectedModes).map(mode => (
                                            <p key={mode}>• <strong>{mode}:</strong> {
                                                selectedAlgorithms[mode].includes('auto')
                                                    ? '🚀 Auto (best algorithms)'
                                                    : `${selectedAlgorithms[mode].length} algorithm${selectedAlgorithms[mode].length > 1 ? 's' : ''} selected`
                                            }</p>
                                        ))}
                                    </div>
                                </div>

                                {/* START TRAINING BUTTON - Prominent */}
                                <div className="flex flex-col gap-2">
                                    <button
                                        onClick={handleStartTraining}
                                        disabled={training || !targetColumn}
                                        className={`px-8 py-3 rounded-xl font-bold text-white shadow-lg transition-all transform hover:scale-105 flex items-center justify-center gap-2 ${training ? 'opacity-60 cursor-wait' : 'hover:shadow-xl'
                                            } ${selectedModes.size > 1
                                                ? 'bg-gradient-to-r from-purple-600 via-blue-600 to-green-600'
                                                : selectedModes.has('nlp')
                                                    ? 'bg-gradient-to-r from-blue-600 to-cyan-600'
                                                    : selectedModes.has('deep_learning')
                                                        ? 'bg-gradient-to-r from-red-600 to-orange-600'
                                                        : 'bg-gradient-to-r from-green-600 to-emerald-600'
                                            }`}
                                    >
                                        {training ? (
                                            <>
                                                <div className="loading-spinner" />
                                                <span>Training {selectedModes.size} Mode{selectedModes.size > 1 ? 's' : ''}...</span>
                                            </>
                                        ) : (
                                            <>
                                                <Play className="w-5 h-5" />
                                                <span>🚀 Start Training</span>
                                            </>
                                        )}
                                    </button>
                                    {training && (
                                        <button
                                            onClick={handleStopTraining}
                                            className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-all flex items-center justify-center gap-2"
                                        >
                                            <Square className="w-4 h-4" />
                                            Stop Training
                                        </button>
                                    )}
                                    {!targetColumn && (
                                        <p className="text-xs text-amber-400">⚠️ Select a target column first</p>
                                    )}
                                </div>
                            </div>

                            {/* Training Progress */}
                            {training && (
                                <div className="mt-4 p-3 rounded-lg bg-black/20">
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="loading-spinner" />
                                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{progressMessage}</span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-2">
                                        <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* Unsupervised: Clustering Configuration */}
                {learningType === 'unsupervised' && availableColumns.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="p-4 rounded-2xl border"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 rounded-xl bg-purple-500/20">
                                <Boxes className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                    🎯 Clustering Configuration
                                </p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    No target column needed - AI will discover groups automatically
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Algorithm Selection */}
                            <div>
                                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                                    Algorithm
                                </label>
                                <select
                                    value={clusteringAlgorithm}
                                    onChange={(e) => setClusteringAlgorithm(e.target.value)}
                                    disabled={training}
                                    className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
                                    style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                >
                                    <option value="kmeans" style={{ backgroundColor: isDark ? '#1f2937' : '#fff', color: isDark ? '#fff' : '#000' }}>K-Means (Fast, Spherical clusters)</option>
                                    <option value="dbscan" style={{ backgroundColor: isDark ? '#1f2937' : '#fff', color: isDark ? '#fff' : '#000' }}>DBSCAN (Finds outliers)</option>
                                    <option value="hierarchical" style={{ backgroundColor: isDark ? '#1f2937' : '#fff', color: isDark ? '#fff' : '#000' }}>Hierarchical (Cluster hierarchy)</option>
                                    <option value="gmm" style={{ backgroundColor: isDark ? '#1f2937' : '#fff', color: isDark ? '#fff' : '#000' }}>Gaussian Mixture (Soft clustering)</option>
                                </select>
                            </div>

                            {/* Cluster Count */}
                            <div>
                                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                                    Number of Clusters
                                </label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="number"
                                        value={clusterCount || ''}
                                        onChange={(e) => setClusterCount(e.target.value ? parseInt(e.target.value) : null)}
                                        placeholder="Auto-detect"
                                        min={2}
                                        max={20}
                                        disabled={training}
                                        className="flex-1 p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
                                        style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                    />
                                </div>
                                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                                    Leave empty to auto-detect optimal clusters
                                </p>
                            </div>
                        </div>

                        {/* Train Clustering Button */}
                        <button
                            onClick={handleStartTraining}
                            disabled={training || !selectedFile}
                            className="mt-4 w-full px-6 py-3 rounded-xl font-medium text-white flex items-center justify-center gap-2
                                     bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500
                                     disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {training ? (
                                <>
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                    Analyzing Clusters...
                                </>
                            ) : (
                                <>
                                    <Boxes className="w-5 h-5" />
                                    Run Clustering Analysis
                                </>
                            )}
                        </button>
                    </motion.div>
                )}

                {/* 🎯 Target Column Selection - ONLY FOR SUPERVISED */}
                {learningType === 'supervised' && availableColumns.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="p-4 rounded-2xl border"
                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                    >
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2 rounded-xl bg-purple-500/20">
                                <Sparkles className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                    🎯 Target Column (What to predict)
                                </p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    Auto-detected: <span className="text-purple-400">{targetColumn}</span> • Change if needed
                                </p>
                            </div>
                        </div>

                        <select
                            value={targetColumn}
                            onChange={(e) => setTargetColumn(e.target.value)}
                            disabled={training}
                            className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
                            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                        >
                            {availableColumns.map((col) => (
                                <option key={col} value={col} style={{ backgroundColor: isDark ? '#1f2937' : '#ffffff', color: isDark ? '#ffffff' : '#000000' }}>
                                    {col}
                                </option>
                            ))}
                        </select>

                        <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                            💡 Tip: Select the column you want the model to predict (e.g., price, category, fraud)
                        </p>
                    </motion.div>
                )}

                {/* 🏥 Data Health Card - Shows before training */}
                {selectedFile && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <DataHealthCard
                            fileName={selectedFile.name}
                            targetColumn={targetColumn}
                        />
                    </motion.div>
                )}

                {/* Instructions when no file selected */}
                {!selectedFile && existingFiles.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-6"
                    >
                        <p style={{ color: 'var(--text-muted)' }}>
                            👆 Select a file above to start training
                        </p>
                    </motion.div>
                )}
            </div>
        );
    }

    // ========================================================================
    // RESULTS VIEW - Showing trained model results
    // ========================================================================

    // If only clustering result exists (no supervised result), show clustering-focused view
    if (!result && clusteringResult) {
        return (
            <div className="space-y-6">
                {/* Clustering Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                    <div className="flex items-center gap-4 w-full md:w-auto">
                        <div className="min-w-0">
                            <h1 className="text-2xl font-bold flex items-center gap-3 truncate" style={{ color: 'var(--text-primary)' }}>
                                <Boxes className="w-8 h-8 flex-shrink-0 text-purple-400" />
                                <span className="truncate">Clustering Results</span>
                            </h1>
                            <p className="text-sm truncate" style={{ color: 'var(--text-muted)' }}>
                                Algorithm: <span className="font-medium text-purple-400">{clusteringResult.algorithm?.toUpperCase()}</span>
                                {' • '}
                                Found: <span className="text-blue-400 font-medium">{clusteringResult.n_clusters} clusters</span>
                                {' • '}
                                Silhouette: <span className="text-amber-400 font-medium">{(clusteringResult.silhouette_score * 100).toFixed(1)}%</span>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => {
                            setClusteringResult(null);
                            loadExistingFiles();
                        }}
                        className="w-full md:w-auto px-4 py-2 rounded-xl border transition-colors flex items-center justify-center gap-2"
                        style={{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}
                    >
                        <RefreshCw className="w-4 h-4" />
                        <span>New Analysis</span>
                    </button>
                </motion.div>

                {/* Clustering Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                        className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-purple-500/20"><Boxes className="w-4 h-4 text-purple-400" /></div>
                            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Clusters</span>
                        </div>
                        <p className="text-2xl font-bold text-purple-400">{clusteringResult.n_clusters}</p>
                    </motion.div>
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}
                        className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-blue-500/20"><TrendingUp className="w-4 h-4 text-blue-400" /></div>
                            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Silhouette Score</span>
                        </div>
                        <p className="text-2xl font-bold" style={{ color: clusteringResult.silhouette_score >= 0.5 ? '#22c55e' : clusteringResult.silhouette_score >= 0.25 ? '#f59e0b' : '#ef4444' }}>
                            {(clusteringResult.silhouette_score * 100).toFixed(1)}%
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                            {clusteringResult.silhouette_score >= 0.5 ? 'Good' : clusteringResult.silhouette_score >= 0.25 ? 'Moderate' : 'Weak'}
                        </p>
                    </motion.div>
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.14 }}
                        className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-emerald-500/20"><Sparkles className="w-4 h-4 text-emerald-400" /></div>
                            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Algorithm</span>
                        </div>
                        <p className="text-lg font-bold text-emerald-400">{clusteringResult.algorithm?.toUpperCase()}</p>
                    </motion.div>
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }}
                        className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-amber-500/20"><Database className="w-4 h-4 text-amber-400" /></div>
                            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Samples</span>
                        </div>
                        <p className="text-2xl font-bold text-amber-400">{clusteringResult.n_samples?.toLocaleString() || 'N/A'}</p>
                    </motion.div>
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }}
                        className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-cyan-500/20"><Activity className="w-4 h-4 text-cyan-400" /></div>
                            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Features</span>
                        </div>
                        <p className="text-2xl font-bold text-cyan-400">{clusteringResult.n_features || clusteringResult.feature_columns?.length || 'N/A'}</p>
                    </motion.div>
                    {clusteringResult.calinski_harabasz_score && (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                            className="p-4 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <div className="flex items-center gap-2 mb-2">
                                <div className="p-1.5 rounded-lg bg-rose-500/20"><Target className="w-4 h-4 text-rose-400" /></div>
                                <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Calinski-Harabasz</span>
                            </div>
                            <p className="text-xl font-bold text-rose-400">{clusteringResult.calinski_harabasz_score.toFixed(1)}</p>
                            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Higher = better</p>
                        </motion.div>
                    )}
                </div>

                {/* TABS - Like Supervised */}
                <div className="overflow-x-auto no-scrollbar pb-2 md:pb-0">
                    <div className="flex gap-2 p-1.5 rounded-xl min-w-max md:min-w-0 border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        {[
                            { id: 'overview', label: 'Overview', icon: PieChart },
                            { id: 'charts', label: 'Visualization', icon: BarChart3 },
                            { id: 'profiles', label: 'Cluster Profiles', icon: Activity },
                            { id: 'predict', label: 'Predict Cluster', icon: Play },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setClusterActiveTab(tab.id as any)}
                                className={`flex-1 flex flex-shrink-0 items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${clusterActiveTab === tab.id
                                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                                    : ''}`}
                                style={clusterActiveTab !== tab.id ? { color: 'var(--text-muted)' } : undefined}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tab Content */}
                <motion.div key={clusterActiveTab} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>

                    {/* OVERVIEW TAB */}
                    {clusterActiveTab === 'overview' && (
                        <div className="space-y-6">
                            {/* Cluster Distribution */}
                            <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                    <BarChart3 className="w-5 h-5 text-purple-400" /> Cluster Distribution
                                </h3>
                                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                                    {clusteringResult.cluster_distribution && Object.entries(clusteringResult.cluster_distribution).map(([cluster, count], i) => {
                                        const total = Object.values(clusteringResult.cluster_distribution as Record<string, number>).reduce((a: number, b: number) => a + b, 0);
                                        const percentage = ((count as number) / total * 100).toFixed(1);
                                        return (
                                            <div key={cluster} className="p-4 rounded-xl text-center border" style={{ borderColor: 'var(--border-color)', backgroundColor: isDark ? 'rgba(168, 85, 247, 0.1)' : 'rgba(168, 85, 247, 0.05)' }}>
                                                <p className="text-2xl font-bold text-purple-400">{count as number}</p>
                                                <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>{cluster}</p>
                                                <div className="w-full bg-gray-700/30 rounded-full h-2 mt-2">
                                                    <div className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500" style={{ width: `${percentage}%` }} />
                                                </div>
                                                <p className="text-xs mt-1 text-purple-400">{percentage}%</p>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Insights */}
                            {clusteringResult.insights && clusteringResult.insights.length > 0 && (
                                <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                        <Sparkles className="w-5 h-5 text-amber-400" /> AI Insights
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {clusteringResult.insights.map((insight: string, i: number) => (
                                            <div key={i} className="flex items-start gap-3 p-3 rounded-lg" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                                <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                                                <span style={{ color: 'var(--text-muted)' }}>{insight}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* CHARTS TAB - Full Clustering Visualizations */}
                    {clusterActiveTab === 'charts' && (
                        <div className="space-y-6">
                            {/* Charts Grid */}
                            {clusteringResult.charts && Object.keys(clusteringResult.charts).length > 0 ? (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    {/* Cluster Scatter Plot */}
                                    {clusteringResult.charts.cluster_scatter && (
                                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <Activity className="w-5 h-5 text-blue-400" /> Cluster Scatter Plot (PCA 2D)
                                            </h3>
                                            <img src={clusteringResult.charts.cluster_scatter} alt="Cluster scatter plot" className="w-full rounded-lg" />
                                            {clusteringResult.pca_variance_explained && (
                                                <p className="text-center mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                                                    PCA captures {(clusteringResult.pca_variance_explained * 100).toFixed(1)}% of data variance
                                                </p>
                                            )}
                                        </div>
                                    )}

                                    {/* Elbow Method */}
                                    {clusteringResult.charts.elbow_method && (
                                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <TrendingUp className="w-5 h-5 text-amber-400" /> Elbow Method
                                            </h3>
                                            <img src={clusteringResult.charts.elbow_method} alt="Elbow method chart" className="w-full rounded-lg" />
                                            <p className="text-center mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                                                Find optimal k where the curve bends (elbow point)
                                            </p>
                                        </div>
                                    )}

                                    {/* Silhouette Comparison */}
                                    {clusteringResult.charts.silhouette_comparison && (
                                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <BarChart3 className="w-5 h-5 text-emerald-400" /> Silhouette Score Analysis
                                            </h3>
                                            <img src={clusteringResult.charts.silhouette_comparison} alt="Silhouette comparison" className="w-full rounded-lg" />
                                            <p className="text-center mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                                                Higher silhouette = better cluster separation
                                            </p>
                                        </div>
                                    )}

                                    {/* Cluster Distribution */}
                                    {clusteringResult.charts.cluster_distribution && (
                                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <PieChart className="w-5 h-5 text-purple-400" /> Cluster Distribution
                                            </h3>
                                            <img src={clusteringResult.charts.cluster_distribution} alt="Cluster distribution" className="w-full rounded-lg" />
                                        </div>
                                    )}

                                    {/* Silhouette Plot */}
                                    {clusteringResult.charts.silhouette_plot && (
                                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <Activity className="w-5 h-5 text-cyan-400" /> Silhouette Plot
                                            </h3>
                                            <img src={clusteringResult.charts.silhouette_plot} alt="Silhouette plot" className="w-full rounded-lg" />
                                            <p className="text-center mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                                                Per-sample silhouette coefficients by cluster
                                            </p>
                                        </div>
                                    )}

                                    {/* Dendrogram (Hierarchical only) */}
                                    {clusteringResult.charts.dendrogram && (
                                        <div className="p-6 rounded-2xl border lg:col-span-2" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <GitBranch className="w-5 h-5 text-rose-400" /> Dendrogram (Hierarchical Tree)
                                            </h3>
                                            <img src={clusteringResult.charts.dendrogram} alt="Dendrogram" className="w-full rounded-lg" />
                                            <p className="text-center mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                                                Hierarchical relationships between clusters
                                            </p>
                                        </div>
                                    )}

                                    {/* Feature Importance */}
                                    {clusteringResult.charts.feature_importance && (
                                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                                <Sparkles className="w-5 h-5 text-orange-400" /> Feature Importance
                                            </h3>
                                            <img src={clusteringResult.charts.feature_importance} alt="Feature importance" className="w-full rounded-lg" />
                                            <p className="text-center mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                                                Features most important for cluster separation
                                            </p>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="p-12 text-center rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                    <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" style={{ color: 'var(--text-muted)' }} />
                                    <p style={{ color: 'var(--text-muted)' }}>No charts available. Re-run clustering to generate visualizations.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* PROFILES TAB */}
                    {clusterActiveTab === 'profiles' && (
                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Activity className="w-5 h-5 text-emerald-400" /> Cluster Profiles
                            </h3>
                            {clusteringResult.cluster_profiles ? (
                                <div className="space-y-4">
                                    {Object.entries(clusteringResult.cluster_profiles).map(([clusterName, profile]: [string, any]) => (
                                        <div key={clusterName} className="p-4 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.01)' }}>
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="font-semibold text-purple-400">{clusterName}</h4>
                                                <span className="text-sm px-2 py-1 rounded-full bg-purple-500/20 text-purple-400">
                                                    {profile.size} samples ({profile.percentage?.toFixed(1)}%)
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                                {profile.characteristics && Object.entries(profile.characteristics).slice(0, 8).map(([feature, stats]: [string, any]) => (
                                                    <div key={feature} className="p-2 rounded-lg text-center" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                                        <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{feature}</p>
                                                        <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>μ = {stats.mean?.toFixed(2)}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p style={{ color: 'var(--text-muted)' }}>Cluster profiles not available. Re-run clustering to generate profiles.</p>
                            )}
                        </div>
                    )}

                    {/* PREDICT TAB */}
                    {clusterActiveTab === 'predict' && (
                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Play className="w-5 h-5 text-purple-400" /> Predict Cluster for New Data
                            </h3>
                            <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
                                Enter feature values to predict which cluster a new data point belongs to
                            </p>

                            {clusteringResult.feature_columns ? (
                                <>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                                        {clusteringResult.feature_columns.map((feature: string) => {
                                            const stats = clusteringResult.feature_stats?.[feature];
                                            return (
                                                <div key={feature}>
                                                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                                                        {feature}
                                                        {stats && <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>({stats.type})</span>}
                                                    </label>
                                                    {stats?.type === 'categorical' && stats.categories ? (
                                                        <select
                                                            value={clusterPredictionInput[feature] || ''}
                                                            onChange={(e) => setClusterPredictionInput(prev => ({ ...prev, [feature]: e.target.value }))}
                                                            className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
                                                            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                                        >
                                                            {stats.categories.map((cat: string, idx: number) => (
                                                                <option key={cat} value={idx} style={{ backgroundColor: isDark ? '#1f2937' : '#fff', color: isDark ? '#fff' : '#000' }}>
                                                                    {cat}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    ) : (
                                                        <input
                                                            type="number"
                                                            value={clusterPredictionInput[feature] || ''}
                                                            onChange={(e) => setClusterPredictionInput(prev => ({ ...prev, [feature]: e.target.value }))}
                                                            placeholder={stats ? `Range: ${stats.min?.toFixed(1)} - ${stats.max?.toFixed(1)}` : 'Enter value'}
                                                            className="w-full p-3 rounded-xl border bg-transparent outline-none focus:border-purple-500 transition-all"
                                                            style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                                                        />
                                                    )}
                                                    {stats && <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Mean: {stats.mean?.toFixed(2)}</p>}
                                                </div>
                                            );
                                        })}
                                    </div>

                                    <button
                                        onClick={handlePredictCluster}
                                        disabled={clusterPredicting}
                                        className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-medium hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 transition-all flex items-center gap-2"
                                    >
                                        {clusterPredicting ? (
                                            <><RefreshCw className="w-5 h-5 animate-spin" /> Predicting...</>
                                        ) : (
                                            <><Play className="w-5 h-5" /> Get Cluster Prediction</>
                                        )}
                                    </button>

                                    {/* Prediction Result */}
                                    {clusterPredictionResult && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="mt-6 p-6 rounded-xl border-2 border-purple-500/50"
                                            style={{ backgroundColor: isDark ? 'rgba(168, 85, 247, 0.1)' : 'rgba(168, 85, 247, 0.05)' }}
                                        >
                                            <p className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>Predicted Cluster</p>
                                            <p className="text-4xl font-bold text-purple-400 mb-2">{clusterPredictionResult.cluster_name}</p>
                                            {clusterPredictionResult.confidence && (
                                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                                    Confidence: <span className="text-purple-400 font-medium">{(clusterPredictionResult.confidence * 100).toFixed(1)}%</span>
                                                </p>
                                            )}
                                            {clusterPredictionResult.cluster_description && (
                                                <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>{clusterPredictionResult.cluster_description}</p>
                                            )}
                                        </motion.div>
                                    )}
                                </>
                            ) : (
                                <div className="text-center py-8">
                                    <p style={{ color: 'var(--text-muted)' }}>Feature information not available. Please re-run clustering.</p>
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>
            </div>
        );
    }

    // Supervised results view - original code
    // At this point, result must exist (we've handled null cases above)
    if (!result) {
        return null; // TypeScript guard - this shouldn't happen
    }
    const metrics = result.best_model?.metrics || {};
    let bestMetric: [string, number] = ['accuracy', 0];

    if (metrics.accuracy !== undefined) {
        bestMetric = ['accuracy', metrics.accuracy];
    } else if (metrics.f1 !== undefined) {
        bestMetric = ['f1', metrics.f1];
    } else if (metrics.r2 !== undefined) {
        bestMetric = ['r2', metrics.r2];
    } else {
        const entries = Object.entries(metrics);
        if (entries.length > 0) {
            bestMetric = entries[0] as [string, number];
        }
    }

    const rankedFeatures = (result.feature_importance && result.feature_importance.length > 0)
        ? result.feature_importance
        : (result.feature_columns || []).map((f, i) => ({
            feature: f,
            importance: 1 / (result.feature_columns?.length || 1),
            rank: i + 1
        }));

    // Determine if this is an NLP-trained model (either single NLP or NLP in multi-mode)
    const isNlpMode = result.mode === 'nlp' || 
        (result as any).modes_trained?.includes('nlp') ||
        (result as any).results_per_mode?.nlp?.success ||
        result.best_model?.name?.toLowerCase().includes('vectorizer') ||
        result.best_model?.name?.toLowerCase().includes('tfidf');
    
    // Get text column for NLP mode
    const nlpTextColumn = (result as any).results_per_mode?.nlp?.text_column ||
        (result as any).primary_text_col ||
        null;

    // Build inputFeatures with proper NLP support
    let inputFeatures: FeatureMetadata[] = (result.feature_metadata && result.feature_metadata.length > 0)
        ? result.feature_metadata
        : rankedFeatures.map(f => ({
            name: f.feature,
            type: 'numeric' as const,
            min: 0,
            max: 100,
            mean: 50,
            options: undefined as string[] | undefined,
            placeholder: undefined as string | undefined
        }));

    // If NLP mode and no text input in feature_metadata, add the text column
    if (isNlpMode && nlpTextColumn && !inputFeatures.some(f => f.name === nlpTextColumn)) {
        inputFeatures = [{
            name: nlpTextColumn,
            type: 'text',
            placeholder: `Enter ${nlpTextColumn} for NLP prediction...`
        }, ...inputFeatures.filter(f => f.name !== nlpTextColumn)];
    }
    
    // If NLP mode and feature_metadata is empty, create text input
    if (isNlpMode && inputFeatures.length === 0 && nlpTextColumn) {
        inputFeatures = [{
            name: nlpTextColumn,
            type: 'text',
            placeholder: `Enter ${nlpTextColumn} for NLP prediction...`
        }];
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
                <div className="flex items-center gap-4 w-full md:w-auto">
                    <div className="min-w-0">
                        <h1 className="text-2xl font-bold flex items-center gap-3 truncate" style={{ color: 'var(--text-primary)' }}>
                            <Brain className="w-8 h-8 flex-shrink-0" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                            <span className="truncate">ML Predictions</span>
                        </h1>
                        <p className="text-sm truncate" style={{ color: 'var(--text-muted)' }}>
                            Target: <span className="font-medium" style={{ color: isDark ? '#4ade80' : '#16a34a' }}>{result.target_column}</span>
                            {' • '}
                            Task: <span className="text-blue-400 font-medium">{result.task_type}</span>
                            {' • '}
                            <span className="text-amber-400 font-medium">{result.processing_time_seconds?.toFixed(1)}s</span>
                        </p>
                    </div>
                </div>
                <button
                    onClick={() => {
                        setResult(null);
                        loadExistingFiles();
                    }}
                    className="w-full md:w-auto px-4 py-2 rounded-xl border transition-colors flex items-center justify-center gap-2"
                    style={{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}
                >
                    <RefreshCw className="w-4 h-4" />
                    <span>New Training</span>
                </button>
            </motion.div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-primary-500/20">
                            <Award className="w-5 h-5" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Best Model</span>
                    </div>
                    <p className="text-2xl font-bold text-primary-500">{result.best_model.name}</p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Target className="w-5 h-5 text-blue-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>{bestMetric[0]?.toUpperCase()}</span>
                    </div>
                    <p className="text-2xl font-bold" style={{ color: getMetricColor(bestMetric[1] as number) }}>
                        {((bestMetric[1] as number) * 100).toFixed(1)}%
                    </p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-emerald-500/20">
                            <Layers className="w-5 h-5 text-emerald-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Models Trained</span>
                    </div>
                    <p className="text-2xl font-bold text-emerald-400">{result.all_models?.length || 0}</p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                    className="p-6 rounded-2xl border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-amber-500/20">
                            <Sparkles className="w-5 h-5 text-amber-400" />
                        </div>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Columns</span>
                    </div>
                    <p className="text-2xl font-bold text-amber-400">{result.data_summary?.columns || result.feature_importance?.length || 0}</p>
                </motion.div>
            </div>

            {/* Tabs - SUPERVISED ONLY (no clustering tab) */}
            <div className="overflow-x-auto no-scrollbar pb-2 md:pb-0">
                <div
                    className="flex gap-2 p-1.5 rounded-xl min-w-max md:min-w-0 border"
                    style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                >
                    {[
                        { id: 'overview', label: 'Overview', icon: PieChart },
                        { id: 'charts', label: 'ML Charts', icon: BarChart3 },
                        { id: 'features', label: 'Features', icon: TrendingUp },
                        { id: 'predict', label: 'Predict', icon: Play },
                        { id: 'playground', label: 'Playground', icon: Sliders },
                        { id: 'history', label: 'History', icon: History },
                        { id: 'data', label: 'Data', icon: Database },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex-1 flex flex-shrink-0 items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                                ? 'bg-gradient-to-r from-primary-500 to-emerald-500 text-white shadow-lg'
                                : ''
                                }`}
                            style={activeTab !== tab.id ? { color: 'var(--text-muted)' } : undefined}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab Content */}
            <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                {activeTab === 'overview' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Multi-Mode Results (if applicable) */}
                        {result.results_per_mode && Object.keys(result.results_per_mode).length > 1 && (
                            <div className="lg:col-span-2 p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                    <Layers className="w-5 h-5 text-purple-400" />
                                    Multi-Mode Training Results
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {Object.entries(result.results_per_mode).map(([mode, modeResult]: [string, any]) => {
                                        const modeColors: Record<string, string> = {
                                            'traditional': '#22c55e',
                                            'nlp': '#3b82f6',
                                            'deep_learning': '#ef4444'
                                        };
                                        const modeIcons: Record<string, string> = {
                                            'traditional': '🌲',
                                            'nlp': '📝',
                                            'deep_learning': '🧠'
                                        };
                                        const modeLabels: Record<string, string> = {
                                            'traditional': 'Traditional ML',
                                            'nlp': 'NLP',
                                            'deep_learning': 'Deep Learning'
                                        };
                                        const acc = modeResult.metrics?.accuracy || modeResult.metrics?.r2 || 0;
                                        const isBest = result.best_overall?.mode === mode;

                                        return (
                                            <div
                                                key={mode}
                                                className={`p-4 rounded-xl border ${isBest ? 'ring-2' : ''}`}
                                                style={{
                                                    borderColor: modeColors[mode],
                                                    backgroundColor: isDark ? `${modeColors[mode]}15` : `${modeColors[mode]}10`,
                                                    ['--tw-ring-color' as any]: isBest ? modeColors[mode] : undefined
                                                }}
                                            >
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="font-semibold flex items-center gap-2" style={{ color: modeColors[mode] }}>
                                                        {modeIcons[mode]} {modeLabels[mode]}
                                                    </span>
                                                    {isBest && (
                                                        <span className="text-xs px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: modeColors[mode] }}>
                                                            BEST
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="text-sm mb-1" style={{ color: 'var(--text-muted)' }}>
                                                    Model: <strong style={{ color: 'var(--text-primary)' }}>{modeResult.best_model || modeResult.algorithm || modeResult.architecture || 'N/A'}</strong>
                                                </p>
                                                <p className="text-2xl font-bold" style={{ color: modeColors[mode] }}>
                                                    {modeResult.success ? `${(acc * 100).toFixed(1)}%` : '❌ Failed'}
                                                </p>
                                                {modeResult.error && (
                                                    <p className="text-xs text-red-400 mt-1">{modeResult.error}</p>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* All Models */}
                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Activity className="w-5 h-5 text-blue-400" />
                                All Models Performance
                            </h3>
                            <div className="space-y-3">
                                {/* Show leaderboard if available (multi-mode), otherwise all_models */}
                                {((result.leaderboard && result.leaderboard.length > 0) ? result.leaderboard : result.all_models)?.slice(0, 8).map((model: any, i: number) => {
                                    const mainMetric = model.score || Object.values(model.metrics || {})[0] || 0;
                                    const modelName = model.model || model.name;
                                    const modeLabel = model.mode ? `[${model.mode}]` : '';
                                    const isBest = modelName === (result.best_overall?.name || result.best_model?.name);
                                    return (
                                        <div key={i} className="flex items-center gap-3">
                                            <span className="w-28 text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }} title={modelName}>
                                                {modeLabel} {modelName}
                                            </span>
                                            <div className="flex-1 rounded-full h-3" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}>
                                                <div
                                                    className={`h-3 rounded-full ${isBest ? 'bg-gradient-to-r from-primary-500 to-emerald-500' : 'bg-blue-500'}`}
                                                    style={{ width: `${mainMetric * 100}%` }}
                                                />
                                            </div>
                                            <span className="w-16 text-sm font-bold text-right" style={{ color: 'var(--text-primary)' }}>
                                                {(mainMetric * 100).toFixed(1)}%
                                            </span>
                                            {isBest && (
                                                <span className="text-xs px-2 py-0.5 bg-primary-500 text-white rounded">BEST</span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Insights */}
                        <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Sparkles className="w-5 h-5 text-amber-400" />
                                AI Insights
                            </h3>
                            <div className="space-y-3">
                                {result.insights?.slice(0, 5).map((insight, i) => (
                                    <div
                                        key={i}
                                        className="p-4 rounded-xl border-l-4 border-l-green-500"
                                        style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                    >
                                        <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{insight}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'playground' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                            <Sliders className="w-5 h-5 text-violet-400" />
                            Interactive Prediction Playground
                        </h3>
                        <PlaygroundTab
                            mode={(() => {
                                // For multi-mode training, use the best mode from result
                                // or 'auto' to let backend detect
                                if (result?.mode) return result.mode as 'traditional' | 'nlp' | 'deep_learning';
                                if ((result as any)?.best_overall?.mode) return (result as any).best_overall.mode;
                                // Check modes_trained for multi-mode
                                const modesTrained = (result as any)?.modes_trained as string[] | undefined;
                                if (modesTrained && modesTrained.length > 0) {
                                    // Return first trained mode, preferring traditional > nlp > deep_learning
                                    if (modesTrained.includes('traditional')) return 'traditional';
                                    if (modesTrained.includes('nlp')) return 'nlp';
                                    if (modesTrained.includes('deep_learning')) return 'deep_learning';
                                }
                                // Fallback to 'auto' to let backend auto-detect
                                return 'auto' as any;
                            })()}
                            onPredictionMade={(pred) => {
                                setPredictionResult(pred);
                                setExplainInputValues(pred.input_values || {});
                            }}
                        />
                    </div>
                )}

                {activeTab === 'charts' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {chartsLoading && (
                            <div className="col-span-2 text-center p-12 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                <RefreshCw className="w-16 h-16 mx-auto mb-4 animate-spin" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                                <p className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Loading Charts...</p>
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Fetching ML visualizations from server</p>
                            </div>
                        )}

                        {/* Filter out clustering-specific charts from supervised view */}
                        {!chartsLoading && result.charts && Object.entries(result.charts)
                            .filter(([chartName]) => !['cluster_scatter', 'elbow_method', 'silhouette_comparison',
                                'silhouette_plot', 'dendrogram', 'cluster_distribution'].includes(chartName))
                            .map(([chartName, chartBase64]) => {
                                // Format chart name: remove prefix and add mode label
                                let displayName = chartName;
                                let modeLabel = '';
                                if (chartName.startsWith('ml_')) {
                                    displayName = chartName.slice(3);
                                    modeLabel = 'Traditional ML';
                                } else if (chartName.startsWith('nlp_')) {
                                    displayName = chartName.slice(4);
                                    modeLabel = 'NLP';
                                } else if (chartName.startsWith('dl_')) {
                                    displayName = chartName.slice(3);
                                    modeLabel = 'Deep Learning';
                                }
                                const formattedName = displayName.replace(/_/g, ' ');

                                return (
                                    <div
                                        key={chartName}
                                        className="rounded-2xl border overflow-hidden transition-all hover:shadow-lg"
                                        style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                                    >
                                        <div className="flex items-center gap-3 px-5 py-4 border-b" style={{ borderColor: 'var(--border-color)' }}>
                                            <div className="p-2 rounded-lg bg-gradient-to-r from-primary-500/20 to-emerald-500/20">
                                                <BarChart3 className="w-4 h-4" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="text-base font-semibold capitalize" style={{ color: 'var(--text-primary)' }}>
                                                    {formattedName}
                                                </h3>
                                                {modeLabel && (
                                                    <span className="text-xs px-2 py-0.5 rounded-full"
                                                        style={{
                                                            backgroundColor: modeLabel === 'NLP' ? 'rgba(59, 130, 246, 0.2)' :
                                                                modeLabel === 'Deep Learning' ? 'rgba(239, 68, 68, 0.2)' :
                                                                    'rgba(34, 197, 94, 0.2)',
                                                            color: modeLabel === 'NLP' ? '#3b82f6' :
                                                                modeLabel === 'Deep Learning' ? '#ef4444' : '#22c55e'
                                                        }}>
                                                        {modeLabel}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="p-4" style={{ backgroundColor: isDark ? '#0f172a' : '#f8fafc' }}>
                                            <img src={chartBase64} alt={chartName} className="w-full rounded-lg" style={{ maxHeight: '350px', objectFit: 'contain' }} />
                                        </div>
                                    </div>
                                );
                            })}

                        {!chartsLoading && (!result.charts || Object.keys(result.charts).length === 0) && (
                            <div className="col-span-2 text-center p-12 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                                <BarChart3 className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
                                <p className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>No Charts Available</p>
                                <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>Charts may not have been generated during training.</p>
                                <button
                                    onClick={async () => {
                                        const userId = getUserIdSync();
                                        setChartsLoading(true);
                                        const charts = await fetchChartsFromAPI(userId);
                                        if (Object.keys(charts).length > 0) {
                                            setResult(prev => prev ? { ...prev, charts } : prev);
                                        }
                                        setChartsLoading(false);
                                    }}
                                    className="px-4 py-2 rounded-lg bg-primary-500 text-white hover:bg-primary-600 transition-colors flex items-center gap-2 mx-auto"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Refresh Charts
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'features' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h3 className="text-lg font-semibold mb-6 flex items-center justify-between" style={{ color: 'var(--text-primary)' }}>
                            <span>Feature Importance Ranking</span>
                            <span className="text-sm font-normal px-3 py-1 rounded-full bg-primary-500/20" style={{ color: isDark ? '#4ade80' : '#16a34a' }}>
                                {rankedFeatures.length} features
                            </span>
                        </h3>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                            {rankedFeatures.map((f, i) => (
                                <div
                                    key={i}
                                    className="flex items-center gap-4 p-3 rounded-xl"
                                    style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
                                >
                                    <span className="w-8 h-8 rounded-lg bg-gradient-to-r from-primary-500 to-emerald-500 flex items-center justify-center text-white font-bold">
                                        {f.rank || i + 1}
                                    </span>
                                    <div className="flex-1">
                                        <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{f.feature}</span>
                                        <div className="w-full rounded-full h-2 mt-1" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}>
                                            <div className="h-2 rounded-full bg-gradient-to-r from-primary-500 to-emerald-500" style={{ width: `${f.importance * 100}%` }} />
                                        </div>
                                    </div>
                                    <span className="font-bold" style={{ color: isDark ? '#4ade80' : '#16a34a' }}>{(f.importance * 100).toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'predict' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h3 className="text-lg font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>
                            Make a Prediction with {result.best_model.name}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                            {inputFeatures
                                // Filter out ID/index columns that shouldn't be user inputs
                                .filter((meta) => {
                                    const name = meta.name.toLowerCase();
                                    // Skip unnamed columns, index columns, and ID columns
                                    if (name.startsWith('unnamed') || name === 'index' || name === '_id') return false;
                                    // Skip pure ID columns (but keep columns like 'movie_id_rating' that might be useful)
                                    if (name === 'id') return false;
                                    return true;
                                })
                                .map((meta) => {
                                    const featureName = meta.name;
                                    const lowerName = featureName.toLowerCase();

                                    // First check if it's a text column by heuristics (PRIORITY over backend type)
                                    const textKeywords = ['text', 'content', 'body', 'email', 'review', 'description',
                                        'summary', 'message', 'overview', 'title', 'name', 'comment', 'note', 'bio',
                                        'abstract', 'story', 'plot', 'tagline', 'headline'];
                                    const isHeuristicText = textKeywords.some(kw => lowerName.includes(kw));
                                    const isExplicitText = meta.type === 'text';
                                    const isNlpTask = (result as any).is_nlp_task && (result as any).primary_text_col === featureName;

                                    // Text if: explicitly marked OR heuristic match OR NLP task primary column
                                    const isText = isExplicitText || isHeuristicText || isNlpTask;

                                    // Check for datetime type
                                    const isDatetime = meta.type === 'datetime';

                                    // Only numeric if NOT a text column and NOT datetime
                                    const isNumeric = !isText && !isDatetime && meta.type === 'numeric';
                                    const isCategorical = !isText && !isNumeric && !isDatetime && (meta.type === 'categorical' || (meta.options && meta.options.length > 0));

                                    return (
                                        <div key={featureName} className={isText ? "col-span-full" : ""}>
                                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                                                {featureName}
                                                <span className="ml-2 text-xs opacity-60">
                                                    ({isText ? 'text input' : isNumeric ? 'numeric' : isDatetime ? 'date' : isCategorical ? 'select' : 'input'})
                                                </span>
                                                {isText && <span className="ml-2 text-xs bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">Text Content</span>}
                                                {isDatetime && <span className="ml-2 text-xs bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded">Date</span>}
                                            </label>

                                            {isText ? (
                                                <textarea
                                                    placeholder={meta.placeholder || `Enter ${featureName}...`}
                                                    value={predictionInput[featureName] || ''}
                                                    onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                    rows={featureName.toLowerCase().includes('overview') || featureName.toLowerCase().includes('description') ? 6 : 3}
                                                    className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors resize-none"
                                                    style={{
                                                        backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                        borderColor: 'var(--border-color)',
                                                        color: 'var(--text-primary)',
                                                    }}
                                                />
                                            ) : isDatetime ? (
                                                <input
                                                    type="date"
                                                    value={predictionInput[featureName] || ''}
                                                    onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                    min={typeof meta.min === 'string' ? meta.min.split('T')[0] : undefined}
                                                    max={typeof meta.max === 'string' ? meta.max.split('T')[0] : undefined}
                                                    className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors"
                                                    style={{
                                                        backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                        borderColor: 'var(--border-color)',
                                                        color: 'var(--text-primary)',
                                                    }}
                                                />
                                            ) : isNumeric ? (
                                                <input
                                                    type="number"
                                                    placeholder={meta.mean !== undefined ? `e.g. ${Number(meta.mean).toFixed(1)}` : `Enter ${featureName}`}
                                                    value={predictionInput[featureName] || ''}
                                                    onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                    className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors"
                                                    style={{
                                                        backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                        borderColor: 'var(--border-color)',
                                                        color: 'var(--text-primary)',
                                                    }}
                                                />
                                            ) : isCategorical ? (
                                                <select
                                                    value={predictionInput[featureName] || ''}
                                                    onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                    className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors"
                                                    style={{
                                                        backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                        borderColor: 'var(--border-color)',
                                                        color: 'var(--text-primary)',
                                                    }}
                                                >
                                                    <option value="">Select {featureName}...</option>
                                                    {(meta.options || []).map((opt: string) => (
                                                        <option key={opt} value={opt}>{opt}</option>
                                                    ))}
                                                </select>
                                            ) : (
                                                <input
                                                    type="text"
                                                    placeholder={`Enter ${featureName}`}
                                                    value={predictionInput[featureName] || ''}
                                                    onChange={(e) => setPredictionInput({ ...predictionInput, [featureName]: e.target.value })}
                                                    className="w-full px-4 py-3 rounded-xl border focus:outline-none focus:border-primary-500 transition-colors"
                                                    style={{
                                                        backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                                                        borderColor: 'var(--border-color)',
                                                        color: 'var(--text-primary)',
                                                    }}
                                                />
                                            )}
                                        </div>
                                    );
                                })}
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    // Detect the correct mode for prediction
                                    let predictMode = result.mode || 'traditional';
                                    
                                    // Check if NLP was trained (for multi-mode or single NLP training)
                                    const wasNlpTrained = (result as any).modes_trained?.includes('nlp') ||
                                        (result as any).results_per_mode?.nlp?.success ||
                                        result.best_model?.name?.toLowerCase().includes('vectorizer') ||
                                        result.best_model?.name?.toLowerCase().includes('tfidf') ||
                                        result.best_model?.name?.toLowerCase().includes('nlp');
                                    
                                    // Check if Deep Learning was trained
                                    const wasDLTrained = (result as any).modes_trained?.includes('deep_learning') ||
                                        (result as any).results_per_mode?.deep_learning?.success ||
                                        result.best_model?.name?.toLowerCase().includes('mlp') ||
                                        result.best_model?.name?.toLowerCase().includes('neural');
                                    
                                    // Determine best mode based on what was trained and best model name
                                    if (wasNlpTrained && (result as any).best_overall?.mode === 'nlp') {
                                        predictMode = 'nlp';
                                    } else if (wasNlpTrained && result.best_model?.name?.toLowerCase().includes('vectorizer')) {
                                        predictMode = 'nlp';
                                    } else if (wasDLTrained && (result as any).best_overall?.mode === 'deep_learning') {
                                        predictMode = 'deep_learning';
                                    } else if (wasDLTrained && result.best_model?.name?.toLowerCase().includes('mlp')) {
                                        predictMode = 'deep_learning';
                                    }
                                    
                                    const dataToSend = {
                                        user_id: getUserIdSync(),
                                        model_name: result.best_model.name,
                                        mode: predictMode,
                                        data: Object.fromEntries(
                                            Object.entries(predictionInput).map(([k, v]) => [k, parseFloat(v) || v])
                                        )
                                    };
                                    console.log('[MLPredictions] Sending prediction with mode:', predictMode);
                                    const response = await fetch('/api/v2/automl/predict', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify(dataToSend)
                                    });
                                    const data = await response.json();
                                    setPredictionResult(data);
                                } catch (e: any) {
                                    toast.error(`Prediction failed: ${e.message}`);
                                }
                            }}
                            className="px-6 py-3 bg-gradient-to-r from-primary-500 to-emerald-500 rounded-xl text-white font-semibold hover:opacity-90 transition-opacity flex items-center gap-2"
                        >
                            <Play className="w-5 h-5" />
                            Get Prediction
                        </button>

                        {predictionResult && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mt-6 p-4 sm:p-6 rounded-xl border-2"
                                style={{
                                    backgroundColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.05)',
                                    borderColor: isDark ? '#22c55e' : '#16a34a',
                                }}
                            >
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <div>
                                        <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                                            Predicted label
                                        </p>
                                        <p
                                            className="text-3xl sm:text-4xl font-bold"
                                            style={{ color: isDark ? '#4ade80' : '#15803d' }}
                                        >
                                            {predictionResult.prediction}
                                        </p>
                                    </div>
                                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
                                        {predictionResult.probability && (
                                            <div className="sm:text-right">
                                                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)' }}>Confidence</p>
                                                <div className="flex items-center gap-2">
                                                    {(() => {
                                                        const probValues = Array.isArray(predictionResult.probability)
                                                            ? predictionResult.probability
                                                            : Object.values(predictionResult.probability as Record<string, number>);
                                                        const maxProb = Math.max(...probValues);
                                                        return (
                                                            <>
                                                                <div
                                                                    className="w-20 sm:w-24 h-3 rounded-full overflow-hidden"
                                                                    style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }}
                                                                >
                                                                    <div
                                                                        className="h-full rounded-full bg-gradient-to-r from-green-500 to-amber-500 transition-all duration-300"
                                                                        style={{ width: `${maxProb * 100}%` }}
                                                                    />
                                                                </div>
                                                                <span className="font-bold" style={{ color: isDark ? '#4ade80' : '#15803d' }}>
                                                                    {(maxProb * 100).toFixed(1)}%
                                                                </span>
                                                            </>
                                                        );
                                                    })()}
                                                </div>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => {
                                                setExplainInputValues(predictionInput);
                                                setShowExplainModal(true);
                                            }}
                                            className="w-full sm:w-auto px-3 py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 text-sm font-medium"
                                            style={{
                                                backgroundColor: isDark ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)',
                                                color: isDark ? '#fbbf24' : '#b45309',
                                            }}
                                        >
                                            <HelpCircle className="w-4 h-4" />
                                            Why this prediction?
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </div>
                )}

                {activeTab === 'history' && (
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <ModelHistory
                            userId={getUserIdSync()}
                            onModelChange={handleModelChange}
                        />
                    </div>
                )}

                {activeTab === 'data' && (
                    <div className="p-12 text-center rounded-2xl border border-dashed" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="max-w-2xl mx-auto">
                            <div className="w-20 h-20 mx-auto bg-primary-500/20 rounded-full flex items-center justify-center mb-6">
                                <Database className="w-10 h-10" style={{ color: isDark ? '#4ade80' : '#16a34a' }} />
                            </div>
                            <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                                Production Assets
                            </h2>
                            <p className="mb-8 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                Download trained model and cleaned dataset for deployment in production environments.
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Trained Model Download */}
                                <div className="p-6 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)' }}>
                                    <div className="w-14 h-14 mx-auto bg-purple-500/20 rounded-full flex items-center justify-center mb-4">
                                        <Brain className="w-7 h-7 text-purple-500" />
                                    </div>
                                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                        Trained Model
                                    </h3>
                                    <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
                                        Download the trained ML model (.pkl) for deployment in your applications.
                                    </p>
                                    <a
                                        href={`/api/v2/automl/download-model?user_id=${getUserIdSync()}`}
                                        className="inline-flex items-center gap-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-xl font-semibold transition-all hover:scale-105"
                                    >
                                        <Download className="w-5 h-5" />
                                        Download Model (.pkl)
                                    </a>
                                    <p className="text-xs mt-3 flex items-center justify-center gap-2" style={{ color: 'var(--text-muted)' }}>
                                        <CheckCircle className="w-3 h-3 text-purple-400" />
                                        {result.best_model?.name || 'ML Model'}
                                    </p>
                                </div>

                                {/* Cleaned Dataset Download - Only show if available */}
                                {result.cleaned_file && (
                                    <div className="p-6 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)' }}>
                                        <div className="w-14 h-14 mx-auto bg-emerald-500/20 rounded-full flex items-center justify-center mb-4">
                                            <Database className="w-7 h-7 text-emerald-500" />
                                        </div>
                                        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                            Cleaned Dataset
                                        </h3>
                                        <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
                                            Production-ready data (Missing values imputed, Categorical encoded, Features scaled).
                                        </p>
                                        <a
                                            href={`/api/v1/files/${getUserIdSync()}/${result.cleaned_file}/download`}
                                            className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold transition-all hover:scale-105"
                                        >
                                            <Download className="w-5 h-5" />
                                            Download CSV
                                        </a>
                                        <p className="text-xs mt-3 flex items-center justify-center gap-2" style={{ color: 'var(--text-muted)' }}>
                                            <CheckCircle className="w-3 h-3 text-emerald-400" />
                                            Ready for Production
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Usage Instructions */}
                            <div className="mt-8 p-4 rounded-xl text-left" style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}>
                                <h4 className="font-semibold mb-2 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                    <Code2 className="w-4 h-4" />
                                    Usage Example
                                </h4>
                                <pre className="text-xs p-3 rounded-lg overflow-x-auto" style={{ backgroundColor: isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)', color: 'var(--text-muted)' }}>
{`import pickle

# Load the trained model
with open('model.pkl', 'rb') as f:
    engine_state = pickle.load(f)

# Access model and components
model = engine_state['model']
scaler = engine_state.get('scaler')
encoders = engine_state.get('label_encoders', {})

# Make predictions
prediction = model.predict(X_new)`}
                                </pre>
                            </div>
                        </motion.div>
                    </div>
                )}
            </motion.div>

            {/* Explain Modal */}
            <ExplainModal
                isOpen={showExplainModal}
                onClose={() => setShowExplainModal(false)}
                inputValues={explainInputValues}
                mode={result.mode || 'traditional'}
            />

            {/* Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="p-4 rounded-xl flex items-center justify-between"
                style={{ backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
            >
                <div className="flex items-center gap-6 text-sm" style={{ color: 'var(--text-muted)' }}>
                    <span>📊 {result.data_summary?.rows?.toLocaleString() || 0} rows</span>
                    <span>📁 {result.data_summary?.columns || 0} columns</span>
                    <span>⚙️ {result.data_summary?.features_engineered || 0} features engineered</span>
                </div>
            </motion.div>
        </div>
    );
};

export default MLPredictions;
