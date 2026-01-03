"""Test direct prediction after loading model"""
from ml.automl_engine import automl_engine

# Load model
automl_engine.load('test')

# Test Row 0
data = {
    'Open': 2568.300049,
    'High': 2568.300049,
    'Low': 2568.300049,
    'Close': 2568.300049,
    'Adj Close': 2568.300049,
    'Volume': 0.0,
    'Index': 'HSI'
}
result = automl_engine.predict(data)
print(f"Input: Close={data['Close']}, Index={data['Index']}")
print(f"Prediction: {result['prediction']}")
print(f"Expected: 333.88 (actual from row 0)")
print()

# Test Row 317 (the row user was testing)
data2 = {
    'Open': 2593.899902,
    'High': 2593.899902,
    'Low': 2593.899902,
    'Close': 2593.899902,
    'Adj Close': 2593.899902,
    'Volume': 0.0,
    'Index': 'HSI'
}
result2 = automl_engine.predict(data2)
print(f"Input: Close={data2['Close']}, Index={data2['Index']}")
print(f"Prediction: {result2['prediction']}")
print(f"Expected: ~337.21 (row 317)")
print()

# Test different index
data3 = {
    'Open': 5000.0,
    'High': 5000.0,
    'Low': 5000.0,
    'Close': 5000.0,
    'Adj Close': 5000.0,
    'Volume': 0.0,
    'Index': 'NYA'
}
result3 = automl_engine.predict(data3)
print(f"Input: Close={data3['Close']}, Index={data3['Index']}")
print(f"Prediction: {result3['prediction']}")
