"""Test script for production ML pipeline"""
import pandas as pd
import numpy as np
from ml.production_ml_core import production_train_pipeline

# Create test data
df = pd.DataFrame({
    'text': [
        'I love this product!', 
        'This is terrible and awful', 
        'Great quality and amazing service',
        'Bad experience, very disappointing', 
        'Amazing! Best purchase ever', 
        'Worst product I have ever bought',
        'Perfect in every way',
        'Very disappointing, do not buy',
        'Excellent value for money',
        'Complete waste of money'
    ],
    'rating': [5, 1, 5, 2, 5, 1, 4, 2, 5, 1],
    'category': ['electronics', 'clothing', 'electronics', 'food', 'electronics', 
                 'clothing', 'food', 'electronics', 'clothing', 'food'],
    'label': ['positive', 'negative', 'positive', 'negative', 'positive', 
              'negative', 'positive', 'negative', 'positive', 'negative']
})

print("Test data:")
print(df)
print()

# Run pipeline
result = production_train_pipeline(df, 'label', 'classification')

print()
print("="*60)
print(f"FINAL RESULT: {result['best_name']} - Score: {result['best_score']:.4f}")
print(f"Features: {len(result['feature_names'])}")
print(f"Task Type: {result['task_type']}")
print("="*60)
