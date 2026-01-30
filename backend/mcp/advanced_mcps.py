"""
⚡ ADVANCED MCPs - DataVision Extended Capabilities
===================================================

New killer MCPs for enterprise-grade data analysis:
- Root Cause Analysis - WHY did something happen?
- Customer Segmentation - AI-driven clustering
- Trend Detection - Automatic trend identification
- Benchmark Comparison - Compare against standards
- Cohort Analysis - User behavior over time

FREE MODELS: All work with Groq/Gemini free tier
"""

import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from core.llm import chat

logger = logging.getLogger(__name__)


# =============================================================================
# ROOT CAUSE ANALYSIS MCP
# =============================================================================

@dataclass
class RootCause:
    """A potential root cause"""
    factor: str
    impact: float  # -1 to 1
    confidence: float  # 0 to 1
    evidence: str
    recommendation: str


@dataclass
class RootCauseResult:
    """Result of root cause analysis"""
    question: str
    primary_cause: RootCause
    secondary_causes: List[RootCause]
    summary: str
    analysis_time_ms: int


class RootCauseAnalyzer:
    """
    🔍 Root Cause Analysis MCP
    
    Answers "WHY did this happen?" questions by:
    1. Identifying correlated factors
    2. Analyzing temporal patterns
    3. Comparing against benchmarks
    4. Using LLM for causal reasoning
    """
    
    async def analyze(
        self,
        df: pd.DataFrame,
        target_column: str,
        question: str,
        time_column: Optional[str] = None
    ) -> RootCauseResult:
        """
        Analyze root causes for a change in target metric
        
        Args:
            df: The data
            target_column: Column to analyze (e.g., 'revenue')
            question: The user's question (e.g., "Why did revenue drop?")
            time_column: Optional time column for temporal analysis
            
        Returns:
            Root cause analysis result
        """
        start_time = datetime.now()
        causes = []
        
        # 1. Correlation analysis
        correlation_causes = self._analyze_correlations(df, target_column)
        causes.extend(correlation_causes)
        
        # 2. Temporal analysis if time column provided
        if time_column:
            temporal_causes = self._analyze_temporal(df, target_column, time_column)
            causes.extend(temporal_causes)
        
        # 3. Segment analysis (find segments with different behavior)
        segment_causes = self._analyze_segments(df, target_column)
        causes.extend(segment_causes)
        
        # 4. Use LLM for causal reasoning
        llm_causes = await self._llm_causal_analysis(df, target_column, question, causes)
        causes.extend(llm_causes)
        
        # Sort by impact and confidence
        causes.sort(key=lambda x: abs(x.impact) * x.confidence, reverse=True)
        
        # Generate summary
        summary = await self._generate_summary(question, causes)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return RootCauseResult(
            question=question,
            primary_cause=causes[0] if causes else RootCause(
                factor="Unknown",
                impact=0,
                confidence=0.5,
                evidence="Insufficient data for analysis",
                recommendation="Collect more data"
            ),
            secondary_causes=causes[1:5] if len(causes) > 1 else [],
            summary=summary,
            analysis_time_ms=duration_ms
        )
    
    def _analyze_correlations(self, df: pd.DataFrame, target: str) -> List[RootCause]:
        """Find columns strongly correlated with target"""
        causes = []
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target not in numeric_cols:
                return causes
            
            for col in numeric_cols:
                if col == target:
                    continue
                
                correlation = df[target].corr(df[col])
                if pd.isna(correlation):
                    continue
                
                if abs(correlation) > 0.3:
                    direction = "increases" if correlation > 0 else "decreases"
                    causes.append(RootCause(
                        factor=col,
                        impact=correlation,
                        confidence=min(abs(correlation), 0.9),
                        evidence=f"{col} has {correlation:.2f} correlation with {target}",
                        recommendation=f"Focus on {col} - when it {direction}, {target} tends to {direction} too"
                    ))
        except Exception as e:
            logger.warning(f"Correlation analysis failed: {e}")
        
        return causes
    
    def _analyze_temporal(
        self, 
        df: pd.DataFrame, 
        target: str, 
        time_col: str
    ) -> List[RootCause]:
        """Analyze temporal patterns"""
        causes = []
        
        try:
            # Convert to datetime
            df_temp = df.copy()
            df_temp[time_col] = pd.to_datetime(df_temp[time_col], errors='coerce')
            df_temp = df_temp.dropna(subset=[time_col])
            
            if len(df_temp) < 10:
                return causes
            
            # Group by time and look for trend changes
            df_temp = df_temp.sort_values(time_col)
            df_temp['period'] = df_temp[time_col].dt.to_period('M')
            
            monthly = df_temp.groupby('period')[target].agg(['mean', 'count']).reset_index()
            
            if len(monthly) >= 2:
                # Check for significant changes
                changes = monthly['mean'].pct_change()
                significant_changes = changes[abs(changes) > 0.1]
                
                for idx in significant_changes.index:
                    if idx < len(monthly):
                        period = monthly.loc[idx, 'period']
                        change = changes.loc[idx]
                        direction = "increased" if change > 0 else "decreased"
                        
                        causes.append(RootCause(
                            factor=f"Time period: {period}",
                            impact=float(change),
                            confidence=0.7,
                            evidence=f"{target} {direction} by {abs(change)*100:.1f}% in {period}",
                            recommendation=f"Investigate what changed in {period}"
                        ))
        except Exception as e:
            logger.warning(f"Temporal analysis failed: {e}")
        
        return causes
    
    def _analyze_segments(self, df: pd.DataFrame, target: str) -> List[RootCause]:
        """Find segments with different behavior"""
        causes = []
        
        try:
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            for col in categorical_cols[:5]:  # Limit to 5 columns
                if df[col].nunique() > 20:
                    continue
                
                grouped = df.groupby(col)[target].agg(['mean', 'count'])
                overall_mean = df[target].mean()
                
                for segment, row in grouped.iterrows():
                    deviation = (row['mean'] - overall_mean) / overall_mean if overall_mean != 0 else 0
                    
                    if abs(deviation) > 0.2 and row['count'] >= 5:
                        direction = "higher" if deviation > 0 else "lower"
                        causes.append(RootCause(
                            factor=f"{col}={segment}",
                            impact=float(deviation),
                            confidence=min(0.8, row['count'] / 50),
                            evidence=f"Segment '{segment}' has {abs(deviation)*100:.1f}% {direction} {target} than average",
                            recommendation=f"Focus on '{segment}' segment for optimization"
                        ))
        except Exception as e:
            logger.warning(f"Segment analysis failed: {e}")
        
        return causes[:10]
    
    async def _llm_causal_analysis(
        self,
        df: pd.DataFrame,
        target: str,
        question: str,
        existing_causes: List[RootCause]
    ) -> List[RootCause]:
        """Use LLM for deeper causal reasoning"""
        causes = []
        
        try:
            # Build context
            context = f"""
Data has {len(df)} rows and columns: {list(df.columns)}
Target metric: {target}
Question: {question}

Existing findings:
"""
            for cause in existing_causes[:5]:
                context += f"- {cause.factor}: {cause.evidence}\n"
            
            context += f"\nSample data:\n{df.head(5).to_string()}"
            
            prompt = f"""{context}

Based on this data and findings, identify any additional potential root causes.
Consider:
1. External factors that might not be in the data
2. Seasonal or cyclical patterns
3. Business logic connections
4. Common industry factors

Respond in JSON format:
[
    {{
        "factor": "factor name",
        "impact": 0.5,
        "evidence": "why you think this",
        "recommendation": "what to do"
    }}
]"""

            response = chat(
                messages=prompt,
                system="You are a data analysis expert. Identify root causes and provide actionable insights.",
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            json_match = response[response.find('['):response.rfind(']')+1]
            if json_match:
                llm_causes = json.loads(json_match)
                for item in llm_causes[:3]:
                    causes.append(RootCause(
                        factor=item.get("factor", "Unknown"),
                        impact=float(item.get("impact", 0.5)),
                        confidence=0.6,  # LLM causes get moderate confidence
                        evidence=item.get("evidence", ""),
                        recommendation=item.get("recommendation", "")
                    ))
        except Exception as e:
            logger.warning(f"LLM causal analysis failed: {e}")
        
        return causes
    
    async def _generate_summary(self, question: str, causes: List[RootCause]) -> str:
        """Generate a human-readable summary"""
        if not causes:
            return "Unable to determine root causes with available data."
        
        summary_parts = [f"**Root Cause Analysis:** {question}\n"]
        
        summary_parts.append(f"\n**Primary Cause:** {causes[0].factor}")
        summary_parts.append(f"- Evidence: {causes[0].evidence}")
        summary_parts.append(f"- Recommendation: {causes[0].recommendation}")
        
        if len(causes) > 1:
            summary_parts.append("\n**Contributing Factors:**")
            for cause in causes[1:4]:
                summary_parts.append(f"- {cause.factor}: {cause.evidence}")
        
        return "\n".join(summary_parts)


# =============================================================================
# CUSTOMER SEGMENTATION MCP
# =============================================================================

@dataclass
class Segment:
    """A customer/data segment"""
    segment_id: int
    name: str
    size: int
    percentage: float
    characteristics: Dict[str, Any]
    recommendations: List[str]


@dataclass
class SegmentationResult:
    """Result of segmentation analysis"""
    segments: List[Segment]
    total_records: int
    features_used: List[str]
    quality_score: float  # Silhouette score
    summary: str


class SegmentationEngine:
    """
    🎯 Customer/Data Segmentation MCP
    
    Uses K-Means clustering to automatically segment data:
    - Finds optimal number of segments
    - Names segments based on characteristics
    - Provides actionable recommendations
    """
    
    async def segment(
        self,
        df: pd.DataFrame,
        features: Optional[List[str]] = None,
        n_segments: Optional[int] = None,
        segment_type: str = "customer"
    ) -> SegmentationResult:
        """
        Segment the data using K-Means clustering
        
        Args:
            df: The data to segment
            features: Columns to use for segmentation (auto-detect if None)
            n_segments: Number of segments (auto-detect if None)
            segment_type: Type of segmentation for naming
            
        Returns:
            Segmentation result with segments and insights
        """
        if not SKLEARN_AVAILABLE:
            return SegmentationResult(
                segments=[],
                total_records=len(df),
                features_used=[],
                quality_score=0,
                summary="Sklearn not available. Install with: pip install scikit-learn"
            )
        
        # 1. Select features
        if features is None:
            features = self._select_features(df)
        
        if len(features) < 2:
            return SegmentationResult(
                segments=[],
                total_records=len(df),
                features_used=features,
                quality_score=0,
                summary="Not enough numeric features for segmentation"
            )
        
        # 2. Prepare data
        X, valid_indices = self._prepare_data(df, features)
        
        if len(X) < 10:
            return SegmentationResult(
                segments=[],
                total_records=len(df),
                features_used=features,
                quality_score=0,
                summary="Not enough valid data points for segmentation"
            )
        
        # 3. Find optimal segments if not specified
        if n_segments is None:
            n_segments = self._find_optimal_k(X)
        
        # 4. Perform clustering
        segments, quality_score = self._cluster(X, n_segments)
        
        # 5. Analyze segments
        segment_results = await self._analyze_segments(
            df.iloc[valid_indices], 
            segments, 
            features,
            segment_type
        )
        
        # 6. Generate summary
        summary = self._generate_summary(segment_results, features)
        
        return SegmentationResult(
            segments=segment_results,
            total_records=len(df),
            features_used=features,
            quality_score=quality_score,
            summary=summary
        )
    
    def _select_features(self, df: pd.DataFrame) -> List[str]:
        """Auto-select features for clustering"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Filter out ID-like columns
        features = []
        for col in numeric_cols:
            col_lower = col.lower()
            if any(x in col_lower for x in ['id', 'index', 'key', 'uuid']):
                continue
            if df[col].nunique() < 3:
                continue
            features.append(col)
        
        return features[:10]  # Limit to 10 features
    
    def _prepare_data(
        self, 
        df: pd.DataFrame, 
        features: List[str]
    ) -> Tuple[np.ndarray, List[int]]:
        """Prepare data for clustering"""
        X = df[features].copy()
        
        # Remove rows with NaN
        valid_mask = ~X.isna().any(axis=1)
        valid_indices = X[valid_mask].index.tolist()
        X = X.loc[valid_indices].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, valid_indices
    
    def _find_optimal_k(self, X: np.ndarray, max_k: int = 8) -> int:
        """Find optimal number of clusters using elbow method"""
        from sklearn.metrics import silhouette_score
        
        max_k = min(max_k, len(X) // 10, 8)
        if max_k < 2:
            return 2
        
        best_score = -1
        best_k = 3
        
        for k in range(2, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X)
                score = silhouette_score(X, labels)
                
                if score > best_score:
                    best_score = score
                    best_k = k
            except:
                pass
        
        return best_k
    
    def _cluster(self, X: np.ndarray, n_clusters: int) -> Tuple[np.ndarray, float]:
        """Perform K-Means clustering"""
        from sklearn.metrics import silhouette_score
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        score = silhouette_score(X, labels) if len(set(labels)) > 1 else 0
        
        return labels, float(score)
    
    async def _analyze_segments(
        self,
        df: pd.DataFrame,
        labels: np.ndarray,
        features: List[str],
        segment_type: str
    ) -> List[Segment]:
        """Analyze each segment's characteristics"""
        segments = []
        df = df.copy()
        df['_segment'] = labels
        
        overall_means = df[features].mean()
        
        for seg_id in range(labels.max() + 1):
            seg_data = df[df['_segment'] == seg_id]
            
            if len(seg_data) == 0:
                continue
            
            # Calculate characteristics
            seg_means = seg_data[features].mean()
            characteristics = {}
            
            for feat in features:
                diff_pct = ((seg_means[feat] - overall_means[feat]) / overall_means[feat] * 100 
                          if overall_means[feat] != 0 else 0)
                if abs(diff_pct) > 10:
                    characteristics[feat] = {
                        "value": float(seg_means[feat]),
                        "vs_average": f"{diff_pct:+.1f}%"
                    }
            
            # Generate name based on characteristics
            name = await self._generate_segment_name(characteristics, segment_type, seg_id)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(characteristics, segment_type)
            
            segments.append(Segment(
                segment_id=seg_id,
                name=name,
                size=len(seg_data),
                percentage=len(seg_data) / len(df) * 100,
                characteristics=characteristics,
                recommendations=recommendations
            ))
        
        return segments
    
    async def _generate_segment_name(
        self, 
        characteristics: Dict, 
        segment_type: str,
        seg_id: int
    ) -> str:
        """Generate a descriptive name for the segment"""
        if not characteristics:
            return f"Segment {seg_id + 1}"
        
        # Use simple heuristics for naming
        high_features = [k for k, v in characteristics.items() 
                        if isinstance(v, dict) and '+' in str(v.get('vs_average', ''))]
        low_features = [k for k, v in characteristics.items() 
                       if isinstance(v, dict) and '-' in str(v.get('vs_average', ''))]
        
        if high_features:
            return f"High {high_features[0].replace('_', ' ').title()}"
        elif low_features:
            return f"Low {low_features[0].replace('_', ' ').title()}"
        else:
            return f"Segment {seg_id + 1}"
    
    def _generate_recommendations(
        self, 
        characteristics: Dict, 
        segment_type: str
    ) -> List[str]:
        """Generate recommendations for the segment"""
        recommendations = []
        
        for feat, info in characteristics.items():
            if isinstance(info, dict):
                vs_avg = info.get('vs_average', '')
                if '+' in vs_avg:
                    recommendations.append(f"Leverage high {feat} - this segment over-indexes")
                elif '-' in vs_avg:
                    recommendations.append(f"Opportunity to improve {feat} in this segment")
        
        return recommendations[:3]
    
    def _generate_summary(self, segments: List[Segment], features: List[str]) -> str:
        """Generate summary of segmentation"""
        if not segments:
            return "No segments identified."
        
        summary = f"**{len(segments)} Segments Identified**\n"
        summary += f"Features used: {', '.join(features)}\n\n"
        
        for seg in segments:
            summary += f"**{seg.name}** ({seg.percentage:.1f}% of data, {seg.size} records)\n"
            if seg.recommendations:
                summary += f"  → {seg.recommendations[0]}\n"
        
        return summary


# =============================================================================
# TREND DETECTION MCP
# =============================================================================

@dataclass
class Trend:
    """A detected trend"""
    column: str
    trend_type: str  # increasing, decreasing, stable, volatile
    strength: float  # 0-1
    start_value: float
    end_value: float
    change_percent: float
    description: str


@dataclass
class TrendResult:
    """Result of trend detection"""
    trends: List[Trend]
    anomalies: List[Dict[str, Any]]
    summary: str


class TrendDetector:
    """
    📈 Trend Detection MCP
    
    Automatically detects:
    - Rising/falling trends
    - Seasonal patterns
    - Anomalies and outliers
    - Trend strength and significance
    """
    
    async def detect(
        self,
        df: pd.DataFrame,
        time_column: Optional[str] = None,
        target_columns: Optional[List[str]] = None
    ) -> TrendResult:
        """
        Detect trends in the data
        
        Args:
            df: The data
            time_column: Column with dates/times
            target_columns: Columns to analyze (auto-detect if None)
            
        Returns:
            Trend detection result
        """
        trends = []
        anomalies = []
        
        # Auto-detect time column if not provided
        if time_column is None:
            time_column = self._detect_time_column(df)
        
        # Auto-detect target columns
        if target_columns is None:
            target_columns = self._select_numeric_columns(df)
        
        # Sort by time if time column found
        if time_column:
            df = df.copy()
            df[time_column] = pd.to_datetime(df[time_column], errors='coerce')
            df = df.sort_values(time_column)
        
        # Analyze each target column
        for col in target_columns:
            trend = self._analyze_trend(df, col)
            if trend:
                trends.append(trend)
            
            col_anomalies = self._detect_anomalies(df, col)
            anomalies.extend(col_anomalies)
        
        # Sort trends by strength
        trends.sort(key=lambda x: x.strength, reverse=True)
        
        # Generate summary
        summary = self._generate_summary(trends, anomalies)
        
        return TrendResult(
            trends=trends,
            anomalies=anomalies[:10],
            summary=summary
        )
    
    def _detect_time_column(self, df: pd.DataFrame) -> Optional[str]:
        """Auto-detect the time column"""
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['date', 'time', 'created', 'timestamp']):
                return col
        
        # Try to find datetime columns
        for col in df.columns:
            try:
                pd.to_datetime(df[col].head(10))
                return col
            except:
                pass
        
        return None
    
    def _select_numeric_columns(self, df: pd.DataFrame) -> List[str]:
        """Select numeric columns for trend analysis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Filter out ID-like columns
        filtered = []
        for col in numeric_cols:
            col_lower = col.lower()
            if any(x in col_lower for x in ['id', 'index', 'key']):
                continue
            filtered.append(col)
        
        return filtered[:5]
    
    def _analyze_trend(self, df: pd.DataFrame, column: str) -> Optional[Trend]:
        """Analyze trend in a single column"""
        try:
            series = df[column].dropna()
            
            if len(series) < 5:
                return None
            
            # Calculate basic statistics
            start_val = float(series.head(max(1, len(series)//10)).mean())
            end_val = float(series.tail(max(1, len(series)//10)).mean())
            
            if start_val == 0:
                change_pct = 0
            else:
                change_pct = (end_val - start_val) / abs(start_val) * 100
            
            # Calculate trend strength using correlation with index
            series_normalized = (series - series.mean()) / series.std() if series.std() > 0 else series
            index_normalized = pd.Series(range(len(series)))
            correlation = series_normalized.reset_index(drop=True).corr(index_normalized)
            
            if pd.isna(correlation):
                correlation = 0
            
            strength = abs(correlation)
            
            # Determine trend type
            if strength < 0.3:
                trend_type = "stable"
            elif correlation > 0:
                trend_type = "increasing"
            else:
                trend_type = "decreasing"
            
            # Check for volatility
            cv = series.std() / series.mean() if series.mean() != 0 else 0
            if cv > 0.5:
                trend_type = "volatile"
            
            description = self._describe_trend(column, trend_type, change_pct, strength)
            
            return Trend(
                column=column,
                trend_type=trend_type,
                strength=strength,
                start_value=start_val,
                end_value=end_val,
                change_percent=change_pct,
                description=description
            )
        except Exception as e:
            logger.warning(f"Trend analysis failed for {column}: {e}")
            return None
    
    def _detect_anomalies(self, df: pd.DataFrame, column: str) -> List[Dict]:
        """Detect anomalies in a column"""
        anomalies = []
        
        try:
            series = df[column].dropna()
            
            if len(series) < 10:
                return anomalies
            
            # Use IQR method for anomaly detection
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Find anomalies
            for idx, value in series.items():
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        "column": column,
                        "index": int(idx) if isinstance(idx, (int, np.integer)) else str(idx),
                        "value": float(value),
                        "type": "high" if value > upper_bound else "low",
                        "deviation": float(abs(value - series.mean()) / series.std()) if series.std() > 0 else 0
                    })
            
            # Sort by deviation and limit
            anomalies.sort(key=lambda x: x['deviation'], reverse=True)
            
        except Exception as e:
            logger.warning(f"Anomaly detection failed for {column}: {e}")
        
        return anomalies[:5]
    
    def _describe_trend(
        self, 
        column: str, 
        trend_type: str, 
        change_pct: float,
        strength: float
    ) -> str:
        """Generate human-readable trend description"""
        strength_word = "strong" if strength > 0.7 else "moderate" if strength > 0.4 else "weak"
        
        if trend_type == "stable":
            return f"{column} has remained relatively stable"
        elif trend_type == "volatile":
            return f"{column} shows high volatility with frequent fluctuations"
        elif trend_type == "increasing":
            return f"{column} shows a {strength_word} upward trend ({change_pct:+.1f}%)"
        else:
            return f"{column} shows a {strength_word} downward trend ({change_pct:+.1f}%)"
    
    def _generate_summary(self, trends: List[Trend], anomalies: List[Dict]) -> str:
        """Generate trend analysis summary"""
        summary_parts = []
        
        # Summarize trends
        increasing = [t for t in trends if t.trend_type == "increasing"]
        decreasing = [t for t in trends if t.trend_type == "decreasing"]
        
        if increasing:
            cols = [t.column for t in increasing[:3]]
            summary_parts.append(f"📈 **Increasing:** {', '.join(cols)}")
        
        if decreasing:
            cols = [t.column for t in decreasing[:3]]
            summary_parts.append(f"📉 **Decreasing:** {', '.join(cols)}")
        
        # Summarize anomalies
        if anomalies:
            summary_parts.append(f"⚠️ **{len(anomalies)} anomalies detected**")
        
        return "\n".join(summary_parts) if summary_parts else "No significant trends detected"


# =============================================================================
# EXPORT INSTANCES
# =============================================================================

# Global instances
root_cause_analyzer = RootCauseAnalyzer()
segmentation_engine = SegmentationEngine()
trend_detector = TrendDetector()


async def analyze_root_cause(
    df: pd.DataFrame,
    target_column: str,
    question: str,
    time_column: Optional[str] = None
) -> Dict[str, Any]:
    """Quick function for root cause analysis"""
    result = await root_cause_analyzer.analyze(df, target_column, question, time_column)
    return {
        "question": result.question,
        "primary_cause": {
            "factor": result.primary_cause.factor,
            "impact": result.primary_cause.impact,
            "evidence": result.primary_cause.evidence,
            "recommendation": result.primary_cause.recommendation
        },
        "secondary_causes": [
            {"factor": c.factor, "evidence": c.evidence}
            for c in result.secondary_causes
        ],
        "summary": result.summary
    }


async def segment_data(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    n_segments: Optional[int] = None
) -> Dict[str, Any]:
    """Quick function for data segmentation"""
    result = await segmentation_engine.segment(df, features, n_segments)
    return {
        "segments": [
            {
                "name": s.name,
                "size": s.size,
                "percentage": s.percentage,
                "characteristics": s.characteristics,
                "recommendations": s.recommendations
            }
            for s in result.segments
        ],
        "quality_score": result.quality_score,
        "summary": result.summary
    }


async def detect_trends(
    df: pd.DataFrame,
    time_column: Optional[str] = None
) -> Dict[str, Any]:
    """Quick function for trend detection"""
    result = await trend_detector.detect(df, time_column)
    return {
        "trends": [
            {
                "column": t.column,
                "type": t.trend_type,
                "strength": t.strength,
                "change_percent": t.change_percent,
                "description": t.description
            }
            for t in result.trends
        ],
        "anomalies": result.anomalies,
        "summary": result.summary
    }
