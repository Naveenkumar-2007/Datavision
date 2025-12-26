
import pandas as pd
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.visualization_engine import ColumnProfile

def test_disease_dataset():
    file_path = "disease_symptoms_test.csv"
    print(f"Loading {file_path}...")
    
    try:
        df = pd.read_csv(file_path, low_memory=False, keep_default_na=True)
        print("Columns found:", df.columns.tolist())
        
        for col in df.columns[:5]: # Check first 5 columns
            series = df[col]
            profile = ColumnProfile(series, col)
            print(f"Column: {col}")
            print(f"  - Numeric: {profile.is_numeric}")
            print(f"  - Datetime: {profile.is_datetime}")
            print(f"  - Text/Dimension: {not profile.is_numeric and not profile.is_datetime}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_disease_dataset()
