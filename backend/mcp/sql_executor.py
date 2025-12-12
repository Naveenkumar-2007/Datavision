# MCP SQL Executor Module
"""
SQL execution tools for MCP integration using DuckDB.

Features:
- In-memory SQL execution
- DataFrame to table conversion
- Query result formatting
- Aggregation support
"""

from typing import Dict, List, Optional, Any
import json


# Global DuckDB connection
_connection = None


def _get_connection():
    """Get or create DuckDB connection"""
    global _connection
    
    if _connection is None:
        try:
            import duckdb
            _connection = duckdb.connect(':memory:')
        except ImportError:
            return None
    
    return _connection


def execute_sql(
    query: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Execute SQL query on data.
    
    Args:
        query: SQL query string
        data: Dict mapping table names to DataFrames
        
    Returns:
        Query results
    """
    try:
        conn = _get_connection()
        
        if conn is None:
            # Fallback to pandas-based execution
            return _execute_sql_pandas(query, data)
        
        import duckdb
        
        # Register DataFrames as tables
        if data:
            for table_name, df_data in data.items():
                import pandas as pd
                
                if isinstance(df_data, pd.DataFrame):
                    df = df_data
                elif isinstance(df_data, list):
                    df = pd.DataFrame(df_data)
                elif isinstance(df_data, dict):
                    df = pd.DataFrame(df_data)
                else:
                    continue
                
                conn.register(table_name, df)
        
        # Execute query
        result = conn.execute(query)
        
        # Get column names
        columns = [desc[0] for desc in result.description] if result.description else []
        
        # Fetch results
        rows = result.fetchall()
        
        # Convert to list of dicts
        records = []
        for row in rows:
            record = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Convert to JSON-serializable types
                if hasattr(val, 'item'):  # numpy types
                    val = val.item()
                record[col] = val
            records.append(record)
        
        return {
            "success": True,
            "columns": columns,
            "data": records,
            "row_count": len(records)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


def _execute_sql_pandas(query: str, data: Optional[Dict] = None) -> Dict:
    """Fallback SQL execution using pandas and sqlite"""
    try:
        import pandas as pd
        import sqlite3
        
        # Create in-memory SQLite connection
        conn = sqlite3.connect(':memory:')
        
        # Load DataFrames as tables
        if data:
            for table_name, df_data in data.items():
                if isinstance(df_data, pd.DataFrame):
                    df = df_data
                elif isinstance(df_data, list):
                    df = pd.DataFrame(df_data)
                elif isinstance(df_data, dict):
                    df = pd.DataFrame(df_data)
                else:
                    continue
                
                df.to_sql(table_name, conn, index=False, if_exists='replace')
        
        # Execute query
        result_df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        return {
            "success": True,
            "columns": list(result_df.columns),
            "data": result_df.to_dict(orient='records'),
            "row_count": len(result_df)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


def create_table_from_df(
    name: str,
    df: Any,
    replace: bool = True
) -> Dict:
    """
    Create virtual table from DataFrame.
    
    Args:
        name: Table name
        df: DataFrame to register
        replace: Whether to replace existing table
        
    Returns:
        Table creation result
    """
    try:
        conn = _get_connection()
        
        if conn is None:
            return {
                "success": False,
                "error": "DuckDB not available",
                "table_name": None
            }
        
        import pandas as pd
        
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, list):
                df = pd.DataFrame(df)
            elif isinstance(df, dict):
                df = pd.DataFrame(df)
            else:
                return {
                    "success": False,
                    "error": "Invalid data type",
                    "table_name": None
                }
        
        conn.register(name, df)
        
        return {
            "success": True,
            "table_name": name,
            "columns": list(df.columns),
            "row_count": len(df)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table_name": None
        }


def query_to_dataframe(query: str) -> Dict:
    """
    Execute query and return DataFrame result.
    
    Args:
        query: SQL query string
        
    Returns:
        Query result as DataFrame dict
    """
    try:
        conn = _get_connection()
        
        if conn is None:
            return {
                "success": False,
                "error": "DuckDB not available",
                "dataframe": None
            }
        
        import pandas as pd
        
        result_df = conn.execute(query).fetchdf()
        
        return {
            "success": True,
            "dataframe": result_df.to_dict(orient='records'),
            "columns": list(result_df.columns),
            "row_count": len(result_df)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "dataframe": None
        }


def aggregate_data(
    table_or_df: Any,
    group_by: List[str],
    aggregations: Dict[str, str]
) -> Dict:
    """
    Perform aggregation on data.
    
    Args:
        table_or_df: Table name (str) or DataFrame
        group_by: Columns to group by
        aggregations: Dict of {column: agg_function}
            agg_function: "sum", "avg", "count", "min", "max"
        
    Returns:
        Aggregated results
    """
    try:
        import pandas as pd
        
        if isinstance(table_or_df, str):
            # It's a table name, query it
            conn = _get_connection()
            if conn is None:
                return {
                    "success": False,
                    "error": "DuckDB not available",
                    "data": None
                }
            
            df = conn.execute(f"SELECT * FROM {table_or_df}").fetchdf()
        elif isinstance(table_or_df, pd.DataFrame):
            df = table_or_df
        else:
            df = pd.DataFrame(table_or_df)
        
        # Build aggregation dict for pandas
        agg_map = {
            "sum": "sum",
            "avg": "mean",
            "count": "count",
            "min": "min",
            "max": "max",
            "mean": "mean"
        }
        
        pandas_agg = {}
        for col, func in aggregations.items():
            if col in df.columns:
                pandas_agg[col] = agg_map.get(func.lower(), func)
        
        # Perform aggregation
        if group_by:
            result = df.groupby(group_by).agg(pandas_agg).reset_index()
        else:
            result = df.agg(pandas_agg).to_frame().T
        
        return {
            "success": True,
            "data": result.to_dict(orient='records'),
            "columns": list(result.columns),
            "row_count": len(result)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


def join_tables(
    left_table: Any,
    right_table: Any,
    left_on: str,
    right_on: str,
    how: str = "inner"
) -> Dict:
    """
    Join two tables.
    
    Args:
        left_table: Left table name or DataFrame
        right_table: Right table name or DataFrame
        left_on: Left join column
        right_on: Right join column
        how: Join type ("inner", "left", "right", "outer")
        
    Returns:
        Joined table
    """
    try:
        import pandas as pd
        
        # Convert to DataFrames
        if isinstance(left_table, str):
            conn = _get_connection()
            left_df = conn.execute(f"SELECT * FROM {left_table}").fetchdf()
        else:
            left_df = pd.DataFrame(left_table)
        
        if isinstance(right_table, str):
            conn = _get_connection()
            right_df = conn.execute(f"SELECT * FROM {right_table}").fetchdf()
        else:
            right_df = pd.DataFrame(right_table)
        
        # Perform join
        result = pd.merge(left_df, right_df, left_on=left_on, right_on=right_on, how=how)
        
        return {
            "success": True,
            "data": result.to_dict(orient='records'),
            "columns": list(result.columns),
            "row_count": len(result)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


def filter_data(
    table_or_df: Any,
    conditions: List[Dict]
) -> Dict:
    """
    Filter data based on conditions.
    
    Args:
        table_or_df: Table name or DataFrame
        conditions: List of {column, operator, value}
            operator: "=", "!=", ">", "<", ">=", "<=", "in", "like"
        
    Returns:
        Filtered data
    """
    try:
        import pandas as pd
        
        if isinstance(table_or_df, str):
            conn = _get_connection()
            df = conn.execute(f"SELECT * FROM {table_or_df}").fetchdf()
        else:
            df = pd.DataFrame(table_or_df)
        
        result = df.copy()
        
        for cond in conditions:
            col = cond.get("column")
            op = cond.get("operator", "=")
            val = cond.get("value")
            
            if col not in result.columns:
                continue
            
            if op == "=" or op == "==":
                result = result[result[col] == val]
            elif op == "!=":
                result = result[result[col] != val]
            elif op == ">":
                result = result[result[col] > val]
            elif op == "<":
                result = result[result[col] < val]
            elif op == ">=":
                result = result[result[col] >= val]
            elif op == "<=":
                result = result[result[col] <= val]
            elif op == "in":
                result = result[result[col].isin(val)]
            elif op == "like":
                result = result[result[col].str.contains(val, case=False, na=False)]
        
        return {
            "success": True,
            "data": result.to_dict(orient='records'),
            "columns": list(result.columns),
            "row_count": len(result),
            "original_count": len(df)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


def reset_connection():
    """Reset the DuckDB connection"""
    global _connection
    _connection = None
    return {"success": True, "message": "Connection reset"}
