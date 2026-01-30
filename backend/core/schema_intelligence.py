"""
🧠 Schema Intelligence - AI-Powered Data Schema Analysis
=========================================================

Automatically detects:
- Domain (e-commerce, finance, healthcare, etc.)
- Key metrics
- Dimensions
- Time columns
- Data quality
- Suggested analyses
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DataQuality:
    """Data quality metrics"""
    completeness: float = 1.0
    row_count: int = 0
    column_count: int = 0
    null_count: int = 0
    duplicate_count: int = 0


@dataclass
class SchemaIntelligence:
    """Complete schema intelligence result"""
    domain: str = "general"
    domain_confidence: float = 0.5
    key_metrics: List[str] = field(default_factory=list)
    dimensions: List[str] = field(default_factory=list)
    time_column: Optional[str] = None
    suggested_analyses: List[str] = field(default_factory=list)
    columns: Dict[str, Dict] = field(default_factory=dict)
    data_quality: DataQuality = field(default_factory=DataQuality)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "domain": self.domain,
            "domain_confidence": self.domain_confidence,
            "key_metrics": self.key_metrics,
            "dimensions": self.dimensions,
            "time_column": self.time_column,
            "suggested_analyses": self.suggested_analyses,
            "columns": self.columns,
            "data_quality": {
                "completeness": self.data_quality.completeness,
                "row_count": self.data_quality.row_count,
                "column_count": self.data_quality.column_count,
                "null_count": self.data_quality.null_count,
                "duplicate_count": self.data_quality.duplicate_count
            }
        }


# =============================================================================
# DOMAIN PATTERNS
# =============================================================================

DOMAIN_PATTERNS = {
    "e-commerce": {
        "columns": ["order", "product", "customer", "price", "quantity", "revenue", "discount", "category", "sku"],
        "metrics": ["revenue", "sales", "price", "profit", "discount"],
        "dimensions": ["product", "category", "customer", "region"]
    },
    "finance": {
        "columns": ["transaction", "amount", "balance", "account", "payment", "invoice", "credit", "debit"],
        "metrics": ["amount", "balance", "payment", "revenue", "cost"],
        "dimensions": ["account", "type", "category"]
    },
    "healthcare": {
        "columns": ["patient", "diagnosis", "treatment", "hospital", "doctor", "insurance", "claim"],
        "metrics": ["cost", "duration", "count"],
        "dimensions": ["diagnosis", "treatment", "department"]
    },
    "marketing": {
        "columns": ["campaign", "impression", "click", "conversion", "ctr", "cpc", "roi", "ad", "channel"],
        "metrics": ["impressions", "clicks", "conversions", "ctr", "cpc", "spend"],
        "dimensions": ["campaign", "channel", "audience"]
    },
    "hr": {
        "columns": ["employee", "salary", "department", "hire", "performance", "leave", "attendance"],
        "metrics": ["salary", "headcount", "attrition"],
        "dimensions": ["department", "role", "location"]
    },
    "sales": {
        "columns": ["sale", "lead", "opportunity", "deal", "quota", "pipeline", "win", "close"],
        "metrics": ["revenue", "deals", "quota", "pipeline"],
        "dimensions": ["product", "region", "salesperson"]
    }
}


# =============================================================================
# UNIVERSAL SCHEMA ANALYZER
# =============================================================================

class UniversalSchemaAnalyzer:
    """
    🧠 AI-Powered Universal Schema Analyzer
    
    Automatically detects:
    - Business domain (e-commerce, finance, etc.)
    - Key metrics (numeric columns for analysis)
    - Dimensions (categorical columns for grouping)
    - Time columns (for time series analysis)
    - Data quality issues
    - Suggested analyses
    """
    
    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        filename: str = "data"
    ) -> SchemaIntelligence:
        """Analyze a DataFrame and return schema intelligence"""
        
        logger.info(f"🧠 Analyzing schema for: {filename}")
        
        # Initialize schema
        schema = SchemaIntelligence()
        
        # Basic stats
        schema.data_quality = DataQuality(
            row_count=len(df),
            column_count=len(df.columns),
            null_count=int(df.isna().sum().sum()),
            duplicate_count=int(df.duplicated().sum()),
            completeness=1 - (df.isna().sum().sum() / (len(df) * len(df.columns)))
        )
        
        # Analyze columns
        schema.columns = self._analyze_columns(df)
        
        # Detect domain
        schema.domain, schema.domain_confidence = self._detect_domain(df)
        
        # Find key metrics (numeric columns)
        schema.key_metrics = self._find_metrics(df)
        
        # Find dimensions (categorical columns)
        schema.dimensions = self._find_dimensions(df)
        
        # Find time column
        schema.time_column = self._find_time_column(df)
        
        # Generate suggested analyses
        schema.suggested_analyses = self._suggest_analyses(df, schema)
        
        logger.info(f"✅ Schema: domain={schema.domain}, metrics={len(schema.key_metrics)}, dims={len(schema.dimensions)}")
        
        return schema
    
    def _analyze_columns(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze each column"""
        columns = {}
        
        for col in df.columns:
            series = df[col]
            
            col_info = {
                "name": col,
                "dtype": str(series.dtype),
                "null_count": int(series.isna().sum()),
                "unique_count": int(series.nunique()),
                "category": self._detect_column_category(series, col)
            }
            
            # Add stats for numeric columns
            if pd.api.types.is_numeric_dtype(series):
                col_info["stats"] = {
                    "mean": float(series.mean()) if not series.isna().all() else None,
                    "std": float(series.std()) if not series.isna().all() else None,
                    "min": float(series.min()) if not series.isna().all() else None,
                    "max": float(series.max()) if not series.isna().all() else None
                }
            
            columns[col] = col_info
        
        return columns
    
    def _detect_column_category(self, series: pd.Series, col_name: str) -> str:
        """Detect column category"""
        col_lower = col_name.lower()
        
        if any(x in col_lower for x in ['id', 'key', 'index', 'uuid']):
            return "identifier"
        elif any(x in col_lower for x in ['date', 'time', 'timestamp', 'created', 'updated']):
            return "temporal"
        elif any(x in col_lower for x in ['price', 'amount', 'cost', 'revenue', 'salary', 'total']):
            return "monetary"
        elif any(x in col_lower for x in ['name', 'title', 'description', 'text']):
            return "text"
        elif any(x in col_lower for x in ['email', 'phone', 'address', 'url']):
            return "contact"
        elif pd.api.types.is_numeric_dtype(series):
            return "numeric"
        else:
            return "categorical"
    
    def _detect_domain(self, df: pd.DataFrame) -> tuple:
        """Detect business domain from column names"""
        columns_lower = [c.lower() for c in df.columns]
        
        scores = {}
        
        for domain, patterns in DOMAIN_PATTERNS.items():
            score = 0
            for pattern in patterns["columns"]:
                for col in columns_lower:
                    if pattern in col:
                        score += 1
            scores[domain] = score
        
        if not scores or max(scores.values()) == 0:
            return "general", 0.5
        
        best_domain = max(scores, key=scores.get)
        confidence = min(scores[best_domain] / 5, 1.0)
        
        return best_domain, confidence
    
    def _find_metrics(self, df: pd.DataFrame) -> List[str]:
        """Find key metric columns"""
        metrics = []
        
        for col in df.columns:
            col_lower = col.lower()
            series = df[col]
            
            # Numeric columns that look like metrics
            if pd.api.types.is_numeric_dtype(series):
                if any(x in col_lower for x in ['price', 'amount', 'revenue', 'sales', 'cost', 'profit', 'total', 'count', 'qty', 'quantity']):
                    metrics.append(col)
                elif series.nunique() > 10:  # High cardinality numeric = likely metric
                    metrics.append(col)
        
        return metrics[:10]
    
    def _find_dimensions(self, df: pd.DataFrame) -> List[str]:
        """Find dimension columns for grouping"""
        dimensions = []
        
        for col in df.columns:
            col_lower = col.lower()
            series = df[col]
            
            # Skip IDs and timestamps
            if any(x in col_lower for x in ['id', 'date', 'time', 'timestamp']):
                continue
            
            # Categorical columns with reasonable cardinality
            if series.dtype == 'object' or series.nunique() <= 50:
                if series.nunique() >= 2:
                    dimensions.append(col)
        
        return dimensions[:10]
    
    def _find_time_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the main time column"""
        for col in df.columns:
            col_lower = col.lower()
            
            # Check column name
            if any(x in col_lower for x in ['date', 'time', 'timestamp', 'created', 'order_date']):
                return col
            
            # Check if datetime type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return col
        
        return None
    
    def _suggest_analyses(self, df: pd.DataFrame, schema: SchemaIntelligence) -> List[str]:
        """Generate suggested analyses"""
        suggestions = []
        
        if schema.key_metrics:
            suggestions.append(f"Trend analysis on {schema.key_metrics[0]}")
        
        if schema.dimensions and schema.key_metrics:
            suggestions.append(f"Breakdown by {schema.dimensions[0]}")
        
        if schema.time_column and schema.key_metrics:
            suggestions.append(f"Time series forecast for {schema.key_metrics[0]}")
        
        if len(schema.key_metrics) >= 2:
            suggestions.append(f"Correlation between {schema.key_metrics[0]} and {schema.key_metrics[1]}")
        
        if schema.domain != "general":
            suggestions.append(f"Domain-specific {schema.domain} analysis")
        
        return suggestions


# =============================================================================
# SCHEMA STORAGE
# =============================================================================

class SchemaStorage:
    """Store and load schema intelligence"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_schema(self, file_id: str, schema: SchemaIntelligence) -> None:
        """Save schema to JSON file"""
        filepath = self.storage_dir / f"{file_id}_schema.json"
        with open(filepath, 'w') as f:
            json.dump(schema.to_dict(), f, indent=2, default=str)
        logger.info(f"💾 Schema saved: {filepath}")
    
    def load_schema(self, file_id: str) -> Optional[SchemaIntelligence]:
        """Load schema from JSON file"""
        filepath = self.storage_dir / f"{file_id}_schema.json"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Reconstruct schema
            schema = SchemaIntelligence(
                domain=data.get("domain", "general"),
                domain_confidence=data.get("domain_confidence", 0.5),
                key_metrics=data.get("key_metrics", []),
                dimensions=data.get("dimensions", []),
                time_column=data.get("time_column"),
                suggested_analyses=data.get("suggested_analyses", []),
                columns=data.get("columns", {})
            )
            
            # Reconstruct data quality
            dq = data.get("data_quality", {})
            schema.data_quality = DataQuality(
                completeness=dq.get("completeness", 1.0),
                row_count=dq.get("row_count", 0),
                column_count=dq.get("column_count", 0),
                null_count=dq.get("null_count", 0),
                duplicate_count=dq.get("duplicate_count", 0)
            )
            
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return None
