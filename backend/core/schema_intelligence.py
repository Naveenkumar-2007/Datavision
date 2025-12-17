"""
Universal AI Schema Intelligence Engine
=======================================
AI-powered schema analyzer that understands ANY business data automatically.
This is the core innovation that makes the system work with any data format.

Features:
- Domain Detection (Sales, Healthcare, HR, Logistics, Manufacturing, etc.)
- Semantic Column Understanding
- Key Metric Discovery
- Auto-Generated Analysis Suggestions
"""

import os
import json
import pandas as pd
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ColumnIntelligence:
    """Represents AI's understanding of a single column"""
    name: str
    detected_type: str  # currency, number, percentage, text, date, category, id, email, boolean
    semantic_role: str  # primary_metric, secondary_metric, dimension, identifier, timestamp, status
    business_meaning: str
    is_key_metric: bool
    is_groupable: bool
    is_filterable: bool
    sample_values: List[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SuggestedAnalysis:
    """AI-suggested analysis based on detected schema"""
    title: str
    description: str
    query: str  # Natural language query
    chart_type: str  # bar, line, pie, table, kpi, area
    x_column: Optional[str]
    y_column: Optional[str]
    group_by: Optional[str]
    priority: int  # 1-5, 1 being highest priority
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DataQuality:
    """Data quality assessment"""
    completeness: float  # 0.0 to 1.0
    row_count: int
    column_count: int
    issues: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SchemaIntelligence:
    """Complete AI understanding of a dataset"""
    domain: str  # Sales, Healthcare, HR, Logistics, Manufacturing, Education, Finance, Retail, Other
    domain_confidence: float
    business_context: str
    columns: List[ColumnIntelligence]
    key_metrics: List[str]
    dimensions: List[str]
    time_column: Optional[str]
    suggested_analyses: List[SuggestedAnalysis]
    data_quality: DataQuality
    
    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "domain_confidence": self.domain_confidence,
            "business_context": self.business_context,
            "columns": [c.to_dict() for c in self.columns],
            "key_metrics": self.key_metrics,
            "dimensions": self.dimensions,
            "time_column": self.time_column,
            "suggested_analyses": [s.to_dict() for s in self.suggested_analyses],
            "data_quality": self.data_quality.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SchemaIntelligence':
        columns = [ColumnIntelligence(**c) for c in data.get("columns", [])]
        analyses = [SuggestedAnalysis(**a) for a in data.get("suggested_analyses", [])]
        quality = DataQuality(**data.get("data_quality", {
            "completeness": 1.0, "row_count": 0, "column_count": 0, "issues": []
        }))
        
        return cls(
            domain=data.get("domain", "Other"),
            domain_confidence=data.get("domain_confidence", 0.5),
            business_context=data.get("business_context", ""),
            columns=columns,
            key_metrics=data.get("key_metrics", []),
            dimensions=data.get("dimensions", []),
            time_column=data.get("time_column"),
            suggested_analyses=analyses,
            data_quality=quality
        )
    
    def get_column(self, name: str) -> Optional[ColumnIntelligence]:
        """Get column by name"""
        for col in self.columns:
            if col.name == name:
                return col
        return None
    
    def get_metric_columns(self) -> List[ColumnIntelligence]:
        """Get all metric columns"""
        return [c for c in self.columns if c.is_key_metric]
    
    def get_dimension_columns(self) -> List[ColumnIntelligence]:
        """Get all dimension columns"""
        return [c for c in self.columns if c.is_groupable]


# =============================================================================
# AI SCHEMA ANALYZER
# =============================================================================

class UniversalSchemaAnalyzer:
    """
    AI-powered schema analyzer that understands ANY business data.
    Uses OpenRouter LLM to analyze data and detect schema semantically.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "deepseek/deepseek-chat"  # Fast and accurate
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def analyze_dataframe(self, df: pd.DataFrame, filename: str = "data") -> SchemaIntelligence:
        """
        Analyze a DataFrame and return complete schema intelligence.
        This is the main entry point for schema analysis.
        """
        # Step 1: Prepare data sample for AI
        sample_data = self._prepare_sample(df)
        
        # Step 2: Get AI analysis
        ai_response = self._call_ai_analyzer(df, sample_data, filename)
        
        # Step 3: Parse response
        schema = self._parse_ai_response(ai_response, df)
        
        # Step 4: Override domain based on column keywords (more reliable than AI)
        schema = self._override_domain_by_keywords(schema, df)
        
        # Step 5: Enhance with data quality
        schema.data_quality = self._assess_data_quality(df)
        
        return schema
    
    def _override_domain_by_keywords(self, schema: SchemaIntelligence, df: pd.DataFrame) -> SchemaIntelligence:
        """Override domain based on column name keywords for better accuracy"""
        all_columns_lower = [col.lower() for col in df.columns]
        all_columns_str = ' '.join(all_columns_lower)
        
        # Domain keyword patterns - ordered by priority
        domain_patterns = {
            "HR": ["employee", "salary", "hire_date", "hire", "department", "job_title", "job", "bonus", "performance", "tenure", "hr", "staff", "payroll", "emp"],
            "Healthcare": ["patient", "diagnosis", "treatment", "doctor", "hospital", "medical", "prescription", "healthcare", "symptom", "disease", "medication"],
            "Sales": ["product", "customer", "revenue", "sales", "order", "invoice", "price", "discount", "gross", "net", "purchase"],
            "Finance": ["transaction", "account", "balance", "credit", "debit", "interest", "bank", "payment", "financial", "budget"],
            "Logistics": ["shipment", "delivery", "route", "warehouse", "carrier", "freight", "transport", "logistics", "tracking"],
            "Education": ["student", "course", "grade", "score", "teacher", "class", "enrollment", "school", "university", "exam"],
            "Manufacturing": ["production", "unit", "defect", "machine", "shift", "assembly", "quality", "batch", "manufacturing"]
        }
        
        # Count matches per domain
        domain_scores = {}
        for domain, keywords in domain_patterns.items():
            score = sum(1 for kw in keywords if kw in all_columns_str)
            if score > 0:
                domain_scores[domain] = score
        
        print(f"🧠 Domain keyword analysis: {domain_scores}")
        
        # Override if we found a clear match (score >= 2) and current is Other/low confidence
        if domain_scores:
            best_domain, best_score = max(domain_scores.items(), key=lambda x: x[1])
            
            if best_score >= 2:
                old_domain = schema.domain
                schema.domain = best_domain
                schema.domain_confidence = min(0.95, best_score / 5)
                schema.business_context = f"Detected {best_domain.lower()} data based on column patterns"
                print(f"✅ Domain OVERRIDDEN: {old_domain} -> {best_domain} (score: {best_score})")
        
        return schema
    
    def _prepare_sample(self, df: pd.DataFrame, max_rows: int = 10) -> str:
        """Prepare a sample of the data for AI analysis"""
        # Get column info
        column_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            unique = df[col].nunique()
            sample_vals = df[col].dropna().head(3).tolist()
            column_info.append(f"  - {col}: type={dtype}, unique_values={unique}, samples={sample_vals}")
        
        # Get data sample
        sample_df = df.head(max_rows)
        
        return f"""
COLUMNS ({len(df.columns)} total):
{chr(10).join(column_info)}

SAMPLE DATA ({max_rows} rows of {len(df)} total):
{sample_df.to_string(index=False)}
"""
    
    def _call_ai_analyzer(self, df: pd.DataFrame, sample_data: str, filename: str) -> dict:
        """Call AI to analyze the schema"""
        
        prompt = f"""You are a Business Data Intelligence Expert. Analyze this dataset and understand its structure.

FILE: {filename}
ROWS: {len(df)}
{sample_data}

Analyze this data and respond with ONLY valid JSON (no markdown, no explanation):

{{
    "domain": "Sales|Healthcare|HR|Logistics|Manufacturing|Education|Finance|Retail|RealEstate|Other",
    "domain_confidence": 0.0-1.0,
    "business_context": "One sentence describing what this data represents",
    
    "columns": [
        {{
            "name": "exact_column_name",
            "detected_type": "currency|number|percentage|text|date|datetime|category|id|email|phone|address|boolean",
            "semantic_role": "primary_metric|secondary_metric|dimension|identifier|timestamp|status|description",
            "business_meaning": "What this column represents in business terms",
            "is_key_metric": true/false,
            "is_groupable": true/false,
            "is_filterable": true/false,
            "sample_values": ["val1", "val2", "val3"]
        }}
    ],
    
    "key_metrics": ["column_names_that_are_primary_metrics"],
    "dimensions": ["column_names_for_grouping"],
    "time_column": "date_column_name_or_null",
    
    "suggested_analyses": [
        {{
            "title": "Analysis Title",
            "description": "What insight this provides",
            "query": "Natural language query to get this analysis",
            "chart_type": "bar|line|pie|table|kpi|area",
            "x_column": "column_name_or_null",
            "y_column": "column_name_or_null",
            "group_by": "column_name_or_null",
            "priority": 1-5
        }}
    ]
}}

IMPORTANT: 
- Analyze ALL columns in the data
- Identify the PRIMARY revenue/amount/value column (usually the main metric)
- Detect currency columns by $ or number patterns
- Suggest 5-8 meaningful analyses based on the actual data
- Respond with ONLY the JSON, no other text"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Business Analyst"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a data analysis expert. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent output
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            # Clean JSON from markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
            
        except Exception as e:
            print(f"AI Schema Analysis Error: {e}")
            # Return fallback schema based on heuristics
            return self._fallback_analysis(df)
    
    def _fallback_analysis(self, df: pd.DataFrame) -> dict:
        """Fallback analysis using heuristics when AI fails"""
        columns = []
        key_metrics = []
        dimensions = []
        time_column = None
        
        # ============================================
        # SMART DOMAIN DETECTION based on column names
        # ============================================
        all_columns_lower = [col.lower() for col in df.columns]
        all_columns_str = ' '.join(all_columns_lower)
        
        # Domain keyword patterns
        domain_patterns = {
            "HR": ["employee", "salary", "hire_date", "department", "job_title", "bonus", "performance", "tenure", "hr", "staff", "payroll"],
            "Healthcare": ["patient", "diagnosis", "treatment", "doctor", "hospital", "medical", "prescription", "healthcare", "symptom", "disease"],
            "Sales": ["product", "customer", "revenue", "sales", "order", "invoice", "price", "discount", "gross", "net"],
            "Finance": ["transaction", "account", "balance", "credit", "debit", "interest", "bank", "payment", "financial", "budget"],
            "Logistics": ["shipment", "delivery", "route", "warehouse", "carrier", "freight", "transport", "logistics", "tracking"],
            "Education": ["student", "course", "grade", "score", "teacher", "class", "enrollment", "school", "university", "exam"],
            "Manufacturing": ["production", "unit", "defect", "machine", "shift", "assembly", "quality", "batch", "manufacturing"]
        }
        
        # Count matches per domain
        domain_scores = {}
        for domain, keywords in domain_patterns.items():
            score = sum(1 for kw in keywords if kw in all_columns_str)
            if score > 0:
                domain_scores[domain] = score
        
        # Select best domain
        if domain_scores:
            detected_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            domain_confidence = min(0.9, domain_scores[detected_domain] / 5)  # Cap at 0.9
        else:
            detected_domain = "Other"
            domain_confidence = 0.5
        
        print(f"🧠 Fallback domain detection: {detected_domain} (scores: {domain_scores})")
        
        for col in df.columns:
            col_lower = col.lower()
            dtype = str(df[col].dtype)
            
            # Detect type heuristically
            if 'date' in col_lower or 'time' in col_lower:
                detected_type = "date"
                semantic_role = "timestamp"
                time_column = col
                is_metric = False
                is_groupable = False
            elif dtype in ['float64', 'int64']:
                # Check if it's a currency/metric
                if any(x in col_lower for x in ['revenue', 'amount', 'price', 'cost', 'total', 'sales', 'value', 'profit', 'salary', 'bonus', 'income', 'expense']):
                    detected_type = "currency"
                    semantic_role = "primary_metric"
                    is_metric = True
                    key_metrics.append(col)
                else:
                    detected_type = "number"
                    semantic_role = "secondary_metric"
                    is_metric = True
                is_groupable = False
            elif df[col].nunique() < 50:
                detected_type = "category"
                semantic_role = "dimension"
                is_metric = False
                is_groupable = True
                dimensions.append(col)
            else:
                detected_type = "text"
                semantic_role = "dimension"
                is_metric = False
                is_groupable = df[col].nunique() < 100
                if is_groupable:
                    dimensions.append(col)
            
            columns.append({
                "name": col,
                "detected_type": detected_type,
                "semantic_role": semantic_role,
                "business_meaning": col.replace("_", " ").title(),
                "is_key_metric": is_metric,
                "is_groupable": is_groupable,
                "is_filterable": True,
                "sample_values": df[col].dropna().head(3).astype(str).tolist()
            })
        
        # Generate suggested analyses
        suggested = []
        for metric in key_metrics[:2]:
            for dim in dimensions[:3]:
                suggested.append({
                    "title": f"{metric} by {dim}",
                    "description": f"Analyze {metric} across different {dim}",
                    "query": f"Show {metric} by {dim}",
                    "chart_type": "bar",
                    "x_column": dim,
                    "y_column": metric,
                    "group_by": None,
                    "priority": 2
                })
        
        return {
            "domain": detected_domain,
            "domain_confidence": domain_confidence,
            "business_context": f"Uploaded {detected_domain.lower()} business data",
            "columns": columns,
            "key_metrics": key_metrics,
            "dimensions": dimensions,
            "time_column": time_column,
            "suggested_analyses": suggested[:6]
        }
    
    def _parse_ai_response(self, response: dict, df: pd.DataFrame) -> SchemaIntelligence:
        """Parse AI response into SchemaIntelligence object"""
        return SchemaIntelligence.from_dict(response)
    
    def _assess_data_quality(self, df: pd.DataFrame) -> DataQuality:
        """Assess the quality of the data"""
        issues = []
        
        # Check for missing values
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
        if missing_pct > 0.1:
            issues.append(f"High missing values: {missing_pct:.1%}")
        
        # Check for duplicates
        dup_pct = df.duplicated().sum() / len(df)
        if dup_pct > 0.05:
            issues.append(f"Duplicate rows: {dup_pct:.1%}")
        
        return DataQuality(
            completeness=1 - missing_pct,
            row_count=len(df),
            column_count=len(df.columns),
            issues=issues
        )


# =============================================================================
# SCHEMA STORAGE
# =============================================================================

class SchemaStorage:
    """Store and retrieve schema intelligence for files"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_schema(self, file_id: str, schema: SchemaIntelligence):
        """Save schema intelligence for a file"""
        schema_file = self.storage_path / f"{file_id}_schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema.to_dict(), f, indent=2)
    
    def load_schema(self, file_id: str) -> Optional[SchemaIntelligence]:
        """Load schema intelligence for a file"""
        schema_file = self.storage_path / f"{file_id}_schema.json"
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                data = json.load(f)
                return SchemaIntelligence.from_dict(data)
        return None
    
    def has_schema(self, file_id: str) -> bool:
        """Check if schema exists for a file"""
        schema_file = self.storage_path / f"{file_id}_schema.json"
        return schema_file.exists()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def analyze_uploaded_file(file_path: Path, user_id: str) -> SchemaIntelligence:
    """
    Convenience function to analyze an uploaded file.
    Call this after file upload to get schema intelligence.
    """
    # Read file
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    # Analyze
    analyzer = UniversalSchemaAnalyzer()
    schema = analyzer.analyze_dataframe(df, file_path.name)
    
    # Store
    from backend.utils.paths import get_user_paths
    paths = get_user_paths(user_id)
    storage = SchemaStorage(paths["storage"] / "schemas")
    storage.save_schema(file_path.stem, schema)
    
    return schema


def get_schema_for_user(user_id: str) -> Optional[SchemaIntelligence]:
    """Get the combined schema for all user's files"""
    from backend.utils.paths import get_user_paths
    paths = get_user_paths(user_id)
    storage = SchemaStorage(paths["storage"] / "schemas")
    
    # Get latest schema
    schema_files = list((paths["storage"] / "schemas").glob("*_schema.json"))
    if schema_files:
        latest = max(schema_files, key=lambda x: x.stat().st_mtime)
        return storage.load_schema(latest.stem.replace("_schema", ""))
    
    return None


# =============================================================================
# DYNAMIC ANALYTICS GENERATOR
# =============================================================================

class DynamicAnalyticsGenerator:
    """
    Generate analytics automatically based on detected schema.
    Creates KPIs, charts, and insights without manual configuration.
    """
    
    def generate_overview_data(self, df: pd.DataFrame, schema: SchemaIntelligence) -> dict:
        """
        Generate overview data dynamically based on detected schema.
        This replaces the hardcoded column detection in analytics.py
        """
        result = {
            "hasData": True,
            "domain": schema.domain,
            "business_context": schema.business_context,
            "metrics": {},
            "timeSeries": [],
            "topItems": {},
            "breakdowns": {}
        }
        
        # Generate KPI metrics from key_metrics
        for metric_name in schema.key_metrics:
            col_info = schema.get_column(metric_name)
            if col_info and metric_name in df.columns:
                # Clean currency values
                values = df[metric_name].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True)
                values = pd.to_numeric(values, errors='coerce').fillna(0)
                
                result["metrics"][metric_name] = {
                    "total": float(values.sum()),
                    "average": float(values.mean()),
                    "count": int(len(values)),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "business_meaning": col_info.business_meaning
                }
        
        # Generate time series if time column detected
        if schema.time_column and schema.time_column in df.columns:
            try:
                df_temp = df.copy()
                df_temp['_date'] = pd.to_datetime(df_temp[schema.time_column], errors='coerce')
                df_temp = df_temp.dropna(subset=['_date'])
                
                if not df_temp.empty and schema.key_metrics:
                    primary_metric = schema.key_metrics[0]
                    if primary_metric in df_temp.columns:
                        # Clean values
                        df_temp['_value'] = df_temp[primary_metric].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True)
                        df_temp['_value'] = pd.to_numeric(df_temp['_value'], errors='coerce').fillna(0)
                        
                        daily = df_temp.groupby(df_temp['_date'].dt.date)['_value'].sum()
                        for date, value in daily.items():
                            result["timeSeries"].append({
                                "date": date.isoformat(),
                                "value": float(value),
                                "metric": primary_metric
                            })
            except Exception as e:
                print(f"Time series error: {e}")
        
        # Generate breakdowns by dimensions
        for dim_name in schema.dimensions[:5]:  # Limit to 5 dimensions
            if dim_name in df.columns and schema.key_metrics:
                primary_metric = schema.key_metrics[0]
                if primary_metric in df.columns:
                    try:
                        df_temp = df.copy()
                        df_temp['_value'] = df_temp[primary_metric].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True)
                        df_temp['_value'] = pd.to_numeric(df_temp['_value'], errors='coerce').fillna(0)
                        
                        breakdown = df_temp.groupby(dim_name)['_value'].sum().sort_values(ascending=False).head(10)
                        result["breakdowns"][dim_name] = [
                            {"name": str(name), "value": float(value)}
                            for name, value in breakdown.items()
                        ]
                    except Exception as e:
                        print(f"Breakdown error for {dim_name}: {e}")
        
        return result


# Export main classes
__all__ = [
    'SchemaIntelligence',
    'ColumnIntelligence',
    'SuggestedAnalysis',
    'DataQuality',
    'UniversalSchemaAnalyzer',
    'SchemaStorage',
    'DynamicAnalyticsGenerator',
    'analyze_uploaded_file',
    'get_schema_for_user'
]
