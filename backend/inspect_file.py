
import pandas as pd
import sys
import os


# Adjust path to locate file
file_path = r"c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\backend\storage\users\08f8fa99-ddb5-4c30-bb4d-f52725e0c50d\files\new_customers_products_with_currency.xlsx"


print(f"📂 Loading {file_path}")

try:
    df = pd.read_excel(file_path)


    with open('backend/cols.txt', 'w', encoding='utf-8') as f:
        f.write(str(list(df.columns)))
    
    # Still test locally
    print(f"Columns written to backend/cols.txt")
except Exception as e:
    with open('backend/cols.txt', 'w') as f:
        f.write(f"Error: {e}")


