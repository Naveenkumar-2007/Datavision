"""
📊 DATA QUALITY ANALYZER v1.0
==============================

Comprehensive data quality analysis and scoring:
- Missing value analysis
- Duplicate detection
- Outlier identification
- Class imbalance detection
- Data type validation
- Cardinality checks
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """Represents a single data quality issue"""
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'missing', 'duplicate', 'outlier', 'imbalance', 'type'
    column: Optional[str]
    description: str
    recommendation: str
    impact_score: float  # 0-100


@dataclass
class QualityReport:
    """Complete data quality report"""
    overall_score: float = 0.0
    grade: str = 'F'
    issues: List[QualityIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    column_scores: Dict[str, float] = field(default_factory=dict)


class DataQualityAnalyzer:
    """
    Production-grade data quality analysis.
    
    Provides:
    - Comprehensive quality scoring (0-100)
    - Issue detection and categorization
    - Actionable recommendations
    - Column-level quality metrics
    """
    
    def __init__(self):
        self.report: Optional[QualityReport] = None
    
    def analyze(self, df: pd.DataFrame, target_col: Optional[str] = None) -> QualityReport:
        """
        Run complete data quality analysis.
        
        Args:
            df: DataFrame to analyze
            target_col: Optional target column name for imbalance checks
        
        Returns:
            QualityReport with scores and recommendations
        """
        logger.info(f"📊 Starting data quality analysis ({len(df)} rows, {len(df.columns)} cols)...")
        
        self.report = QualityReport()
        self.report.metrics['n_rows'] = len(df)
        self.report.metrics['n_cols'] = len(df.columns)
        
        # Run all checks
        self._check_missing_values(df)
        self._check_duplicates(df)
        self._check_outliers(df)
        self._check_cardinality(df)
        self._check_data_types(df)
        
        if target_col and target_col in df.columns:
            self._check_class_imbalance(df, target_col)
        
        # Calculate overall score
        self._calculate_overall_score()
        
        # Generate summary recommendations
        self._generate_recommendations()
        
        logger.info(f"   ✅ Quality Score: {self.report.overall_score:.1f}/100 (Grade: {self.report.grade})")
        
        return self.report
    
    def _check_missing_values(self, df: pd.DataFrame):
        """Analyze missing values in each column"""
        logger.info("   🔍 Checking missing values...")
        
        missing_pct = df.isnull().sum() / len(df) * 100
        self.report.metrics['missing_summary'] = missing_pct.to_dict()
        
        for col, pct in missing_pct.items():
            self.report.column_scores[col] = self.report.column_scores.get(col, 100)
            
            if pct > 50:
                self.report.issues.append(QualityIssue(
                    severity='critical',
                    category='missing',
                    column=col,
                    description=f"Column '{col}' has {pct:.1f}% missing values",
                    recommendation=f"Consider dropping '{col}' or using advanced imputation",
                    impact_score=30
                ))
                self.report.column_scores[col] -= 50
            elif pct > 30:
                self.report.issues.append(QualityIssue(
                    severity='high',
                    category='missing',
                    column=col,
                    description=f"Column '{col}' has {pct:.1f}% missing values",
                    recommendation=f"Apply imputation strategy for '{col}'",
                    impact_score=20
                ))
                self.report.column_scores[col] -= 30
            elif pct > 10:
                self.report.issues.append(QualityIssue(
                    severity='medium',
                    category='missing',
                    column=col,
                    description=f"Column '{col}' has {pct:.1f}% missing values",
                    recommendation=f"Review missing pattern in '{col}'",
                    impact_score=10
                ))
                self.report.column_scores[col] -= 15
    
    def _check_duplicates(self, df: pd.DataFrame):
        """Check for duplicate rows"""
        logger.info("   🔍 Checking duplicates...")
        
        dup_count = df.duplicated().sum()
        dup_pct = dup_count / len(df) * 100
        
        self.report.metrics['duplicate_count'] = int(dup_count)
        self.report.metrics['duplicate_pct'] = round(dup_pct, 2)
        
        if dup_pct > 20:
            self.report.issues.append(QualityIssue(
                severity='high',
                category='duplicate',
                column=None,
                description=f"Dataset has {dup_pct:.1f}% duplicate rows ({dup_count} rows)",
                recommendation="Review and remove duplicate rows to avoid data leakage",
                impact_score=20
            ))
        elif dup_pct > 5:
            self.report.issues.append(QualityIssue(
                severity='medium',
                category='duplicate',
                column=None,
                description=f"Dataset has {dup_pct:.1f}% duplicate rows",
                recommendation="Consider deduplication before training",
                impact_score=10
            ))
    
    def _check_outliers(self, df: pd.DataFrame):
        """Detect outliers in numeric columns using IQR method"""
        logger.info("   🔍 Checking outliers...")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_summary = {}
        
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 10:
                continue
            
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            
            if iqr == 0:
                continue
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = ((series < lower_bound) | (series > upper_bound)).sum()
            outlier_pct = outliers / len(series) * 100
            
            outlier_summary[col] = {
                'count': int(outliers),
                'pct': round(outlier_pct, 2),
                'lower_bound': round(lower_bound, 2),
                'upper_bound': round(upper_bound, 2)
            }
            
            self.report.column_scores[col] = self.report.column_scores.get(col, 100)
            
            if outlier_pct > 10:
                self.report.issues.append(QualityIssue(
                    severity='medium',
                    category='outlier',
                    column=col,
                    description=f"Column '{col}' has {outlier_pct:.1f}% outliers ({outliers} values)",
                    recommendation=f"Consider outlier treatment for '{col}' (capping, transformation, or removal)",
                    impact_score=10
                ))
                self.report.column_scores[col] -= 10
        
        self.report.metrics['outlier_summary'] = outlier_summary
    
    def _check_cardinality(self, df: pd.DataFrame):
        """Check cardinality of categorical columns"""
        logger.info("   🔍 Checking cardinality...")
        
        cardinality_summary = {}
        
        for col in df.columns:
            n_unique = df[col].nunique()
            unique_ratio = n_unique / len(df)
            
            cardinality_summary[col] = {
                'n_unique': int(n_unique),
                'unique_ratio': round(unique_ratio, 4)
            }
            
            # High cardinality categorical
            if df[col].dtype == 'object' and n_unique > 100:
                self.report.issues.append(QualityIssue(
                    severity='medium',
                    category='cardinality',
                    column=col,
                    description=f"Column '{col}' has high cardinality ({n_unique} unique values)",
                    recommendation=f"Consider target encoding or frequency encoding for '{col}'",
                    impact_score=5
                ))
            
            # Constant column
            if n_unique == 1:
                self.report.issues.append(QualityIssue(
                    severity='high',
                    category='cardinality',
                    column=col,
                    description=f"Column '{col}' is constant (only 1 unique value)",
                    recommendation=f"Drop constant column '{col}' - provides no information",
                    impact_score=15
                ))
            
            # Near-unique column (likely ID)
            if unique_ratio > 0.95 and df[col].dtype in ['int64', 'object']:
                self.report.issues.append(QualityIssue(
                    severity='low',
                    category='cardinality',
                    column=col,
                    description=f"Column '{col}' appears to be an ID column ({unique_ratio:.1%} unique)",
                    recommendation=f"Consider excluding '{col}' from features",
                    impact_score=5
                ))
        
        self.report.metrics['cardinality_summary'] = cardinality_summary
    
    def _check_data_types(self, df: pd.DataFrame):
        """Validate data types and detect mismatches"""
        logger.info("   🔍 Checking data types...")
        
        type_summary = {}
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            type_summary[col] = dtype
            
            # Check for numeric stored as string
            if df[col].dtype == 'object':
                try:
                    numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
                    if numeric_count / len(df) > 0.9:
                        self.report.issues.append(QualityIssue(
                            severity='low',
                            category='type',
                            column=col,
                            description=f"Column '{col}' appears numeric but stored as string",
                            recommendation=f"Convert '{col}' to numeric type for better performance",
                            impact_score=3
                        ))
                except:
                    pass
        
        self.report.metrics['data_types'] = type_summary
    
    def _check_class_imbalance(self, df: pd.DataFrame, target_col: str):
        """Check for class imbalance in target variable"""
        logger.info(f"   🔍 Checking class imbalance in '{target_col}'...")
        
        if df[target_col].dtype in ['float64', 'float32']:
            # Regression target - skip imbalance check
            return
        
        class_counts = df[target_col].value_counts()
        n_classes = len(class_counts)
        
        if n_classes < 2:
            return
        
        imbalance_ratio = class_counts.max() / class_counts.min()
        
        self.report.metrics['class_distribution'] = class_counts.to_dict()
        self.report.metrics['imbalance_ratio'] = round(imbalance_ratio, 2)
        self.report.metrics['n_classes'] = n_classes
        
        if imbalance_ratio > 10:
            self.report.issues.append(QualityIssue(
                severity='critical',
                category='imbalance',
                column=target_col,
                description=f"Severe class imbalance (ratio: {imbalance_ratio:.1f}:1)",
                recommendation="Apply SMOTE, class weighting, or undersampling",
                impact_score=25
            ))
        elif imbalance_ratio > 5:
            self.report.issues.append(QualityIssue(
                severity='high',
                category='imbalance',
                column=target_col,
                description=f"Significant class imbalance (ratio: {imbalance_ratio:.1f}:1)",
                recommendation="Consider class balancing techniques",
                impact_score=15
            ))
        elif imbalance_ratio > 3:
            self.report.issues.append(QualityIssue(
                severity='medium',
                category='imbalance',
                column=target_col,
                description=f"Moderate class imbalance (ratio: {imbalance_ratio:.1f}:1)",
                recommendation="Monitor model performance across classes",
                impact_score=8
            ))
    
    def _calculate_overall_score(self):
        """Calculate overall data quality score"""
        base_score = 100
        
        # Deduct points for each issue based on severity
        severity_weights = {
            'critical': 15,
            'high': 10,
            'medium': 5,
            'low': 2
        }
        
        for issue in self.report.issues:
            base_score -= severity_weights.get(issue.severity, 5)
        
        # Ensure score is between 0-100
        self.report.overall_score = max(0, min(100, base_score))
        
        # Assign grade
        if self.report.overall_score >= 90:
            self.report.grade = 'A'
        elif self.report.overall_score >= 80:
            self.report.grade = 'B'
        elif self.report.overall_score >= 70:
            self.report.grade = 'C'
        elif self.report.overall_score >= 60:
            self.report.grade = 'D'
        else:
            self.report.grade = 'F'
    
    def _generate_recommendations(self):
        """Generate prioritized recommendations"""
        # Group issues by severity
        critical_issues = [i for i in self.report.issues if i.severity == 'critical']
        high_issues = [i for i in self.report.issues if i.severity == 'high']
        
        if critical_issues:
            self.report.recommendations.append(
                f"🚨 CRITICAL: Address {len(critical_issues)} critical issues before training"
            )
        
        if high_issues:
            self.report.recommendations.append(
                f"⚠️ HIGH PRIORITY: Fix {len(high_issues)} high-severity issues for better accuracy"
            )
        
        # Add specific recommendations
        for issue in self.report.issues[:5]:  # Top 5 issues
            self.report.recommendations.append(issue.recommendation)
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get report as dictionary for API response"""
        if not self.report:
            return {}
        
        return {
            'overall_score': self.report.overall_score,
            'grade': self.report.grade,
            'n_issues': len(self.report.issues),
            'issues': [
                {
                    'severity': i.severity,
                    'category': i.category,
                    'column': i.column,
                    'description': i.description,
                    'recommendation': i.recommendation
                }
                for i in self.report.issues
            ],
            'metrics': self.report.metrics,
            'recommendations': self.report.recommendations,
            'column_scores': self.report.column_scores
        }


def analyze_data_quality(df: pd.DataFrame, target_col: str = None) -> Dict[str, Any]:
    """
    Convenience function to run data quality analysis.
    
    Args:
        df: DataFrame to analyze
        target_col: Optional target column
    
    Returns:
        Dictionary with quality report
    """
    analyzer = DataQualityAnalyzer()
    analyzer.analyze(df, target_col)
    return analyzer.get_summary_dict()
