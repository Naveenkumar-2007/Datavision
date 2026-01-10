"""
🚀 AUTOML API - Production ML Endpoints
========================================
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import pandas as pd
import io

logger = logging.getLogger(__name__)
router = APIRouter()


class PredictRequest(BaseModel):
    user_id: str
    model_name: str
    data: dict


@router.post("/production_train")
async def production_train(
    file: UploadFile = File(...),
    target_column: Optional[str] = Form(None),
    user_id: str = Form("default")
):
    """
    🚀 SILICON VALLEY GRADE ML TRAINING
    
    Uses production-grade pipeline for 80%+ accuracy:
    - Smart data cleaning
    - Advanced feature engineering
    - 15+ algorithms (XGBoost, LightGBM, CatBoost, etc.)
    - Ensemble methods
    """
    try:
        print("🚀 [PRODUCTION] Silicon Valley Grade Training")
        
        content = await file.read()
        filename = file.filename or "data.csv"
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        print(f"📂 File: {filename} ({df.shape[0]} rows, {df.shape[1]} cols)")
        
        from ml.automl_engine import automl_engine
        
        # Run synchronous blocking training in a separate thread
        # This allows the API to process /stop_training requests concurrently
        import asyncio
        loop = asyncio.get_running_loop()
        print(f"🧵 Offloading training to thread pool for user {user_id}")
        result = await loop.run_in_executor(
            None, 
            lambda: automl_engine.production_train(df, target_column, user_id)
        )
        
        # Use charts already generated during training
        charts = result.charts or {}
        print(f"📊 Charts available: {list(charts.keys())}")
        
        # JSON safe helper
        def json_safe(obj):
            import math
            import numpy as np
            if obj is None: return None
            if isinstance(obj, (np.integer,)): return int(obj)
            if isinstance(obj, (np.floating,)):
                return None if math.isnan(obj) or math.isinf(obj) else float(obj)
            if isinstance(obj, float):
                return None if math.isnan(obj) or math.isinf(obj) else obj
            if isinstance(obj, dict): return {k: json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list): return [json_safe(v) for v in obj]
            if isinstance(obj, np.ndarray): return json_safe(obj.tolist())
            return obj
        
        return json_safe({
            "success": True,
            "pipeline": "SILICON_VALLEY_GRADE",
            "task_type": result.task_type,
            "target_column": result.target_column,
            "data_summary": {
                "rows": result.n_rows,
                "columns": result.n_cols,
                "features_used": len(result.feature_columns)
            },
            "best_model": {
                "name": result.best_model_name,
                "metrics": result.best_model_metrics
            },
            "all_models": result.leaderboard,
            "feature_importance": result.feature_importance,
            "charts": charts,  # Generated matplotlib charts
            "processing_time_seconds": result.processing_time,
            "cleaned_file": getattr(result, 'cleaned_file_path', None), # Return cleaned filename
            "feature_columns": result.feature_columns,  # For predictions
            "feature_metadata": getattr(result, 'feature_metadata', []),
            "insights": [
                f"🚀 Silicon Valley Grade Pipeline",
                f"🏆 Best: {result.best_model_name}",
                f"📊 Trained with 15+ algorithms"
            ]
        })
        
    except Exception as e:
        if "Training cancelled" in str(e):
            print(f"🛑 Training stopped for user {user_id}")
            return {"success": False, "detail": "Training stopped by user request"}

        logger.error(f"Production train error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train_with_test")
async def train_with_test_file(
    train_file: UploadFile = File(..., description="Training data file"),
    test_file: UploadFile = File(..., description="Test/evaluation data file"),
    target_column: Optional[str] = Form(None),
    user_id: str = Form("default")
):
    """
    Train with SEPARATE train and test files.
    Use this when you have pre-split training and test datasets.
    """
    try:
        print("🚀 [AUTOML] Training with separate train/test files")
        
        # Load train file
        train_content = await train_file.read()
        train_filename = train_file.filename or "train.csv"
        if train_filename.endswith('.csv'):
            train_df = pd.read_csv(io.BytesIO(train_content))
        else:
            train_df = pd.read_excel(io.BytesIO(train_content))
        print(f"📂 [AUTOML] Train file: {train_filename} ({train_df.shape[0]} rows)")
        
        # Load test file
        test_content = await test_file.read()
        test_filename = test_file.filename or "test.csv"
        if test_filename.endswith('.csv'):
            test_df = pd.read_csv(io.BytesIO(test_content))
        else:
            test_df = pd.read_excel(io.BytesIO(test_content))
        print(f"📂 [AUTOML] Test file: {test_filename} ({test_df.shape[0]} rows)")
        
        # Validate columns match
        if set(train_df.columns) != set(test_df.columns):
            missing_in_test = set(train_df.columns) - set(test_df.columns)
            missing_in_train = set(test_df.columns) - set(train_df.columns)
            raise HTTPException(
                status_code=400, 
                detail=f"Column mismatch. Missing in test: {missing_in_test}, Missing in train: {missing_in_train}"
            )
        
        from ml.automl_engine import automl_engine
        from ml.chart_generator import chart_generator
        
        # Train with separate test set
        result = await automl_engine.train_with_test_set(
            train_df=train_df,
            test_df=test_df,
            target_col=target_column,
            user_id=user_id
        )
        
        # Use charts already generated during training
        charts = result.charts or {}
        print(f"📊 Charts available: {list(charts.keys())}")
        
        # Helper for JSON safety
        def json_safe(obj):
            import math
            import numpy as np
            if obj is None: return None
            if isinstance(obj, (np.integer,)): return int(obj)
            if isinstance(obj, (np.floating,)):
                return None if math.isnan(obj) or math.isinf(obj) else float(obj)
            if isinstance(obj, float):
                return None if math.isnan(obj) or math.isinf(obj) else obj
            if isinstance(obj, dict): return {k: json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list): return [json_safe(v) for v in obj]
            if isinstance(obj, np.ndarray): return json_safe(obj.tolist())
            return obj
        
        return json_safe({
            "success": True,
            "task_type": result.task_type,
            "target_column": result.target_column,
            "data_summary": {
                "train_rows": train_df.shape[0],
                "test_rows": test_df.shape[0],
                "columns": train_df.shape[1],
                "features_used": len(result.feature_columns)
            },
            "best_model": {
                "name": result.best_model_name,
                "metrics": result.best_model_metrics
            },
            "all_models": result.leaderboard,
            "feature_importance": result.feature_importance,
            "charts": charts,
            "processing_time_seconds": result.processing_time,
            "insights": [
                f"🏆 Best model: {result.best_model_name}",
                f"📊 Trained on {train_df.shape[0]} samples, tested on {test_df.shape[0]} samples"
            ]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AutoML error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_automl(
    file: UploadFile = File(...),
    target_column: Optional[str] = Form(None),
    user_id: str = Form("default")
):
    """
    Full AutoML training pipeline with BOTH:
    - Supervised Learning (Classification/Regression)
    - Unsupervised Learning (Clustering)
    """
    try:
        print("🚀 [AUTOML] Training request received")
        
        # Load file
        content = await file.read()
        filename = file.filename or "data.csv"
        print(f"📂 [AUTOML] File: {filename}")
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
        
        print(f"📊 [AUTOML] Data: {df.shape[0]} rows, {df.shape[1]} columns")
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="Empty dataset")
        
        # =========================================
        # SUPERVISED LEARNING (SILICON VALLEY GRADE)
        # =========================================
        from ml.automl_engine import automl_engine
        import asyncio
        loop = asyncio.get_running_loop()
        
        # Use production training ONLY (no legacy fallback - legacy has broken prediction)
        # Run in thread pool to prevent blocking event loop (Crucial for Cancellation)
        result = await loop.run_in_executor(
            None,
            lambda: automl_engine.production_train(df, target_column, user_id)
        )
        
        # =========================================
        # GENERATE PRODUCTION ML CHARTS (Base64 Images)
        # =========================================
        # Use charts already generated during training
        charts = result.charts or {}
        print(f"📊 Charts available: {list(charts.keys())}")
        
        # =========================================
        # UNSUPERVISED LEARNING (AUTO CLUSTERING)
        # =========================================
        clustering_result = None
        try:
            print("🔮 [AUTOML] Running automatic clustering...")
            clustering_result = automl_engine.run_clustering(df, n_clusters=None, algorithm='kmeans')
            
            if clustering_result.get('success'):
                print(f"   ✅ Clustering: {clustering_result.get('n_clusters')} clusters found")
                print(f"   📊 Silhouette Score: {clustering_result.get('metrics', {}).get('silhouette_score', 0):.3f}")
                
                # Add clustering charts
                if clustering_result.get('charts'):
                    charts.update(clustering_result['charts'])
            else:
                print(f"   ⚠️ Clustering skipped: {clustering_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"⚠️ Clustering error: {e}")
        
        # Helper to make values JSON-safe (NaN/inf -> None)
        def json_safe(obj):
            import math
            import numpy as np
            if obj is None:
                return None
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float64, np.float32)):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return float(obj)
            if isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return obj
            if isinstance(obj, dict):
                return {k: json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [json_safe(v) for v in obj]
            if isinstance(obj, np.ndarray):
                return json_safe(obj.tolist())
            return obj
        
        # Build response
        response = {
            "success": True,
            "task_type": result.task_type,
            "target_column": result.target_column,
            "data_summary": {
                "rows": result.n_rows,
                "columns": result.n_cols,
                "features_engineered": len(result.feature_columns)
            },
            "best_model": {
                "name": result.best_model_name,
                "metrics": json_safe(result.best_model_metrics)
            },
            "all_models": json_safe(result.leaderboard),
            "feature_importance": json_safe(result.feature_importance),
            "feature_metadata": json_safe(result.feature_metadata),
            "feature_columns": result.feature_columns,
            "charts": json_safe(charts),
            "processing_time_seconds": json_safe(result.processing_time),
            "cleaned_file": getattr(result, 'cleaned_file_path', None),
            "is_nlp_task": getattr(result, 'is_nlp_task', False),
            "primary_text_col": getattr(result, 'primary_text_col', None),
            "bias_reports": [],
            "insights": [
                f"🏆 Best model: {result.best_model_name}",
                f"📊 Trained on {result.n_rows} samples with {len(result.feature_columns)} features",
                f"⚡ Task type: {result.task_type}"
            ],
            "recommendations": [
                "Use the 'Predictions' tab to make real-time predictions",
                "View 'Clustering' tab for customer segmentation insights"
            ]
        }
        
        # Add clustering results if available
        if clustering_result and clustering_result.get('success'):
            response['clustering'] = {
                'algorithm': clustering_result.get('algorithm'),
                'n_clusters': clustering_result.get('n_clusters'),
                'silhouette_score': json_safe(clustering_result.get('metrics', {}).get('silhouette_score')),
                'cluster_distribution': json_safe(clustering_result.get('cluster_distribution'))
            }
            response['insights'].append(f"🔮 Found {clustering_result.get('n_clusters')} natural clusters in your data")
        
        return json_safe(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AutoML error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def predict(request: PredictRequest):
    """Make prediction"""
    try:
        from ml.automl_engine import automl_engine
        
        print(f"🔮 [PREDICT] Input: {request.data}")
        
        # Load model if not in memory
        if automl_engine.model is None:
            loaded = automl_engine.load(request.user_id)
            if not loaded:
                raise HTTPException(status_code=400, detail="No model trained. Please train first.")
        
        result = automl_engine.predict(request.data)
        print(f"🔮 [PREDICT] Output: {result}")
        
        return {
            "success": True,
            "prediction": result['prediction'],
            "probability": result.get('probability'),
            "confidence": result.get('confidence'),
            "model": result.get('model'),
            "message": f"Predicted using {result.get('model')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get engine status"""
    try:
        from ml.automl_engine import automl_engine
        return {
            "ready": True,
            "model_trained": automl_engine.model is not None,
            "best_model": automl_engine.model_name,
            "feature_columns": automl_engine.feature_columns,
            "feature_metadata": automl_engine.get_feature_metadata()
        }
    except:
        return {"ready": True, "model_trained": False}


@router.post("/stop_training")
async def stop_training(user_id: str = Form(...)):
    """
    ⛔ stop current training task for user
    Sets the cancellation flag which checked by the training engine loop.
    """
    try:
        print(f"🛑 [STOP] Received stop request for user: {user_id}")
        from ml.automl_engine import cancel_training
        cancel_training(user_id)
        return {"success": True, "message": "Training stop signal sent"}
    except Exception as e:
        logger.error(f"Stop error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/predict")
async def make_prediction(request: PredictRequest):
    """
    🔮 MAKE PREDICTION - Use trained model to predict new data
    
    Uses AutoMLEngine hydration to ensure exact feature pipeline replication.
    """
    try:
        print(f"🔮 [PREDICT] Request from user: {request.user_id}")
        
        from ml.model_persistence import ModelPersistenceManager
        from ml.automl_engine import ProductionMLEngine
        import numpy as np
        
        # Load the model state
        persistence = ModelPersistenceManager()
        engine_state = persistence.load_model(request.user_id)
        
        if not engine_state:
            return {
                "success": False,
                "error": "No trained model found. Please train a model first."
            }
            
        # 1. Hydrate ProductionMLEngine (Silicon Valley V2)
        # matches the definition in automl_engine.py
        try:
            # Create fresh engine
            engine = ProductionMLEngine()
            
            # Load state dict into engine instance
            if isinstance(engine_state, dict):
                # Manually restore critical attributes for _preprocess_single
                # (ProductionMLEngine uses these keys)
                engine.model = engine_state.get('model') or engine_state.get('best_model')
                engine.numeric_cols = engine_state.get('numeric_cols', [])
                engine.categorical_cols = engine_state.get('categorical_cols', [])
                engine.text_cols = engine_state.get('text_cols', [])
                engine.numeric_fill_values = engine_state.get('numeric_fill_values', {})
                engine.scaler = engine_state.get('scaler')
                engine.label_encoders = engine_state.get('label_encoders', {})
                engine.text_vectorizers = engine_state.get('text_vectorizers', {})
                engine.text_svd_transformers = engine_state.get('text_svd_transformers', {})
                engine.is_nlp_task = engine_state.get('is_nlp_task', False)
                engine.primary_text_col = engine_state.get('primary_text_col')
                engine.task_type_simple = engine_state.get('task_type_simple', 'regression')
                engine.target_encoder = engine_state.get('target_encoder')
                
                # Restore feature engineer (Critical for Poly features)
                engine.feature_engineer = engine_state.get('feature_engineer')
                
                # Also restore production engineer if present
                engine.production_engineer = engine_state.get('production_engineer')
            else:
                # Fallback for old simple model saves
                engine.model = engine_state
        
            if engine.model is None:
                 return {"success": False, "error": "Model object missing in saved state"}
                 
        except Exception as e:
            logger.error(f"Hydration failed: {e}")
            return {"success": False, "error": f"Failed to load model architecture: {e}"}

        # 2. Preprocess Input
        # Uses the engine's internal logic to handle missing vals, encoding, scaling exactly like training
        try:
            print("🔮 [PREDICT] Running AutoMLEngine._preprocess_single...")
            X_input = engine._preprocess_single(request.data)
            print(f"🔮 [PREDICT] Processed input shape: {X_input.shape}")
        except Exception as pre_err:
            logger.error(f"Preprocessing failed: {pre_err}")
            return {"success": False, "error": f"Data preprocessing failed: {pre_err}"}
            
        # 3. Predict
        prediction = engine.model.predict(X_input)
        
        # 4. Format Output
        if engine.task_type_simple == 'classification':
            # Handle classification output
            label = str(prediction[0])
            if engine.target_encoder:
                try:
                    label = engine.target_encoder.inverse_transform(prediction)[0]
                except:
                    pass
            elif hasattr(engine, 'label_encoders') and 'target' in engine.label_encoders:
                 # Fallback if target was encoded as a feature
                 pass
            
            # Probabilities
            probs = None
            if hasattr(engine.model, 'predict_proba'):
                try:
                    probs_arr = engine.model.predict_proba(X_input)[0]
                    if engine.target_encoder:
                         probs = {str(engine.target_encoder.inverse_transform([i])[0]): float(p) for i, p in enumerate(probs_arr)}
                    else:
                         probs = {f"class_{i}": float(p) for i, p in enumerate(probs_arr)}
                except:
                    pass

            return {
                "success": True,
                "task_type": "classification",
                "prediction": label,
                "probabilities": probs,
                "model_used": type(engine.model).__name__
            }
        else:
            # Regression
            val = float(prediction[0])
            
            # IMPORTANT: Current engine does NOT scale Y for regression, 
            # so raw output is correct.
            
            return {
                "success": True,
                "task_type": "regression",
                "prediction": val,
                "formatted_prediction": f"{val:,.4f}",
                "model_used": type(engine.model).__name__
            }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

