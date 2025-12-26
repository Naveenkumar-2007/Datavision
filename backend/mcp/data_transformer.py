# MCP Data Transformer Module
"""
Advanced Data Transformation Tools for MCP Integration.

Features:
- Format conversion (CSV ↔ JSON ↔ Excel)
- Pivot/unpivot operations
- Column mapping and renaming
- Data aggregation
- Schema inference
- Data type conversion
"""

import json
import io
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


@dataclass
class TransformResult:
    """Result from data transformation"""
    success: bool
    data: Any
    message: str
    rows_before: int = 0
    rows_after: int = 0
    columns: List[str] = None
    metadata: Dict = None


class DataTransformer:
    """
    Enterprise Data Transformer MCP.
    
    Provides powerful data transformation capabilities:
    - Format conversions
    - Pivot operations
    - Aggregations
    - Schema transformations
    """
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'excel', 'dict']
    
    def convert_format(
        self,
        data: Any,
        source_format: str,
        target_format: str,
        **options
    ) -> Dict[str, Any]:
        """
        Convert data between formats.
        
        Args:
            data: Input data
            source_format: 'csv', 'json', 'excel', 'dict'
            target_format: Desired output format
            options: Format-specific options
            
        Returns:
            Converted data with metadata
        """
        try:
            import pandas as pd
            
            # Parse input
            df = self._parse_input(data, source_format)
            if df is None:
                return {"success": False, "error": "Could not parse input data"}
            
            # Convert to output format
            output = self._to_format(df, target_format, **options)
            
            return {
                "success": True,
                "data": output,
                "source_format": source_format,
                "target_format": target_format,
                "rows": len(df),
                "columns": list(df.columns)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_input(self, data: Any, format_type: str) -> Any:
        """Parse input data based on format type"""
        import pandas as pd
        
        if isinstance(data, pd.DataFrame):
            return data
        
        if format_type == 'csv':
            if isinstance(data, str):
                return pd.read_csv(io.StringIO(data))
        elif format_type == 'json':
            if isinstance(data, str):
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return pd.DataFrame(parsed)
                return pd.DataFrame([parsed])
            elif isinstance(data, (list, dict)):
                if isinstance(data, list):
                    return pd.DataFrame(data)
                return pd.DataFrame([data])
        elif format_type == 'dict':
            if isinstance(data, dict):
                if 'data' in data:
                    return pd.DataFrame(data['data'])
                return pd.DataFrame(data)
            elif isinstance(data, list):
                return pd.DataFrame(data)
        
        # Try pandas auto-detection
        try:
            return pd.DataFrame(data)
        except:
            return None
    
    def _to_format(self, df: Any, format_type: str, **options) -> Any:
        """Convert DataFrame to specified format"""
        if format_type == 'csv':
            return df.to_csv(index=False)
        elif format_type == 'json':
            orient = options.get('orient', 'records')
            return df.to_json(orient=orient)
        elif format_type == 'dict':
            return df.to_dict(orient='records')
        elif format_type == 'excel':
            output = io.BytesIO()
            df.to_excel(output, index=False)
            return output.getvalue()
        return df.to_dict(orient='records')
    
    def pivot_data(
        self,
        data: Any,
        index: str,
        columns: str,
        values: str,
        aggfunc: str = 'sum'
    ) -> Dict[str, Any]:
        """
        Pivot data to restructure it.
        
        Args:
            data: Input data
            index: Column to use as row index
            columns: Column to pivot on
            values: Column with values
            aggfunc: Aggregation function ('sum', 'mean', 'count', 'max', 'min')
            
        Returns:
            Pivoted data
        """
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            pivot_df = df.pivot_table(
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            ).reset_index()
            
            # Flatten column names if MultiIndex
            pivot_df.columns = [
                f"{a}_{b}" if b else a 
                for a, b in pivot_df.columns
            ] if pivot_df.columns.nlevels > 1 else pivot_df.columns
            
            return {
                "success": True,
                "data": pivot_df.to_dict(orient='records'),
                "rows": len(pivot_df),
                "columns": list(pivot_df.columns),
                "operation": "pivot"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def unpivot_data(
        self,
        data: Any,
        id_vars: List[str],
        value_vars: Optional[List[str]] = None,
        var_name: str = 'variable',
        value_name: str = 'value'
    ) -> Dict[str, Any]:
        """
        Unpivot (melt) data from wide to long format.
        
        Args:
            data: Input data
            id_vars: Columns to keep as identifiers
            value_vars: Columns to unpivot (None = all others)
            var_name: Name for variable column
            value_name: Name for value column
            
        Returns:
            Unpivoted data
        """
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            melted = pd.melt(
                df,
                id_vars=id_vars,
                value_vars=value_vars,
                var_name=var_name,
                value_name=value_name
            )
            
            return {
                "success": True,
                "data": melted.to_dict(orient='records'),
                "rows": len(melted),
                "columns": list(melted.columns),
                "operation": "unpivot"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def aggregate_data(
        self,
        data: Any,
        group_by: List[str],
        aggregations: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Aggregate data with grouping.
        
        Args:
            data: Input data
            group_by: Columns to group by
            aggregations: {column: aggfunc} mapping
                e.g. {'revenue': 'sum', 'orders': 'count'}
            
        Returns:
            Aggregated data
        """
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            # Build aggregation dict
            agg_dict = {}
            for col, func in aggregations.items():
                if col in df.columns:
                    agg_dict[col] = func
            
            if not agg_dict:
                return {"success": False, "error": "No valid aggregation columns"}
            
            result = df.groupby(group_by).agg(agg_dict).reset_index()
            
            return {
                "success": True,
                "data": result.to_dict(orient='records'),
                "rows": len(result),
                "columns": list(result.columns),
                "groups": len(result),
                "operation": "aggregate"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def rename_columns(
        self,
        data: Any,
        mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Rename columns in data.
        
        Args:
            data: Input data
            mapping: {old_name: new_name} mapping
            
        Returns:
            Data with renamed columns
        """
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            df = df.rename(columns=mapping)
            
            return {
                "success": True,
                "data": df.to_dict(orient='records'),
                "renamed": list(mapping.keys()),
                "new_names": list(mapping.values()),
                "columns": list(df.columns)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def infer_schema(self, data: Any) -> Dict[str, Any]:
        """
        Infer data schema with types and statistics.
        
        Args:
            data: Input data
            
        Returns:
            Schema information
        """
        try:
            import pandas as pd
            import numpy as np
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            schema = {
                "columns": [],
                "row_count": len(df),
                "column_count": len(df.columns)
            }
            
            for col in df.columns:
                col_info = {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isna().sum()),
                    "unique_count": int(df[col].nunique()),
                    "sample_values": df[col].dropna().head(3).tolist()
                }
                
                # Add statistics for numeric columns
                if df[col].dtype in ['int64', 'float64']:
                    col_info.update({
                        "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                        "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                        "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                        "is_numeric": True
                    })
                else:
                    col_info["is_numeric"] = False
                
                schema["columns"].append(col_info)
            
            return {
                "success": True,
                "schema": schema
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def convert_column_types(
        self,
        data: Any,
        type_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Convert column data types.
        
        Args:
            data: Input data
            type_mapping: {column: target_type} mapping
                Types: 'int', 'float', 'str', 'datetime', 'bool'
            
        Returns:
            Data with converted types
        """
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            converted = []
            errors = []
            
            for col, target_type in type_mapping.items():
                if col not in df.columns:
                    errors.append(f"Column '{col}' not found")
                    continue
                
                try:
                    if target_type == 'int':
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                    elif target_type == 'float':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif target_type == 'str':
                        df[col] = df[col].astype(str)
                    elif target_type == 'datetime':
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    elif target_type == 'bool':
                        df[col] = df[col].astype(bool)
                    
                    converted.append(col)
                except Exception as e:
                    errors.append(f"Error converting '{col}': {str(e)}")
            
            return {
                "success": len(errors) == 0,
                "data": df.to_dict(orient='records'),
                "converted": converted,
                "errors": errors if errors else None,
                "columns": list(df.columns)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Convenience functions for direct MCP calls
def transform_pivot(data, index, columns, values, aggfunc='sum'):
    """Pivot data transformation"""
    transformer = DataTransformer()
    return transformer.pivot_data(data, index, columns, values, aggfunc)


def transform_aggregate(data, group_by, aggregations):
    """Aggregate data transformation"""
    transformer = DataTransformer()
    return transformer.aggregate_data(data, group_by, aggregations)


def transform_convert(data, source_format, target_format, **options):
    """Format conversion"""
    transformer = DataTransformer()
    return transformer.convert_format(data, source_format, target_format, **options)


def infer_data_schema(data):
    """Infer data schema"""
    transformer = DataTransformer()
    return transformer.infer_schema(data)


# Quick test
if __name__ == "__main__":
    test_data = [
        {"product": "A", "region": "North", "sales": 100},
        {"product": "A", "region": "South", "sales": 150},
        {"product": "B", "region": "North", "sales": 200},
        {"product": "B", "region": "South", "sales": 175},
    ]
    
    transformer = DataTransformer()
    
    # Test pivot
    result = transformer.pivot_data(test_data, "product", "region", "sales")
    print("Pivot Result:", result)
    
    # Test aggregation
    result = transformer.aggregate_data(
        test_data, 
        ["product"], 
        {"sales": "sum"}
    )
    print("Aggregate Result:", result)
    
    # Test schema inference
    result = transformer.infer_schema(test_data)
    print("Schema:", result)
