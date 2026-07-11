import json
import logging
import pandas as pd
from typing import Dict, Any, Tuple
from core.llm import chat

logger = logging.getLogger(__name__)

def parse_what_if_query(query: str, columns: list) -> Dict[str, Any]:
    """
    Uses an LLM to extract the causal simulation parameters from a What-If query.
    """
    prompt = f"""You are a Causal AI Simulator. 
The user is asking a "What-If" question to simulate a change in their dataset.

AVAILABLE COLUMNS IN DATASET:
{columns}

USER QUERY: "{query}"

Extract the simulation parameters.
1. 'manipulated_variable': The exact column name from the list above that the user wants to change.
2. 'operation': 'increase', 'decrease', 'set', or 'multiply'.
3. 'value': The numerical value of the change (e.g. 20 for 20%).
4. 'is_percentage': true if they said "20%", false if they said "by $20".

Output ONLY a valid JSON object:
{{
    "manipulated_variable": "Column_Name",
    "operation": "increase",
    "value": 20,
    "is_percentage": true
}}
If no simulation parameters can be parsed, return an empty JSON {{}}.
"""
    try:
        response = chat(prompt, temperature=0.1, max_tokens=150)
        
        # Parse JSON
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
            
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            response = response[start:end]
            
        decision = json.loads(response)
        return decision
    except Exception as e:
        logger.error(f"Failed to parse what-if query: {e}")
        return {}

def simulate_what_if(query: str, df: pd.DataFrame) -> Tuple[bool, pd.DataFrame, Dict[str, Any]]:
    """
    Simulates a what-if scenario on the DataFrame based on the user's query.
    Returns (Success: bool, Simulated_DF: DataFrame, Simulation_Details: Dict)
    """
    if df is None or df.empty:
        return False, df, {}
        
    try:
        columns = list(df.columns)
        sim_params = parse_what_if_query(query, columns)
        
        if not sim_params or "manipulated_variable" not in sim_params:
            return False, df, {}
            
        col = sim_params["manipulated_variable"]
        op = sim_params.get("operation", "increase")
        val = float(sim_params.get("value", 0))
        is_pct = sim_params.get("is_percentage", False)
        
        if col not in df.columns:
            return False, df, {"error": f"Column {col} not found"}
            
        # Create a deep copy of the dataframe for simulation
        sim_df = df.copy()
        
        # Ensure column is numeric before manipulating
        if pd.api.types.is_numeric_dtype(sim_df[col]):
            if op == "increase":
                if is_pct:
                    sim_df[col] = sim_df[col] * (1 + (val / 100))
                else:
                    sim_df[col] = sim_df[col] + val
            elif op == "decrease":
                if is_pct:
                    sim_df[col] = sim_df[col] * (1 - (val / 100))
                else:
                    sim_df[col] = sim_df[col] - val
            elif op == "multiply":
                sim_df[col] = sim_df[col] * val
            elif op == "set":
                sim_df[col] = val
                
            return True, sim_df, sim_params
        else:
            return False, df, {"error": f"Column {col} is not numeric."}
            
    except Exception as e:
        logger.error(f"Error in simulate_what_if: {e}")
        return False, df, {"error": str(e)}
