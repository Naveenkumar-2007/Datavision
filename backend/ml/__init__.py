"""
DataVision ML Module
====================

Production-grade Machine Learning components:
- AutoML Engine: Automated model training and selection
- Clustering Engine: K-Means, DBSCAN, K-Prototypes, K-Modes
- Model Persistence: Save/load trained models per user
- Feature Engineering: Advanced data preprocessing
- Explainability: SHAP-based model explanations
"""

# Lazy imports to avoid circular dependencies and reduce startup time
__all__ = [
    'automl_engine',
    'ProductionMLEngine',
    'ProductionClusteringEngine',
    'ModelPersistenceManager',
]
