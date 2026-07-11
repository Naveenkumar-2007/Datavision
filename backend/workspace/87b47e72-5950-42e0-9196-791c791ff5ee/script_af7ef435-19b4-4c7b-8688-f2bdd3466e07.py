import pandas as pd
import numpy as np
import pickle
import os

# AutoML SaaS Builder - IDE
# 1. To run this script, click 'RUN CODE'
# 2. To modify this script, chat with the AI Architect on the right!

def main():
    print("Welcome to your Web IDE!")
    print("Checking for existing models...")
    
    # Try to load existing model
    model_path = os.path.join(os.getcwd(), 'uploads', '87b47e72-5950-42e0-9196-791c791ff5ee', 'clustering_model.pkl')
    if os.path.exists(model_path):
        print(f"✅ Found clustering model at {model_path}")
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
            print("Model Data Loaded:", list(model_data.keys()))
    else:
        print("❌ No model found. Run clustering first!")

if __name__ == "__main__":
    main()
