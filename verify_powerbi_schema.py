
import pandas as pd
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.visualization_engine import ColumnProfile, RealPowerBIEngine

def test_powerbi_schema():
    data = {
        'IsActive': [0, 1, 1, 0, 1],
        'HasPromo': ['Yes', 'No', 'Yes', 'Yes', 'No'],
        'City': ['New York', 'London', 'Paris', 'Tokyo', 'Berlin'],
        'Latitude': [40.71, 51.50, 48.85, 35.67, 52.52],
        'Sales': [100, 200, 150, 300, 250],
        'OrderID': ['ORD-001', 'ORD-002', 'ORD-003', 'ORD-004', 'ORD-005']
    }
    df = pd.DataFrame(data)
    
    print("Testing DataFrame Columns:", df.columns.tolist())
    
    engine = RealPowerBIEngine(df)
    
    print("\n--- Column Profiles ---")
    for col, profile in engine.profiles.items():
        print(f"Column: {col}")
        print(f"  - Boolean: {profile.is_boolean}")
        print(f"  - Geo: {profile.is_geo}")
        print(f"  - Numeric: {profile.is_numeric}")
        print(f"  - Categorical: {profile.is_categorical}")
        
    print("\n--- Engine Lists ---")
    print(f"Metrics (Numeric): {engine.metrics}")
    print(f"Dimensions (Categorical): {engine.dimensions}")
    print(f"Geo Columns: {engine.geo_columns}")
    print(f"Boolean Columns: {engine.boolean_columns}")
    print(f"Time Columns: {engine.time_columns}")

if __name__ == "__main__":
    test_powerbi_schema()
