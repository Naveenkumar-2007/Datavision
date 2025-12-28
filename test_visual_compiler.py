"""
Test Script: Visual Intelligence Compiler
=========================================
Verifies the full pipeline:
Data -> Signals -> Forces -> Grammar
"""

import pandas as pd
import sys
sys.path.insert(0, 'backend')

from core.data_signal_processor import DataSignalProcessor
from core.visual_force_engine import VisualForceEngine
from core.visual_grammar_resolver import VisualGrammarResolver

def test_compiler():
    print("="*60)
    print("🧪 VISUAL INTELLIGENCE COMPILER TEST")
    print("="*60)

    # 1. Load Data
    try:
        df = pd.read_csv('test_data_sales_comprehensive.csv')
        print(f"✅ Loaded Data: {len(df)} rows, {len(df.columns)} cols")
    except:
        print("❌ Could not load test data")
        return

    # 2. Compute Signals
    processor = DataSignalProcessor()
    signals = processor.process_signals(df)
    print("\n📡 SIGNALS (The Senses):")
    for k, v in signals.items():
        print(f"   {k:<25}: {v:.4f}")

    # 3. Compute Forces
    force_engine = VisualForceEngine()
    forces = force_engine.compute_forces(signals)
    print("\n⚛️  FORCES (The Physics):")
    for k, v in forces.to_dict().items():
        print(f"   {k:<25}: {v:.4f}")

    # 4. Resolve Grammar
    resolver = VisualGrammarResolver()
    
    # Mock column info for resolver
    col_info = {
        "datetime": processor._detect_datetime_cols(df),
        "numeric": df.select_dtypes(include=['number']).columns.tolist(),
        "categorical": df.select_dtypes(include=['object']).columns.tolist()
    }
    
    grammar = resolver.resolve(forces, col_info, len(df))
    
    print(f"\n📐 GRAMMAR (The Layout Strategy: {grammar['strategy']}):")
    for i, prim in enumerate(grammar['primitives']):
        print(f"   Primitive {i+1}: {prim['type']} ({prim['subtype']})")
        print(f"      Encoding: {prim['encoding']}")
        print(f"      Style:    {prim['style']}")

    print("\n" + "="*60)

if __name__ == "__main__":
    test_compiler()
