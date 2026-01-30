"""
🤖 PRO AGENT ENGINE v2.0 - DataVision Autonomous AI
====================================================

Full autonomous agent with intelligent task orchestration.

Features:
- 🎯 Autonomous Task Decomposition
- 🔧 Multi-Tool Orchestration
- 🌐 MCP Integration
- 🔄 Error Recovery with Fallbacks
- 📊 Progress Tracking
- 💡 Self-Reflection & Learning

Built for DataVision - Autonomous AI for ANY task!

Author: DataVision Team
Version: 2.0.0
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import re
import json

logger = logging.getLogger(__name__)

# LLM for intelligent responses
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Smart Visualization for dynamic charts
try:
    from mcp.smart_visualization import smart_visualize, SmartVisualization
    SMART_VIZ_AVAILABLE = True
except ImportError:
    SMART_VIZ_AVAILABLE = False

# Advanced Hybrid Intelligence System
try:
    from core.knowledge_sources import (
        KnowledgeSource, SourceClassifier, HybridResponseCombiner,
        SOURCE_BADGES, classify_query, get_source_badge
    )
    HYBRID_KNOWLEDGE_AVAILABLE = True
except ImportError:
    HYBRID_KNOWLEDGE_AVAILABLE = False

try:
    from core.advanced_rag import AdaptiveRAG, AgenticRAG, RAGType
    ADVANCED_RAG_AVAILABLE = True
except ImportError:
    ADVANCED_RAG_AVAILABLE = False

try:
    from core.deep_agents import ReActAgent, HybridAgent, deep_agent_query
    DEEP_AGENTS_AVAILABLE = True
except ImportError:
    DEEP_AGENTS_AVAILABLE = False

# Intelligent Visualizer (Knowledge Graphs, Mind Maps, 20+ Charts)
try:
    from core.intelligent_visualizer import (
        IntelligentVisualizer, VizType, smart_visualize,
        generate_knowledge_graph, generate_mind_map
    )
    INTELLIGENT_VIZ_AVAILABLE = True
except ImportError:
    INTELLIGENT_VIZ_AVAILABLE = False

# Intelligent Query Processor (Claude-style)
try:
    from core.intelligent_processor import IntelligentQueryProcessor, intelligent_process
    INTELLIGENT_PROCESSOR_AVAILABLE = True
except ImportError:
    INTELLIGENT_PROCESSOR_AVAILABLE = False


# =============================================================================
# AGENT TOOLS & CAPABILITIES
# =============================================================================

class ToolType(Enum):
    """Types of tools the agent can use"""
    DATA_ANALYSIS = "data_analysis"
    CALCULATION = "calculation"
    VISUALIZATION = "visualization"
    WEB_SEARCH = "web_search"
    FILE_OPERATION = "file_operation"
    DATABASE = "database"
    ML_MODEL = "ml_model"
    TEXT_PROCESSING = "text_processing"


@dataclass
class Tool:
    """Definition of an agent tool"""
    name: str
    tool_type: ToolType
    description: str
    function: Optional[Callable] = None
    available: bool = True


@dataclass
class TaskStep:
    """A step in the agent's execution plan"""
    step_id: int
    description: str
    tool_needed: ToolType
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: str = None


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task"""
    task_description: str
    steps: List[TaskStep] = field(default_factory=list)
    fallbacks: Dict[int, List[str]] = field(default_factory=dict)
    success_criteria: str = ""
    estimated_time: str = ""


# =============================================================================
# BUILT-IN TOOLS
# =============================================================================

def tool_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Summarize a dataframe with ACTUAL computed statistics"""
    if df is None or df.empty:
        return {"error": "No data provided"}
    
    result = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns)
    }
    
    # Calculate actual statistics for each numeric column
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        stats_by_column = {}
        for col in numeric_cols:
            try:
                stats_by_column[col] = {
                    "mean": round(float(df[col].mean()), 2),
                    "median": round(float(df[col].median()), 2),
                    "std": round(float(df[col].std()), 2),
                    "min": round(float(df[col].min()), 2),
                    "max": round(float(df[col].max()), 2),
                    "sum": round(float(df[col].sum()), 2),
                    "count": int(df[col].count()),
                    "missing": int(df[col].isna().sum())
                }
            except:
                pass
        result["column_statistics"] = stats_by_column
    
    # Calculate stats for categorical columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        cat_stats = {}
        for col in cat_cols[:5]:  # Limit to 5
            try:
                cat_stats[col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(3).to_dict()
                }
            except:
                pass
        result["categorical_statistics"] = cat_stats
    
    return result


def tool_calculate_stats(df: pd.DataFrame, column: str, operation: str) -> Dict[str, Any]:
    """Calculate statistics on a column"""
    if df is None or column not in df.columns:
        return {"error": f"Column {column} not found"}
    
    operations = {
        "mean": lambda x: x.mean(),
        "sum": lambda x: x.sum(),
        "count": lambda x: x.count(),
        "min": lambda x: x.min(),
        "max": lambda x: x.max(),
        "median": lambda x: x.median(),
        "std": lambda x: x.std()
    }
    
    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}
    
    try:
        result = operations[operation](df[column])
        return {"column": column, "operation": operation, "result": float(result)}
    except:
        return {"error": f"Could not perform {operation} on {column}"}


def tool_group_by_analysis(df: pd.DataFrame, group_col: str, agg_col: str, operation: str = "mean") -> Dict[str, Any]:
    """Group by analysis"""
    if df is None or group_col not in df.columns or agg_col not in df.columns:
        return {"error": "Columns not found"}
    
    try:
        grouped = df.groupby(group_col)[agg_col].agg(operation)
        return {"group_by": group_col, "aggregated": agg_col, "operation": operation, "results": grouped.to_dict()}
    except Exception as e:
        return {"error": str(e)}


def tool_find_correlations(df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, Any]:
    """Find strongly correlated columns"""
    if df is None:
        return {"error": "No data provided"}
    
    numeric_df = df.select_dtypes(include=[np.number])
    if len(numeric_df.columns) < 2:
        return {"error": "Need at least 2 numeric columns"}
    
    corr = numeric_df.corr()
    strong_correlations = []
    
    for i, col1 in enumerate(corr.columns):
        for col2 in corr.columns[i+1:]:
            val = corr.loc[col1, col2]
            if abs(val) >= threshold:
                strong_correlations.append({
                    "col1": col1, "col2": col2, "correlation": round(val, 3)
                })
    
    return {"threshold": threshold, "correlations": strong_correlations}


def tool_detect_outliers(df: pd.DataFrame, column: str, method: str = "iqr") -> Dict[str, Any]:
    """Detect outliers in a column"""
    if df is None or column not in df.columns:
        return {"error": f"Column {column} not found"}
    
    try:
        data = df[column].dropna()
        
        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = data[(data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)]
        elif method == "zscore":
            z = (data - data.mean()) / data.std()
            outliers = data[abs(z) > 3]
        else:
            return {"error": f"Unknown method: {method}"}
        
        return {
            "column": column,
            "method": method,
            "n_outliers": len(outliers),
            "percentage": round(len(outliers) / len(data) * 100, 2),
            "sample_outliers": outliers.head(5).tolist()
        }
    except Exception as e:
        return {"error": str(e)}


# Web search tool (optional)
def tool_web_search(query: str) -> Dict[str, Any]:
    """Perform web search (requires external API)"""
    try:
        from utils.tavily_search import TavilySearch
        search = TavilySearch()
        results = search.search(query, max_results=3)
        return {"query": query, "results": results}
    except:
        return {"error": "Web search not available", "query": query}


# =============================================================================
# TASK PLANNER
# =============================================================================

def plan_task(query: str, available_tools: List[Tool], df: pd.DataFrame = None) -> ExecutionPlan:
    """
    Create an intelligent execution plan for a task.
    """
    q_lower = query.lower()
    steps = []
    step_id = 1
    
    # Analyze what the task needs
    needs_data_analysis = any(kw in q_lower for kw in ['analyze', 'summary', 'describe', 'statistics'])
    needs_comparison = any(kw in q_lower for kw in ['compare', 'versus', 'difference'])
    needs_correlation = any(kw in q_lower for kw in ['relationship', 'correlation', 'affect'])
    needs_outliers = any(kw in q_lower for kw in ['outlier', 'anomaly', 'unusual'])
    needs_grouping = any(kw in q_lower for kw in ['by category', 'per', 'group by', 'breakdown'])
    needs_visualization = any(kw in q_lower for kw in ['chart', 'graph', 'visualize', 'plot'])
    needs_web = any(kw in q_lower for kw in ['search', 'internet', 'web', 'online', 'look up'])
    
    # Build steps based on needs
    if needs_data_analysis or not any([needs_comparison, needs_correlation, needs_outliers]):
        steps.append(TaskStep(
            step_id=step_id,
            description="Analyze and summarize the dataset",
            tool_needed=ToolType.DATA_ANALYSIS
        ))
        step_id += 1
    
    if needs_correlation:
        steps.append(TaskStep(
            step_id=step_id,
            description="Find correlations between variables",
            tool_needed=ToolType.CALCULATION
        ))
        step_id += 1
    
    if needs_outliers:
        steps.append(TaskStep(
            step_id=step_id,
            description="Detect outliers and anomalies",
            tool_needed=ToolType.DATA_ANALYSIS
        ))
        step_id += 1
    
    if needs_grouping:
        steps.append(TaskStep(
            step_id=step_id,
            description="Perform group-by analysis",
            tool_needed=ToolType.CALCULATION
        ))
        step_id += 1
    
    if needs_visualization:
        steps.append(TaskStep(
            step_id=step_id,
            description=query,  # Pass full query for chart type/color detection
            tool_needed=ToolType.VISUALIZATION
        ))
        step_id += 1
    
    if needs_web:
        steps.append(TaskStep(
            step_id=step_id,
            description="Search for external information",
            tool_needed=ToolType.WEB_SEARCH
        ))
        step_id += 1
    
    # Always add synthesis step
    steps.append(TaskStep(
        step_id=step_id,
        description="Synthesize results and generate response",
        tool_needed=ToolType.TEXT_PROCESSING
    ))
    
    # Create fallbacks
    fallbacks = {}
    for step in steps:
        if step.tool_needed == ToolType.WEB_SEARCH:
            fallbacks[step.step_id] = ["Skip web search and use available data"]
        elif step.tool_needed == ToolType.CALCULATION:
            fallbacks[step.step_id] = ["Try alternative calculation method"]
    
    return ExecutionPlan(
        task_description=query,
        steps=steps,
        fallbacks=fallbacks,
        success_criteria="Generate comprehensive response answering user's question",
        estimated_time=f"{len(steps) * 2}s"
    )


# =============================================================================
# PRO AGENT ENGINE CLASS
# =============================================================================

class ProAgentEngine:
    """
    🤖 PRO AGENT ENGINE - DataVision Autonomous AI
    
    Full autonomous agent with intelligent task orchestration.
    
    💡 WHEN TO USE:
    - Complex multi-step tasks
    - Tasks requiring multiple tools
    - Autonomous analysis and reporting
    - When you want AI to figure out the steps
    
    Features:
    - Autonomous task planning
    - Multi-tool execution
    - Error recovery
    - Progress tracking
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tools = self._register_tools()
        self.execution_history = []
    
    def _register_tools(self) -> List[Tool]:
        """Register available tools."""
        return [
            Tool("data_summary", ToolType.DATA_ANALYSIS, "Summarize dataset", tool_data_summary),
            Tool("calculate_stats", ToolType.CALCULATION, "Calculate statistics", tool_calculate_stats),
            Tool("group_by_analysis", ToolType.CALCULATION, "Group by analysis", tool_group_by_analysis),
            Tool("find_correlations", ToolType.CALCULATION, "Find correlations", tool_find_correlations),
            Tool("detect_outliers", ToolType.DATA_ANALYSIS, "Detect outliers", tool_detect_outliers),
            Tool("web_search", ToolType.WEB_SEARCH, "Search the web", tool_web_search, available=False),
        ]
    
    def process(
        self,
        query: str,
        context: str = "",
        df: pd.DataFrame = None,
        enable_web_search: bool = False,
        enable_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process a task with full autonomous capabilities.
        Uses DYNAMIC routing - data queries use agent, general queries use AI.
        """
        result = {
            "answer": "",
            "mode": "agent",
            "confidence": 0.85,
            "sources": ["Agent"],
            "execution_log": [],
            "tools_used": []
        }
        
        start_time = datetime.now()
        
        # =================================================================
        # 🔄 DYNAMIC ROUTING: Check if query relates to actual data
        # =================================================================
        q_lower = query.lower()
        
        # Get column names from data
        column_names = [col.lower() for col in df.columns] if df is not None and not df.empty else []
        column_names_spaced = [col.replace('_', ' ') for col in column_names]
        
        # Check if query mentions ANY column or data-related term
        data_terms = column_names + column_names_spaced + [
            'my data', 'my ', 'our ', 'the data', 'uploaded', 'dataset',
            'total', 'sum', 'average', 'count', 'revenue', 'sales', 'customer'
        ]
        
        query_is_about_data = any(term in q_lower for term in data_terms if term)
        
        # If NOT about data, use pure AI Knowledge
        if not query_is_about_data:
            logger.info("🌐 Agent: Routing to AI KNOWLEDGE (query not about data)")
            
            try:
                from core.llm import chat as llm_chat
                
                ai_prompt = f"""You are an AI Agent with autonomous capabilities.

Answer this question using your knowledge:

{query}

Provide a helpful, accurate, and informative response. Think step by step if needed."""

                llm_response = llm_chat(ai_prompt, temperature=0.7, max_tokens=700)
                
                result["answer"] = f"""## 🤖 Agent

🌐 **AI Knowledge**

{llm_response}

---
*💡 This is general AI knowledge. For autonomous analysis of YOUR data, ask about specific columns.*"""
                result["confidence"] = 0.85
                result["sources"] = ["AI Knowledge"]
                result["execution_log"].append("🌐 Answered using AI Knowledge (query not about user data)")
                
                exec_time = (datetime.now() - start_time).total_seconds()
                result["execution_time"] = f"{exec_time:.2f}s"
                return result
                
            except Exception as e:
                logger.error(f"AI Knowledge error: {e}")
        
        # =================================================================
        # 📊 DATA PATH - Query IS about user's data, use full agent
        # =================================================================
        logger.info("📊 Agent: Routing to DATA ANALYSIS with tools")
        
        # Create execution plan
        plan = plan_task(query, self.tools, df)
        result["execution_log"].append(f"📋 Created plan with {len(plan.steps)} steps")
        
        # Execute each step
        step_results = {}
        
        for step in plan.steps:
            try:
                step.status = "running"
                result["execution_log"].append(f"⏳ Step {step.step_id}: {step.description}")
                
                # Execute based on tool type
                step_result = self._execute_step(step, df, step_results)
                
                step.result = step_result
                step.status = "completed"
                result["tools_used"].append(step.tool_needed.value)
                result["execution_log"].append(f"✅ Step {step.step_id}: Completed")
                
                step_results[step.step_id] = step_result
                
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                result["execution_log"].append(f"❌ Step {step.step_id}: Failed - {str(e)[:50]}")
                
                # Try fallback
                if step.step_id in plan.fallbacks:
                    result["execution_log"].append(f"🔄 Trying fallback for step {step.step_id}")
                    step_results[step.step_id] = {"fallback": True, "error": str(e)}
        
        # Generate final response
        response = self._generate_response(query, plan, step_results, context)
        
        result["answer"] = response
        result["confidence"] = self._calculate_confidence(plan.steps)
        
        # Extract chart from step results if generated
        for step_id, step_result in step_results.items():
            if isinstance(step_result, dict) and 'chart' in step_result:
                result["chart"] = step_result["chart"]
                result["visualization"] = step_result["chart"]
                result["viz_type"] = step_result.get("chart_type", "auto")
                break
        
        # Execution time
        exec_time = (datetime.now() - start_time).total_seconds()
        result["execution_time"] = f"{exec_time:.2f}s"
        result["steps_completed"] = sum(1 for s in plan.steps if s.status == "completed")
        result["steps_total"] = len(plan.steps)
        
        return result
    
    def _execute_step(
        self,
        step: TaskStep,
        df: pd.DataFrame,
        previous_results: Dict[int, Any]
    ) -> Any:
        """Execute a single step."""
        
        if step.tool_needed == ToolType.DATA_ANALYSIS:
            return tool_data_summary(df)
        
        elif step.tool_needed == ToolType.CALCULATION:
            # Determine what calculation to do
            if "correlation" in step.description.lower():
                return tool_find_correlations(df)
            elif "outlier" in step.description.lower():
                if df is not None and len(df.columns) > 0:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        return tool_detect_outliers(df, numeric_cols[0])
            elif "group" in step.description.lower():
                if df is not None:
                    categorical = df.select_dtypes(include=['object']).columns
                    numeric = df.select_dtypes(include=[np.number]).columns
                    if len(categorical) > 0 and len(numeric) > 0:
                        return tool_group_by_analysis(df, categorical[0], numeric[0])
            
            # Default: basic stats
            if df is not None:
                numeric = df.select_dtypes(include=[np.number]).columns
                if len(numeric) > 0:
                    return tool_calculate_stats(df, numeric[0], "mean")
            
            return {"result": "No calculation performed"}
        
        elif step.tool_needed == ToolType.WEB_SEARCH:
            return tool_web_search(step.description)
        
        elif step.tool_needed == ToolType.VISUALIZATION:
            # Use LLM-driven visualization for dynamic chart generation
            if df is not None:
                try:
                    # Try LLM visualizer first (Claude-style)
                    from core.llm_visualizer import llm_visualize
                    viz_result = llm_visualize(df, step.description, self.user_id)
                    if viz_result.get("success") and viz_result.get("chart"):
                        return {
                            "chart_type": viz_result.get("visualization_type", "auto"),
                            "chart": viz_result.get("chart"),
                            "status": "visualization_generated"
                        }
                except Exception as e:
                    logger.warning(f"LLM visualizer failed: {e}")
                
                # Fallback to smart_visualize
                try:
                    if INTELLIGENT_VIZ_AVAILABLE:
                        viz_result = smart_visualize(self.user_id, step.description, df)
                        if viz_result.get("success") and viz_result.get("chart"):
                            return {
                                "chart_type": viz_result.get("visualization_type", "auto"),
                                "chart": viz_result.get("chart"),
                                "status": "visualization_generated"
                            }
                except Exception as e:
                    logger.warning(f"Smart visualize failed: {e}")
            
            return {"chart_type": "auto", "status": "visualization_failed"}
        
        elif step.tool_needed == ToolType.TEXT_PROCESSING:
            return {"synthesis": "ready", "previous_steps": len(previous_results)}
        
        return {"result": "Step executed"}
    
    def _generate_response(
        self,
        query: str,
        plan: ExecutionPlan,
        results: Dict[int, Any],
        context: str
    ) -> str:
        """Generate comprehensive response from execution results - QUERY FOCUSED."""
        
        # Extract key data from results
        data_stats = {}
        categorical_stats = {}
        correlations = []
        outliers = []
        visualizations = []
        
        for step_id, result_data in results.items():
            if isinstance(result_data, dict):
                if 'column_statistics' in result_data:
                    data_stats = result_data['column_statistics']
                if 'categorical_statistics' in result_data:
                    categorical_stats = result_data['categorical_statistics']
                if 'rows' in result_data:
                    data_stats['_meta'] = {
                        'rows': result_data.get('rows'),
                        'columns': result_data.get('columns'),
                        'column_names': result_data.get('column_names', [])
                    }
                if 'correlations' in result_data:
                    correlations = result_data['correlations']
                if 'outliers' in result_data or 'outlier_indices' in result_data:
                    outliers = result_data
                if 'chart' in result_data:
                    visualizations.append(result_data)
        
        # Build a compact summary for LLM
        compact_summary = ""
        meta = data_stats.get('_meta', {})
        if meta:
            compact_summary += f"Dataset: {meta.get('rows', '?')} rows, {meta.get('columns', '?')} cols\n"
        
        # Add categorical column stats (UNIQUE COUNTS)
        if categorical_stats:
            compact_summary += "\nCategorical Columns:\n"
            for col, stats in categorical_stats.items():
                unique = stats.get('unique_values', 'N/A')
                top_vals = stats.get('top_values', {})
                top_str = ", ".join(f"{k}: {v}" for k, v in list(top_vals.items())[:3])
                compact_summary += f"- {col}: {unique} unique values. Top: {top_str}\n"
        
        # Add numeric column stats
        if data_stats:
            compact_summary += "\nNumeric Columns:\n"
            shown = 0
            for col, stats in data_stats.items():
                if col == '_meta' or shown >= 8:
                    continue
                if isinstance(stats, dict) and 'mean' in stats:
                    compact_summary += f"- {col}: mean={stats.get('mean')}, "
                    compact_summary += f"min={stats.get('min')}, max={stats.get('max')}\n"
                    shown += 1
        
        if correlations:
            compact_summary += f"\nCorrelations found: {len(correlations)}\n"
            for corr in correlations[:3]:
                compact_summary += f"- {corr}\n"
        
        # Initialize response - will append chart later
        response = "## 🤖 Agent Analysis\n\n"
        
        if LLM_AVAILABLE:
            prompt = f"""You are an AI Agent. Answer the user's SPECIFIC question directly.

USER QUESTION: {query}

AVAILABLE DATA:
{compact_summary}

{f'CONTEXT: {context[:300]}' if context else ''}

INSTRUCTIONS:
1. DIRECTLY answer the question "{query}"
2. Use specific numbers from the data
3. Be concise - 2-4 sentences for simple questions, more for complex analysis
4. If the question asks "what is X", just answer with X
5. If asking about a specific metric, show that metric's value
6. Don't list all columns unless asked for overview

Format: Start with the direct answer, then supporting details if needed."""

            try:
                llm_response = llm_chat(prompt, temperature=0.3, max_tokens=600)
                response += llm_response
                # DON'T return here - continue to append chart below
            except Exception as e:
                logger.error(f"LLM error: {e}")
                response += f"📊 **From Your Data:**\n\n{compact_summary}"
        else:
            response += f"📊 **From Your Data:**\n\n{compact_summary}"
        
        # Fallback logic only if response is still minimal (LLM failed or unavailable)
        q_lower = query.lower()
        
        # SKIP fallback if LLM gave good response - go directly to chart embedding
        # Only do fallback logic for specific query types if response is short
        if len(response) < 100:
            # UNIQUE COUNT QUERIES
            if 'unique' in q_lower or ('how many' in q_lower and any(word in q_lower for word in ['location', 'category', 'type', 'name'])):
                # Check for specific column in query
                found_answer = False
                for word in query.split():
                    word_lower = word.lower().rstrip('?.,!')
                    for col, stats in categorical_stats.items():
                        if word_lower in col.lower():
                            unique_count = stats.get('unique_values', 'N/A')
                            top_vals = stats.get('top_values', {})
                            response += f"**Unique {col}:** {unique_count}\n\n"
                            if top_vals:
                                response += f"**Top values:** {', '.join(f'{k} ({v})' for k, v in list(top_vals.items())[:5])}\n\n"
                            found_answer = True
                            break
                    if found_answer:
                        break
                
                # If no specific column found, show all categorical unique counts
                if not found_answer and categorical_stats:
                    response += "**Unique Value Counts:**\n"
                    for col, stats in categorical_stats.items():
                        response += f"• **{col}:** {stats.get('unique_values', 'N/A')} unique values\n"
                    response += "\n"
        
        # EMBED CHART IN RESPONSE - Critical for frontend rendering
        if visualizations:
            for viz in visualizations:
                chart_data = viz.get('chart')
                if chart_data and isinstance(chart_data, dict):
                    # Ensure chart has data and layout
                    if 'data' in chart_data and 'layout' in chart_data:
                        import json
                        chart_json = json.dumps(chart_data, default=str)
                        response += f"\n\n```plotly_chart\n{chart_json}\n```"
                        break  # Only one chart
        
        return response
    
    def _calculate_confidence(self, steps: List[TaskStep]) -> float:
        """Calculate confidence based on step success rate."""
        if not steps:
            return 0.5
        
        completed = sum(1 for s in steps if s.status == "completed")
        return min(0.95, (completed / len(steps)) * 0.9 + 0.1)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def agent_response(
    user_id: str,
    query: str,
    context: str = "",
    enable_web_search: bool = True
) -> Dict[str, Any]:
    """Quick function for agent response."""
    engine = ProAgentEngine(user_id)
    return engine.process(query, context)


def agent_response_sync(
    user_id: str,
    query: str,
    context: str = "",
    df: pd.DataFrame = None
) -> Dict[str, Any]:
    """Synchronous agent response for compatibility."""
    engine = ProAgentEngine(user_id)
    return engine.process(query, context, df)


# Alias for backwards compatibility
AgentEngine = ProAgentEngine

__all__ = ['ProAgentEngine', 'AgentEngine', 'agent_response', 'agent_response_sync']
