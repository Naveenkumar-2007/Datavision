"""
📊 ENTERPRISE MCPs - DataVision Advanced Analytics
===================================================

Additional killer MCPs:
- Cohort Analysis - User retention and behavior over time
- Benchmark Comparison - Compare against industry standards
- What-If Simulation - Scenario planning
- AutoML - Automatic model selection

FREE: All work with Groq/Gemini free tier + sklearn
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from core.llm import chat

logger = logging.getLogger(__name__)


# =============================================================================
# COHORT ANALYSIS MCP
# =============================================================================

@dataclass
class CohortMetrics:
    """Metrics for a single cohort"""
    cohort_name: str
    cohort_size: int
    retention_rates: Dict[int, float]  # period -> retention %
    avg_value: float
    total_value: float


@dataclass
class CohortResult:
    """Result of cohort analysis"""
    cohorts: List[CohortMetrics]
    retention_matrix: List[List[float]]
    periods: List[str]
    cohort_names: List[str]
    summary: str
    best_cohort: str
    worst_cohort: str


class CohortAnalyzer:
    """
    📈 Cohort Analysis MCP
    
    Analyze user retention and behavior over time:
    - Group users by signup/acquisition date
    - Track behavior across periods
    - Identify best/worst performing cohorts
    """
    
    async def analyze(
        self,
        df: pd.DataFrame,
        date_column: str,
        user_column: str,
        value_column: Optional[str] = None,
        period: str = "M"  # M=month, W=week, Q=quarter
    ) -> CohortResult:
        """
        Perform cohort analysis
        
        Args:
            df: Transaction/activity data
            date_column: Column with activity date
            user_column: Column identifying users
            value_column: Optional column with transaction value
            period: Grouping period (M, W, Q)
            
        Returns:
            Cohort analysis result
        """
        try:
            # Prepare data
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            df = df.dropna(subset=[date_column, user_column])
            
            if len(df) == 0:
                return self._empty_result("No valid data")
            
            # Determine cohort (first activity date for each user)
            user_cohorts = df.groupby(user_column)[date_column].min().reset_index()
            user_cohorts.columns = [user_column, 'cohort_date']
            user_cohorts['cohort'] = user_cohorts['cohort_date'].dt.to_period(period)
            
            # Merge back
            df = df.merge(user_cohorts[[user_column, 'cohort']], on=user_column)
            df['activity_period'] = df[date_column].dt.to_period(period)
            
            # Calculate period number
            df['period_number'] = (df['activity_period'] - df['cohort']).apply(lambda x: x.n if hasattr(x, 'n') else 0)
            
            # Build retention matrix
            cohort_data = df.groupby(['cohort', 'period_number'])[user_column].nunique().unstack(fill_value=0)
            
            # Calculate retention rates
            cohort_sizes = cohort_data[0] if 0 in cohort_data.columns else cohort_data.iloc[:, 0]
            retention_matrix = cohort_data.divide(cohort_sizes, axis=0) * 100
            
            # Build cohort metrics
            cohorts = []
            for cohort_name in retention_matrix.index:
                retention_rates = retention_matrix.loc[cohort_name].to_dict()
                size = int(cohort_sizes.get(cohort_name, 0))
                
                # Calculate value if available
                avg_val = 0
                total_val = 0
                if value_column and value_column in df.columns:
                    cohort_df = df[df['cohort'] == cohort_name]
                    avg_val = float(cohort_df[value_column].mean()) if len(cohort_df) > 0 else 0
                    total_val = float(cohort_df[value_column].sum())
                
                cohorts.append(CohortMetrics(
                    cohort_name=str(cohort_name),
                    cohort_size=size,
                    retention_rates={int(k): round(v, 1) for k, v in retention_rates.items()},
                    avg_value=round(avg_val, 2),
                    total_value=round(total_val, 2)
                ))
            
            # Convert matrix to list
            matrix_list = retention_matrix.values.tolist()
            periods = [str(p) for p in retention_matrix.columns.tolist()]
            cohort_names = [str(c) for c in retention_matrix.index.tolist()]
            
            # Find best/worst cohorts (by period 1 retention if available)
            if len(cohorts) > 0:
                sorted_by_retention = sorted(
                    cohorts, 
                    key=lambda c: c.retention_rates.get(1, 0), 
                    reverse=True
                )
                best_cohort = sorted_by_retention[0].cohort_name
                worst_cohort = sorted_by_retention[-1].cohort_name
            else:
                best_cohort = "N/A"
                worst_cohort = "N/A"
            
            # Generate summary
            summary = self._generate_summary(cohorts, best_cohort, worst_cohort)
            
            return CohortResult(
                cohorts=cohorts,
                retention_matrix=matrix_list,
                periods=periods,
                cohort_names=cohort_names,
                summary=summary,
                best_cohort=best_cohort,
                worst_cohort=worst_cohort
            )
            
        except Exception as e:
            logger.error(f"Cohort analysis error: {e}")
            return self._empty_result(str(e))
    
    def _empty_result(self, error: str) -> CohortResult:
        """Return empty result with error"""
        return CohortResult(
            cohorts=[],
            retention_matrix=[],
            periods=[],
            cohort_names=[],
            summary=f"Could not perform cohort analysis: {error}",
            best_cohort="N/A",
            worst_cohort="N/A"
        )
    
    def _generate_summary(
        self, 
        cohorts: List[CohortMetrics],
        best: str,
        worst: str
    ) -> str:
        """Generate cohort analysis summary"""
        if not cohorts:
            return "No cohorts analyzed."
        
        total_users = sum(c.cohort_size for c in cohorts)
        avg_period1_retention = np.mean([c.retention_rates.get(1, 0) for c in cohorts])
        
        return f"""**Cohort Analysis Summary**

📊 **{len(cohorts)} cohorts** with **{total_users:,} total users**
📈 Average Period 1 Retention: **{avg_period1_retention:.1f}%**
✅ Best Performing: **{best}**
⚠️ Needs Improvement: **{worst}**"""


# =============================================================================
# AUTOML MCP
# =============================================================================

@dataclass
class ModelResult:
    """Result from a trained model"""
    model_name: str
    r2_score: float
    mae: float
    cv_score: float
    feature_importance: Dict[str, float]


@dataclass
class AutoMLResult:
    """Result of AutoML process"""
    best_model: str
    best_score: float
    all_models: List[ModelResult]
    predictions: List[float]
    feature_importance: Dict[str, float]
    summary: str


class AutoMLEngine:
    """
    🤖 AutoML MCP
    
    Automatic machine learning:
    - Try multiple algorithms
    - Cross-validation
    - Feature importance
    - Best model selection
    """
    
    def __init__(self):
        self.models = {}
        if SKLEARN_AVAILABLE:
            self.models = {
                "LinearRegression": LinearRegression(),
                "Ridge": Ridge(alpha=1.0),
                "RandomForest": RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42),
                "GradientBoosting": GradientBoostingRegressor(n_estimators=50, max_depth=5, random_state=42),
            }
    
    async def fit_predict(
        self,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: Optional[List[str]] = None,
        test_size: float = 0.2
    ) -> AutoMLResult:
        """
        Automatically train and select best model
        
        Args:
            df: Training data
            target_column: Column to predict
            feature_columns: Features to use (auto-detect if None)
            test_size: Fraction for testing
            
        Returns:
            AutoML result with best model and predictions
        """
        if not SKLEARN_AVAILABLE:
            return AutoMLResult(
                best_model="N/A",
                best_score=0,
                all_models=[],
                predictions=[],
                feature_importance={},
                summary="sklearn not available. Install with: pip install scikit-learn"
            )
        
        try:
            # Prepare data
            df = df.copy()
            
            # Auto-detect features
            if feature_columns is None:
                feature_columns = self._select_features(df, target_column)
            
            if len(feature_columns) == 0:
                return self._empty_result("No valid features found")
            
            # Prepare X and y
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())
            
            # Remove non-numeric
            X = X.select_dtypes(include=[np.number])
            if len(X.columns) == 0:
                return self._empty_result("No numeric features")
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train and evaluate each model
            results = []
            best_score = -float('inf')
            best_model_name = None
            best_model = None
            
            for name, model in self.models.items():
                try:
                    # Cross-validation
                    cv_scores = cross_val_score(model, X_scaled, y, cv=min(5, len(y)//5), scoring='r2')
                    cv_score = float(np.mean(cv_scores))
                    
                    # Fit model
                    model.fit(X_scaled, y)
                    predictions = model.predict(X_scaled)
                    
                    r2 = float(r2_score(y, predictions))
                    mae = float(mean_absolute_error(y, predictions))
                    
                    # Feature importance
                    importance = {}
                    if hasattr(model, 'feature_importances_'):
                        for i, col in enumerate(X.columns):
                            importance[col] = float(model.feature_importances_[i])
                    elif hasattr(model, 'coef_'):
                        coef = model.coef_ if len(model.coef_.shape) == 1 else model.coef_[0]
                        for i, col in enumerate(X.columns):
                            importance[col] = float(abs(coef[i]))
                    
                    results.append(ModelResult(
                        model_name=name,
                        r2_score=r2,
                        mae=mae,
                        cv_score=cv_score,
                        feature_importance=importance
                    ))
                    
                    if cv_score > best_score:
                        best_score = cv_score
                        best_model_name = name
                        best_model = model
                        
                except Exception as e:
                    logger.warning(f"Model {name} failed: {e}")
            
            if best_model is None:
                return self._empty_result("All models failed")
            
            # Get predictions from best model
            final_predictions = best_model.predict(X_scaled).tolist()
            
            # Get importance from best model
            best_importance = next(
                (r.feature_importance for r in results if r.model_name == best_model_name),
                {}
            )
            
            # Generate summary
            summary = self._generate_summary(results, best_model_name, best_score)
            
            return AutoMLResult(
                best_model=best_model_name,
                best_score=best_score,
                all_models=results,
                predictions=final_predictions[:100],  # Limit output
                feature_importance=best_importance,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"AutoML error: {e}")
            return self._empty_result(str(e))
    
    def _select_features(self, df: pd.DataFrame, target: str) -> List[str]:
        """Auto-select features"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Exclude target and ID-like columns
        features = []
        for col in numeric_cols:
            if col == target:
                continue
            col_lower = col.lower()
            if any(x in col_lower for x in ['id', 'index', 'key', 'uuid']):
                continue
            features.append(col)
        
        return features[:20]  # Limit features
    
    def _empty_result(self, error: str) -> AutoMLResult:
        """Return empty result"""
        return AutoMLResult(
            best_model="N/A",
            best_score=0,
            all_models=[],
            predictions=[],
            feature_importance={},
            summary=f"AutoML failed: {error}"
        )
    
    def _generate_summary(
        self, 
        results: List[ModelResult],
        best_name: str,
        best_score: float
    ) -> str:
        """Generate AutoML summary"""
        summary = f"""**AutoML Results**

🏆 **Best Model:** {best_name} (R² = {best_score:.3f})

**All Models Tested:**
"""
        for r in sorted(results, key=lambda x: x.cv_score, reverse=True):
            summary += f"• {r.model_name}: R²={r.r2_score:.3f}, MAE={r.mae:.2f}\n"
        
        return summary


# =============================================================================
# WHAT-IF SIMULATION MCP
# =============================================================================

@dataclass
class SimulationScenario:
    """A what-if scenario"""
    name: str
    changes: Dict[str, float]  # column -> new value or multiplier
    predicted_outcome: float
    confidence: float
    impact_description: str


@dataclass
class SimulationResult:
    """Result of simulation"""
    baseline: float
    scenarios: List[SimulationScenario]
    best_scenario: str
    worst_scenario: str
    summary: str


class WhatIfSimulator:
    """
    🔮 What-If Simulation MCP
    
    Simulate different scenarios:
    - "What if we increase price by 10%?"
    - "What if marketing spend goes down 20%?"
    """
    
    async def simulate(
        self,
        df: pd.DataFrame,
        target_column: str,
        scenarios: List[Dict[str, Any]],
        model_type: str = "auto"
    ) -> SimulationResult:
        """
        Run what-if simulations
        
        Args:
            df: Historical data
            target_column: Outcome to predict
            scenarios: List of scenarios with changes
            model_type: Model to use (auto, linear, forest)
            
        Returns:
            Simulation results
        """
        try:
            # Calculate baseline
            baseline = float(df[target_column].mean())
            
            # Get correlations for simple simulation
            correlations = df.corr()[target_column].drop(target_column, errors='ignore')
            
            scenario_results = []
            
            for i, scenario in enumerate(scenarios):
                name = scenario.get("name", f"Scenario {i+1}")
                changes = scenario.get("changes", {})
                
                # Estimate impact based on correlations
                total_impact = 0
                impact_parts = []
                
                for col, change in changes.items():
                    if col in correlations:
                        corr = correlations[col]
                        # Estimate impact: correlation * change percentage * column std
                        col_std = df[col].std() if col in df.columns else 1
                        impact = corr * change * col_std
                        total_impact += impact
                        
                        direction = "increase" if (corr * change) > 0 else "decrease"
                        impact_parts.append(f"{col} change {direction}s outcome")
                
                predicted = baseline * (1 + total_impact / baseline) if baseline != 0 else baseline + total_impact
                confidence = min(0.9, 0.5 + abs(total_impact) / (baseline + 1) * 0.3)
                
                scenario_results.append(SimulationScenario(
                    name=name,
                    changes=changes,
                    predicted_outcome=round(predicted, 2),
                    confidence=round(confidence, 2),
                    impact_description="; ".join(impact_parts) if impact_parts else "Minimal impact"
                ))
            
            # Sort scenarios by predicted outcome
            sorted_scenarios = sorted(scenario_results, key=lambda s: s.predicted_outcome, reverse=True)
            best = sorted_scenarios[0].name if sorted_scenarios else "N/A"
            worst = sorted_scenarios[-1].name if sorted_scenarios else "N/A"
            
            summary = self._generate_summary(baseline, scenario_results, best, worst)
            
            return SimulationResult(
                baseline=round(baseline, 2),
                scenarios=scenario_results,
                best_scenario=best,
                worst_scenario=worst,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return SimulationResult(
                baseline=0,
                scenarios=[],
                best_scenario="N/A",
                worst_scenario="N/A",
                summary=f"Simulation failed: {e}"
            )
    
    def _generate_summary(
        self,
        baseline: float,
        scenarios: List[SimulationScenario],
        best: str,
        worst: str
    ) -> str:
        """Generate simulation summary"""
        summary = f"""**What-If Simulation Results**

📊 **Baseline:** {baseline:,.2f}
✅ **Best Scenario:** {best}
⚠️ **Worst Scenario:** {worst}

**Scenario Predictions:**
"""
        for s in scenarios:
            change_pct = ((s.predicted_outcome - baseline) / baseline * 100) if baseline != 0 else 0
            emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            summary += f"{emoji} {s.name}: {s.predicted_outcome:,.2f} ({change_pct:+.1f}%)\n"
        
        return summary


# =============================================================================
# EXPORT INSTANCES
# =============================================================================

cohort_analyzer = CohortAnalyzer()
automl_engine = AutoMLEngine()
whatif_simulator = WhatIfSimulator()


async def analyze_cohorts(
    df: pd.DataFrame,
    date_column: str,
    user_column: str,
    value_column: Optional[str] = None
) -> Dict[str, Any]:
    """Quick function for cohort analysis"""
    result = await cohort_analyzer.analyze(df, date_column, user_column, value_column)
    return {
        "cohorts": [
            {
                "name": c.cohort_name,
                "size": c.cohort_size,
                "retention": c.retention_rates,
                "avg_value": c.avg_value
            }
            for c in result.cohorts
        ],
        "best_cohort": result.best_cohort,
        "worst_cohort": result.worst_cohort,
        "summary": result.summary
    }


async def run_automl(
    df: pd.DataFrame,
    target_column: str,
    feature_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Quick function for AutoML"""
    result = await automl_engine.fit_predict(df, target_column, feature_columns)
    return {
        "best_model": result.best_model,
        "best_score": result.best_score,
        "models": [
            {"name": m.model_name, "r2": m.r2_score, "mae": m.mae}
            for m in result.all_models
        ],
        "feature_importance": result.feature_importance,
        "summary": result.summary
    }


async def simulate_scenarios(
    df: pd.DataFrame,
    target_column: str,
    scenarios: List[Dict]
) -> Dict[str, Any]:
    """Quick function for what-if simulation"""
    result = await whatif_simulator.simulate(df, target_column, scenarios)
    return {
        "baseline": result.baseline,
        "scenarios": [
            {
                "name": s.name,
                "predicted": s.predicted_outcome,
                "confidence": s.confidence
            }
            for s in result.scenarios
        ],
        "best": result.best_scenario,
        "worst": result.worst_scenario,
        "summary": result.summary
    }
