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
    query: str
    chart_type: str  # bar, line, pie, table, kpi, area, donut, treemap, ranking
    x_column: Optional[str]
    y_column: Optional[str]
    group_by: Optional[str] = None
    priority: int = 1
    widget_size: str = "medium"  # small, medium, large, full
    visual_config: Dict[str, Any] = None
    layout: str = "both"  # overview, dashboard, or both
    
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
    domain: str
    domain_confidence: float
    business_context: str
    columns: List[ColumnIntelligence]
    key_metrics: List[str]
    dimensions: List[str]
    time_column: Optional[str]
    suggested_analyses: List[SuggestedAnalysis]
    data_quality: DataQuality
    ui_theme: Dict[str, Any] = None
    
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
            "data_quality": self.data_quality.to_dict(),
            "ui_theme": self.ui_theme
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
            data_quality=quality,
            ui_theme=data.get("ui_theme")
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
    
    "ui_theme": {{
        "primary_color": "hex_color",
        "secondary_color": "hex_color",
        "accent_gradient": ["color1", "color2"],
        "icon_set": "retail|finance|health|factory|people|default"
    }},
    
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
            "query": "Natural language query",
            "chart_type": "bar|line|pie|area|donut|treemap|ranking|scatter",
            "x_column": "column_name_or_null",
            "y_column": "column_name_or_null",
            "group_by": "column_name_or_null",
            "priority": 1-5,
            "widget_size": "small|medium|large|full",
            "visual_config": {{"compare_prev": true, "show_trend": true, "columns": ["col1", "col2"]}}
        }}
    ]
}}

IMPORTANT: 
- For the Executive Dashboard (Image 2), suggest 4 `executive_kpi` widgets, 1 `bar` (trend), 1 `matrix` (regional), and 1 `ranking_pro`.
- For the Overview Snapshot (Image 1), suggest 4 `donut` widgets for categorical splits and 1 `master_table` for detailed record lists.
- For `master_table`, ensure it includes "Status" and "Health" in visual_config if possible.
- Choose `ui_theme` colors that match the domain.
- Use `donut` for small category splits (<6 values), `pie` for others.
- Respond with ONLY the JSON, no other text.
- If you see columns like "Invoice", "Amount", "USD", treat them as primary metrics.
- Ensure `widget_size` is "small" for KPIs, "medium" for donuts/charts, and "full" for master_table.
"""

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
            if col.startswith('_'):
                continue
            col_lower = col.lower()
            dtype = str(df[col].dtype)
            unique_count = df[col].nunique()
            row_count = len(df)
            
            # ============================================
            # 100% DATA-DRIVEN DETECTION - NO KEYWORDS
            # ============================================
            
            # Check if column contains currency symbols in VALUES (not column name)
            has_currency_symbols = False
            is_numeric_ish = False
            if dtype == 'object':
                try:
                    sample_vals = df[col].dropna().head(50).astype(str)
                    # Check for currency symbols in actual data values
                    currency_pattern = r'[\$€£¥₹]'
                    has_currency_symbols = sample_vals.str.contains(currency_pattern, regex=True).any()
                    # Strip symbols and check if numeric
                    cleaned_vals = sample_vals.str.replace(r'[\$,€£¥₹\s]', '', regex=True)
                    numeric_vals = pd.to_numeric(cleaned_vals, errors='coerce')
                    if numeric_vals.notnull().mean() > 0.7:  # 70%+ numeric values
                        is_numeric_ish = True
                except:
                    pass
            
            # Check if it's a date column by attempting to parse
            is_date = False
            if dtype == 'object' or 'datetime' in dtype:
                try:
                    if 'datetime' in dtype:
                        is_date = True
                    else:
                        sample_vals = df[col].dropna().head(20).astype(str)
                        parsed = pd.to_datetime(sample_vals, errors='coerce', infer_datetime_format=True)
                        if parsed.notnull().mean() > 0.7:  # 70%+ are valid dates
                            is_date = True
                except:
                    pass
            
            # ============================================
            # CLASSIFICATION BASED ON DATA CHARACTERISTICS
            # ============================================
            
            if is_date:
                detected_type = "date"
                semantic_role = "timestamp"
                time_column = col
                is_metric = False
                is_groupable = False
                
            elif dtype in ['float64', 'int64', 'float32', 'int32'] or is_numeric_ish:
                # Numeric column - decide if metric or dimension based on CARDINALITY
                if unique_count < 15:  # Low cardinality numeric = dimension (like ratings 1-5)
                    detected_type = "category"
                    semantic_role = "dimension"
                    is_metric = False
                    is_groupable = True
                    if col not in dimensions:
                        dimensions.append(col)
                else:
                    # High cardinality numeric = metric
                    # Currency detected from VALUES, not column name
                    detected_type = "currency" if has_currency_symbols else "number"
                    semantic_role = "primary_metric"
                    is_metric = True
                    is_groupable = False
                    if col not in key_metrics:
                        key_metrics.append(col)
                        
            elif unique_count < max(100, row_count * 0.1):  # Less than 100 or 10% of rows = category
                detected_type = "category"
                semantic_role = "dimension"
                is_metric = False
                is_groupable = True
                if col not in dimensions:
                    dimensions.append(col)
                    
            elif unique_count < max(1000, row_count * 0.5):  # Less than 1000 or 50% = text dimension
                detected_type = "text"
                semantic_role = "dimension"
                is_metric = False
                is_groupable = True
                if col not in dimensions:
                    dimensions.append(col)
            else:
                # Very high cardinality = identifier (not useful for grouping)
                detected_type = "identifier"
                semantic_role = "identifier"
                is_metric = False
                is_groupable = False
            
            columns.append({
                "name": col,
                "detected_type": detected_type,
                "semantic_role": semantic_role,
                "business_meaning": col.replace("_", " ").title(),
                "is_key_metric": is_metric,
                "is_groupable": is_groupable,
                "is_filterable": is_groupable or unique_count < 200,  # Filterable if reasonable cardinality
                "sample_values": df[col].dropna().head(3).astype(str).tolist()
            })
        
        # =====================================================
        # POWER BI COLUMN SCORING: Score each metric for KPI selection
        # =====================================================
        metric_scores = []
        for metric in key_metrics:
            try:
                col_data = df[metric]
                non_null_ratio = col_data.notnull().mean()
                # Prefer columns with high fill rate and meaningful variation
                unique_ratio = col_data.nunique() / max(len(col_data), 1)
                aggregation_score = non_null_ratio * 0.7 + (1 - unique_ratio) * 0.3  # Prefer less unique = more aggregatable
                metric_scores.append((metric, aggregation_score, non_null_ratio))
            except:
                metric_scores.append((metric, 0.5, 0.5))
        
        # Sort by score descending
        metric_scores.sort(key=lambda x: x[1], reverse=True)
        top_metrics = [m[0] for m in metric_scores[:4]]  # Max 4 KPIs for overview
        
        # Score dimensions by cardinality (prefer low cardinality for slicers, medium for charts)
        dimension_scores = []
        for dim in dimensions:
            try:
                cardinality = df[dim].nunique()
                # Sweet spot: 2-15 categories for charts, lower for slicers
                if 2 <= cardinality <= 15:
                    score = 1.0
                elif cardinality < 2:
                    score = 0.2
                else:
                    score = max(0.1, 1.0 - (cardinality - 15) / 100)
                dimension_scores.append((dim, score, cardinality))
            except:
                dimension_scores.append((dim, 0.5, 10))
        
        dimension_scores.sort(key=lambda x: x[1], reverse=True)
        top_dimensions = [d[0] for d in dimension_scores[:3]]
        
        print(f"📊 Power BI Scoring - Top Metrics: {top_metrics}, Top Dimensions: {top_dimensions}")
        
        # =====================================================
        # POWER BI VISUAL SELECTION: Generate Overview + Dashboard layouts
        # =====================================================
        suggested = []
        
        # === OVERVIEW VISUALS (Max 6, No Scroll) ===
        
        # 1. KPI CARDS (Top 3-4 metrics by score)
        for i, metric in enumerate(top_metrics[:4]):
            metric_info = next((m for m in metric_scores if m[0] == metric), None)
            fill_rate = f"{int(metric_info[2] * 100)}%" if metric_info else "N/A"
            suggested.append({
                "title": metric.replace('_', ' ').title(),
                "description": f"Aggregated total ({fill_rate} fill rate)",
                "query": f"sum({metric})",
                "chart_type": "kpi_card",  # Power BI standard
                "x_column": None,
                "y_column": metric,
                "priority": 1,
                "widget_size": "small",
                "layout": "overview"
            })
        
        # 2. PRIMARY CHART: Trend (if time) or Bar (if dimension)
        if time_column and top_metrics:
            suggested.append({
                "title": f"{top_metrics[0].replace('_', ' ').title()} Over Time",
                "description": "Time-series trend analysis",
                "query": f"trend {top_metrics[0]} by {time_column}",
                "chart_type": "line_chart",  # Power BI line for trends
                "x_column": time_column,
                "y_column": top_metrics[0],
                "priority": 2,
                "widget_size": "large",
                "layout": "overview"
            })
        elif top_dimensions and top_metrics:
            suggested.append({
                "title": f"{top_metrics[0].replace('_', ' ').title()} by {top_dimensions[0].replace('_', ' ').title()}",
                "description": "Category comparison",
                "query": f"{top_metrics[0]} by {top_dimensions[0]}",
                "chart_type": "bar_chart",  # Power BI bar for categories
                "x_column": top_dimensions[0],
                "y_column": top_metrics[0],
                "priority": 2,
                "widget_size": "large",
                "layout": "overview"
            })
        
        # 3. SUPPORTING CHARTS (Max 2): Donut + Bar
        if len(top_dimensions) >= 1 and top_metrics:
            suggested.append({
                "title": f"{top_dimensions[0].replace('_', ' ').title()} Distribution",
                "description": "Share breakdown",
                "query": f"breakdown by {top_dimensions[0]}",
                "chart_type": "donut_chart",  # Power BI donut for share
                "x_column": top_dimensions[0],
                "y_column": top_metrics[0] if top_metrics else None,
                "priority": 3,
                "widget_size": "medium",
                "layout": "overview"
            })
        
        if len(top_dimensions) >= 2 and top_metrics:
            suggested.append({
                "title": f"{top_metrics[0].replace('_', ' ').title()} by {top_dimensions[1].replace('_', ' ').title()}",
                "description": "Secondary breakdown",
                "query": f"{top_metrics[0]} by {top_dimensions[1]}",
                "chart_type": "bar_chart",
                "x_column": top_dimensions[1],
                "y_column": top_metrics[0],
                "priority": 3,
                "widget_size": "medium",
                "layout": "overview"
            })
        
        # === DASHBOARD VISUALS (Dense, Scrollable) ===
        
        # All Overview visuals + Additional detail charts
        for sug in suggested:
            sug["layout"] = "both"  # Show in both Overview and Dashboard
        
        # Additional Dashboard-only visuals
        if time_column and len(top_metrics) >= 2:
            suggested.append({
                "title": f"{top_metrics[1].replace('_', ' ').title()} Trend",
                "description": "Secondary trend",
                "query": f"trend {top_metrics[1]} by {time_column}",
                "chart_type": "area_chart",
                "x_column": time_column,
                "y_column": top_metrics[1],
                "priority": 4,
                "widget_size": "medium",
                "layout": "dashboard"
            })
        
        # Clustered bar for multi-dimension comparison
        if len(top_dimensions) >= 2 and top_metrics:
            suggested.append({
                "title": f"{top_dimensions[0].replace('_', ' ').title()} vs {top_dimensions[1].replace('_', ' ').title()}",
                "description": "Multi-dimension comparison",
                "query": f"compare {top_dimensions[0]} and {top_dimensions[1]}",
                "chart_type": "clustered_bar",
                "x_column": top_dimensions[0],
                "y_column": top_metrics[0],
                "group_by": top_dimensions[1],
                "priority": 4,
                "widget_size": "large",
                "layout": "dashboard"
            })
        
        # Data table for detailed records
        suggested.append({
            "title": f"{detected_domain} Details",
            "description": "Detailed record view",
            "query": "show all records",
            "chart_type": "data_table",
            "x_column": None,
            "y_column": None,
            "priority": 5,
            "widget_size": "full",
            "layout": "dashboard"
        })
        
        # Generate slicers for filtering
        slicers = []
        if time_column:
            slicers.append({
                "name": time_column,
                "label": time_column.replace('_', ' ').title(),
                "type": "date_range",
                "options": []
            })
        
        for dim, score, cardinality in dimension_scores[:3]:
            if cardinality <= 20:  # Only low-cardinality for slicers
                try:
                    options = df[dim].dropna().unique().tolist()[:20]
                    slicers.append({
                        "name": dim,
                        "label": dim.replace('_', ' ').title(),
                        "type": "dropdown",
                        "options": [str(o) for o in options]
                    })
                except:
                    pass
        
        return {
            "domain": detected_domain,
            "domain_confidence": domain_confidence,
            "business_context": f"Uploaded {detected_domain.lower()} business data",
            "columns": columns,
            "key_metrics": top_metrics,  # Use scored metrics
            "dimensions": [d[0] for d in dimension_scores],
            "time_column": time_column,
            "suggested_analyses": suggested,
            "slicers": slicers
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
    
    def resolve_widgets(self, df: pd.DataFrame, schema: SchemaIntelligence) -> List[Dict[str, Any]]:
        """
        Execute the actual data aggregations for AI-suggested analyses.
        Returns a list of widgets ready for the frontend WidgetFactory.
        """
        resolved_widgets = []
        
        for analysis in schema.suggested_analyses:
            try:
                widget_data = {
                    "title": analysis.title,
                    "description": analysis.description,
                    "chart_type": analysis.chart_type,
                    "widget_size": analysis.widget_size,
                    "visual_config": analysis.visual_config or {},
                    "data": []
                }
                
                df_temp = df.copy()
                y_col = analysis.y_column or (schema.key_metrics[0] if schema.key_metrics else None)
                if not y_col: continue
                
                # Normalize Y
                df_temp['_y'] = pd.to_numeric(df_temp[y_col].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True), errors='coerce').fillna(0)
                
                # 1. Executive KPIs (Image 2 style: Value + Comparison + Sparkline)
                if analysis.chart_type == 'executive_kpi':
                    val = float(df_temp['_y'].sum())
                    widget_data["value"] = val
                    
                    # Try to generate sparkline
                    if analysis.x_column and analysis.x_column in df.columns:
                        df_temp['_x'] = pd.to_datetime(df_temp[analysis.x_column], errors='coerce')
                        df_temp = df_temp.dropna(subset=['_x'])
                        if not df_temp.empty:
                            grouped = df_temp.groupby(df_temp['_x'].dt.to_period('M'))['_y'].sum().sort_index()
                            widget_data["sparkline"] = [{"x": str(k), "y": float(v)} for k, v in grouped.tail(12).items()]
                            
                            # Comparison (Last month vs Month before)
                            if len(grouped) >= 2:
                                current_val = grouped.iloc[-1]
                                prev_val = grouped.iloc[-2]
                                diff = current_val - prev_val
                                pct = (diff / prev_val * 100) if prev_val != 0 else 0
                                widget_data["comparison"] = {
                                    "prev_value": float(prev_val),
                                    "change_pct": float(pct),
                                    "is_positive": pct >= 0
                                }
                    resolved_widgets.append(widget_data)
                
                # 2. Regional Matrix (Image 2 style: Table with multiple aggregations)
                elif analysis.chart_type == 'matrix':
                    if not analysis.x_column: continue
                    cols = widget_data["visual_config"].get("columns", [y_col])
                    # Ensure cols exist
                    valid_cols = [c for c in cols if c in df.columns]
                    
                    # Create aggregations
                    agg_map = {}
                    for c in valid_cols:
                        df_temp[f'_{c}'] = pd.to_numeric(df_temp[c].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True), errors='coerce').fillna(0)
                        agg_map[f'_{c}'] = 'sum'
                    
                    grouped = df_temp.groupby(analysis.x_column).agg(agg_map).head(20)
                    # Flatten and rename back
                    data_list = []
                    for k, row in grouped.iterrows():
                        flat_row = {"dimension": str(k)}
                        for c in valid_cols:
                            flat_row[c] = float(row[f'_{c}'])
                        data_list.append(flat_row)
                    
                    widget_data["data"] = data_list
                    widget_data["columns"] = valid_cols
                    resolved_widgets.append(widget_data)

                # 3. Ranking Pro (Image 2 style: Interactive ranking)
                elif analysis.chart_type == 'ranking_pro':
                    if not analysis.x_column: continue
                    grouped = df_temp.groupby(analysis.x_column)['_y'].sum().sort_values(ascending=False)
                    widget_data["top"] = [{"name": str(k), "value": float(v)} for k, v in grouped.head(5).items()]
                    widget_data["bottom"] = [{"name": str(k), "value": float(v)} for k, v in grouped.tail(5).items()]
                    resolved_widgets.append(widget_data)

                # 4. Donut Groups / Standard Charts (Portfolio style)
                elif analysis.chart_type in ['donut', 'donut_group', 'bar', 'pie', 'treemap']:
                    if not analysis.x_column: continue
                    grouped = df_temp.groupby(analysis.x_column)['_y'].sum().sort_values(ascending=False).head(10)
                    widget_data["data"] = [{"category": str(k), "name": str(k), "value": float(v)} for k, v in grouped.items()]
                    resolved_widgets.append(widget_data)
                
                # 5. Master Data Table (Image 1 style: progress bars)
                elif analysis.chart_type == 'master_table':
                    # Return raw rows with health indicator logic
                    rows = []
                    for i, row in df.head(10).iterrows():
                        r = row.to_dict()
                        # Inject synthetic health for demo if none exists
                        if 'Health' not in r:
                            r['Health'] = 100 if i % 3 == 0 else (60 if i % 2 == 0 else 30)
                        rows.append(r)
                    widget_data["data"] = rows
                    resolved_widgets.append(widget_data)
                
                # 6. Fallback/Standard
                elif widget_data["data"] or "value" in widget_data:
                    resolved_widgets.append(widget_data)
                    
            except Exception as e:
                import traceback
                print(f"Error resolving widget {analysis.title}: {e}")
                traceback.print_exc()
                
        return resolved_widgets

    def generate_overview_data(self, df: pd.DataFrame, schema: SchemaIntelligence) -> dict:
        """
        Generate overview data dynamically based on detected schema.
        """
        resolved_widgets = self.resolve_widgets(df, schema)
        
        result = {
            "hasData": True,
            "domain": schema.domain,
            "business_context": schema.business_context,
            "ui_theme": schema.ui_theme,
            "widgets": resolved_widgets,
            # Legacy fields for backward compatibility if needed
            "metrics": {},
            "timeSeries": [],
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
        result["performance_snapshot"] = []
        for dim_name in schema.dimensions[:3]:
            if dim_name in df.columns and schema.key_metrics:
                primary_metric = schema.key_metrics[0]
                if primary_metric in df.columns:
                    try:
                        df_temp = df.copy()
                        df_temp['_value'] = pd.to_numeric(df_temp[primary_metric].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True), errors='coerce').fillna(0)
                        
                        grouped = df_temp.groupby(dim_name)['_value'].sum().sort_values(ascending=False)
                        if not grouped.empty:
                            result["performance_snapshot"].append({
                                "dimension": dim_name,
                                "metric": primary_metric,
                                "top": {"name": str(grouped.index[0]), "value": float(grouped.iloc[0])},
                                "bottom": {"name": str(grouped.index[-1]), "value": float(grouped.iloc[-1])}
                            })
                            
                        # Existing breakdown logic
                        result["breakdowns"][dim_name] = [
                            {"name": str(name), "value": float(value)}
                            for name, value in grouped.head(10).items()
                        ]
                    except Exception as e:
                        print(f"Performance snapshot error for {dim_name}: {e}")
        
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
