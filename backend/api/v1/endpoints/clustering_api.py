"""
🎯 Clustering API - Unsupervised Machine Learning
=================================================
Provides K-Means, DBSCAN, GMM, and Spectral Clustering algorithms

🛡️ PRODUCTION INTELLIGENCE INTEGRATED:
- Data quality assessment
- Feature validation
- Missing data handling
- Reliability scoring for cluster quality
- Validation warnings
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, SpectralClustering
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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
