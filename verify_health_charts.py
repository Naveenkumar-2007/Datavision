
import pandas as pd
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.visualization_engine import RealPowerBIEngine

def test_health_dataset():
    # Simulate Health Data (purely categorical)
    data = {
        'Disease': ['Fungal infection', 'Fungal infection', 'Allergy', 'Allergy', 'GERD'],
        'Symptom_1': ['itching', 'skin_rash', 'sneezing', 'sneezing', 'stomach_pain']
    }
    df = pd.DataFrame(data)
    
    print("Testing Health Dataset (Categorical Only)...")
    engine = RealPowerBIEngine(df)
    
    print(f"Metrics: {engine.metrics}")
    print(f"Dimensions: {engine.dimensions}")
    print(f"Use Count as Metric: {engine.use_count_as_metric}")
    
    print("\n--- Chart Scores ---")
    scores = engine._score_chart_fitness()
    for chart, score in scores.items():
        if score > 0:
            print(f"{chart}: {score}")

if __name__ == "__main__":
    test_health_dataset()
