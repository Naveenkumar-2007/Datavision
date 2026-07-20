"""
🧠 AGENTIC AUTOPILOT ENGINE v1.0
=================================

The world's first fully autonomous data science agent.

Given a dataset and a goal (or no goal at all), this engine:
1. Profiles the data autonomously
2. Cleans and prepares it
3. Discovers patterns and insights
4. Trains the best ML model
5. Generates visualizations
6. Produces a complete analysis report
7. Deploys a prediction API

All with ZERO human intervention. The user just uploads data and watches.

Architecture:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PLANNER    │────▶│  EXECUTOR    │────▶│  EVALUATOR   │
│ (Goal → Plan)│     │ (Run Steps)  │     │ (Check/Fix)  │
└──────────────┘     └──────────────┘     └──────────────┘
       ▲                                         │
       └─────────────────────────────────────────┘
                    (Re-plan if needed)
"""

import logging
import json
import time
import traceback
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AutopilotPhase(Enum):
    PLANNING = "planning"
    DATA_PROFILING = "data_profiling"
    DATA_CLEANING = "data_cleaning"
    FEATURE_DISCOVERY = "feature_discovery"
    INSIGHT_EXTRACTION = "insight_extraction"
    VISUALIZATION = "visualization"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    CODE_GENERATION = "code_generation"
    REPORT_GENERATION = "report_generation"
    COMPLETE = "complete"


@dataclass
class AutopilotStep:
    """A single step in the autopilot execution plan."""
    id: str
    phase: AutopilotPhase
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0  # 0-100

    def to_dict(self):
        return {
            "id": self.id,
            "phase": self.phase.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": int((self.completed_at - self.started_at) * 1000) if self.started_at and self.completed_at else None,
            "progress": self.progress
        }


@dataclass
class AutopilotState:
    """Full state of an autopilot run."""
    user_id: str
    session_id: str
    goal: str
    filename: str
    df: Optional[pd.DataFrame] = None
    target_column: Optional[str] = None
    task_type: Optional[str] = None
    steps: List[AutopilotStep] = field(default_factory=list)
    current_step_index: int = 0
    insights: List[str] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    model_result: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    started_at: float = 0.0
    completed_at: Optional[float] = None
    cancelled: bool = False

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "filename": self.filename,
            "target_column": self.target_column,
            "task_type": self.task_type,
            "current_step": self.current_step_index,
            "total_steps": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
            "insights": self.insights,
            "charts": self.charts,
            "elapsed_seconds": round(time.time() - self.started_at, 1) if self.started_at else 0,
        }


class AgenticAutopilot:
    """
    The Agentic Autopilot — an autonomous data science agent.
    
    Usage:
        autopilot = AgenticAutopilot(user_id, df, goal="Predict customer churn")
        async for event in autopilot.run():
            # event is a dict: {"type": "step_start"|"step_complete"|"insight"|"chart"|...}
            yield event
    """

    def __init__(self, user_id: str, df: pd.DataFrame, filename: str = "data.csv",
                 goal: str = "", target_column: str = None, session_id: str = None):
        import uuid
        self.state = AutopilotState(
            user_id=user_id,
            session_id=session_id or str(uuid.uuid4()),
            goal=goal or "Perform comprehensive autonomous data analysis",
            filename=filename,
            df=df,
            target_column=target_column,
            started_at=time.time()
        )
        self._event_callback: Optional[Callable] = None
        self._build_plan()

    def _build_plan(self):
        """Build the execution plan based on the goal and data."""
        steps = [
            AutopilotStep(
                id="plan", phase=AutopilotPhase.PLANNING,
                title="🧠 Analyzing Goal & Planning Strategy",
                description="Understanding your data and formulating an optimal analysis plan"
            ),
            AutopilotStep(
                id="profile", phase=AutopilotPhase.DATA_PROFILING,
                title="🔍 Deep Data Profiling",
                description="Scanning every column — types, distributions, missing values, correlations"
            ),
            AutopilotStep(
                id="clean", phase=AutopilotPhase.DATA_CLEANING,
                title="🧹 Autonomous Data Cleaning",
                description="Fixing missing values, outliers, duplicates, and type errors"
            ),
            AutopilotStep(
                id="features", phase=AutopilotPhase.FEATURE_DISCOVERY,
                title="⚡ Intelligent Feature Discovery",
                description="Engineering new features and selecting the most predictive ones"
            ),
            AutopilotStep(
                id="insights", phase=AutopilotPhase.INSIGHT_EXTRACTION,
                title="💡 Extracting Key Insights",
                description="Finding patterns, trends, anomalies, and correlations in your data"
            ),
            AutopilotStep(
                id="viz", phase=AutopilotPhase.VISUALIZATION,
                title="📊 Generating Visualizations",
                description="Creating the most informative charts and plots for your data"
            ),
            AutopilotStep(
                id="train", phase=AutopilotPhase.MODEL_TRAINING,
                title="🏋️ Training ML Models",
                description="Testing multiple algorithms with cross-validation to find the best model"
            ),
            AutopilotStep(
                id="eval", phase=AutopilotPhase.MODEL_EVALUATION,
                title="📈 Evaluating & Explaining Model",
                description="Computing metrics, feature importance, and reliability scores"
            ),
            AutopilotStep(
                id="code", phase=AutopilotPhase.CODE_GENERATION,
                title="💻 Generating Deployment Code",
                description="Creating a production-ready prediction API you can run locally"
            ),
            AutopilotStep(
                id="report", phase=AutopilotPhase.REPORT_GENERATION,
                title="📋 Compiling Analysis Report",
                description="Summarizing everything into an executive-ready report"
            ),
        ]
        self.state.steps = steps

    async def run(self):
        """
        Execute the full autopilot pipeline.
        Yields SSE-compatible event dicts as it progresses.
        """
        yield self._event("session_start", {
            "session_id": self.state.session_id,
            "goal": self.state.goal,
            "total_steps": len(self.state.steps),
            "filename": self.state.filename,
            "rows": len(self.state.df),
            "cols": len(self.state.df.columns),
        })

        for i, step in enumerate(self.state.steps):
            if self.state.cancelled:
                yield self._event("cancelled", {"step": step.id})
                return

            self.state.current_step_index = i
            step.status = StepStatus.RUNNING
            step.started_at = time.time()

            yield self._event("step_start", {
                "step_index": i,
                "step": step.to_dict()
            })

            try:
                result = await self._execute_step(step)
                step.status = StepStatus.COMPLETED
                step.completed_at = time.time()
                step.result = result
                step.progress = 100.0

                yield self._event("step_complete", {
                    "step_index": i,
                    "step": step.to_dict()
                })

            except Exception as e:
                step.status = StepStatus.FAILED
                step.completed_at = time.time()
                step.error = str(e)
                logger.error(f"Autopilot step {step.id} failed: {e}")
                traceback.print_exc()

                yield self._event("step_error", {
                    "step_index": i,
                    "step": step.to_dict(),
                    "error": str(e)
                })
                # Continue with next step despite error
                continue

        self.state.completed_at = time.time()
        elapsed = round(self.state.completed_at - self.state.started_at, 1)

        session_payload = {
            "session_id": self.state.session_id,
            "elapsed_seconds": elapsed,
            "insights_count": len(self.state.insights),
            "charts_count": len(self.state.charts),
            "model_trained": self.state.model_result is not None,
            "model_result": self.state.model_result,
            "data_profile": self.state.steps[1].result if len(self.state.steps) > 1 and self.state.steps[1].result else None,
            "insights": self.state.insights,
            "summary": self.state.report or "Analysis complete.",
        }
        
        yield self._event("session_complete", session_payload)

        # Fire webhooks asynchronously without blocking the stream
        asyncio.create_task(self._trigger_webhooks(session_payload))

    async def _trigger_webhooks(self, payload: dict):
        """Fire HTTP requests to the user's registered webhooks."""
        try:
            from database.db import AsyncSessionLocal
            from database.orm import Webhook
            from sqlalchemy import select
            import httpx
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Webhook).filter(
                        Webhook.user_id == self.state.user_id,
                        Webhook.status == "active"
                    )
                )
                webhooks = result.scalars().all()
                
            user_webhooks = [
                w for w in webhooks 
                if "autopilot.completed" in (w.events or [])
            ]
            
            if not user_webhooks:
                return
                
            async with httpx.AsyncClient() as client:
                for wh in user_webhooks:
                    try:
                        await client.post(
                            wh.url,
                            json={"event": "autopilot.completed", "data": payload},
                            timeout=10.0
                        )
                        logger.info(f"Successfully fired webhook to {wh.url}")
                    except Exception as e:
                        logger.warning(f"Webhook {wh.url} failed: {e}")
        except Exception as e:
            logger.error(f"Failed to process webhooks: {e}")

    async def _execute_step(self, step: AutopilotStep) -> Dict[str, Any]:
        """Route execution to the correct handler."""
        handlers = {
            AutopilotPhase.PLANNING: self._step_planning,
            AutopilotPhase.DATA_PROFILING: self._step_profiling,
            AutopilotPhase.DATA_CLEANING: self._step_cleaning,
            AutopilotPhase.FEATURE_DISCOVERY: self._step_features,
            AutopilotPhase.INSIGHT_EXTRACTION: self._step_insights,
            AutopilotPhase.VISUALIZATION: self._step_visualization,
            AutopilotPhase.MODEL_TRAINING: self._step_training,
            AutopilotPhase.MODEL_EVALUATION: self._step_evaluation,
            AutopilotPhase.CODE_GENERATION: self._step_code_generation,
            AutopilotPhase.REPORT_GENERATION: self._step_report,
        }
        handler = handlers.get(step.phase)
        if handler:
            # Add a small artificial delay so the user can see the AI "thinking"
            # and the UI animations have time to run smoothly.
            await asyncio.sleep(1.5)
            # Run the handler
            return await handler(step)
        return {"status": "skipped"}

    # =========================================================================
    # STEP HANDLERS
    # =========================================================================

    async def _step_planning(self, step: AutopilotStep) -> Dict:
        """Analyze goal and data to create intelligent plan."""
        df = self.state.df
        
        # Auto-detect target column if not provided
        if not self.state.target_column:
            # Heuristics: last column, or columns with names like "target", "label", "class", "price", "sales"
            target_keywords = ['target', 'label', 'class', 'churn', 'fraud', 'price', 'sales',
                             'revenue', 'profit', 'rating', 'score', 'outcome', 'result',
                             'survival', 'default', 'response', 'converted', 'purchased']
            
            for col in df.columns:
                if any(kw in col.lower() for kw in target_keywords):
                    self.state.target_column = col
                    break
            
            if not self.state.target_column:
                # Use last numeric column
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    self.state.target_column = numeric_cols[-1]
                else:
                    self.state.target_column = df.columns[-1]
        
        # Detect task type
        target_col = self.state.target_column
        if target_col in df.columns:
            nunique = df[target_col].nunique()
            dtype = df[target_col].dtype
            
            if dtype == 'object' or (dtype in ['int64', 'float64'] and nunique <= 20 and nunique / len(df) < 0.05):
                self.state.task_type = "classification"
            else:
                self.state.task_type = "regression"
        else:
            self.state.task_type = "regression"

        plan_summary = (
            f"📋 **Analysis Plan:**\n"
            f"- Dataset: {self.state.filename} ({len(df):,} rows × {len(df.columns)} cols)\n"
            f"- Target: `{self.state.target_column}`\n"
            f"- Task: {self.state.task_type}\n"
            f"- Goal: {self.state.goal}\n"
            f"- Strategy: Full autonomous pipeline — profile → clean → engineer → train → deploy"
        )
        
        self.state.insights.append(plan_summary)
        
        return {
            "target_column": self.state.target_column,
            "task_type": self.state.task_type,
            "rows": len(df),
            "cols": len(df.columns),
            "plan": plan_summary
        }

    async def _step_profiling(self, step: AutopilotStep) -> Dict:
        """Deep data profiling."""
        df = self.state.df
        
        profile = {
            "shape": {"rows": len(df), "cols": len(df.columns)},
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing": {col: int(df[col].isnull().sum()) for col in df.columns if df[col].isnull().sum() > 0},
            "missing_pct": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
            "duplicates": int(df.duplicated().sum()),
            "numeric_cols": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_cols": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }
        
        # Compute basic stats for numerics
        numeric_stats = {}
        for col in profile["numeric_cols"][:15]:  # Limit to 15 cols for speed
            numeric_stats[col] = {
                "mean": round(float(df[col].mean()), 3) if not df[col].isnull().all() else None,
                "std": round(float(df[col].std()), 3) if not df[col].isnull().all() else None,
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
            }
        profile["numeric_stats"] = numeric_stats

        # Generate profiling insight
        insight = (
            f"🔍 **Data Profile:** {len(df):,} rows × {len(df.columns)} cols | "
            f"{len(profile['numeric_cols'])} numeric, {len(profile['categorical_cols'])} categorical | "
            f"{profile['missing_pct']}% missing | {profile['duplicates']} duplicates | "
            f"{profile['memory_mb']} MB"
        )
        self.state.insights.append(insight)

        return profile

    async def _step_cleaning(self, step: AutopilotStep) -> Dict:
        """Autonomous data cleaning."""
        df = self.state.df.copy()
        fixes = []
        
        original_shape = df.shape

        # 1. Remove duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            df = df.drop_duplicates()
            fixes.append(f"Removed {dup_count} duplicate rows")

        # 2. Handle missing values
        for col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                pct = missing / len(df) * 100
                if pct > 60:
                    df = df.drop(columns=[col])
                    fixes.append(f"Dropped column `{col}` ({pct:.0f}% missing)")
                elif df[col].dtype in ['float64', 'int64']:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    fixes.append(f"Filled {missing} missing values in `{col}` with median ({median_val:.2f})")
                else:
                    mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else "Unknown"
                    df[col] = df[col].fillna(mode_val)
                    fixes.append(f"Filled {missing} missing values in `{col}` with mode ({mode_val})")

        self.state.df = df

        insight = f"🧹 **Data Cleaning:** Applied {len(fixes)} fixes. Shape: {original_shape} → {df.shape}"
        self.state.insights.append(insight)

        return {"fixes": fixes, "original_shape": list(original_shape), "new_shape": list(df.shape)}

    async def _step_features(self, step: AutopilotStep) -> Dict:
        """Feature discovery and engineering."""
        df = self.state.df
        new_features = []
        
        # Auto-detect and engineer date features
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    if parsed.notna().sum() > len(df) * 0.5:
                        df[f'{col}_year'] = parsed.dt.year
                        df[f'{col}_month'] = parsed.dt.month
                        df[f'{col}_dayofweek'] = parsed.dt.dayofweek
                        new_features.extend([f'{col}_year', f'{col}_month', f'{col}_dayofweek'])
                        df = df.drop(columns=[col])
                except:
                    pass

        self.state.df = df
        
        # Compute correlations with target
        target = self.state.target_column
        correlations = {}
        if target in df.columns and df[target].dtype in ['float64', 'int64']:
            numeric_df = df.select_dtypes(include=[np.number])
            if target in numeric_df.columns:
                corrs = numeric_df.corr()[target].drop(target, errors='ignore').abs().sort_values(ascending=False)
                correlations = {col: round(float(val), 3) for col, val in corrs.head(10).items()}

        insight = f"⚡ **Features:** Engineered {len(new_features)} new features. Top correlations with `{target}`: {', '.join(f'{k}({v})' for k, v in list(correlations.items())[:5])}"
        self.state.insights.append(insight)

        return {
            "new_features": new_features,
            "top_correlations": correlations,
            "total_features": len(df.columns)
        }

    async def _step_insights(self, step: AutopilotStep) -> Dict:
        """Extract key data insights using statistical analysis."""
        df = self.state.df
        key_insights = []

        # 1. Distribution insights
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols[:10]:
            skewness = df[col].skew()
            if abs(skewness) > 1:
                direction = "right" if skewness > 0 else "left"
                key_insights.append(f"📊 `{col}` is heavily {direction}-skewed (skew={skewness:.2f})")

        # 2. Categorical insights
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in cat_cols[:5]:
            top_val = df[col].value_counts().head(1)
            if len(top_val) > 0:
                pct = top_val.values[0] / len(df) * 100
                if pct > 50:
                    key_insights.append(f"⚠️ `{col}` is dominated by '{top_val.index[0]}' ({pct:.0f}% of data)")

        # 3. Correlation insights
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.8:
                        key_insights.append(
                            f"🔗 Strong {'positive' if corr_val > 0 else 'negative'} correlation between "
                            f"`{numeric_cols[i]}` and `{numeric_cols[j]}` ({corr_val:.2f})"
                        )

        self.state.insights.extend(key_insights[:10])  # Cap at 10

        return {"insights": key_insights[:10], "count": len(key_insights)}

    async def _step_visualization(self, step: AutopilotStep) -> Dict:
        """Generate key visualizations."""
        df = self.state.df
        charts = []
        
        target = self.state.target_column
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # 1. Target distribution chart
        if target in df.columns:
            if self.state.task_type == "classification":
                value_counts = df[target].value_counts().head(10)
                charts.append({
                    "type": "bar",
                    "title": f"Distribution of {target}",
                    "data": {"labels": value_counts.index.tolist(), "values": value_counts.values.tolist()},
                    "description": f"Class distribution of target variable `{target}`"
                })
            else:
                charts.append({
                    "type": "histogram",
                    "title": f"Distribution of {target}",
                    "data": {"values": df[target].dropna().tolist()[:1000]},
                    "description": f"Histogram of target variable `{target}`"
                })

        # 2. Correlation heatmap data
        if len(numeric_cols) > 1:
            top_cols = numeric_cols[:10]
            corr = df[top_cols].corr().round(3)
            charts.append({
                "type": "heatmap",
                "title": "Feature Correlation Matrix",
                "data": {
                    "labels": top_cols,
                    "values": corr.values.tolist()
                },
                "description": "Correlation heatmap of top numeric features"
            })

        # 3. Top feature bar chart
        if target in df.columns and target in numeric_cols and len(numeric_cols) > 1:
            corrs = df[numeric_cols].corr()[target].drop(target, errors='ignore').abs().sort_values(ascending=False).head(8)
            charts.append({
                "type": "bar",
                "title": f"Top Features Correlated with {target}",
                "data": {"labels": corrs.index.tolist(), "values": corrs.values.tolist()},
                "description": "Features most correlated with the target variable"
            })

        self.state.charts = charts

        return {"charts_generated": len(charts)}

    async def _step_training(self, step: AutopilotStep) -> Dict:
        """Train ML model using the existing God-Level AutoML engine."""
        try:
            from ml.god_level_automl import run_god_level
            import asyncio
            
            # Run the heavy blocking AutoML training in a separate thread
            # to prevent starving the event loop and freezing the SSE stream.
            result = await asyncio.to_thread(
                run_god_level,
                df=self.state.df,
                target_column=self.state.target_column,
                user_id=self.state.user_id,
                mode="balanced"
            )
            
            self.state.model_result = {
                "best_model": result.best_model_name,
                "metrics": result.best_model_metrics,
                "reliability": result.best_model_reliability,
                "leaderboard": result.leaderboard[:5] if result.leaderboard else [],
                "processing_time": result.processing_time,
            }
            
            insight = (
                f"🏆 **Best Model: {result.best_model_name}** | "
                f"Reliability: {result.best_model_reliability:.1f}/100 | "
                f"Trained in {result.processing_time:.1f}s"
            )
            self.state.insights.append(insight)

            return self.state.model_result

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            # Fallback to simple sklearn
            return await self._fallback_training(step)

    async def _fallback_training(self, step: AutopilotStep) -> Dict:
        """Fallback training with basic sklearn if God-Level fails."""
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import accuracy_score, r2_score, mean_squared_error

        df = self.state.df.copy()
        target = self.state.target_column

        if target not in df.columns:
            return {"error": f"Target column '{target}' not found"}

        # Prepare data
        X = df.drop(columns=[target])
        y = df[target]

        # Encode categoricals
        encoders = {}
        for col in X.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le

        if y.dtype == 'object':
            le_target = LabelEncoder()
            y = le_target.fit_transform(y)

        # Drop remaining non-numeric
        X = X.select_dtypes(include=[np.number])

        # Fill any remaining NaN
        X = X.fillna(0)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if self.state.task_type == "classification":
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            score = accuracy_score(y_test, y_pred)
            metric_name = "accuracy"
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            score = r2_score(y_test, y_pred)
            metric_name = "r2"

        # Save model
        try:
            from ml.model_persistence import model_persistence
            model_persistence.save_model(
                user_id=self.state.user_id,
                model=model,
                metadata={
                    "model_name": "RandomForest",
                    "task_type": self.state.task_type,
                    "target_column": self.state.target_column,
                    "feature_columns": X.columns.tolist(),
                    metric_name: round(score, 4),
                    "source": "autopilot"
                }
            )
        except Exception as save_err:
            logger.warning(f"Could not save model: {save_err}")

        self.state.model_result = {
            "best_model": "RandomForest",
            "metrics": {metric_name: round(score, 4)},
            "reliability": round(score * 100, 1),
            "processing_time": round(time.time() - step.started_at, 1),
        }

        insight = f"🏆 **Best Model: RandomForest** | {metric_name}: {score:.4f}"
        self.state.insights.append(insight)

        return self.state.model_result

    async def _step_evaluation(self, step: AutopilotStep) -> Dict:
        """Evaluate model and generate explanations."""
        if not self.state.model_result:
            return {"status": "skipped", "reason": "No model trained"}

        eval_result = {
            "model": self.state.model_result.get("best_model"),
            "metrics": self.state.model_result.get("metrics", {}),
            "reliability": self.state.model_result.get("reliability", 0),
            "verdict": "✅ Model is production-ready" if self.state.model_result.get("reliability", 0) > 70 else "⚠️ Model needs improvement"
        }

        self.state.insights.append(eval_result["verdict"])
        return eval_result

    async def _step_code_generation(self, step: AutopilotStep) -> Dict:
        """Generate deployment code."""
        if not self.state.model_result:
            return {"status": "skipped", "reason": "No model to deploy"}

        try:
            from ml.ml_code_generator import generate_code_zip
            from config.settings import Settings
            from ml.model_persistence import model_persistence

            base_storage = Settings.STORAGE
            model_path = base_storage / "models" / self.state.user_id / "active_model.pkl"

            if model_path.exists():
                meta_path = model_path.parent / "active_metadata.json"
                metadata = {}
                if meta_path.exists():
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)

                buf = generate_code_zip(model_path, metadata)
                
                self.state.insights.append("💻 **Deployment code generated** — Ready to run as a local API server")
                return {"status": "generated", "files_count": 5}
            else:
                return {"status": "skipped", "reason": "Model file not found at expected path"}
        except Exception as e:
            logger.warning(f"Code generation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _step_report(self, step: AutopilotStep) -> Dict:
        """Generate the final analysis report."""
        elapsed = round(time.time() - self.state.started_at, 1)
        
        report_lines = [
            f"# 🚀 DataVision Autopilot Report",
            f"",
            f"**Dataset:** {self.state.filename}",
            f"**Goal:** {self.state.goal}",
            f"**Target:** `{self.state.target_column}` ({self.state.task_type})",
            f"**Total Time:** {elapsed}s",
            f"",
            f"---",
            f"",
            f"## Key Insights",
            f"",
        ]
        
        for i, insight in enumerate(self.state.insights):
            report_lines.append(f"{i+1}. {insight}")
        
        if self.state.model_result:
            report_lines.extend([
                f"",
                f"## Model Performance",
                f"",
                f"- **Best Model:** {self.state.model_result.get('best_model', 'N/A')}",
                f"- **Metrics:** {json.dumps(self.state.model_result.get('metrics', {}), indent=2)}",
                f"- **Reliability:** {self.state.model_result.get('reliability', 0)}/100",
            ])

        report_lines.extend([
            f"",
            f"---",
            f"*Generated by DataVision Agentic Autopilot v5.0*",
        ])

        self.state.report = "\n".join(report_lines)
        return {"report": self.state.report}

    def _event(self, event_type: str, data: Dict) -> Dict:
        """Create a standardized event dict."""
        return {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

    def cancel(self):
        """Cancel the running autopilot."""
        self.state.cancelled = True


# Global registry of active autopilot sessions
active_sessions: Dict[str, AgenticAutopilot] = {}
