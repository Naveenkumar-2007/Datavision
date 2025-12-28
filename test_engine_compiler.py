"""Test Compiler Integration in Engine"""
import pandas as pd
import sys
sys.path.insert(0, 'backend')
from core.overview_engine_v2 import OverviewEngineV2

df = pd.read_csv('test_data_sales_comprehensive.csv')

print("="*60)
print("TESTING ENGINE COMPILER INTEGRATION")
print("="*60)

engine = OverviewEngineV2()
result = engine.generate(df)

print(f"\nMode: {result['mode']}")
print("\nMETADATA (The Brain):")
meta = result['compiler_metadata']
print(" Signals:", meta['signals'])
print(" Forces: ", meta['forces'])
print(" Grammar:", meta['grammar']['strategy'])

print("\nPRIMITIVES (The Output):")
for p in result['visual_primitives']:
    print(f" - {p['title']} [{p['visual_properties']['chart_type']}]")
    
print("\n" + "="*60)
