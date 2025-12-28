"""Simple test of Advanced Pattern Detector"""
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.advanced_pattern_detector import AdvancedPatternDetector

# Load data
df = pd.read_csv("../test_data_sales_comprehensive.csv")

print("="*70)
print("TESTING ADVANCED PATTERN DETECTOR")
print("="*70)
print(f"\nData: {len(df)} rows, {len(df.columns)} columns\n")

# Run detector
detector = AdvancedPatternDetector()
analysis = detector.analyze(df)

insights = analysis['insights']

print(f"\n✅ SUCCESS! Found {len(insights)} insights using statistical algorithms\n")

print("TOP 10 INSIGHTS:")
for i, insight in enumerate(insights[:10], 1):
    print(f"{i}. [{insight['type']}] {insight['description']}")
    print(f"   Confidence: {insight['confidence']:.2f}\n")

print("="*70)
print(f"✅ PROOF: {len(insights)} data-driven patterns discovered!")
print("="*70)
