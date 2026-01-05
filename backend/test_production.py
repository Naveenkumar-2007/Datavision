import pandas as pd
import sys
sys.path.insert(0, '.')

from ml.production_ml_core import production_train_pipeline

# Load data
df = pd.read_csv(r'storage/users/21ed4a72-43de-4689-9556-7b866d79e9de/files/train.csv')
print('Data loaded:', df.shape)

# Run production pipeline
result = production_train_pipeline(df, 'price_range')
print('\nFinal Result:')
print('Best Model:', result['best_name'])
print('Best Score:', result['best_score'])
