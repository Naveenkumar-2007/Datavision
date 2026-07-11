import logging
import pandas as pd
import json
import ast
import traceback
from typing import Dict, Any, Tuple
from core.llm import chat

logger = logging.getLogger(__name__)

def generate_etl_script(df: pd.DataFrame, user_instructions: str = "") -> str:
    """
    Generates a Python Pandas script to clean the data.
    """
    sample_data = df.head(3).to_csv(index=False)
    dtypes = df.dtypes.to_dict()
    missing_info = df.isnull().sum().to_dict()
    
    prompt = f"""You are an Expert Data Engineer. 
Write a Python script using pandas to clean this dataset.

DATASET INFO:
Columns and Types: {dtypes}
Missing Values: {missing_info}
Sample Data:
{sample_data}

USER INSTRUCTIONS (if any): {user_instructions}

RULES:
1. The script MUST define a function called `clean_data(df)` that takes a pandas DataFrame and returns a pandas DataFrame.
2. Fix missing values, convert bad data types, drop obvious duplicates, and remove extreme outliers.
3. Use ONLY the 'pandas' and 'numpy' libraries. Do NOT use any other libraries (no os, sys, subprocess, etc).
4. Output ONLY the raw python code. No markdown formatting, no explanation. Just the raw code.
5. Example format:

import pandas as pd
import numpy as np

def clean_data(df):
    df = df.drop_duplicates()
    df['Age'] = df['Age'].fillna(df['Age'].mean())
    return df
"""
    try:
        response = chat(prompt, temperature=0.1, max_tokens=1000)
        
        # Clean up response if it wrapped in markdown
        if '```python' in response:
            response = response.split('```python')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
            
        return response
    except Exception as e:
        logger.error(f"Failed to generate ETL script: {e}")
        return "def clean_data(df):\n    return df"

def safe_execute_etl(df: pd.DataFrame, code_str: str) -> Tuple[bool, pd.DataFrame, str]:
    """
    Safely executes the AI-generated pandas script on the DataFrame.
    Returns (success, cleaned_df, error_message).
    """
    # 1. Security Check: Parse AST to ensure no dangerous imports/calls
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name not in ['pandas', 'numpy']:
                        return False, df, f"Security Violation: Import of '{module_name}' is not allowed. Only pandas and numpy are permitted."
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'open', '__import__']:
                        return False, df, f"Security Violation: Function '{node.func.id}' is not allowed."
    except SyntaxError as e:
        return False, df, f"Syntax Error in AI code: {e}"
        
    # 2. Execute Code safely
    local_env = {
        'pd': pd,
        'np': __import__('numpy')
    }
    
    try:
        # Execute the function definition into our local_env
        exec(code_str, {}, local_env)
        
        if 'clean_data' not in local_env:
            return False, df, "Function 'clean_data' was not defined by the AI."
            
        # Run the function on a copy of the dataframe
        df_copy = df.copy()
        cleaned_df = local_env['clean_data'](df_copy)
        
        if not isinstance(cleaned_df, pd.DataFrame):
            return False, df, "The 'clean_data' function did not return a DataFrame."
            
        return True, cleaned_df, code_str
        
    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"ETL Execution failed: {error_msg}")
        return False, df, f"Runtime Error: {e}"
