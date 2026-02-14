# 🚀 DataVision AutoML - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Training Modes](#training-modes)
3. [Supervised Learning Algorithms](#supervised-learning-algorithms)
4. [Unsupervised Learning Algorithms](#unsupervised-learning-algorithms)
5. [NLP Algorithms](#nlp-algorithms)
6. [Deep Learning Architectures](#deep-learning-architectures)
7. [Charts & Visualizations](#charts--visualizations)
8. [API Endpoints](#api-endpoints)

---

## Overview

DataVision AutoML is a production-grade machine learning platform supporting:
- **30+ ML Algorithms** (Classification, Regression, Clustering)
- **Auto GPU/CPU Detection** (CUDA, ROCm, Metal)
- **Advanced Data Cleaning** (Smart Imputation, Outlier Detection)
- **Feature Selection** (Variance, Correlation, Mutual Info, RFE)
- **Bayesian Hyperparameter Optimization** (Optuna)
- **Ensemble Methods** (Stacking, Voting, Blending)
- **20+ Visualization Charts**

---

## Training Modes

### 1. Fast Mode (Default)
- **Speed**: ~30-60 seconds
- **Algorithms**: Top 5 performing algorithms
- **CV Folds**: 3-fold cross-validation
- **Use Case**: Quick prototyping, small datasets

### 2. Ultra Mode
- **Speed**: 2-10 minutes
- **Algorithms**: All 15+ algorithms
- **CV Folds**: 5-fold stratified cross-validation
- **Features**: Hyperparameter tuning, ensemble stacking
- **Use Case**: Production models, maximum accuracy

### 3. Multi-Mode Training
- **Combines**: Traditional ML + NLP + Deep Learning
- **Parallel Training**: Runs selected modes simultaneously
- **Best Model Selection**: Cross-mode comparison

---

## Supervised Learning Algorithms

### Classification Algorithms

| Algorithm | Parameters | Use Case | Chart Support |
|-----------|-----------|----------|---------------|
| **XGBoost** | `n_estimators=100-500`, `max_depth=3-10`, `learning_rate=0.01-0.3`, `subsample=0.6-1.0`, `colsample_bytree=0.6-1.0`, `min_child_weight=1-10`, `gamma=0-5`, `reg_alpha=0-1`, `reg_lambda=0-1` | Large datasets, tabular data | ✅ All |
| **LightGBM** | `n_estimators=100-500`, `max_depth=3-15`, `learning_rate=0.01-0.3`, `num_leaves=20-150`, `subsample=0.6-1.0`, `colsample_bytree=0.6-1.0`, `min_child_samples=10-100`, `reg_alpha=0-1`, `reg_lambda=0-1` | Fast training, large data | ✅ All |
| **CatBoost** | `iterations=100-500`, `depth=4-10`, `learning_rate=0.01-0.3`, `l2_leaf_reg=1-10`, `border_count=32-255`, `random_strength=0-10` | Categorical features, GPU | ✅ All |
| **Random Forest** | `n_estimators=100-500`, `max_depth=5-30`, `min_samples_split=2-20`, `min_samples_leaf=1-10`, `max_features='sqrt'/'log2'/0.5-1.0`, `bootstrap=True/False` | General purpose, interpretable | ✅ All |
| **Gradient Boosting** | `n_estimators=100-300`, `max_depth=3-8`, `learning_rate=0.01-0.2`, `subsample=0.6-1.0`, `min_samples_split=2-20`, `min_samples_leaf=1-10` | Balanced performance | ✅ All |
| **Extra Trees** | `n_estimators=100-500`, `max_depth=5-30`, `min_samples_split=2-20`, `min_samples_leaf=1-10`, `max_features='sqrt'/'log2'/0.5-1.0` | Fast random splits | ✅ All |
| **Hist Gradient Boosting** | `max_iter=100-500`, `max_depth=3-15`, `learning_rate=0.01-0.3`, `min_samples_leaf=10-50`, `l2_regularization=0-1` | Fast, native categorical | ✅ All |
| **AdaBoost** | `n_estimators=50-200`, `learning_rate=0.01-1.0`, `algorithm='SAMME'/'SAMME.R'` | Boosting weak learners | ✅ All |
| **Bagging** | `n_estimators=10-50`, `max_samples=0.5-1.0`, `max_features=0.5-1.0`, `bootstrap=True/False` | Variance reduction | ✅ All |
| **Logistic Regression** | `C=0.001-100`, `penalty='l1'/'l2'/'elasticnet'`, `solver='lbfgs'/'saga'/'liblinear'`, `max_iter=100-1000`, `l1_ratio=0-1` | Linear baseline, interpretable | ✅ All |
| **SVC (SVM)** | `C=0.1-100`, `kernel='rbf'/'linear'/'poly'/'sigmoid'`, `gamma='scale'/'auto'/0.001-10`, `degree=2-5`, `class_weight='balanced'/None` | Non-linear boundaries | ✅ All |
| **Linear SVC** | `C=0.1-100`, `penalty='l1'/'l2'`, `loss='hinge'/'squared_hinge'`, `max_iter=1000-10000` | Large-scale linear | ✅ All |
| **K-Neighbors** | `n_neighbors=3-15`, `weights='uniform'/'distance'`, `metric='euclidean'/'manhattan'/'minkowski'`, `p=1-2`, `leaf_size=20-50` | Instance-based | ✅ All |
| **Gaussian NB** | `var_smoothing=1e-9-1e-6` | Text, probabilistic | ✅ All |
| **Multinomial NB** | `alpha=0.01-1.0`, `fit_prior=True/False` | Text classification | ✅ All |
| **Complement NB** | `alpha=0.01-1.0`, `norm=True/False` | Imbalanced text | ✅ All |
| **Bernoulli NB** | `alpha=0.01-1.0`, `binarize=0.0-1.0` | Binary features | ✅ All |
| **MLP Classifier** | `hidden_layer_sizes=(64,32)-(256,128,64)`, `activation='relu'/'tanh'`, `solver='adam'/'sgd'`, `alpha=0.0001-0.01`, `learning_rate='constant'/'adaptive'`, `max_iter=200-1000`, `early_stopping=True` | Neural network | ✅ All |
| **Decision Tree** | `max_depth=3-20`, `min_samples_split=2-20`, `min_samples_leaf=1-10`, `criterion='gini'/'entropy'`, `splitter='best'/'random'` | Interpretable rules | ✅ All |
| **LDA** | `solver='svd'/'lsqr'/'eigen'`, `shrinkage='auto'/0-1` | Dimensionality reduction | ✅ All |
| **QDA** | `reg_param=0-1` | Quadratic boundaries | ✅ All |
| **SGD Classifier** | `loss='hinge'/'log_loss'/'perceptron'`, `penalty='l1'/'l2'/'elasticnet'`, `alpha=0.0001-0.01`, `max_iter=1000-5000`, `learning_rate='optimal'/'constant'/'adaptive'` | Large-scale online | ✅ All |
| **Passive Aggressive** | `C=0.1-10`, `max_iter=1000-5000`, `loss='hinge'/'squared_hinge'` | Online learning | ✅ All |

### Regression Algorithms

| Algorithm | Parameters | Use Case |
|-----------|-----------|----------|
| **XGBoost Regressor** | Same as classifier | General regression |
| **LightGBM Regressor** | Same as classifier | Fast regression |
| **CatBoost Regressor** | Same as classifier | Categorical features |
| **Random Forest Regressor** | Same as classifier | General purpose |
| **Gradient Boosting Regressor** | Same as classifier | Balanced |
| **Extra Trees Regressor** | Same as classifier | Fast |
| **Ridge** | `alpha=0.01-100`, `solver='auto'/'svd'/'cholesky'/'lsqr'` | L2 regularization |
| **Lasso** | `alpha=0.01-100`, `max_iter=1000-10000` | L1 regularization, feature selection |
| **ElasticNet** | `alpha=0.01-100`, `l1_ratio=0-1`, `max_iter=1000-10000` | Combined L1+L2 |
| **SVR** | `C=0.1-100`, `kernel='rbf'/'linear'/'poly'`, `epsilon=0.01-0.5`, `gamma='scale'/'auto'` | Non-linear |
| **Linear SVR** | `C=0.1-100`, `epsilon=0-0.5`, `max_iter=1000-10000` | Large-scale linear |
| **K-Neighbors Regressor** | Same as classifier | Instance-based |
| **MLP Regressor** | Same as classifier | Neural network |
| **Bayesian Ridge** | `alpha_1=1e-6`, `alpha_2=1e-6`, `lambda_1=1e-6`, `lambda_2=1e-6` | Probabilistic |
| **Huber Regressor** | `epsilon=1.0-2.0`, `alpha=0.0001-0.01`, `max_iter=100-500` | Robust to outliers |
| **Poisson Regressor** | `alpha=0-1`, `max_iter=100-500` | Count data |
| **Quantile Regressor** | `quantile=0.1-0.9`, `alpha=0-1` | Quantile estimation |
| **Lasso Lars** | `alpha=0.01-100`, `max_iter=500-1000` | Feature selection |

---

## Unsupervised Learning Algorithms

### Clustering Algorithms

| Algorithm | Parameters | Charts Generated | Use Case |
|-----------|-----------|------------------|----------|
| **KMeans** | `n_clusters=2-15` (auto-detect), `init='k-means++'/'random'`, `n_init=10-30`, `max_iter=300-500`, `tol=1e-4`, `algorithm='lloyd'/'elkan'` | Elbow, Silhouette, Scatter, Distribution, Heatmap, PCA, 3D, t-SNE, UMAP, Pairplot, Boxplot, Violin, Correlation, Radar | General clustering |
| **DBSCAN** | `eps=auto-detect` (k-distance), `min_samples=max(3, n//100)` (auto), `metric='euclidean'/'manhattan'`, `algorithm='auto'/'ball_tree'/'kd_tree'` | K-Distance, Scatter, Distribution, Silhouette, Heatmap, PCA, 3D, t-SNE, UMAP, Pairplot, Boxplot, Violin, Correlation, Radar | Noise detection, arbitrary shapes |
| **Hierarchical (Agglomerative)** | `n_clusters=2-15`, `linkage='ward'/'average'/'complete'/'single'`, `metric='euclidean'`, `compute_full_tree='auto'` | **Dendrogram**, Silhouette, Scatter, Distribution, Heatmap, PCA, 3D, t-SNE, UMAP, Pairplot, Boxplot, Violin, Correlation, Radar | Hierarchical structure |
| **GMM (Gaussian Mixture)** | `n_components=2-15`, `covariance_type='full'/'tied'/'diag'/'spherical'`, `n_init=10`, `max_iter=200`, `init_params='k-means++'` | **BIC/AIC Chart**, Silhouette, Scatter, Distribution, Heatmap, PCA, 3D, t-SNE, UMAP, Pairplot, Boxplot, Violin, Correlation, Radar | Probabilistic clustering |
| **Spectral** | `n_clusters=2-15`, `affinity='nearest_neighbors'/'rbf'`, `n_neighbors=10-30`, `assign_labels='cluster_qr'/'kmeans'`, `gamma=1.0` | **Affinity Matrix**, Silhouette, Scatter, Distribution, Heatmap, PCA, 3D, t-SNE, UMAP, Pairplot, Boxplot, Violin, Correlation, Radar | Graph-based clustering |

### Clustering Charts (17 Total)

| Chart | Description | Size (figsize) | When Generated |
|-------|-------------|----------------|----------------|
| `cluster_scatter` | PCA 2D scatter with centroids | (10, 8) | Always |
| `elbow_method` | Silhouette scores vs k | (10, 6) | KMeans/Hierarchical/GMM/Spectral |
| `silhouette_plot` | Per-sample silhouette coefficients | (10, 8) | n_clusters≥2, n_samples≥50 |
| `cluster_distribution` | Bar chart of cluster sizes | (10, 6) | Always |
| `cluster_heatmap` | Feature means per cluster | (12, 8) | n_features≥3, n_clusters≥2 |
| `pca_variance` | Explained variance per component | (14, 5) | n_features≥3 |
| `cluster_3d` | PCA 3D scatter | (12, 10) | n_features≥3, n_samples≥50 |
| `dendrogram` | Hierarchical tree structure | (14, 8) | **Hierarchical only** |
| `gmm_bic_aic` | BIC/AIC model selection | (10, 6) | **GMM only** |
| `dbscan_kdist` | K-distance graph for eps | (10, 6) | **DBSCAN only** |
| `spectral_affinity` | Affinity matrix heatmap | (10, 8) | **Spectral only**, n_samples≤500 |
| `tsne` | t-SNE 2D visualization | (10, 8) | 100≤n_samples≤3000, n_features≥3 |
| `umap` | UMAP 2D visualization | (10, 8) | 100≤n_samples≤5000, n_features≥3 |
| `pairplot` | Feature pairwise scatter | auto | 2≤n_features≤6, n_samples≤2000 |
| `boxplots` | Feature distribution by cluster | (4*n_features, 6) | n_features≥2, n_clusters≥2 |
| `violin_plots` | Violin distribution by cluster | (5*n_features, 6) | n_features≥2, n_clusters≥2, n_samples≥50 |
| `correlation_heatmap` | Feature correlation matrix | (10, 8) | n_features≥3 |
| `radar_chart` | Cluster comparison radar | (10, 10) | n_features≥3, n_clusters≥2 |

### Clustering Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| `silhouette_score` | [-1, 1] | Higher is better, cluster cohesion vs separation |
| `calinski_harabasz_score` | [0, ∞) | Higher is better, variance ratio |
| `davies_bouldin_score` | [0, ∞) | Lower is better, average similarity |
| `reliability_score` | [0, 100] | Production intelligence quality score |

---

## NLP Algorithms

### Text Classification Algorithms

| Algorithm | Parameters | Vectorizer | Use Case |
|-----------|-----------|------------|----------|
| **TF-IDF + Logistic Regression** | `C=0.1-100`, `max_iter=500` | TF-IDF: `max_features=5000-20000`, `ngram_range=(1,2)/(1,3)`, `min_df=2-5`, `max_df=0.9-0.95` | General text |
| **TF-IDF + SVM** | `C=0.1-100`, `kernel='linear'/'rbf'` | Same as above | High accuracy |
| **TF-IDF + Naive Bayes** | `alpha=0.01-1.0` | Same as above | Fast, probabilistic |
| **TF-IDF + Random Forest** | `n_estimators=100-300` | Same as above | Feature importance |
| **TF-IDF + XGBoost** | Same as classifier | Same as above | Best accuracy |
| **BOW + Classifiers** | Same as TF-IDF | CountVectorizer: same params | Simple baseline |
| **N-gram Models** | Same as TF-IDF | `ngram_range=(2,3)/(1,4)` | Phrase patterns |

### NLP-Specific Charts

| Chart | Description | When Generated |
|-------|-------------|----------------|
| `confusion_matrix` | Class prediction matrix | Always |
| `word_cloud` | Important words visualization | Text data |
| `class_distribution` | Target class frequencies | Always |
| `roc_curve` | ROC-AUC per class | Multi-class |
| `precision_recall` | PR curve per class | Multi-class |

---

## Deep Learning Architectures

### MLP (Multi-Layer Perceptron) Architectures

| Architecture | Hidden Layers | Parameters | Use Case |
|--------------|---------------|-----------|----------|
| **mlp_small** | (64, 32) | ~5K params | Small data, fast |
| **mlp_medium** | (128, 64, 32) | ~15K params | Balanced |
| **mlp_large** | (256, 128, 64) | ~50K params | Complex patterns |
| **mlp_wide** | (512, 256) | ~150K params | High-dimensional |
| **mlp_deep** | (128, 128, 128, 128) | ~70K params | Deep representation |

### MLP Training Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `activation` | 'relu', 'tanh', 'logistic' | Activation function |
| `solver` | 'adam', 'sgd', 'lbfgs' | Optimizer |
| `alpha` | 0.0001-0.01 | L2 regularization |
| `learning_rate` | 'constant', 'adaptive', 'invscaling' | LR schedule |
| `learning_rate_init` | 0.001-0.01 | Initial LR |
| `max_iter` | 200-1000 | Max epochs |
| `early_stopping` | True | Validation-based stopping |
| `validation_fraction` | 0.1 | Validation split |
| `n_iter_no_change` | 10 | Early stopping patience |
| `batch_size` | 32-256, 'auto' | Mini-batch size |

### Deep Learning Charts

| Chart | Description | When Generated |
|-------|-------------|----------------|
| `learning_curve` | Loss vs epochs | Training history |
| `confusion_matrix` | Prediction matrix | Classification |
| `feature_importance` | Input weights | All |
| `activation_distribution` | Layer activations | Debug |

---

## Charts & Visualizations

### Supervised Learning Charts (Classification)

| Chart Key | Description | Size | Parameters |
|-----------|-------------|------|------------|
| `confusion_matrix` | True vs Predicted heatmap | (10, 8) | `cmap='Blues'`, `annot=True`, `fmt='d'` |
| `feature_importance` | Top 15 features bar chart | (12, 8) | Sorted descending |
| `roc_curve` | ROC curves per class | (10, 8) | `lw=2`, AUC in legend |
| `precision_recall` | PR curves per class | (10, 8) | AP in legend |
| `class_distribution` | Target class bar chart | (10, 6) | With percentages |
| `learning_curve` | Train/Val score vs size | (10, 6) | CV=5 |
| `calibration_curve` | Predicted vs actual prob | (10, 8) | Perfectly calibrated line |
| `lift_curve` | Cumulative gains | (10, 8) | Baseline comparison |
| `correlation_heatmap` | Feature correlations | (12, 10) | `cmap='coolwarm'` |
| `shap_summary` | SHAP feature values | (12, 10) | Requires SHAP |

### Supervised Learning Charts (Regression)

| Chart Key | Description | Size | Parameters |
|-----------|-------------|------|------------|
| `actual_vs_predicted` | Scatter with ideal line | (10, 8) | `alpha=0.5` |
| `residual_plot` | Residuals vs predicted | (10, 6) | Zero line |
| `residual_distribution` | Residual histogram+KDE | (10, 6) | Normal curve overlay |
| `feature_importance` | Top 15 features | (12, 8) | Sorted descending |
| `error_by_range` | MAE per target bin | (10, 6) | 10 bins |
| `qq_plot` | Quantile-quantile | (8, 8) | Normal reference |
| `learning_curve` | Train/Val RMSE vs size | (10, 6) | CV=5 |
| `cook_distance` | Influential points | (10, 6) | Threshold line |

### Chart Generation Parameters

```python
# Common matplotlib settings
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['savefig.facecolor'] = 'white'

# Color palettes
CLASSIFICATION_COLORS = ['#2563eb', '#16a34a', '#dc2626', '#ea580c', '#9333ea', 
                         '#0891b2', '#db2777', '#d97706', '#0d9488', '#4f46e5']
REGRESSION_COLORS = ['#3b82f6', '#ef4444']
CLUSTER_COLORS = ['#2563eb', '#16a34a', '#dc2626', '#ea580c', '#9333ea', 
                  '#0891b2', '#db2777', '#d97706', '#0d9488', '#4f46e5',
                  '#84cc16', '#06b6d4', '#f43f5e', '#8b5cf6', '#14b8a6']
```

---

## API Endpoints

### Supervised Learning

| Endpoint | Method | Mode | Description |
|----------|--------|------|-------------|
| `/api/v1/automl/production_train` | POST | Fast | Quick training with top algorithms |
| `/api/v1/automl/train` | POST | Standard | Full training pipeline |
| `/api/v1/automl/ultra_train` | POST | Ultra | Maximum accuracy mode |
| `/api/v1/automl/multi_mode/train` | POST | Multi | Combined Traditional+NLP+Deep |
| `/api/v1/automl/predict` | POST | - | Single prediction |
| `/api/v1/automl/batch_predict` | POST | - | Batch predictions |
| `/api/v1/automl/saved-result` | GET | - | Load saved model results |
| `/api/v1/automl/stop_training` | POST | - | Cancel ongoing training |

### NLP

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/automl/nlp/train` | POST | Text classification training |
| `/api/v1/automl/nlp/predict` | POST | Text prediction |

### Deep Learning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/automl/deep_learning/train` | POST | Neural network training |
| `/api/v1/automl/deep_learning/predict` | POST | Deep learning prediction |

### Unsupervised Learning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ml/clustering` | POST | Clustering analysis |
| `/api/v1/ml/clustering/predict` | POST | Predict cluster for new data |
| `/api/v1/ml/clustering/download-model/{user_id}` | GET | Download PKL model |
| `/api/v1/ml/clustering/download-data/{user_id}` | GET | Download clustered CSV |

---

## Production Intelligence

### Reliability Score (0-100)

Computed based on:
- Data quality (missing values, outliers)
- Model validation (CV performance, overfitting check)
- Feature quality (variance, correlation)
- Sample size adequacy

### Validation Warnings

| Warning Type | Trigger |
|--------------|---------|
| `small_dataset` | n_samples < 100 |
| `high_cardinality` | categorical unique > 50% |
| `class_imbalance` | minority class < 10% |
| `missing_values` | missing > 20% |
| `potential_leakage` | feature corr > 0.95 with target |
| `low_variance` | feature variance ≈ 0 |

---

## File Outputs

### Saved Artifacts

| File | Location | Content |
|------|----------|---------|
| `best_model.pkl` | `storage/users/{user_id}/models/` | Trained model + metadata |
| `cleaned_data.csv` | `storage/users/{user_id}/files/` | Preprocessed data |
| `multimode_metadata.json` | `storage/users/{user_id}/models/` | Training configuration |
| `clustering_model.pkl` | `storage/users/{user_id}/models/` | Clustering model + scaler |
| `clustered_data.csv` | `storage/users/{user_id}/files/` | Data with cluster labels |

---

## Version Info

- **Engine Version**: 7.0
- **Last Updated**: February 2026
- **Supported Python**: 3.11+
- **Key Dependencies**: scikit-learn>=1.3.0, xgboost>=2.0.0, lightgbm>=4.2.0, catboost>=1.2.0, optuna>=3.4.0
