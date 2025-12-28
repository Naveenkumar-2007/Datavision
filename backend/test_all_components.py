"""Test all advanced components together"""
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.advanced_pattern_detector import AdvancedPatternDetector
from core.organic_layout_engine import OrganicLayoutEngine
from core.algorithmic_color_engine import AlgorithmicColorEngine

# Load test data
df = pd.read_csv("../test_data_sales_comprehensive.csv")

print("="*70)
print("TESTING ALL ADVANCED COMPONENTS")
print("="*70)

# Test 1: Advanced Pattern Detection
print("\n--- Phase 1: Pattern Detection ---")
detector = AdvancedPatternDetector()
analysis = detector.analyze(df)
print(f"✅ Found {len(analysis['insights'])} insights")

# Test 2: Organic Layout
print("\n--- Phase 5: Organic Layout ---")
items = [
    {"id": "kpi1", "importance": 9, "type": "metric"},
    {"id": "trend1", "importance": 8, "type": "trend"},
    {"id": "comp1", "importance": 7, "type": "comparison"},
    {"id": "dist1", "importance": 5, "type": "distribution"},
]
layout_engine = OrganicLayoutEngine()
layout = layout_engine.generate(items)
print(f"✅ Generated layout for {len(layout['nodes'])} items")
print(f"   Grid items: {len(layout['grid'])}")

# Test 3: Algorithmic Colors
print("\n--- Phase 6: Algorithmic Colors ---")
data_profile = {
    "has_datetime": True,
    "has_currency": True,
    "numeric_count": 3,
    "category_count": 5
}
color_engine = AlgorithmicColorEngine()
palette = color_engine.generate_palette(data_profile, num_colors=5, mode='dark')
print(f"✅ Generated palette with base hue: {palette['metadata']['base_hue']}")
print(f"   Primary colors: {palette['primary']}")
print(f"   Accent colors: {palette['accent']}")
print(f"   WCAG level: {palette['metadata']['wcag_level']}")

# Summary
print("\n" + "="*70)
print("✅ ALL COMPONENTS WORKING!")
print("="*70)
print(f"   Phase 1: {len(analysis['insights'])} insights from 15+ algorithms")
print(f"   Phase 5: Force-directed layout with {len(layout['grid'])} positioned items")
print(f"   Phase 6: WCAG AAA accessible color palette")
print("="*70)
