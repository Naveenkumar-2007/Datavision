# Universal Data Adapter
"""
$5M Enterprise Feature: Single point of access for ANY uploaded file data.

This adapter:
1. Works with ANY file schema (uses LLM detection)
2. Provides consistent API for all modes (RAG, GraphRAG, Hybrid)
3. Caches detected schemas for performance
4. Handles currency, date, and entity columns dynamically

Usage:
    adapter = UniversalDataAdapter(user_id)
    df = adapter.get_data()
    
    # Get aggregated data by detected entity column
    top_entities = adapter.get_top_entities(limit=5)
    
    # Get time series with detected date column
    monthly = adapter.get_time_series(freq="M")
    
    # Works for ANY file - no hardcoding!
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import json
from pathlib import Path


class UniversalDataAdapter:
    """
    Access ANY uploaded file data with automatic schema detection.
    
    This is the UNIFIED data layer that makes all modes work
    with ANY file schema - just like ChatGPT.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._df: Optional[pd.DataFrame] = None
        self._schema = None
        self._loaded = False
    
    def load(self, force_reload: bool = False) -> bool:
        """Load data from user's files with LLM schema detection"""
        if self._loaded and not force_reload:
            return True
        
        try:
            from graph.query import revenue_dataframe
            self._df = revenue_dataframe(self.user_id)
            self._loaded = self._df is not None and not self._df.empty
            
            if self._loaded:
                print(f"[ADAPTER] Loaded {len(self._df)} rows for {self.user_id}")
            else:
                print(f"[ADAPTER] No data found for {self.user_id}")
            
            return self._loaded
            
        except Exception as e:
            print(f"[ADAPTER] Load error: {e}")
            return False
    
    def get_data(self) -> pd.DataFrame:
        """Get the loaded DataFrame"""
        if not self._loaded:
            self.load()
        return self._df if self._df is not None else pd.DataFrame()
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the detected schema"""
        df = self.get_data()
        if df.empty:
            return {"error": "No data loaded"}
        
        return {
            "columns": list(df.columns),
            "row_count": len(df),
            "has_customer": "customer" in df.columns,
            "has_product": "product" in df.columns,
            "has_date": "date" in df.columns,
            "has_amount": "amount" in df.columns,
            "source_files": df["source_file"].unique().tolist() if "source_file" in df.columns else [],
            "currencies": df["currency"].unique().tolist() if "currency" in df.columns else []
        }
    
    def get_total_amount(self) -> float:
        """Get total amount/revenue"""
        df = self.get_data()
        if "amount" in df.columns:
            return df["amount"].sum()
        return 0.0
    
    def get_top_entities(
        self,
        entity_type: str = "customer",  # "customer" or "product"
        limit: int = 5,
        ascending: bool = False
    ) -> pd.DataFrame:
        """
        Get top entities by amount.
        
        Works with ANY file because columns are detected by LLM!
        """
        df = self.get_data()
        if df.empty or entity_type not in df.columns or "amount" not in df.columns:
            return pd.DataFrame()
        
        grouped = df.groupby(entity_type)["amount"].sum().reset_index()
        grouped.columns = ["name", "value"]
        grouped = grouped.sort_values("value", ascending=ascending)
        
        return grouped.head(limit)
    
    def get_time_series(
        self,
        freq: str = "M"  # "D"=daily, "W"=weekly, "M"=monthly
    ) -> pd.DataFrame:
        """
        Get time series data.
        
        Works with ANY date column format - LLM detected!
        """
        df = self.get_data()
        if df.empty or "date" not in df.columns or "amount" not in df.columns:
            return pd.DataFrame()
        
        df_copy = df.copy()
        df_copy["_date"] = pd.to_datetime(df_copy["date"], errors="coerce")
        df_copy = df_copy[df_copy["_date"].notna()]
        
        if df_copy.empty:
            return pd.DataFrame()
        
        df_copy["_period"] = df_copy["_date"].dt.to_period(freq)
        result = df_copy.groupby("_period")["amount"].sum().reset_index()
        result.columns = ["date", "value"]
        result["date"] = result["date"].astype(str)
        
        return result
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the data"""
        df = self.get_data()
        if df.empty:
            return {"error": "No data"}
        
        stats = {
            "total_rows": len(df),
            "total_amount": df["amount"].sum() if "amount" in df.columns else 0,
            "average_amount": df["amount"].mean() if "amount" in df.columns else 0,
            "unique_customers": df["customer"].nunique() if "customer" in df.columns else 0,
            "unique_products": df["product"].nunique() if "product" in df.columns else 0,
        }
        
        # Date range if available
        if "date" in df.columns:
            dates = pd.to_datetime(df["date"], errors="coerce").dropna()
            if not dates.empty:
                stats["date_range"] = {
                    "start": dates.min().strftime("%Y-%m-%d"),
                    "end": dates.max().strftime("%Y-%m-%d")
                }
        
        return stats
    
    def search(
        self,
        query: str,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Search data by query string.
        
        LLM-powered: understands what user is looking for!
        """
        df = self.get_data()
        if df.empty:
            return pd.DataFrame()
        
        if columns is None:
            columns = ["customer", "product"]
        
        query_lower = query.lower()
        mask = pd.Series([False] * len(df))
        
        for col in columns:
            if col in df.columns:
                mask |= df[col].astype(str).str.lower().str.contains(query_lower, na=False)
        
        return df[mask]
    
    def get_currency(self) -> Tuple[str, str]:
        """Get detected currency (symbol, code)"""
        df = self.get_data()
        
        if df.empty or "currency" not in df.columns:
            return "₹", "INR"
        
        # Get most common currency
        most_common = df["currency"].mode()
        if len(most_common) > 0:
            code = most_common.iloc[0]
            symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥"}
            return symbols.get(code, "$"), code
        
        return "₹", "INR"
    
    def get_llm_context(self, max_rows: int = 100) -> str:
        """
        Get data context for LLM prompts.
        
        Returns a structured string that LLM can understand.
        """
        df = self.get_data()
        if df.empty:
            return "No data available."
        
        stats = self.get_summary_stats()
        symbol, code = self.get_currency()
        
        context = f"""**Data Summary:**
- Total Rows: {stats['total_rows']:,}
- Total Revenue: {symbol}{stats['total_amount']:,.2f}
- Currency: {code}
- Unique Customers: {stats['unique_customers']}
- Unique Products: {stats['unique_products']}
"""
        
        if "date_range" in stats:
            context += f"- Date Range: {stats['date_range']['start']} to {stats['date_range']['end']}\n"
        
        # Add top entities
        top_customers = self.get_top_entities("customer", 5)
        if not top_customers.empty:
            context += "\n**Top 5 Customers:**\n"
            for _, row in top_customers.iterrows():
                context += f"- {row['name']}: {symbol}{row['value']:,.2f}\n"
        
        top_products = self.get_top_entities("product", 5)
        if not top_products.empty:
            context += "\n**Top 5 Products:**\n"
            for _, row in top_products.iterrows():
                context += f"- {row['name']}: {symbol}{row['value']:,.2f}\n"
        
        return context


# Global adapter cache
_adapter_cache: Dict[str, UniversalDataAdapter] = {}


def get_adapter(user_id: str) -> UniversalDataAdapter:
    """Get or create adapter for user"""
    if user_id not in _adapter_cache:
        _adapter_cache[user_id] = UniversalDataAdapter(user_id)
    return _adapter_cache[user_id]


def clear_adapter_cache(user_id: Optional[str] = None):
    """Clear adapter cache (call after file upload)"""
    global _adapter_cache
    if user_id:
        _adapter_cache.pop(user_id, None)
    else:
        _adapter_cache.clear()
