"""
🧪 PREDICTION TESTING SCRIPT
Tests the trained model against real data and analyzes prediction accuracy.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, r"c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\backend")

def test_predictions():
    """Test predictions and compare with actual values"""
    
    user_id = "21ed4a72-43de-4689-9556-7b866d79e9de"
    
    # Load the original data
    data_path = rf"c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\backend\storage\users\{user_id}\files\top_250_crypto_20251222.csv"
    
    print("=" * 60)
    print("🧪 PREDICTION TESTING SCRIPT")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(data_path)
    print(f"\n📂 Loaded data: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"📊 Columns: {list(df.columns)}")
    print(f"\n📈 Sample data:")
    print(df.head(5))
    
    # Load saved model
    from ml.model_persistence import ModelPersistenceManager
    
    # Handle path resolution based on where script is run from
    if os.path.exists("backend/storage/models"):
        storage_path = "backend/storage/models"
    elif os.path.exists("storage/models"):
        storage_path = "storage/models"
    else:
        # Fallback to absolute assumption
        storage_path = r"c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\backend\storage\models"
        
    print(f"📂 Storage Path: {storage_path}")
    persistence = ModelPersistenceManager(base_path=storage_path)
    loaded = persistence.load_model(user_id)
    
    if not loaded:
        print("\n❌ No trained model found!")
        return
    
    model = loaded['model']
    metadata = loaded.get('metadata', {})
    feature_columns = metadata.get('feature_columns', [])
    scaler = metadata.get('scaler')
    task_type = metadata.get('task_type', 'regression')
    target_column = metadata.get('target_column', 'current_price')
    
    print(f"\n🔮 Model: {type(model).__name__}")
    print(f"🎯 Task type: {task_type}")
    print(f"🎯 Target column: {target_column}")
    print(f"📊 Feature columns: {len(feature_columns)} features")
    
    # Get actual target values
    if target_column in df.columns:
        y_actual = df[target_column].values
    else:
        print(f"\n❌ Target column '{target_column}' not found in data!")
        return
    
    # For testing, we'll use the first 10 rows
    test_df = df.head(10).copy()
    
    print("\n" + "=" * 60)
    print("🔮 MAKING PREDICTIONS (First 10 rows)")
    print("=" * 60)
    
    print("\n" + "=" * 60)
    print("🔮 MAKING PREDICTIONS (First 10 rows)")
    print("=" * 60)
    
    # NEW ROBUST PREDICTION LOGIC (Hydration)
    from ml.automl_engine import AutoMLEngine
    engine = AutoMLEngine()
    
    # Hydrate engine
    if isinstance(loaded, dict):
        engine.model = loaded.get('model') or loaded.get('best_model')
        engine.numeric_cols = loaded.get('numeric_cols', [])
        engine.categorical_cols = loaded.get('categorical_cols', [])
        engine.text_cols = loaded.get('text_cols', [])
        engine.numeric_fill_values = loaded.get('numeric_fill_values', {})
        engine.scaler = loaded.get('scaler')
        engine.label_encoders = loaded.get('label_encoders', {})
        
        # Safe extraction of collections
        tv = loaded.get('text_vectorizers', {})
        engine.text_vectorizers = tv if isinstance(tv, dict) else {}
        
        tsvd = loaded.get('text_svd_transformers', {})
        engine.text_svd_transformers = tsvd if isinstance(tsvd, dict) else {}
        
        engine.is_nlp_task = loaded.get('is_nlp_task', False)
        engine.primary_text_col = loaded.get('primary_text_col')
        
        # Restore production engineer if present
        engine.production_engineer = loaded.get('production_engineer')
    else:
        engine.model = loaded

    if engine.model is None:
        print("❌ Model hydration failed")
        return
        
    print(f"✅ AutoMLEngine hydrated with {len(engine.numeric_cols)} numeric cols")

    results = []
    
    for idx, row in test_df.iterrows():
        actual = row[target_column]
        
        # Prepare input dict (mimic API request)
        input_data = row.to_dict()
        
        try:
            # Use engine's preprocessing
            X_input = engine._preprocess_single(input_data)
            
            # Predict
            pred = engine.model.predict(X_input)[0]
            
            # Error
            error = abs(pred - actual)
            if actual != 0:
                error_pct = (error / abs(actual)) * 100
            else:
                error_pct = 0.0
            
            status = "✅" if error_pct < 20 else "⚠️" if error_pct < 50 else "❌"
            
            results.append({
                'actual': actual,
                'predicted': pred,
                'error_pct': error_pct
            })
            
            print(f"{status} Row {idx}: Pred={pred:,.2f} | Actual={actual:,.2f} | Error={error_pct:.1f}%")
            
        except Exception as e:
            print(f"❌ Prediction failed for row {idx}: {e}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("📊 ACCURACY SUMMARY")
    print("=" * 60)
    
    if results:
        errors = [r['error_pct'] for r in results]
        print(f"\n📈 Mean Absolute Percentage Error: {np.mean(errors):.1f}%")
        print(f"📈 Median Error: {np.median(errors):.1f}%")
        
        # Accuracy tiers
        within_10 = sum(1 for e in errors if e <= 10)
        within_25 = sum(1 for e in errors if e <= 25)
        
        print(f"\n✅ Within 10% accuracy: {within_10}/{len(errors)} ({within_10/len(errors)*100:.0f}%)")
        print(f"✅ Within 25% accuracy: {within_25}/{len(errors)} ({within_25/len(errors)*100:.0f}%)")

if __name__ == "__main__":
    test_predictions()
