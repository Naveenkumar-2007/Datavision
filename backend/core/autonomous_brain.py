"""
🧠 AUTONOMOUS DATA BRAIN - DataVision Core Intelligence
========================================================

The brain that makes DataVision magical. Drop ANY file and get:
- Complete data profiling in seconds
- Automatic quality scoring and fix suggestions
- Column relationship discovery
- AI-generated insights and visualizations
- Predictive recommendations

FREE MODELS FIRST: Groq (Llama 3.3 70B), Gemini Free
"""

import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from core.llm import chat

logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"            # 70-89%
    FAIR = "fair"            # 50-69%
    POOR = "poor"            # 0-49%


class ColumnType(Enum):
    """Detected column types"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    ID = "id"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"


@dataclass
class ColumnProfile:
    """Profile for a single column"""
    name: str
    detected_type: ColumnType
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    sample_values: List[Any]
    
    # Numeric stats (if applicable)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    
    # Categorical stats (if applicable)
    top_values: Optional[Dict[str, int]] = None
    
    # Quality issues
    issues: List[str] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)


@dataclass
class DataRelationship:
    """Relationship between columns"""
    column1: str
    column2: str
    relationship_type: str  # correlation, categorical_group, time_series, etc.
    strength: float  # 0-1
    description: str


@dataclass
class DataInsight:
    """AI-generated insight"""
    title: str
    description: str
    importance: str  # high, medium, low
    category: str  # trend, anomaly, pattern, recommendation
    data_points: Dict[str, Any] = field(default_factory=dict)
    visualization_suggestion: Optional[str] = None


@dataclass
class BrainAnalysis:
    """Complete autonomous analysis result"""
    # Metadata
    file_name: str
    analysis_timestamp: str
    analysis_duration_ms: int
    
    # Data overview
    total_rows: int
    total_columns: int
    memory_usage_mb: float
    
    # Quality
    quality_score: float
    quality_level: DataQuality
    quality_issues: List[str]
    
    # Column profiles
    columns: List[ColumnProfile]
    
    # Relationships
    relationships: List[DataRelationship]
    
    # AI Insights
    insights: List[DataInsight]
    
    # Suggested visualizations
    suggested_charts: List[Dict[str, Any]]
    
    # Quick summary for LLM context
    summary: str


class AutonomousBrain:
    """
    🧠 The DataVision Autonomous Brain
    
    Automatically analyzes ANY data and generates:
    - Complete data profile
    - Quality assessment with fix suggestions
    - Column relationships and correlations
    - AI-powered insights
    - Visualization recommendations
    """
    
    def __init__(self):
        self.analysis_cache: Dict[str, BrainAnalysis] = {}
    
    async def analyze(
        self, 
        df: pd.DataFrame, 
        file_name: str = "data",
        generate_insights: bool = True
    ) -> BrainAnalysis:
        """
        🚀 Main entry point - Analyze ANY DataFrame autonomously
        
        Args:
            df: The DataFrame to analyze
            file_name: Name of the source file
            generate_insights: Whether to generate AI insights (slower but richer)
            
        Returns:
            Complete BrainAnalysis with all findings
        """
        start_time = datetime.now()
        
        logger.info(f"🧠 Autonomous Brain analyzing: {file_name} ({len(df)} rows, {len(df.columns)} cols)")
        
        # 1. Profile all columns
        column_profiles = self._profile_columns(df)
        
        # 2. Calculate quality score
        quality_score, quality_issues = self._calculate_quality(df, column_profiles)
        quality_level = self._get_quality_level(quality_score)
        
        # 3. Discover relationships
        relationships = self._discover_relationships(df, column_profiles)
        
        # 4. Generate AI insights (if enabled)
        insights = []
        if generate_insights:
            insights = await self._generate_insights(df, column_profiles, relationships)
        
        # 5. Suggest visualizations
        suggested_charts = self._suggest_visualizations(df, column_profiles, relationships)
        
        # 6. Create summary
        summary = self._create_summary(df, column_profiles, quality_score, insights)
        
        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        analysis = BrainAnalysis(
            file_name=file_name,
            analysis_timestamp=datetime.now().isoformat(),
            analysis_duration_ms=duration_ms,
            total_rows=len(df),
            total_columns=len(df.columns),
            memory_usage_mb=df.memory_usage(deep=True).sum() / (1024 * 1024),
            quality_score=quality_score,
            quality_level=quality_level,
            quality_issues=quality_issues,
            columns=column_profiles,
            relationships=relationships,
            insights=insights,
            suggested_charts=suggested_charts,
            summary=summary
        )
        
        # Cache the analysis
        self.analysis_cache[file_name] = analysis
        
        logger.info(f"✅ Analysis complete in {duration_ms}ms - Quality: {quality_score:.1f}%")
        
        return analysis
    
    def _profile_columns(self, df: pd.DataFrame) -> List[ColumnProfile]:
        """Profile each column in the DataFrame"""
        profiles = []
        
        for col in df.columns:
            series = df[col]
            
            # Detect type
            detected_type = self._detect_column_type(series, col)
            
            # Basic stats
            null_count = series.isna().sum()
            null_pct = (null_count / len(series)) * 100 if len(series) > 0 else 0
            unique_count = series.nunique()
            unique_pct = (unique_count / len(series)) * 100 if len(series) > 0 else 0
            
            # Sample values (non-null)
            sample_values = series.dropna().head(5).tolist()
            
            profile = ColumnProfile(
                name=col,
                detected_type=detected_type,
                null_count=null_count,
                null_percentage=round(null_pct, 2),
                unique_count=unique_count,
                unique_percentage=round(unique_pct, 2),
                sample_values=sample_values
            )
            
            # Add numeric stats if applicable
            if detected_type in [ColumnType.NUMERIC, ColumnType.CURRENCY, ColumnType.PERCENTAGE]:
                numeric_series = pd.to_numeric(series, errors='coerce')
                profile.min_value = float(numeric_series.min()) if not numeric_series.isna().all() else None
                profile.max_value = float(numeric_series.max()) if not numeric_series.isna().all() else None
                profile.mean_value = float(numeric_series.mean()) if not numeric_series.isna().all() else None
                profile.median_value = float(numeric_series.median()) if not numeric_series.isna().all() else None
                profile.std_value = float(numeric_series.std()) if not numeric_series.isna().all() else None
            
            # Add categorical stats if applicable
            if detected_type == ColumnType.CATEGORICAL:
                value_counts = series.value_counts().head(10).to_dict()
                profile.top_values = {str(k): int(v) for k, v in value_counts.items()}
            
            # Detect issues
            profile.issues, profile.fix_suggestions = self._detect_column_issues(series, profile)
            
            profiles.append(profile)
        
        return profiles
    
    def _detect_column_type(self, series: pd.Series, col_name: str) -> ColumnType:
        """Intelligently detect the column type"""
        col_lower = col_name.lower()
        
        # Check by column name patterns first
        if any(x in col_lower for x in ['id', '_id', 'uuid', 'key']):
            return ColumnType.ID
        if any(x in col_lower for x in ['email', 'mail']):
            return ColumnType.EMAIL
        if any(x in col_lower for x in ['url', 'link', 'website']):
            return ColumnType.URL
        if any(x in col_lower for x in ['phone', 'mobile', 'tel']):
            return ColumnType.PHONE
        if any(x in col_lower for x in ['price', 'cost', 'amount', 'revenue', 'salary', 'fee']):
            return ColumnType.CURRENCY
        if any(x in col_lower for x in ['percent', 'rate', 'ratio', 'pct', '%']):
            return ColumnType.PERCENTAGE
        if any(x in col_lower for x in ['date', 'time', 'created', 'updated', 'timestamp']):
            return ColumnType.DATETIME
        
        # Check by data type
        if pd.api.types.is_bool_dtype(series):
            return ColumnType.BOOLEAN
        
        if pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME
        
        if pd.api.types.is_numeric_dtype(series):
            return ColumnType.NUMERIC
        
        # Check string content
        if series.dtype == 'object':
            non_null = series.dropna()
            if len(non_null) > 0:
                # Check if it's a date string
                try:
                    pd.to_datetime(non_null.head(10))
                    return ColumnType.DATETIME
                except:
                    pass
                
                # Check cardinality for categorical
                unique_ratio = non_null.nunique() / len(non_null)
                avg_length = non_null.astype(str).str.len().mean()
                
                if unique_ratio < 0.5 or non_null.nunique() < 50:
                    return ColumnType.CATEGORICAL
                
                if avg_length > 100:
                    return ColumnType.TEXT
        
        return ColumnType.CATEGORICAL
    
    def _detect_column_issues(
        self, 
        series: pd.Series, 
        profile: ColumnProfile
    ) -> Tuple[List[str], List[str]]:
        """Detect quality issues and suggest fixes"""
        issues = []
        fixes = []
        
        # High null percentage
        if profile.null_percentage > 50:
            issues.append(f"High missing values ({profile.null_percentage}%)")
            fixes.append("Consider dropping this column or imputing missing values")
        elif profile.null_percentage > 10:
            issues.append(f"Moderate missing values ({profile.null_percentage}%)")
            fixes.append("Consider imputing with mean/median/mode")
        
        # Check for duplicates in ID columns
        if profile.detected_type == ColumnType.ID:
            if profile.unique_percentage < 100:
                issues.append("Duplicate IDs detected")
                fixes.append("Remove duplicate rows or fix ID generation")
        
        # Low cardinality in numeric columns
        if profile.detected_type == ColumnType.NUMERIC:
            if profile.unique_count < 10 and profile.null_percentage < 50:
                issues.append("Low cardinality - might be categorical")
                fixes.append("Consider converting to categorical type")
        
        # Check for outliers in numeric columns
        if profile.detected_type == ColumnType.NUMERIC and profile.std_value:
            if profile.std_value > 0:
                cv = profile.std_value / abs(profile.mean_value) if profile.mean_value else 0
                if cv > 2:
                    issues.append("High variance - possible outliers")
                    fixes.append("Investigate extreme values and consider winsorizing")
        
        # High cardinality in categorical
        if profile.detected_type == ColumnType.CATEGORICAL:
            if profile.unique_percentage > 80:
                issues.append("High cardinality - might be text or ID")
                fixes.append("Consider using as text or creating embeddings")
        
        return issues, fixes
    
    def _calculate_quality(
        self, 
        df: pd.DataFrame, 
        profiles: List[ColumnProfile]
    ) -> Tuple[float, List[str]]:
        """Calculate overall data quality score"""
        scores = []
        issues = []
        
        # 1. Completeness score (missing values)
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0
        scores.append(completeness)
        
        if completeness < 90:
            issues.append(f"Data completeness: {completeness:.1f}%")
        
        # 2. Uniqueness score (for ID columns)
        id_cols = [p for p in profiles if p.detected_type == ColumnType.ID]
        if id_cols:
            uniqueness = sum(p.unique_percentage for p in id_cols) / len(id_cols)
            scores.append(uniqueness)
            if uniqueness < 100:
                issues.append(f"ID uniqueness: {uniqueness:.1f}%")
        
        # 3. Column issue score
        total_issues = sum(len(p.issues) for p in profiles)
        max_issues = len(profiles) * 3  # Assume max 3 issues per column
        issue_score = max(0, 100 - (total_issues / max_issues * 100)) if max_issues > 0 else 100
        scores.append(issue_score)
        
        if total_issues > 0:
            issues.append(f"{total_issues} quality issues detected")
        
        # 4. Data type consistency
        type_scores = []
        for profile in profiles:
            non_null = df[profile.name].dropna()
            if len(non_null) > 0 and profile.detected_type == ColumnType.NUMERIC:
                numeric_valid = pd.to_numeric(non_null, errors='coerce').notna().sum()
                type_scores.append((numeric_valid / len(non_null)) * 100)
        
        if type_scores:
            consistency = sum(type_scores) / len(type_scores)
            scores.append(consistency)
        
        # Overall quality score
        quality_score = sum(scores) / len(scores) if scores else 100
        
        return round(quality_score, 1), issues
    
    def _get_quality_level(self, score: float) -> DataQuality:
        """Convert score to quality level"""
        if score >= 90:
            return DataQuality.EXCELLENT
        elif score >= 70:
            return DataQuality.GOOD
        elif score >= 50:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR
    
    def _discover_relationships(
        self, 
        df: pd.DataFrame, 
        profiles: List[ColumnProfile]
    ) -> List[DataRelationship]:
        """Discover relationships between columns"""
        relationships = []
        
        # Get numeric columns for correlation
        numeric_cols = [p.name for p in profiles 
                       if p.detected_type in [ColumnType.NUMERIC, ColumnType.CURRENCY, ColumnType.PERCENTAGE]]
        
        # Get categorical columns
        categorical_cols = [p.name for p in profiles 
                          if p.detected_type == ColumnType.CATEGORICAL]
        
        # Get datetime columns
        datetime_cols = [p.name for p in profiles 
                        if p.detected_type == ColumnType.DATETIME]
        
        # 1. Numeric correlations
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols].corr()
                for i, col1 in enumerate(numeric_cols):
                    for col2 in numeric_cols[i+1:]:
                        corr = corr_matrix.loc[col1, col2]
                        if not pd.isna(corr) and abs(corr) > 0.3:
                            strength = abs(corr)
                            relationship_type = "positive_correlation" if corr > 0 else "negative_correlation"
                            description = f"{'Strong' if strength > 0.7 else 'Moderate'} {relationship_type.replace('_', ' ')} ({corr:.2f})"
                            
                            relationships.append(DataRelationship(
                                column1=col1,
                                column2=col2,
                                relationship_type=relationship_type,
                                strength=strength,
                                description=description
                            ))
            except Exception as e:
                logger.warning(f"Error calculating correlations: {e}")
        
        # 2. Categorical groupings (categories that segment numeric values)
        for cat_col in categorical_cols[:5]:  # Limit to top 5
            for num_col in numeric_cols[:5]:
                try:
                    grouped = df.groupby(cat_col)[num_col].agg(['mean', 'std']).dropna()
                    if len(grouped) >= 2:
                        # Check if there's significant variation between groups
                        cv = grouped['std'].mean() / grouped['mean'].mean() if grouped['mean'].mean() != 0 else 0
                        if cv > 0.1:  # Significant variation
                            relationships.append(DataRelationship(
                                column1=cat_col,
                                column2=num_col,
                                relationship_type="categorical_grouping",
                                strength=min(1.0, cv),
                                description=f"{cat_col} segments {num_col} with noticeable variation"
                            ))
                except Exception:
                    pass
        
        # 3. Time series relationships
        for dt_col in datetime_cols:
            for num_col in numeric_cols[:5]:
                try:
                    # Check if data varies over time
                    temp_df = df[[dt_col, num_col]].dropna()
                    if len(temp_df) > 10:
                        relationships.append(DataRelationship(
                            column1=dt_col,
                            column2=num_col,
                            relationship_type="time_series",
                            strength=0.8,
                            description=f"{num_col} tracked over {dt_col}"
                        ))
                except Exception:
                    pass
        
        # Sort by strength and limit
        relationships.sort(key=lambda x: x.strength, reverse=True)
        return relationships[:20]
    
    async def _generate_insights(
        self, 
        df: pd.DataFrame, 
        profiles: List[ColumnProfile],
        relationships: List[DataRelationship]
    ) -> List[DataInsight]:
        """Generate AI-powered insights using LLM"""
        insights = []
        
        # 1. Statistical insights (no LLM needed)
        for profile in profiles:
            if profile.detected_type in [ColumnType.NUMERIC, ColumnType.CURRENCY]:
                if profile.std_value and profile.mean_value:
                    cv = profile.std_value / abs(profile.mean_value) if profile.mean_value else 0
                    if cv > 1:
                        insights.append(DataInsight(
                            title=f"High variability in {profile.name}",
                            description=f"{profile.name} has high variance (CV={cv:.2f}). This could indicate outliers or diverse data segments.",
                            importance="medium",
                            category="pattern",
                            data_points={"coefficient_of_variation": cv},
                            visualization_suggestion="box"
                        ))
        
        # 2. Relationship insights
        strong_correlations = [r for r in relationships if r.strength > 0.7]
        for rel in strong_correlations[:3]:
            insights.append(DataInsight(
                title=f"Strong relationship: {rel.column1} ↔ {rel.column2}",
                description=rel.description,
                importance="high",
                category="pattern",
                data_points={"strength": rel.strength, "type": rel.relationship_type},
                visualization_suggestion="scatter"
            ))
        
        # 3. Use LLM for deeper insights
        try:
            # Build context for LLM
            context = self._build_llm_context(df, profiles, relationships)
            
            prompt = f"""Analyze this data and provide 3-5 actionable business insights.

DATA CONTEXT:
{context}

Respond in this exact JSON format:
[
    {{
        "title": "Short insight title",
        "description": "Detailed explanation of the insight",
        "importance": "high/medium/low",
        "category": "trend/anomaly/pattern/recommendation",
        "action": "Suggested action to take"
    }}
]

Focus on:
1. Trends and patterns
2. Anomalies or unusual findings
3. Actionable recommendations
4. Potential risks or opportunities"""

            response = await self._call_llm(prompt)
            
            if response:
                try:
                    # Extract JSON from response
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start >= 0 and json_end > json_start:
                        llm_insights = json.loads(response[json_start:json_end])
                        for item in llm_insights:
                            insights.append(DataInsight(
                                title=item.get("title", "Insight"),
                                description=item.get("description", ""),
                                importance=item.get("importance", "medium"),
                                category=item.get("category", "pattern"),
                                data_points={"action": item.get("action", "")}
                            ))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM insights")
        except Exception as e:
            logger.warning(f"LLM insight generation failed: {e}")
        
        return insights[:10]
    
    def _build_llm_context(
        self, 
        df: pd.DataFrame, 
        profiles: List[ColumnProfile],
        relationships: List[DataRelationship]
    ) -> str:
        """Build context string for LLM"""
        lines = []
        
        # Data overview
        lines.append(f"Dataset: {len(df)} rows x {len(df.columns)} columns")
        
        # Column summary
        lines.append("\nColumns:")
        for p in profiles[:15]:
            type_str = p.detected_type.value
            stats = ""
            if p.detected_type in [ColumnType.NUMERIC, ColumnType.CURRENCY]:
                if p.mean_value is not None:
                    stats = f" | mean={p.mean_value:.2f}, min={p.min_value:.2f}, max={p.max_value:.2f}"
            elif p.detected_type == ColumnType.CATEGORICAL:
                if p.top_values:
                    top = list(p.top_values.keys())[:3]
                    stats = f" | top values: {', '.join(top)}"
            lines.append(f"  - {p.name} ({type_str}){stats}")
        
        # Key relationships
        if relationships:
            lines.append("\nKey Relationships:")
            for r in relationships[:5]:
                lines.append(f"  - {r.description}")
        
        # Sample data
        lines.append("\nSample Data (first 5 rows):")
        lines.append(df.head(5).to_string())
        
        return "\n".join(lines)
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the LLM (uses existing chat function)"""
        try:
            response = chat(
                messages=prompt,
                system="You are a data analysis expert. Provide insights in valid JSON format.",
                temperature=0.3,
                max_tokens=1500
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None
    
    def _suggest_visualizations(
        self, 
        df: pd.DataFrame, 
        profiles: List[ColumnProfile],
        relationships: List[DataRelationship]
    ) -> List[Dict[str, Any]]:
        """Suggest the best visualizations based on data"""
        suggestions = []
        
        numeric_cols = [p.name for p in profiles 
                       if p.detected_type in [ColumnType.NUMERIC, ColumnType.CURRENCY, ColumnType.PERCENTAGE]]
        categorical_cols = [p.name for p in profiles 
                          if p.detected_type == ColumnType.CATEGORICAL]
        datetime_cols = [p.name for p in profiles 
                        if p.detected_type == ColumnType.DATETIME]
        
        # 1. Distribution charts for numeric columns
        for col in numeric_cols[:3]:
            suggestions.append({
                "type": "histogram",
                "title": f"Distribution of {col}",
                "columns": [col],
                "priority": "high"
            })
        
        # 2. Time series if datetime exists
        if datetime_cols and numeric_cols:
            for num_col in numeric_cols[:2]:
                suggestions.append({
                    "type": "line",
                    "title": f"{num_col} Over Time",
                    "columns": [datetime_cols[0], num_col],
                    "priority": "high"
                })
        
        # 3. Categorical breakdowns
        if categorical_cols and numeric_cols:
            for cat_col in categorical_cols[:2]:
                for num_col in numeric_cols[:2]:
                    suggestions.append({
                        "type": "bar",
                        "title": f"{num_col} by {cat_col}",
                        "columns": [cat_col, num_col],
                        "priority": "medium"
                    })
        
        # 4. Correlation scatter plots
        for rel in relationships:
            if rel.relationship_type in ["positive_correlation", "negative_correlation"]:
                suggestions.append({
                    "type": "scatter",
                    "title": f"{rel.column1} vs {rel.column2}",
                    "columns": [rel.column1, rel.column2],
                    "priority": "high"
                })
        
        # 5. Pie/donut for categorical with few values
        for profile in profiles:
            if profile.detected_type == ColumnType.CATEGORICAL:
                if profile.unique_count <= 10 and profile.unique_count > 1:
                    suggestions.append({
                        "type": "pie",
                        "title": f"{profile.name} Distribution",
                        "columns": [profile.name],
                        "priority": "medium"
                    })
        
        # 6. Heatmap for multiple numeric columns
        if len(numeric_cols) >= 3:
            suggestions.append({
                "type": "heatmap",
                "title": "Correlation Heatmap",
                "columns": numeric_cols[:8],
                "priority": "high"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        return suggestions[:10]
    
    def _create_summary(
        self, 
        df: pd.DataFrame, 
        profiles: List[ColumnProfile],
        quality_score: float,
        insights: List[DataInsight]
    ) -> str:
        """Create a human-readable summary"""
        lines = []
        
        # Overview
        lines.append(f"📊 Dataset Overview: {len(df):,} rows × {len(df.columns)} columns")
        lines.append(f"✨ Quality Score: {quality_score:.1f}%")
        
        # Column types breakdown
        type_counts = {}
        for p in profiles:
            t = p.detected_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        type_str = ", ".join(f"{v} {k}" for k, v in type_counts.items())
        lines.append(f"📋 Columns: {type_str}")
        
        # Top insights
        if insights:
            lines.append(f"\n🔍 Key Insights ({len(insights)} found):")
            for insight in insights[:3]:
                lines.append(f"  • {insight.title}")
        
        return "\n".join(lines)
    
    def to_dict(self, analysis: BrainAnalysis) -> Dict[str, Any]:
        """Convert analysis to JSON-serializable dict"""
        result = {
            "file_name": analysis.file_name,
            "analysis_timestamp": analysis.analysis_timestamp,
            "analysis_duration_ms": analysis.analysis_duration_ms,
            "total_rows": analysis.total_rows,
            "total_columns": analysis.total_columns,
            "memory_usage_mb": round(analysis.memory_usage_mb, 2),
            "quality_score": analysis.quality_score,
            "quality_level": analysis.quality_level.value,
            "quality_issues": analysis.quality_issues,
            "summary": analysis.summary,
            "columns": [
                {
                    "name": c.name,
                    "type": c.detected_type.value,
                    "null_percentage": c.null_percentage,
                    "unique_count": c.unique_count,
                    "issues": c.issues,
                    "fix_suggestions": c.fix_suggestions,
                    "stats": {
                        "min": c.min_value,
                        "max": c.max_value,
                        "mean": c.mean_value,
                        "median": c.median_value,
                    } if c.min_value is not None else None,
                    "top_values": c.top_values
                }
                for c in analysis.columns
            ],
            "relationships": [
                {
                    "column1": r.column1,
                    "column2": r.column2,
                    "type": r.relationship_type,
                    "strength": r.strength,
                    "description": r.description
                }
                for r in analysis.relationships
            ],
            "insights": [
                {
                    "title": i.title,
                    "description": i.description,
                    "importance": i.importance,
                    "category": i.category,
                    "visualization": i.visualization_suggestion
                }
                for i in analysis.insights
            ],
            "suggested_charts": analysis.suggested_charts
        }
        return result


# Global brain instance
_brain_instance: Optional[AutonomousBrain] = None


def get_brain() -> AutonomousBrain:
    """Get or create the global brain instance"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousBrain()
    return _brain_instance


async def analyze_data(
    df: pd.DataFrame, 
    file_name: str = "data",
    generate_insights: bool = True
) -> Dict[str, Any]:
    """
    Quick function to analyze data and get JSON result
    
    Usage:
        result = await analyze_data(df, "sales.csv")
    """
    brain = get_brain()
    analysis = await brain.analyze(df, file_name, generate_insights)
    return brain.to_dict(analysis)
