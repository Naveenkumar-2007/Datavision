"""
🎯 Clustering API - Unsupervised Machine Learning (Production AutoML)
=====================================================================
Real AutoML Unsupervised Learning with:
- Multiple algorithm comparison (KMeans, DBSCAN, GMM, Hierarchical, Spectral, K-Prototypes)
- Automatic optimal k detection (elbow + silhouette)
- Model persistence for predictions
- Comprehensive visualization & charts
- Production intelligence & reliability scoring

🛡️ PRODUCTION INTELLIGENCE INTEGRATED:
- Data quality assessment
- Feature validation
- Missing data handling
- Reliability scoring for cluster quality
- Validation warnings
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, SpectralClustering, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import io
import logging
import pickle
import uuid
import json
from pathlib import Path
from datetime import datetime
import base64

# Import production clustering engine
try:
    from ml.clustering_engine import ProductionClusteringEngine, clustering_engine
except ImportError:
    clustering_engine = None

# Import user paths utility
try:
    from utils.paths import get_user_paths
except ImportError:
    def get_user_paths(user_id):
        base = Path("storage/users") / user_id
        paths = {"base": base, "files": base / "files", "models": base / "models"}
        for p in paths.values():
            p.mkdir(parents=True, exist_ok=True)
        return paths

logger = logging.getLogger(__name__)
router = APIRouter()


# ===========================================================================
# REQUEST/RESPONSE MODELS
# ===========================================================================

class ClusteringRequest(BaseModel):
    """Request model for clustering from file_id"""
    file_id: str
    user_id: Optional[str] = None
    algorithm: str = "auto"  # auto, kmeans, dbscan, hierarchical, gmm, spectral
    n_clusters: Optional[int] = None  # None = auto-detect
    compare_all: bool = False  # Compare all algorithms
    exclude_columns: Optional[List[str]] = None


class ClusterPredictRequest(BaseModel):
    """Request model for predicting cluster of new data point"""
    user_id: Optional[str] = None
    model_id: str
    features: Dict[str, float]


# ===========================================================================
# 🎯 MAIN CLUSTERING ENDPOINT - JSON API (Used by frontend)
# ===========================================================================

@router.post("/clustering")
async def run_clustering_analysis(
    request: ClusteringRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    🎯 PRODUCTION AutoML Unsupervised Learning
    
    Takes a file_id and runs real clustering analysis with:
    - Automatic algorithm selection based on data type
    - Optimal k detection via silhouette analysis
    - Multiple algorithm comparison (optional)
    - Model persistence for predictions
    - Comprehensive visualizations
    
    Request Body:
    - file_id: User's file name/id
    - algorithm: 'auto', 'kmeans', 'dbscan', 'hierarchical', 'gmm', 'spectral'
    - n_clusters: Number of clusters (auto-detect if None)
    - compare_all: Run all algorithms and compare
    - exclude_columns: Columns to exclude from clustering
    """
    user_id = request.user_id or x_user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    logger.info(f"🎯 Clustering request: user={user_id}, file={request.file_id}, algo={request.algorithm}")
    
    try:
        # 1. Load user's file
        paths = get_user_paths(user_id)
        files_dir = paths.get("files", paths["base"] / "files")
        
        # Try multiple file path patterns
        file_path = None
        for pattern in [
            files_dir / request.file_id,
            files_dir / f"{request.file_id}.csv",
            Path(f"storage/users/{user_id}/files/{request.file_id}"),
            Path(f"storage/users/{user_id}/files/{request.file_id}.csv"),
            Path(f"backend/storage/users/{user_id}/files/{request.file_id}"),
            Path(f"backend/storage/users/{user_id}/files/{request.file_id}.csv"),
        ]:
            if pattern.exists():
                file_path = pattern
                break
        
        if not file_path:
            raise HTTPException(
                status_code=404, 
                detail=f"File not found: {request.file_id}. Upload a file in DataHub first."
            )
        
        # 2. Read data
        df = pd.read_csv(file_path)
        logger.info(f"📊 Loaded {len(df)} rows x {len(df.columns)} columns")
        
        if len(df) < 10:
            raise HTTPException(status_code=400, detail="Need at least 10 rows for clustering")
        
        # 3. Prepare exclude columns
        exclude_cols = request.exclude_columns or []
        
        # Auto-exclude obvious ID/datetime columns
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['id', 'index', 'key', 'timestamp', 'date', 'time', 'created', 'updated']):
                if col not in exclude_cols:
                    exclude_cols.append(col)
        
        # 4. Run clustering with production engine or fallback
        result = await _run_production_clustering(
            df=df,
            algorithm=request.algorithm,
            n_clusters=request.n_clusters,
            exclude_columns=exclude_cols,
            compare_all=request.compare_all,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Clustering failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Clustering error: {str(e)}")


async def _run_production_clustering(
    df: pd.DataFrame,
    algorithm: str,
    n_clusters: Optional[int],
    exclude_columns: List[str],
    compare_all: bool,
    user_id: str
) -> Dict[str, Any]:
    """
    Core clustering logic using production-grade algorithms.
    """
    import math
    
    # Prepare numeric data
    df_clean = df.drop(columns=exclude_columns, errors='ignore')
    
    # Drop datetime columns
    datetime_cols = df_clean.select_dtypes(include=['datetime64']).columns.tolist()
    df_clean = df_clean.drop(columns=datetime_cols, errors='ignore')
    
    # Get numeric columns only for clustering
    numeric_df = df_clean.select_dtypes(include=[np.number])
    
    if numeric_df.empty or len(numeric_df.columns) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 numeric columns for clustering")
    
    # Fill missing values
    numeric_df = numeric_df.fillna(numeric_df.median())
    
    # Drop zero-variance columns
    zero_var_cols = numeric_df.columns[numeric_df.std() == 0].tolist()
    numeric_df = numeric_df.drop(columns=zero_var_cols, errors='ignore')
    
    feature_columns = numeric_df.columns.tolist()
    X = numeric_df.values
    
    logger.info(f"📊 Clustering {len(X)} samples with {len(feature_columns)} features")
    
    # Scale data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Initialize k_scores for elbow method chart
    k_scores = None
    
    # =======================================================================
    # AUTO-DETECT OPTIMAL K (if not provided)
    # =======================================================================
    if n_clusters is None and algorithm not in ['dbscan']:
        n_clusters, k_scores = _find_optimal_k(X_scaled, max_k=min(15, len(X) // 10))
        logger.info(f"✅ Auto-detected optimal k={n_clusters}")
    elif n_clusters is None:
        n_clusters = 3  # Default for DBSCAN (will auto-detect anyway)
    
    # =======================================================================
    # RUN CLUSTERING (compare all or single algorithm)
    # =======================================================================
    if compare_all:
        # Run all algorithms and compare
        all_results = _compare_all_algorithms(X_scaled, n_clusters)
        best_algo = max(all_results, key=lambda x: all_results[x]['silhouette_score'])
        best_result = all_results[best_algo]
        labels = np.array(best_result['labels'])
        algorithm = best_algo
        comparison_results = all_results
    else:
        # Single algorithm
        if algorithm == 'auto':
            algorithm = 'kmeans'  # Default to kmeans for numeric data
        
        labels, model, metrics = _run_single_clustering(X_scaled, algorithm, n_clusters)
        comparison_results = None
    
    # =======================================================================
    # CALCULATE METRICS
    # =======================================================================
    metrics = _calculate_clustering_metrics(X_scaled, labels)
    
    # Cluster distribution
    unique_labels, counts = np.unique(labels, return_counts=True)
    cluster_distribution = {
        f"Cluster {int(k)}" if k != -1 else "Noise": int(v)
        for k, v in zip(unique_labels, counts)
    }
    
    actual_n_clusters = len([l for l in unique_labels if l != -1])
    
    # =======================================================================
    # PCA FOR VISUALIZATION
    # =======================================================================
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X_scaled)
    pca_variance = sum(pca.explained_variance_ratio_)
    
    # =======================================================================
    # COMPUTE FEATURE STATISTICS PER CLUSTER
    # =======================================================================
    feature_stats = {}
    for col in feature_columns:
        col_idx = feature_columns.index(col)
        stats = {
            'mean': float(numeric_df[col].mean()),
            'std': float(numeric_df[col].std()),
            'min': float(numeric_df[col].min()),
            'max': float(numeric_df[col].max()),
        }
        feature_stats[col] = stats
    
    # Cluster centroids in original scale
    cluster_profiles = {}
    for cluster_id in unique_labels:
        if cluster_id == -1:
            continue
        mask = labels == cluster_id
        cluster_data = numeric_df.values[mask]
        profile = {}
        for i, col in enumerate(feature_columns):
            profile[col] = {
                'mean': float(np.mean(cluster_data[:, i])),
                'std': float(np.std(cluster_data[:, i])),
            }
        cluster_profiles[f"Cluster {cluster_id}"] = profile
    
    # =======================================================================
    # GENERATE COMPREHENSIVE CHARTS
    # =======================================================================
    charts = _generate_clustering_charts(
        X_2d=X_2d,
        labels=labels,
        algorithm=algorithm,
        n_clusters=actual_n_clusters,
        silhouette=metrics['silhouette_score'],
        feature_names=feature_columns,
        cluster_profiles=cluster_profiles,
        X_scaled=X_scaled,
        X_original=numeric_df.values,
        k_scores=k_scores
    )
    
    # =======================================================================
    # RELIABILITY SCORE (Production Intelligence)
    # =======================================================================
    reliability_score, validation_warnings = _compute_reliability_score(
        n_samples=len(X),
        n_features=len(feature_columns),
        silhouette=metrics['silhouette_score'],
        calinski=metrics.get('calinski_harabasz_score', 0),
        davies=metrics.get('davies_bouldin_score', float('inf')),
        df=df
    )
    
    # =======================================================================
    # SAVE MODEL FOR PREDICTIONS
    # =======================================================================
    model_id = f"clustering_{uuid.uuid4().hex[:8]}"
    model_data = {
        'algorithm': algorithm,
        'n_clusters': actual_n_clusters,
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist(),
        'feature_columns': feature_columns,
        'labels': labels.tolist(),
        'centroids_scaled': _get_cluster_centroids(X_scaled, labels).tolist() if actual_n_clusters > 0 else [],
        'created_at': datetime.now().isoformat(),
    }
    
    # Save to user's model directory
    _save_clustering_model(user_id, model_id, model_data)
    
    # =======================================================================
    # SAVE CLEANED DATA WITH CLUSTER LABELS
    # =======================================================================
    cleaned_file = None
    model_pkl_file = None
    
    try:
        # Create cleaned dataframe with cluster assignments
        cleaned_df = df.copy()
        cleaned_df['Cluster'] = labels
        cleaned_df['Cluster_Name'] = [f'Cluster_{l}' if l >= 0 else 'Noise' for l in labels]
        
        # Add PCA components for visualization
        cleaned_df['PCA_1'] = X_2d[:, 0]
        cleaned_df['PCA_2'] = X_2d[:, 1]
        
        # Save cleaned CSV
        cleaned_filename = f"clustered_data_{model_id}.csv"
        cleaned_path = paths.get("files", paths["base"] / "files") / cleaned_filename
        cleaned_df.to_csv(cleaned_path, index=False)
        cleaned_file = cleaned_filename
        logger.info(f"✅ Saved cleaned data: {cleaned_path}")
        
        # Save PKL model file
        import pickle
        pkl_filename = f"clustering_model_{model_id}.pkl"
        pkl_path = paths.get("models", paths["base"] / "models") / pkl_filename
        pkl_path.parent.mkdir(parents=True, exist_ok=True)
        
        pkl_data = {
            'algorithm': algorithm,
            'n_clusters': actual_n_clusters,
            'scaler': scaler,
            'feature_columns': feature_columns,
            'centroids_scaled': _get_cluster_centroids(X_scaled, labels) if actual_n_clusters > 0 else None,
            'labels': labels,
            'model_id': model_id,
            'created_at': datetime.now().isoformat(),
            'silhouette_score': metrics['silhouette_score'],
            'cluster_profiles': cluster_profiles,
        }
        
        with open(pkl_path, 'wb') as f:
            pickle.dump(pkl_data, f)
        model_pkl_file = pkl_filename
        logger.info(f"✅ Saved PKL model: {pkl_path}")
        
    except Exception as e:
        logger.warning(f"Failed to save cleaned data/PKL: {e}")
    
    # =======================================================================
    # BUILD RESPONSE
    # =======================================================================
    response = {
        'success': True,
        'model_id': model_id,
        'algorithm': algorithm,
        'n_clusters': actual_n_clusters,
        'n_samples': len(X),
        'n_features': len(feature_columns),
        'feature_columns': feature_columns,
        'feature_stats': feature_stats,
        'silhouette_score': metrics['silhouette_score'],
        'calinski_harabasz_score': metrics.get('calinski_harabasz_score', 0),
        'davies_bouldin_score': metrics.get('davies_bouldin_score', 0),
        'cluster_distribution': cluster_distribution,
        'cluster_profiles': cluster_profiles,
        'pca_variance_explained': pca_variance,
        'labels': labels.tolist(),
        'visualization': {
            'x': X_2d[:, 0].tolist(),
            'y': X_2d[:, 1].tolist(),
        },
        'charts': charts,
        'reliability_score': reliability_score,
        'validation_warnings': validation_warnings if validation_warnings else None,
        'comparison_results': comparison_results,
        'cleaned_file': cleaned_file,
        'model_pkl_file': model_pkl_file,
        'k_scores': k_scores,  # For elbow chart on frontend
    }
    
    logger.info(f"✅ Clustering complete: {actual_n_clusters} clusters, silhouette={metrics['silhouette_score']:.3f}")
    
    return response


def _find_optimal_k(X_scaled: np.ndarray, max_k: int = 10) -> tuple:
    """
    Find optimal number of clusters using multiple metrics:
    - Silhouette Score (primary)
    - Elbow Method (inertia)
    - Calinski-Harabasz Index
    """
    max_k = min(max_k, len(X_scaled) - 1, 15)
    max_k = max(max_k, 3)
    
    scores = {}
    inertias = []
    calinski_scores = []
    best_k = 2
    best_score = -1
    
    for k in range(2, max_k + 1):
        try:
            # Use k-means++ initialization with multiple runs
            kmeans = KMeans(
                n_clusters=k, 
                random_state=42, 
                n_init=15,  # More initializations for stability
                max_iter=500,  # More iterations for convergence
                init='k-means++',
                algorithm='lloyd'
            )
            labels = kmeans.fit_predict(X_scaled)
            
            if len(set(labels)) > 1:
                score = silhouette_score(X_scaled, labels)
                scores[k] = score
                inertias.append(kmeans.inertia_)
                
                try:
                    calinski = calinski_harabasz_score(X_scaled, labels)
                    calinski_scores.append(calinski)
                except:
                    calinski_scores.append(0)
                
                if score > best_score:
                    best_score = score
                    best_k = k
        except Exception as e:
            logger.warning(f"Optimal k search failed for k={k}: {e}")
    
    # If silhouette fails, try elbow method
    if best_score < 0 and inertias:
        # Find elbow using rate of change
        deltas = np.diff(inertias)
        if len(deltas) > 1:
            delta2 = np.diff(deltas)
            elbow_idx = np.argmax(delta2) + 2
            best_k = elbow_idx + 2  # Adjust for range starting at 2
    
    logger.info(f"🎯 Optimal k detection: best_k={best_k}, silhouette={best_score:.3f}")
    return best_k, scores


def _run_single_clustering(X_scaled: np.ndarray, algorithm: str, n_clusters: int):
    """
    Run a single clustering algorithm with PRODUCTION-QUALITY settings.
    Enhanced with:
    - Better hyperparameters
    - Multiple initializations
    - Adaptive parameters based on data size
    """
    metrics = {}
    n_samples = len(X_scaled)
    
    if algorithm == 'kmeans':
        # Production K-Means with k-means++ and stability settings
        model = KMeans(
            n_clusters=n_clusters, 
            random_state=42, 
            n_init=20,  # More initializations for better results
            max_iter=500,  # More iterations
            init='k-means++',  # Smart initialization
            algorithm='lloyd',
            tol=1e-5  # Stricter convergence
        )
        labels = model.fit_predict(X_scaled)
        metrics['inertia'] = model.inertia_
        metrics['n_iter'] = model.n_iter_
        
    elif algorithm == 'dbscan':
        # Auto-detect eps using k-distance graph with better heuristics
        from sklearn.neighbors import NearestNeighbors
        
        # Adaptive k based on data size
        k = min(max(5, n_samples // 50), 15, n_samples - 1)
        nn = NearestNeighbors(n_neighbors=k)
        nn.fit(X_scaled)
        distances, _ = nn.kneighbors(X_scaled)
        
        # Use multiple percentiles and pick best
        sorted_distances = np.sort(distances[:, -1])
        
        # Try different eps values and pick best silhouette
        best_eps = np.percentile(sorted_distances, 90)
        best_labels = None
        best_sil = -1
        
        for pct in [80, 85, 90, 95]:
            try:
                eps = np.percentile(sorted_distances, pct)
                min_samples = max(3, n_samples // 100)
                
                model = DBSCAN(eps=eps, min_samples=min_samples)
                test_labels = model.fit_predict(X_scaled)
                
                n_clusters_found = len(set(test_labels)) - (1 if -1 in test_labels else 0)
                if n_clusters_found >= 2:
                    mask = test_labels != -1
                    if mask.sum() > 10:
                        sil = silhouette_score(X_scaled[mask], test_labels[mask])
                        if sil > best_sil:
                            best_sil = sil
                            best_eps = eps
                            best_labels = test_labels
            except:
                pass
        
        if best_labels is not None:
            labels = best_labels
        else:
            model = DBSCAN(eps=best_eps, min_samples=max(3, n_samples // 100))
            labels = model.fit_predict(X_scaled)
        
        metrics['eps'] = best_eps
        
    elif algorithm == 'hierarchical':
        # Use ward linkage for compactness, try different linkage if fails
        try:
            model = AgglomerativeClustering(
                n_clusters=n_clusters, 
                linkage='ward',
                metric='euclidean'
            )
            labels = model.fit_predict(X_scaled)
        except Exception:
            # Fallback to average linkage
            model = AgglomerativeClustering(
                n_clusters=n_clusters, 
                linkage='average'
            )
            labels = model.fit_predict(X_scaled)
        
        metrics['linkage'] = 'ward'
        
    elif algorithm == 'gmm':
        # Gaussian Mixture with multiple covariance types and select best
        from sklearn.mixture import GaussianMixture
        
        best_model = None
        best_bic = float('inf')
        
        for cov_type in ['full', 'tied', 'diag', 'spherical']:
            try:
                model = GaussianMixture(
                    n_components=n_clusters, 
                    random_state=42, 
                    n_init=10,
                    max_iter=200,
                    covariance_type=cov_type,
                    init_params='k-means++'
                )
                model.fit(X_scaled)
                bic = model.bic(X_scaled)
                
                if bic < best_bic:
                    best_bic = bic
                    best_model = model
            except Exception:
                pass
        
        if best_model is None:
            # Fallback to simple GMM
            best_model = GaussianMixture(
                n_components=n_clusters, 
                random_state=42, 
                n_init=5
            )
            best_model.fit(X_scaled)
        
        labels = best_model.predict(X_scaled)
        metrics['bic'] = best_model.bic(X_scaled)
        metrics['aic'] = best_model.aic(X_scaled)
        
    elif algorithm == 'spectral':
        # Spectral clustering with adaptive neighbors
        n_neighbors = min(max(10, n_samples // 50), 30, n_samples - 1)
        
        try:
            model = SpectralClustering(
                n_clusters=n_clusters, 
                random_state=42, 
                affinity='nearest_neighbors',
                n_neighbors=n_neighbors,
                assign_labels='cluster_qr'  # Better assignment
            )
            labels = model.fit_predict(X_scaled)
        except Exception:
            # Fallback with simpler settings
            model = SpectralClustering(
                n_clusters=n_clusters, 
                random_state=42, 
                affinity='rbf'
            )
            labels = model.fit_predict(X_scaled)
        
    else:
        raise HTTPException(status_code=400, detail=f"Unknown algorithm: {algorithm}")
    
    return labels, model, metrics


def _compare_all_algorithms(X_scaled: np.ndarray, n_clusters: int) -> Dict[str, Any]:
    """Compare all clustering algorithms."""
    results = {}
    algorithms = ['kmeans', 'hierarchical', 'gmm', 'spectral', 'dbscan']
    
    for algo in algorithms:
        try:
            labels, model, _ = _run_single_clustering(X_scaled, algo, n_clusters)
            metrics = _calculate_clustering_metrics(X_scaled, labels)
            
            actual_k = len(set(labels)) - (1 if -1 in labels else 0)
            
            results[algo] = {
                'labels': labels.tolist(),
                'n_clusters': actual_k,
                **metrics
            }
        except Exception as e:
            logger.warning(f"Algorithm {algo} failed: {e}")
    
    return results


def _calculate_clustering_metrics(X_scaled: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """Calculate clustering quality metrics."""
    mask = labels != -1
    unique_labels = set(labels[mask])
    
    metrics = {
        'silhouette_score': 0.0,
        'calinski_harabasz_score': 0.0,
        'davies_bouldin_score': 0.0,
    }
    
    if len(unique_labels) <= 1 or mask.sum() < 2:
        return metrics
    
    try:
        metrics['silhouette_score'] = float(silhouette_score(X_scaled[mask], labels[mask]))
    except Exception:
        pass
    
    try:
        metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(X_scaled[mask], labels[mask]))
    except Exception:
        pass
    
    try:
        metrics['davies_bouldin_score'] = float(davies_bouldin_score(X_scaled[mask], labels[mask]))
    except Exception:
        pass
    
    return metrics


def _get_cluster_centroids(X_scaled: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Calculate cluster centroids."""
    unique_labels = [l for l in np.unique(labels) if l != -1]
    centroids = []
    for label in unique_labels:
        mask = labels == label
        centroid = X_scaled[mask].mean(axis=0)
        centroids.append(centroid)
    return np.array(centroids) if centroids else np.array([])


def _compute_reliability_score(
    n_samples: int,
    n_features: int,
    silhouette: float,
    calinski: float,
    davies: float,
    df: pd.DataFrame
) -> tuple:
    """Compute reliability score and validation warnings."""
    import math
    
    validation_warnings = []
    
    # Data quality checks
    missing_ratio = df.isna().sum().sum() / df.size if df.size > 0 else 0
    duplicate_ratio = df.duplicated().sum() / n_samples if n_samples > 0 else 0
    
    if missing_ratio > 0.2:
        validation_warnings.append(f"⚠️ High missing data: {missing_ratio:.1%}")
    if duplicate_ratio > 0.1:
        validation_warnings.append(f"⚠️ Many duplicates: {duplicate_ratio:.1%}")
    if n_samples < 100:
        validation_warnings.append(f"⚠️ Small dataset ({n_samples} samples)")
    if n_features > 50:
        validation_warnings.append(f"⚠️ High dimensionality ({n_features} features)")
    if silhouette < 0.2:
        validation_warnings.append(f"⚠️ Low silhouette score ({silhouette:.3f}) - clusters may overlap")
    
    # Compute reliability score
    silhouette_points = max(0, (silhouette + 1) / 2 * 40)
    calinski_points = min(25, math.log(calinski + 1) * 3) if calinski > 0 else 0
    davies_points = max(0, 20 - davies * 5) if davies < float('inf') else 10
    
    if n_samples >= 1000:
        size_points = 15
    elif n_samples >= 500:
        size_points = 12
    elif n_samples >= 100:
        size_points = 8
    else:
        size_points = 5
    
    reliability_score = min(100, silhouette_points + calinski_points + davies_points + size_points)
    
    return reliability_score, validation_warnings


def _generate_clustering_charts(
    X_2d: np.ndarray,
    labels: np.ndarray,
    algorithm: str,
    n_clusters: int,
    silhouette: float,
    feature_names: List[str],
    cluster_profiles: Dict,
    X_scaled: np.ndarray = None,
    X_original: np.ndarray = None,
    k_scores: Dict[int, float] = None
) -> Dict[str, str]:
    """
    Generate COMPREHENSIVE visualization charts for unsupervised learning.
    Only generates charts when data is sufficient and suitable.
    
    Charts included (when data permits):
    1. Cluster Scatter Plot (PCA 2D)
    2. Elbow Method Graph
    3. Silhouette Score Plot
    4. Cluster Distribution Bar Chart
    5. Cluster Profile Heatmap
    6. PCA Explained Variance Plot
    7. Pairplot (feature relationships) - up to 4 features
    8. 3D Cluster Visualization
    9. Dendrogram (Hierarchical only)
    10. t-SNE Visualization (if samples < 5000)
    11. Boxplot per Cluster
    12. Violin Plot per Cluster
    13. Correlation Heatmap
    14. Radar Chart for Cluster Comparison
    """
    charts = {}
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import seaborn as sns
        from matplotlib.colors import LinearSegmentedColormap
        
        # Set style
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Professional color palette
        colors = ['#2563eb', '#16a34a', '#dc2626', '#ea580c', '#9333ea', 
                  '#0891b2', '#db2777', '#d97706', '#0d9488', '#4f46e5',
                  '#84cc16', '#06b6d4', '#f43f5e', '#8b5cf6', '#14b8a6']
        
        unique_labels = sorted([l for l in set(labels) if l >= 0])
        n_samples = len(labels)
        n_features = len(feature_names) if feature_names else 0
        
        # ==================================================================
        # 1. CLUSTER SCATTER PLOT (PCA 2D) - Always generate if possible
        # ==================================================================
        if X_2d is not None and len(X_2d) > 0:
            try:
                fig, ax = plt.subplots(figsize=(10, 8))
                
                for i, label in enumerate(sorted(set(labels))):
                    mask = labels == label
                    color = colors[i % len(colors)] if label >= 0 else '#6b7280'
                    label_name = f'Cluster {label}' if label >= 0 else 'Noise'
                    ax.scatter(X_2d[mask, 0], X_2d[mask, 1], 
                              c=color, label=label_name, alpha=0.7, s=50,
                              edgecolors='white', linewidth=0.5)
                
                # Add cluster centroids
                for i, label in enumerate(unique_labels):
                    mask = labels == label
                    centroid = X_2d[mask].mean(axis=0)
                    ax.scatter(centroid[0], centroid[1], c=colors[i % len(colors)], 
                              s=200, marker='X', edgecolors='black', linewidth=2, zorder=10)
                
                ax.set_xlabel('PCA Component 1', fontweight='bold', fontsize=12)
                ax.set_ylabel('PCA Component 2', fontweight='bold', fontsize=12)
                ax.set_title(f'🔮 {algorithm.upper()} Clustering (Silhouette: {silhouette:.3f})', 
                            fontweight='bold', pad=15, fontsize=14)
                ax.legend(loc='best', fontsize=10)
                ax.grid(alpha=0.3)
                fig.tight_layout()
                
                charts['cluster_scatter'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Cluster scatter plot failed: {e}")
        
        # ==================================================================
        # 2. ELBOW METHOD GRAPH - Only if k_scores provided
        # ==================================================================
        if k_scores and len(k_scores) >= 3:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                k_values = sorted(k_scores.keys())
                scores = [k_scores[k] for k in k_values]
                
                ax.plot(k_values, scores, 'bo-', linewidth=2, markersize=10)
                
                # Highlight optimal k
                optimal_k = k_values[np.argmax(scores)]
                optimal_score = max(scores)
                ax.scatter([optimal_k], [optimal_score], c='red', s=200, zorder=10, 
                          marker='*', label=f'Optimal k={optimal_k}')
                ax.axvline(x=optimal_k, color='red', linestyle='--', alpha=0.5)
                
                ax.set_xlabel('Number of Clusters (k)', fontweight='bold', fontsize=12)
                ax.set_ylabel('Silhouette Score', fontweight='bold', fontsize=12)
                ax.set_title('📈 Elbow Method - Optimal Cluster Selection', fontweight='bold', pad=15, fontsize=14)
                ax.legend(loc='best')
                ax.grid(alpha=0.3)
                fig.tight_layout()
                
                charts['elbow_method'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Elbow method chart failed: {e}")
        
        # ==================================================================
        # 3. SILHOUETTE SCORE PLOT - Need sklearn and enough samples
        # ==================================================================
        if X_scaled is not None and n_clusters >= 2 and n_samples >= 50:
            try:
                from sklearn.metrics import silhouette_samples
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                sample_silhouette_values = silhouette_samples(X_scaled, labels)
                
                y_lower = 10
                for i, label in enumerate(unique_labels):
                    cluster_silhouette_vals = sample_silhouette_values[labels == label]
                    cluster_silhouette_vals.sort()
                    
                    cluster_size = cluster_silhouette_vals.shape[0]
                    y_upper = y_lower + cluster_size
                    
                    ax.fill_betweenx(np.arange(y_lower, y_upper),
                                    0, cluster_silhouette_vals,
                                    facecolor=colors[i % len(colors)], alpha=0.7)
                    ax.text(-0.05, y_lower + 0.5 * cluster_size, f'Cluster {label}',
                           fontsize=10, fontweight='bold')
                    
                    y_lower = y_upper + 10
                
                ax.axvline(x=silhouette, color='red', linestyle='--', linewidth=2,
                          label=f'Mean: {silhouette:.3f}')
                ax.set_xlabel('Silhouette Coefficient', fontweight='bold', fontsize=12)
                ax.set_ylabel('Cluster', fontweight='bold', fontsize=12)
                ax.set_title('📊 Silhouette Analysis - Cluster Quality', fontweight='bold', pad=15, fontsize=14)
                ax.legend(loc='best')
                ax.grid(alpha=0.3, axis='x')
                fig.tight_layout()
                
                charts['silhouette_plot'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Silhouette plot failed: {e}")
        
        # ==================================================================
        # 4. CLUSTER DISTRIBUTION BAR CHART - Always generate
        # ==================================================================
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            cluster_names = [f'Cluster {l}' if l >= 0 else 'Noise' for l in sorted(set(labels))]
            cluster_counts = [np.sum(labels == l) for l in sorted(set(labels))]
            cluster_colors = [colors[i % len(colors)] if l >= 0 else '#6b7280' 
                             for i, l in enumerate(sorted(set(labels)))]
            
            bars = ax.bar(cluster_names, cluster_counts, color=cluster_colors, 
                         edgecolor='white', linewidth=2)
            
            # Add counts on bars
            for bar, count in zip(bars, cluster_counts):
                pct = count / n_samples * 100
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                       f'{count}\n({pct:.1f}%)', ha='center', va='bottom', 
                       fontweight='bold', fontsize=10)
            
            ax.set_xlabel('Cluster', fontweight='bold', fontsize=12)
            ax.set_ylabel('Number of Samples', fontweight='bold', fontsize=12)
            ax.set_title('📊 Cluster Size Distribution', fontweight='bold', pad=15, fontsize=14)
            ax.grid(axis='y', alpha=0.3)
            fig.tight_layout()
            
            charts['cluster_distribution'] = _fig_to_base64(fig)
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Distribution chart failed: {e}")
        
        # ==================================================================
        # 5. CLUSTER PROFILE HEATMAP - Need profiles and features
        # ==================================================================
        if cluster_profiles and len(feature_names) >= 3 and len(unique_labels) >= 2:
            try:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # Build heatmap data
                top_features = feature_names[:min(15, len(feature_names))]
                heatmap_data = []
                cluster_labels_list = []
                
                for cluster_name, profile in sorted(cluster_profiles.items()):
                    row = [profile.get(f, {}).get('mean', 0) for f in top_features]
                    heatmap_data.append(row)
                    cluster_labels_list.append(cluster_name)
                
                heatmap_array = np.array(heatmap_data)
                
                # Normalize per feature (column)
                for j in range(heatmap_array.shape[1]):
                    col_min = heatmap_array[:, j].min()
                    col_max = heatmap_array[:, j].max()
                    if col_max - col_min > 0:
                        heatmap_array[:, j] = (heatmap_array[:, j] - col_min) / (col_max - col_min)
                
                sns.heatmap(heatmap_array, annot=True, fmt='.2f', cmap='RdYlGn',
                           xticklabels=top_features, yticklabels=cluster_labels_list,
                           ax=ax, linewidths=0.5, cbar_kws={'label': 'Normalized Value'})
                
                ax.set_title('🔥 Cluster Profile Heatmap', fontweight='bold', pad=15, fontsize=14)
                ax.set_xlabel('Features', fontweight='bold', fontsize=12)
                ax.set_ylabel('Clusters', fontweight='bold', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                fig.tight_layout()
                
                charts['cluster_heatmap'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Heatmap failed: {e}")
        
        # ==================================================================
        # 6. PCA EXPLAINED VARIANCE PLOT - Need enough features
        # ==================================================================
        if X_scaled is not None and n_features >= 3:
            try:
                from sklearn.decomposition import PCA as PCAViz
                
                n_components = min(10, n_features, n_samples)
                pca_full = PCAViz(n_components=n_components)
                pca_full.fit(X_scaled)
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
                
                # Individual variance
                variance = pca_full.explained_variance_ratio_
                components = range(1, len(variance) + 1)
                ax1.bar(components, variance * 100, color=colors[0], edgecolor='white', linewidth=1.5)
                ax1.set_xlabel('Principal Component', fontweight='bold', fontsize=12)
                ax1.set_ylabel('Variance Explained (%)', fontweight='bold', fontsize=12)
                ax1.set_title('📊 Individual Variance per Component', fontweight='bold', pad=15, fontsize=14)
                ax1.grid(axis='y', alpha=0.3)
                
                # Cumulative variance
                cumulative = np.cumsum(variance) * 100
                ax2.plot(components, cumulative, 'bo-', linewidth=2, markersize=8)
                ax2.fill_between(components, cumulative, alpha=0.3, color=colors[0])
                ax2.axhline(y=90, color='red', linestyle='--', label='90% threshold')
                ax2.set_xlabel('Number of Components', fontweight='bold', fontsize=12)
                ax2.set_ylabel('Cumulative Variance (%)', fontweight='bold', fontsize=12)
                ax2.set_title('📈 Cumulative Explained Variance', fontweight='bold', pad=15, fontsize=14)
                ax2.legend()
                ax2.grid(alpha=0.3)
                
                fig.tight_layout()
                charts['pca_variance'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"PCA variance plot failed: {e}")
        
        # ==================================================================
        # 7. PAIRPLOT (Feature Relationships) - Need 2-4 features, <2000 samples
        # ==================================================================
        if X_original is not None and 2 <= n_features <= 6 and n_samples <= 2000:
            try:
                import pandas as pd
                
                # Select top 4 features
                plot_features = feature_names[:min(4, len(feature_names))]
                df_plot = pd.DataFrame(X_original[:, :len(plot_features)], columns=plot_features)
                df_plot['Cluster'] = [f'C{l}' for l in labels]
                
                palette = {f'C{l}': colors[i % len(colors)] for i, l in enumerate(unique_labels)}
                palette['C-1'] = '#6b7280'  # Noise
                
                g = sns.pairplot(df_plot, hue='Cluster', palette=palette, 
                                diag_kind='kde', plot_kws={'alpha': 0.6, 's': 30})
                g.fig.suptitle('🔍 Feature Relationships by Cluster', fontweight='bold', y=1.02, fontsize=14)
                
                charts['pairplot'] = _fig_to_base64(g.fig)
                plt.close(g.fig)
            except Exception as e:
                logger.warning(f"Pairplot failed: {e}")
        
        # ==================================================================
        # 8. 3D CLUSTER VISUALIZATION - Need 3+ features
        # ==================================================================
        if X_scaled is not None and n_features >= 3 and n_samples <= 5000:
            try:
                from sklearn.decomposition import PCA as PCA3D
                from mpl_toolkits.mplot3d import Axes3D
                
                pca_3d = PCA3D(n_components=3)
                X_3d = pca_3d.fit_transform(X_scaled)
                
                fig = plt.figure(figsize=(12, 10))
                ax = fig.add_subplot(111, projection='3d')
                
                for i, label in enumerate(sorted(set(labels))):
                    mask = labels == label
                    color = colors[i % len(colors)] if label >= 0 else '#6b7280'
                    label_name = f'Cluster {label}' if label >= 0 else 'Noise'
                    ax.scatter(X_3d[mask, 0], X_3d[mask, 1], X_3d[mask, 2],
                              c=color, label=label_name, alpha=0.6, s=30)
                
                ax.set_xlabel('PC1', fontweight='bold')
                ax.set_ylabel('PC2', fontweight='bold')
                ax.set_zlabel('PC3', fontweight='bold')
                ax.set_title('🌐 3D Cluster Visualization', fontweight='bold', pad=20, fontsize=14)
                ax.legend(loc='best')
                
                charts['cluster_3d'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"3D plot failed: {e}")
        
        # ==================================================================
        # 9. DENDROGRAM - Only for hierarchical clustering or when suitable
        # ==================================================================
        if algorithm == 'hierarchical' and X_scaled is not None and n_samples <= 500:
            try:
                from scipy.cluster.hierarchy import dendrogram, linkage
                
                # Use ward linkage
                Z = linkage(X_scaled[:min(200, n_samples)], method='ward')
                
                fig, ax = plt.subplots(figsize=(14, 8))
                dendrogram(Z, ax=ax, truncate_mode='lastp', p=30, 
                          leaf_rotation=90, leaf_font_size=10,
                          color_threshold=0.7*max(Z[:,2]))
                
                ax.set_xlabel('Sample Index / Cluster Size', fontweight='bold', fontsize=12)
                ax.set_ylabel('Distance', fontweight='bold', fontsize=12)
                ax.set_title('🌳 Hierarchical Clustering Dendrogram', fontweight='bold', pad=15, fontsize=14)
                ax.axhline(y=0.7*max(Z[:,2]), color='red', linestyle='--', 
                          label=f'Cut-off ({n_clusters} clusters)')
                ax.legend()
                fig.tight_layout()
                
                charts['dendrogram'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Dendrogram failed: {e}")
        
        # ==================================================================
        # 10. t-SNE VISUALIZATION - Best for <5000 samples
        # ==================================================================
        if X_scaled is not None and 100 <= n_samples <= 3000 and n_features >= 3:
            try:
                from sklearn.manifold import TSNE
                
                perplexity = min(30, n_samples // 5)
                tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, n_iter=500)
                X_tsne = tsne.fit_transform(X_scaled)
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                for i, label in enumerate(sorted(set(labels))):
                    mask = labels == label
                    color = colors[i % len(colors)] if label >= 0 else '#6b7280'
                    label_name = f'Cluster {label}' if label >= 0 else 'Noise'
                    ax.scatter(X_tsne[mask, 0], X_tsne[mask, 1],
                              c=color, label=label_name, alpha=0.7, s=40)
                
                ax.set_xlabel('t-SNE 1', fontweight='bold', fontsize=12)
                ax.set_ylabel('t-SNE 2', fontweight='bold', fontsize=12)
                ax.set_title('🔬 t-SNE Visualization', fontweight='bold', pad=15, fontsize=14)
                ax.legend(loc='best')
                ax.grid(alpha=0.3)
                fig.tight_layout()
                
                charts['tsne'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"t-SNE plot failed: {e}")
        
        # ==================================================================
        # 10b. UMAP VISUALIZATION - Optional (requires umap-learn package)
        # ==================================================================
        if X_scaled is not None and 100 <= n_samples <= 5000 and n_features >= 3:
            try:
                import umap
                
                reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
                X_umap = reducer.fit_transform(X_scaled)
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                for i, label in enumerate(sorted(set(labels))):
                    mask = labels == label
                    color = colors[i % len(colors)] if label >= 0 else '#6b7280'
                    label_name = f'Cluster {label}' if label >= 0 else 'Noise'
                    ax.scatter(X_umap[mask, 0], X_umap[mask, 1],
                              c=color, label=label_name, alpha=0.7, s=40)
                
                ax.set_xlabel('UMAP 1', fontweight='bold', fontsize=12)
                ax.set_ylabel('UMAP 2', fontweight='bold', fontsize=12)
                ax.set_title('🗺️ UMAP Visualization', fontweight='bold', pad=15, fontsize=14)
                ax.legend(loc='best')
                ax.grid(alpha=0.3)
                fig.tight_layout()
                
                charts['umap'] = _fig_to_base64(fig)
                plt.close(fig)
            except ImportError:
                logger.info("UMAP not installed - skipping UMAP visualization")
            except Exception as e:
                logger.warning(f"UMAP plot failed: {e}")
        
        # ==================================================================
        # 11. BOXPLOT PER CLUSTER - Need features
        # ==================================================================
        if X_original is not None and n_features >= 2 and len(unique_labels) >= 2:
            try:
                import pandas as pd
                
                # Select top 4 features for box plots
                top_features = feature_names[:min(4, len(feature_names))]
                n_plot = len(top_features)
                
                fig, axes = plt.subplots(1, n_plot, figsize=(4*n_plot, 6))
                if n_plot == 1:
                    axes = [axes]
                
                for idx, feature in enumerate(top_features):
                    feature_idx = feature_names.index(feature)
                    data_by_cluster = [X_original[labels == l, feature_idx] for l in unique_labels]
                    
                    bp = axes[idx].boxplot(data_by_cluster, patch_artist=True,
                                          labels=[f'C{l}' for l in unique_labels])
                    
                    for i, patch in enumerate(bp['boxes']):
                        patch.set_facecolor(colors[i % len(colors)])
                        patch.set_alpha(0.7)
                    
                    axes[idx].set_xlabel('Cluster', fontweight='bold', fontsize=11)
                    axes[idx].set_ylabel(feature, fontweight='bold', fontsize=11)
                    axes[idx].set_title(f'{feature}', fontweight='bold', fontsize=12)
                    axes[idx].grid(axis='y', alpha=0.3)
                
                fig.suptitle('📦 Feature Distribution by Cluster (Boxplots)', fontweight='bold', fontsize=14, y=1.02)
                fig.tight_layout()
                
                charts['boxplots'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Boxplot failed: {e}")
        
        # ==================================================================
        # 12. VIOLIN PLOT PER CLUSTER - Alternative to boxplot
        # ==================================================================
        if X_original is not None and n_features >= 2 and len(unique_labels) >= 2 and n_samples >= 50:
            try:
                import pandas as pd
                
                # Select top 3 features for violin plots
                top_features = feature_names[:min(3, len(feature_names))]
                
                fig, axes = plt.subplots(1, len(top_features), figsize=(5*len(top_features), 6))
                if len(top_features) == 1:
                    axes = [axes]
                
                for idx, feature in enumerate(top_features):
                    feature_idx = feature_names.index(feature)
                    
                    # Create dataframe for seaborn
                    df_violin = pd.DataFrame({
                        'Value': X_original[:, feature_idx],
                        'Cluster': [f'C{l}' for l in labels]
                    })
                    
                    palette = {f'C{l}': colors[i % len(colors)] for i, l in enumerate(unique_labels)}
                    
                    sns.violinplot(data=df_violin, x='Cluster', y='Value', 
                                  palette=palette, ax=axes[idx])
                    axes[idx].set_xlabel('Cluster', fontweight='bold', fontsize=11)
                    axes[idx].set_ylabel(feature, fontweight='bold', fontsize=11)
                    axes[idx].set_title(f'{feature}', fontweight='bold', fontsize=12)
                    axes[idx].grid(axis='y', alpha=0.3)
                
                fig.suptitle('🎻 Feature Distribution by Cluster (Violin Plots)', fontweight='bold', fontsize=14, y=1.02)
                fig.tight_layout()
                
                charts['violin_plots'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Violin plot failed: {e}")
        
        # ==================================================================
        # 13. CORRELATION HEATMAP - Need enough features
        # ==================================================================
        if X_original is not None and n_features >= 3:
            try:
                import pandas as pd
                
                df_corr = pd.DataFrame(X_original, columns=feature_names)
                corr_matrix = df_corr.corr()
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
                sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                           cmap='coolwarm', center=0, ax=ax,
                           linewidths=0.5, cbar_kws={'label': 'Correlation'})
                
                ax.set_title('🔗 Feature Correlation Heatmap', fontweight='bold', pad=15, fontsize=14)
                plt.xticks(rotation=45, ha='right')
                fig.tight_layout()
                
                charts['correlation_heatmap'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Correlation heatmap failed: {e}")
        
        # ==================================================================
        # 14. RADAR CHART FOR CLUSTER COMPARISON - Need profiles
        # ==================================================================
        if cluster_profiles and len(feature_names) >= 3 and len(unique_labels) >= 2:
            try:
                fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
                
                top_features = feature_names[:min(8, len(feature_names))]
                n_features_plot = len(top_features)
                angles = np.linspace(0, 2 * np.pi, n_features_plot, endpoint=False).tolist()
                angles += angles[:1]
                
                for cluster_name, profile in sorted(cluster_profiles.items()):
                    values = [profile.get(f, {}).get('mean', 0) for f in top_features]
                    
                    # Normalize to 0-1 range across all clusters
                    all_vals = [cluster_profiles[cn].get(f, {}).get('mean', 0) 
                               for cn in cluster_profiles for f in top_features]
                    val_min, val_max = min(all_vals), max(all_vals)
                    if val_max - val_min > 0:
                        values = [(v - val_min) / (val_max - val_min) for v in values]
                    values += values[:1]
                    
                    cluster_idx = int(cluster_name.split()[-1])
                    ax.plot(angles, values, 'o-', linewidth=2, 
                           label=cluster_name, color=colors[cluster_idx % len(colors)])
                    ax.fill(angles, values, alpha=0.15, color=colors[cluster_idx % len(colors)])
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(top_features, fontsize=10)
                ax.set_title('🎯 Radar Chart - Cluster Comparison', fontweight='bold', pad=25, fontsize=14)
                ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
                fig.tight_layout()
                
                charts['radar_chart'] = _fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Radar chart failed: {e}")
        
        logger.info(f"✅ Generated {len(charts)} clustering charts")
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        import traceback
        traceback.print_exc()
    
    return charts


def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


def _save_clustering_model(user_id: str, model_id: str, model_data: Dict):
    """Save clustering model for predictions."""
    try:
        paths = get_user_paths(user_id)
        models_dir = paths.get("models", paths["base"] / "models")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = models_dir / f"{model_id}.json"
        with open(model_path, 'w') as f:
            json.dump(model_data, f)
        
        # Also save as active clustering model
        active_path = models_dir / "active_clustering.json"
        with open(active_path, 'w') as f:
            json.dump({'model_id': model_id, **model_data}, f)
        
        logger.info(f"✅ Saved clustering model: {model_path}")
    except Exception as e:
        logger.warning(f"Failed to save model: {e}")


# ===========================================================================
# 🔮 CLUSTER PREDICTION ENDPOINT
# ===========================================================================

@router.post("/clustering/predict")
async def predict_cluster(
    request: ClusterPredictRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Predict which cluster a new data point belongs to.
    
    Uses the saved model to find the nearest cluster centroid.
    """
    user_id = request.user_id or x_user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    try:
        # Load model
        paths = get_user_paths(user_id)
        models_dir = paths.get("models", paths["base"] / "models")
        
        model_path = models_dir / f"{request.model_id}.json"
        if not model_path.exists():
            # Try active model
            model_path = models_dir / "active_clustering.json"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="Clustering model not found. Run clustering first.")
        
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        # Prepare input features
        feature_columns = model_data['feature_columns']
        features_array = np.array([request.features.get(col, 0) for col in feature_columns]).reshape(1, -1)
        
        # Scale features
        scaler_mean = np.array(model_data['scaler_mean'])
        scaler_scale = np.array(model_data['scaler_scale'])
        features_scaled = (features_array - scaler_mean) / scaler_scale
        
        # Find nearest centroid
        centroids = np.array(model_data['centroids_scaled'])
        if len(centroids) == 0:
            raise HTTPException(status_code=400, detail="No cluster centroids available")
        
        distances = np.linalg.norm(centroids - features_scaled, axis=1)
        predicted_cluster = int(np.argmin(distances))
        confidence = float(1.0 / (1.0 + distances[predicted_cluster]))
        
        # Get cluster characteristics
        cluster_name = f"Cluster {predicted_cluster}"
        
        return {
            'success': True,
            'cluster': predicted_cluster,
            'cluster_name': cluster_name,
            'confidence': confidence,
            'distances_to_centroids': distances.tolist(),
            'algorithm': model_data.get('algorithm', 'unknown'),
            'n_clusters': model_data.get('n_clusters', len(centroids)),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cluster prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clustering/models/{user_id}/active")
async def get_active_clustering_model(user_id: str):
    """Get the active clustering model for a user."""
    try:
        paths = get_user_paths(user_id)
        models_dir = paths.get("models", paths["base"] / "models")
        active_path = models_dir / "active_clustering.json"
        
        if not active_path.exists():
            return {'success': True, 'has_model': False}
        
        with open(active_path, 'r') as f:
            model_data = json.load(f)
        
        return {
            'success': True,
            'has_model': True,
            'model_id': model_data.get('model_id'),
            'algorithm': model_data.get('algorithm'),
            'n_clusters': model_data.get('n_clusters'),
            'created_at': model_data.get('created_at'),
        }
    except Exception as e:
        logger.error(f"Failed to get active model: {e}")
        return {'success': False, 'error': str(e)}


# ===========================================================================
# LEGACY FILE UPLOAD ENDPOINTS (Keep for backward compatibility)
# ===========================================================================


@router.post("/cluster")
async def perform_clustering(
    file: UploadFile = File(...),
    algorithm: str = Form("kmeans"),
    n_clusters: Optional[int] = Form(3),
    features: Optional[str] = Form(None),
    eps: Optional[float] = Form(0.5),
    min_samples: Optional[int] = Form(5),
    normalize: bool = Form(True)
):
    """
    Perform clustering analysis on uploaded data
    
    Parameters:
    - algorithm: 'kmeans', 'dbscan', 'gmm', 'spectral'
    - n_clusters: Number of clusters (for kmeans, gmm, spectral)
    - features: Comma-separated feature names (optional)
    - eps: DBSCAN epsilon parameter
    - min_samples: DBSCAN min samples parameter
    - normalize: Whether to normalize features
    """
    try:
        # Read uploaded file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        logger.info(f"📊 Clustering {len(df)} rows with {algorithm.upper()}")
        
        # Select features
        if features:
            feature_list = [f.strip() for f in features.split(",")]
            X = df[feature_list].select_dtypes(include=[np.number])
        else:
            X = df.select_dtypes(include=[np.number])
        
        if X.empty:
            raise HTTPException(status_code=400, detail="No numeric features found")
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Normalize if requested
        if normalize:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X.values
        
        # Perform clustering
        if algorithm == "kmeans":
            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = model.fit_predict(X_scaled)
            cluster_centers = model.cluster_centers_
            
        elif algorithm == "dbscan":
            model = DBSCAN(eps=eps, min_samples=min_samples)
            labels = model.fit_predict(X_scaled)
            cluster_centers = None
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
        elif algorithm == "gmm":
            model = GaussianMixture(n_components=n_clusters, random_state=42)
            labels = model.fit_predict(X_scaled)
            cluster_centers = model.means_
            
        elif algorithm == "spectral":
            model = SpectralClustering(n_clusters=n_clusters, random_state=42)
            labels = model.fit_predict(X_scaled)
            cluster_centers = None
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown algorithm: {algorithm}")
        
        # Calculate metrics (only if more than 1 cluster)
        metrics = {}
        if len(set(labels)) > 1 and len(set(labels)) < len(X_scaled):
            try:
                metrics["silhouette_score"] = float(silhouette_score(X_scaled, labels))
                metrics["davies_bouldin_score"] = float(davies_bouldin_score(X_scaled, labels))
                metrics["calinski_harabasz_score"] = float(calinski_harabasz_score(X_scaled, labels))
            except Exception as e:
                logger.warning(f"Could not calculate metrics: {e}")
        
        # PCA for visualization (2D)
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # Prepare results
        cluster_counts = pd.Series(labels).value_counts().to_dict()
        
        # =============================================================
        # 🛡️ PRODUCTION INTELLIGENCE: Data quality & reliability
        # =============================================================
        reliability_score = 75  # Default
        validation_warnings = []
        data_quality = {}
        
        try:
            # 1. Check data quality
            n_samples = len(df)
            n_features = X.shape[1]
            missing_ratio = df.isna().sum().sum() / df.size if df.size > 0 else 0
            duplicate_ratio = df.duplicated().sum() / n_samples if n_samples > 0 else 0
            
            data_quality = {
                'n_samples': n_samples,
                'n_features': n_features,
                'missing_ratio': float(missing_ratio),
                'duplicate_ratio': float(duplicate_ratio),
                'size_category': 'small' if n_samples < 500 else 'medium' if n_samples < 5000 else 'large'
            }
            
            # Data quality warnings
            if missing_ratio > 0.2:
                validation_warnings.append(f"⚠️ High missing data: {missing_ratio:.1%} - may affect cluster quality")
            if duplicate_ratio > 0.1:
                validation_warnings.append(f"⚠️ Many duplicates: {duplicate_ratio:.1%} - consider removing")
            if n_samples < 100:
                validation_warnings.append(f"⚠️ Small dataset ({n_samples} samples) - clusters may be unreliable")
            if n_features > 50:
                validation_warnings.append(f"⚠️ High dimensionality ({n_features} features) - consider dimensionality reduction")
            
            # 2. Compute reliability score for clustering
            # Based on silhouette score, cluster separation, and sample size
            silhouette = metrics.get('silhouette_score', 0)
            calinski = metrics.get('calinski_harabasz_score', 0)
            davies = metrics.get('davies_bouldin_score', float('inf'))
            
            # Silhouette contributes 40 points (scaled from -1 to 1)
            silhouette_points = max(0, (silhouette + 1) / 2 * 40)
            
            # Calinski-Harabasz contributes 25 points (log-scaled)
            import math
            calinski_points = min(25, math.log(calinski + 1) * 3) if calinski > 0 else 0
            
            # Davies-Bouldin contributes 20 points (lower is better)
            davies_points = max(0, 20 - davies * 5) if davies < float('inf') else 10
            
            # Sample size contributes 15 points
            if n_samples >= 1000:
                size_points = 15
            elif n_samples >= 500:
                size_points = 12
            elif n_samples >= 100:
                size_points = 8
            else:
                size_points = 5
            
            reliability_score = min(100, silhouette_points + calinski_points + davies_points + size_points)
            
            # Add cluster quality assessment
            if silhouette < 0.2:
                validation_warnings.append(f"⚠️ Low silhouette score ({silhouette:.3f}) - clusters may overlap significantly")
            if silhouette > 0.7:
                logger.info(f"✅ Excellent cluster separation (silhouette={silhouette:.3f})")
            
            logger.info(f"🛡️ Clustering Reliability Score: {reliability_score:.1f}/100")
            
        except Exception as intel_err:
            logger.warning(f"Production Intelligence check failed: {intel_err}")
        
        result = {
            "algorithm": algorithm,
            "n_clusters": n_clusters if algorithm != "dbscan" else len(set(labels)) - (1 if -1 in labels else 0),
            "n_samples": len(df),
            "n_features": X.shape[1],
            "features_used": list(X.columns),
            "labels": labels.tolist(),
            "cluster_counts": {str(k): int(v) for k, v in cluster_counts.items()},
            "metrics": metrics,
            "visualization": {
                "x": X_pca[:, 0].tolist(),
                "y": X_pca[:, 1].tolist(),
                "explained_variance": pca.explained_variance_ratio_.tolist()
            },
            # 🛡️ PRODUCTION INTELLIGENCE outputs
            "reliability_score": reliability_score,
            "validation_warnings": validation_warnings if validation_warnings else None,
            "data_quality": data_quality,
        }
        
        # Add cluster centers if available
        if cluster_centers is not None:
            if normalize:
                cluster_centers = scaler.inverse_transform(cluster_centers)
            result["cluster_centers"] = cluster_centers.tolist()
        
        logger.info(f"✅ Clustering complete: {result['n_clusters']} clusters found")
        
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Empty CSV file")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Feature not found: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Clustering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cluster/optimal")
async def find_optimal_clusters(
    file: UploadFile = File(...),
    algorithm: str = Form("kmeans"),
    max_clusters: int = Form(10),
    features: Optional[str] = Form(None),
    normalize: bool = Form(True)
):
    """
    Find optimal number of clusters using elbow method and silhouette analysis
    """
    try:
        # Read uploaded file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Select features
        if features:
            feature_list = [f.strip() for f in features.split(",")]
            X = df[feature_list].select_dtypes(include=[np.number])
        else:
            X = df.select_dtypes(include=[np.number])
        
        if X.empty:
            raise HTTPException(status_code=400, detail="No numeric features found")
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Normalize if requested
        if normalize:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X.values
        
        # Test different numbers of clusters
        inertias = []
        silhouettes = []
        k_range = range(2, min(max_clusters + 1, len(X_scaled)))
        
        for k in k_range:
            if algorithm == "kmeans":
                model = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = model.fit_predict(X_scaled)
                inertias.append(model.inertia_)
            elif algorithm == "gmm":
                model = GaussianMixture(n_components=k, random_state=42)
                labels = model.fit_predict(X_scaled)
                inertias.append(-model.bic(X_scaled))  # Negative BIC
            else:
                raise HTTPException(status_code=400, detail=f"Optimal search not supported for {algorithm}")
            
            # Calculate silhouette score
            silhouette = silhouette_score(X_scaled, labels)
            silhouettes.append(silhouette)
        
        # Find optimal k (highest silhouette)
        optimal_k = list(k_range)[np.argmax(silhouettes)]
        
        return {
            "algorithm": algorithm,
            "k_range": list(k_range),
            "inertias": inertias,
            "silhouette_scores": silhouettes,
            "optimal_k": optimal_k,
            "max_silhouette": max(silhouettes)
        }
        
    except Exception as e:
        logger.error(f"❌ Optimal clustering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/info")
async def get_clustering_info():
    """
    Get information about available clustering algorithms
    """
    return {
        "algorithms": {
            "kmeans": {
                "name": "K-Means",
                "description": "Partition-based clustering that minimizes within-cluster variance",
                "parameters": ["n_clusters"],
                "pros": ["Fast", "Scalable", "Works well with spherical clusters"],
                "cons": ["Requires specifying k", "Sensitive to outliers", "Assumes spherical clusters"]
            },
            "dbscan": {
                "name": "DBSCAN",
                "description": "Density-based clustering that can find arbitrarily shaped clusters",
                "parameters": ["eps", "min_samples"],
                "pros": ["No need to specify k", "Finds arbitrary shapes", "Identifies outliers"],
                "cons": ["Sensitive to parameters", "Struggles with varying densities"]
            },
            "gmm": {
                "name": "Gaussian Mixture Model",
                "description": "Probabilistic model that assumes data is generated from mixture of Gaussians",
                "parameters": ["n_clusters"],
                "pros": ["Soft clustering", "Provides probabilities", "Flexible cluster shapes"],
                "cons": ["Computationally expensive", "Sensitive to initialization"]
            },
            "spectral": {
                "name": "Spectral Clustering",
                "description": "Uses eigenvalues of similarity matrix to reduce dimensions before clustering",
                "parameters": ["n_clusters"],
                "pros": ["Works with non-convex clusters", "Graph-based approach"],
                "cons": ["Computationally expensive", "Memory intensive for large datasets"]
            }
        },
        "metrics": {
            "silhouette_score": "Measures how similar a point is to its own cluster vs other clusters (-1 to 1, higher is better)",
            "davies_bouldin_score": "Average similarity ratio of each cluster with most similar cluster (lower is better)",
            "calinski_harabasz_score": "Ratio of between-cluster to within-cluster dispersion (higher is better)"
        }
    }


@router.get("/clustering/download-model/{user_id}")
async def download_clustering_model(user_id: str):
    """
    Download the trained clustering model as PKL file
    """
    from fastapi.responses import FileResponse
    
    try:
        paths = get_user_paths(user_id)
        models_dir = paths.get("models", paths["base"] / "models")
        
        # Find the latest clustering model
        pkl_files = list(models_dir.glob("clustering_model_*.pkl"))
        
        if not pkl_files:
            raise HTTPException(status_code=404, detail="No clustering model found. Train a model first.")
        
        # Get the most recent file
        latest_pkl = max(pkl_files, key=lambda p: p.stat().st_mtime)
        
        return FileResponse(
            path=str(latest_pkl),
            media_type='application/octet-stream',
            filename=latest_pkl.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clustering/download-data/{user_id}")
async def download_clustered_data(user_id: str):
    """
    Download the cleaned data with cluster assignments
    """
    from fastapi.responses import FileResponse
    
    try:
        paths = get_user_paths(user_id)
        files_dir = paths.get("files", paths["base"] / "files")
        
        # Find the latest clustered data file
        csv_files = list(files_dir.glob("clustered_data_*.csv"))
        
        if not csv_files:
            raise HTTPException(status_code=404, detail="No clustered data found. Run clustering first.")
        
        # Get the most recent file
        latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
        
        return FileResponse(
            path=str(latest_csv),
            media_type='text/csv',
            filename=latest_csv.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))