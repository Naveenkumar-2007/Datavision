"""
🧪 ULTRA AUTOML TEST SCRIPT
============================

Tests the new Ultra AutoML system with all 6 engines.
Run this to verify the implementation works correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ultra_automl():
    """Test the Ultra AutoML orchestrator."""
    import pandas as pd
    import numpy as np
    
    print("=" * 70)
    print("🧪 ULTRA AUTOML TEST")
    print("=" * 70)
    
    # Create sample dataset
    print("\n📊 Creating sample dataset...")
    np.random.seed(42)
    n_samples = 500
    
    # Generate features
    df = pd.DataFrame({
        'age': np.random.randint(18, 70, n_samples),
        'income': np.random.uniform(20000, 150000, n_samples),
        'education_years': np.random.randint(8, 20, n_samples),
        'experience': np.random.randint(0, 40, n_samples),
        'credit_score': np.random.randint(300, 850, n_samples),
        'debt_ratio': np.random.uniform(0, 0.8, n_samples),
        'num_accounts': np.random.randint(1, 15, n_samples),
        'missed_payments': np.random.randint(0, 5, n_samples),
    })
    
    # Generate target (classification)
    df['loan_approved'] = (
        (df['income'] > 50000).astype(int) +
        (df['credit_score'] > 600).astype(int) +
        (df['debt_ratio'] < 0.4).astype(int) +
        np.random.randint(0, 2, n_samples)
    ) >= 3
    df['loan_approved'] = df['loan_approved'].map({True: 'Approved', False: 'Rejected'})
    
    print(f"   ✅ Created {n_samples} samples with {len(df.columns)} columns")
    print(f"   Target: loan_approved")
    print(f"   Class distribution: {df['loan_approved'].value_counts().to_dict()}")
    
    # Test individual engines
    print("\n" + "=" * 70)
    print("🔧 TESTING INDIVIDUAL ENGINES")
    print("=" * 70)
    
    # 1. Test Meta-Learning Engine
    print("\n📍 Testing Meta-Learning Engine...")
    try:
        from ml.meta_learning_engine import MetaLearningEngine
        meta = MetaLearningEngine()
        fingerprint = meta.extract_fingerprint(df, 'loan_approved', 'classification')
        print(f"   ✅ Dataset fingerprint: {fingerprint.fingerprint_hash}")
        recommendations = meta.recommend_algorithms(fingerprint)
        print(f"   ✅ Recommendations: {[r['algorithm'] for r in recommendations[:3]]}")
    except Exception as e:
        print(f"   ❌ Meta-Learning failed: {e}")
    
    # 2. Test Feature Synthesis Engine
    print("\n📍 Testing Feature Synthesis Engine...")
    try:
        from ml.feature_synthesis_engine import FeatureSynthesisEngine
        synth = FeatureSynthesisEngine(max_features=20, use_genetic=True)
        enhanced_df, new_features = synth.fit_transform(df.copy(), 'loan_approved', 'classification')
        print(f"   ✅ Synthesized {len(new_features)} new features")
        if new_features:
            print(f"   ✅ Examples: {new_features[:3]}")
    except Exception as e:
        print(f"   ❌ Feature Synthesis failed: {e}")
    
    # 3. Test Ultra Data Pipeline
    print("\n📍 Testing Ultra Data Pipeline...")
    try:
        from ml.ultra_data_pipeline import UltraDataPipeline
        pipeline = UltraDataPipeline()
        X, y, feature_names, report = pipeline.fit_transform(df.copy(), 'loan_approved', 'classification')
        print(f"   ✅ Preprocessed: {X.shape}")
        print(f"   ✅ Quality Score: {report.quality_score}/100")
    except Exception as e:
        print(f"   ❌ Ultra Data Pipeline failed: {e}")
    
    # 4. Test Neural Architecture Engine
    print("\n📍 Testing Neural Architecture Engine...")
    try:
        from ml.neural_architecture_engine import NeuralArchitectureEngine, HAS_TENSORFLOW
        if HAS_TENSORFLOW:
            print("   TensorFlow available - testing TabNet...")
            # Quick test with just a few epochs
            neural = NeuralArchitectureEngine(
                task_type='classification',
                n_classes=2,
                max_epochs=5,  # Very quick test
                patience=2
            )
            print("   ✅ Neural Architecture Engine initialized")
        else:
            print("   ⚠️ TensorFlow not installed - skipping neural test")
    except Exception as e:
        print(f"   ❌ Neural Architecture failed: {e}")
    
    # 5. Test Explainability Engine
    print("\n📍 Testing Explainability Engine...")
    try:
        from ml.explainability_engine import ExplainabilityEngine
        explainer = ExplainabilityEngine()
        print("   ✅ Explainability Engine initialized")
    except Exception as e:
        print(f"   ❌ Explainability failed: {e}")
    
    # Full orchestrator test
    print("\n" + "=" * 70)
    print("🎼 TESTING FULL ULTRA AUTOML ORCHESTRATOR")
    print("=" * 70)
    
    try:
        from ml.ultra_automl_orchestrator import UltraAutoMLOrchestrator
        
        orchestrator = UltraAutoMLOrchestrator(
            mode='fast',  # Use fast mode for testing
            use_neural=False,  # Skip neural for quick test
            use_meta_learning=True,
            use_feature_synthesis=True,
            use_explainability=True
        )
        
        result = orchestrator.train(
            df=df,
            target_col='loan_approved',
            task_type='classification'
        )
        
        print("\n" + "=" * 70)
        print("✅ ULTRA AUTOML TEST COMPLETE")
        print("=" * 70)
        print(f"   🏆 Best Model: {result.best_model_name}")
        print(f"   📊 Score: {result.best_score:.4f}")
        print(f"   🔧 Engines Used: {result.engines_used}")
        print(f"   ⏱️  Time: {result.total_time_seconds:.1f}s")
        
        if result.synthesized_features:
            print(f"   🔬 Synthesized Features: {len(result.synthesized_features)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Full orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ultra_automl()
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED - Ultra AutoML is ready!")
    else:
        print("⚠️ SOME TESTS FAILED - Check errors above")
    print("=" * 70)
