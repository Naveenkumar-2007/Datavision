"""Test V2 Engine Output Format"""
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.overview_engine import OverviewEngine
from core.overview_engine_v2 import OverviewEngineV2

# Load data
df = pd.read_csv("../test_data_sales_comprehensive.csv")

print("="*70)
print("COMPARING V1 vs V2 OUTPUT FORMAT")
print("="*70)

# Test V1 (original)
print("\n--- V1 (Original Engine) ---")
v1 = OverviewEngine()
result_v1 = v1.generate(df)
print(f"Keys: {list(result_v1.keys())}")
print(f"Primitives: {len(result_v1['visual_primitives'])}")
print(f"Primitive types: {[p['primitive'] for p in result_v1['visual_primitives']]}")

# Test V2 (new)
print("\n--- V2 (Advanced Engine) ---")
v2 = OverviewEngineV2()
result_v2 = v2.generate(df)
print(f"Keys: {list(result_v2.keys())}")
print(f"Primitives: {len(result_v2['visual_primitives'])}")
print(f"Primitive types: {[p['primitive'] for p in result_v2['visual_primitives']]}")

# Compare formats
print("\n" + "="*70)
print("FORMAT COMPARISON")
print("="*70)
v1_keys = set(result_v1.keys())
v2_keys = set(result_v2.keys())

if v1_keys == v2_keys:
    print("✅ TOP-LEVEL KEYS MATCH!")
else:
    print(f"❌ Keys differ: V1={v1_keys}, V2={v2_keys}")

# Compare primitive format
v1_p = result_v1['visual_primitives'][0] if result_v1['visual_primitives'] else {}
v2_p = result_v2['visual_primitives'][0] if result_v2['visual_primitives'] else {}

if set(v1_p.keys()) == set(v2_p.keys()):
    print("✅ PRIMITIVE KEYS MATCH!")
else:
    print(f"❌ Primitive keys differ: V1={set(v1_p.keys())}, V2={set(v2_p.keys())}")

# Overall verdict
if v1_keys == v2_keys and set(v1_p.keys()) == set(v2_p.keys()):
    print("\n🎉 V2 OUTPUT FORMAT IS COMPATIBLE!")
    print("   Safe to switch API to use V2 engines")
else:
    print("\n⚠️ Format mismatch - need to fix V2")
