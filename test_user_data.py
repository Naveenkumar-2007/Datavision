"""
Test Script: User Data Checks
Computes Signals and Forces for the specific user_orders.csv
"""
import pandas as pd
import sys
sys.path.insert(0, 'backend')
from core.data_signal_processor import DataSignalProcessor
from core.visual_force_engine import VisualForceEngine
from core.visual_grammar_resolver import VisualGrammarResolver

def test_user_data():
    print("="*60)
    print("🔍 ANALYZING USER ORDERS DATA")
    print("="*60)
    
    # Load
    try:
        df = pd.read_csv('user_orders.csv')
    except:
        print("❌ Data file missing")
        return

    # Signals
    processor = DataSignalProcessor()
    signals = processor.process_signals(df)
    
    print(f"\n📡 Signals:")
    print(f"   Time Strength: {signals['temporal_strength']:.2f}")
    print(f"   Entropy:       {signals['entropy']:.2f}")
    print(f"   Relations:     {signals['relationship_density']:.2f}")
    
    # Forces
    engine = VisualForceEngine()
    forces = engine.compute_forces(signals)
    
    print(f"\n⚛️  Forces:")
    print(f"   Flow:          {forces.flow:.2f} (Target: >0.7 for Area Chart)")
    print(f"   Cohesion:      {forces.cohesion:.2f} (Target: >0.7 for Network)")
    
    # Grammar
    resolver = VisualGrammarResolver()
    col_info = {
        "datetime": processor._detect_datetime_cols(df),
        "numeric": df.select_dtypes(include=['number']).columns.tolist(),
        "categorical": df.select_dtypes(include=['object']).columns.tolist()
    }
    grammar = resolver.resolve(forces, col_info, len(df))
    
    print(f"\n📐 Strategy: {grammar['strategy']}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_user_data()
