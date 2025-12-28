"""Test fixed engines with real data"""
import pandas as pd
import sys
sys.path.insert(0, 'backend')
from core.overview_engine_v2 import OverviewEngineV2
from core.dashboard_engine_v2 import DashboardEngineV2

df = pd.read_csv('test_data_sales_comprehensive.csv')

print('Testing FIXED engines...')
print('='*60)

# Test Overview
ov = OverviewEngineV2()
ov_result = ov.generate(df)

print('\nOVERVIEW PRIMITIVES:')
for p in ov_result['visual_primitives'][:5]:
    prim_type = p['primitive']
    title = p['title']
    chart_type = p['visual_properties'].get('chart_type', 'n/a')
    formatted = p['visual_properties'].get('formatted_value', '')
    if prim_type == 'metric_display':
        print(f'  KPI: {title} = {formatted}')
    else:
        print(f'  Chart [{chart_type}]: {title[:50]}')

print()

# Test Dashboard
db = DashboardEngineV2()
db_result = db.generate(df)

print('\nDASHBOARD PRIMITIVES:')
for p in db_result['visual_primitives'][:8]:
    prim_type = p['primitive']
    title = p['title']
    chart_type = p['visual_properties'].get('chart_type', 'n/a')
    formatted = p['visual_properties'].get('formatted_value', '')
    if prim_type == 'metric_display':
        print(f'  KPI: {title} = {formatted}')
    else:
        print(f'  Chart [{chart_type}]: {title[:50]}')

print('\n' + '='*60)
print('SUCCESS! Now restart backend and refresh browser.')
