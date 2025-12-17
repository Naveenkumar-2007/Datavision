
import sys
import os
import pandas as pd
import traceback
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

from utils.paths import get_user_paths, STORAGE_BASE
from utils.currency import convert_currency, load_currency_metadata, CURRENCY_CONFIG

def log(msg):
    with open("debug_output.txt", "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    print(msg)

def debug_dashboard():
    try:
        log("🚀 Starting Debug Dashboard")
        user_id = "demo_user"
        paths = get_user_paths(user_id)
        log(f"📂 Paths: {paths}")
        
        csv_files = list(paths["files"].glob("*.csv"))
        log(f"📄 Found {len(csv_files)} CSV files")
        
        all_dfs = []
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                df['source_file'] = file.name
                all_dfs.append(df)
                log(f"✅ Loaded {file.name}: {len(df)} rows")
            except Exception as e:
                log(f"❌ Error loading {file.name}: {e}")
        
        if not all_dfs:
            log("❌ No DFs loaded")
            return
            
        df = pd.concat(all_dfs, ignore_index=True)
        log(f"📊 Total Rows: {len(df)}")
        log(f"📊 Columns: {list(df.columns)}")
        
        # SMART DETECTION
        def find_column_smart(patterns, columns):
            col_lower_map = {c.lower(): c for c in columns}
            for pattern in patterns:
                if pattern.lower() in col_lower_map:
                    return col_lower_map[pattern.lower()]
            for pattern in patterns:
                for col_lower, col_original in col_lower_map.items():
                    if pattern.lower() in col_lower:
                        return col_original
            return None
            
        amount_patterns = ['invoice_amount', 'amount', 'revenue', 'total', 'price', 'value', 'sales', 'cost']
        amount_col = find_column_smart(amount_patterns, df.columns)
        
        # FALLBACK
        if not amount_col:
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                col_lower = col.lower()
                if 'id' not in col_lower and 'code' not in col_lower and 'year' not in col_lower:
                    amount_col = col
                    break
        
        log(f"💰 Amount Column: {amount_col}")
        
        customer_patterns = ['client_name', 'customer_name', 'client', 'customer', 'buyer', 'company']
        customer_col = find_column_smart(customer_patterns, df.columns)
        log(f"👤 Customer Column: {customer_col}")
        
        target_currency = load_currency_metadata(user_id, STORAGE_BASE) or 'USD'
        log(f"💱 Target Currency: {target_currency}")
        
        if amount_col:
            df[amount_col] = df[amount_col].astype(str).str.replace(r'[₹$€£¥,\s]', '', regex=True)
            df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
            
            has_multi_currency = 'currency' in df.columns and df['currency'].nunique() > 1
            log(f"💱 Multi-currency: {has_multi_currency}")
            
            if has_multi_currency or target_currency != 'USD':
                total_revenue = 0.0
                for i, row in df.iterrows():
                    try:
                        amount = float(row[amount_col]) if pd.notna(row[amount_col]) else 0
                        currency_code = row['currency'] if 'currency' in df.columns else 'USD'
                        val = convert_currency(amount, currency_code, target_currency)
                        total_revenue += val
                        if i < 5:
                             log(f"   Row {i}: {amount} {currency_code} -> {val} {target_currency}")
                    except Exception as e:
                        log(f"❌ Error in loop row {i}: {e}")
                        break
                log(f"💰 Total Revenue: {total_revenue}")
            else:
                 log(f"💰 Total Revenue: {df[amount_col].sum()}")

    except Exception as e:
        log(f"❌ CRITICAL ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_dashboard()
