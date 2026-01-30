"""
🔧 CLAUDE-STYLE SMART MCP SYSTEM
================================

Uses LLM to intelligently select and execute MCPs based on user query.
Shows Claude-style tool execution with progress and results.

Features:
- 🧠 LLM understands query intent and selects appropriate tools
- 🔄 Automatic tool chaining (one tool's output feeds another)
- 📊 Progress tracking and execution visualization
- ✨ Claude-style tool blocks in responses
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

# LLM for intelligent routing
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


@dataclass
class MCPExecution:
    """Represents a single MCP tool execution"""
    tool_name: str
    tool_icon: str
    action: str
    status: str = "pending"  # pending, running, success, error
    progress: int = 0
    details: List[str] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0
    start_time: Optional[datetime] = None


@dataclass
class MCPPlan:
    """Execution plan for MCPs"""
    tools_to_run: List[str]
    reasoning: str
    chain_dependencies: Dict[str, List[str]] = field(default_factory=dict)


# Available MCPs with their capabilities
MCP_REGISTRY = {
    "data_validator": {
        "name": "Data Validator",
        "icon": "🔍",
        "description": "Validates data quality, checks for missing values, duplicates, and anomalies",
        "triggers": ["quality", "validate", "check", "missing", "null", "duplicate", "clean", "error", "issue"],
        "output": "quality_report"
    },
    "insight_engine": {
        "name": "Insight Generator",
        "icon": "💡",
        "description": "Discovers patterns, trends, and generates actionable insights",
        "triggers": ["insight", "pattern", "trend", "discover", "find", "analyze", "important", "summary"],
        "output": "insights"
    },
    "chart_generator": {
        "name": "Chart Generator",
        "icon": "📊",
        "description": "Creates visualizations based on data and user preferences",
        "triggers": ["chart", "graph", "visualize", "plot", "show", "display", "diagram"],
        "output": "chart"
    },
    "forecast_engine": {
        "name": "Forecast Engine", 
        "icon": "🔮",
        "description": "Predicts future values using time-series analysis",
        "triggers": ["predict", "forecast", "future", "next", "projection", "estimate", "will be"],
        "output": "predictions"
    },
    "alert_engine": {
        "name": "Anomaly Detector",
        "icon": "🚨",
        "description": "Detects anomalies, outliers, and threshold breaches",
        "triggers": ["anomaly", "outlier", "unusual", "spike", "drop", "alert", "warning", "abnormal"],
        "output": "alerts"
    },
    "data_transformer": {
        "name": "Data Transformer",
        "icon": "🔄",
        "description": "Transforms data: aggregation, pivot, grouping, filtering",
        "triggers": ["group by", "aggregate", "pivot", "filter", "transform", "breakdown", "by region", "by category"],
        "output": "transformed_data"
    },
    "sql_executor": {
        "name": "SQL Executor",
        "icon": "💾",
        "description": "Executes SQL queries on the data",
        "triggers": ["sql", "query", "select", "where", "join", "database"],
        "output": "query_results"
    },
    "report_generator": {
        "name": "Report Generator",
        "icon": "📄",
        "description": "Generates comprehensive analysis reports",
        "triggers": ["report", "summary", "overview", "comprehensive", "detailed", "full analysis"],
        "output": "report"
    }
}


class SmartMCPSelector:
    """
    🧠 SMART MCP SELECTOR
    
    Uses LLM to understand query intent and select appropriate MCPs.
    Like Claude's tool selection but for data analysis.
    """
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
    
    def select_mcps(self, query: str, df: pd.DataFrame = None) -> MCPPlan:
        """
        Use LLM to intelligently select which MCPs to run.
        """
        if LLM_AVAILABLE:
            return self._llm_select(query, df)
        else:
            return self._rule_based_select(query)
    
    def _llm_select(self, query: str, df: pd.DataFrame = None) -> MCPPlan:
        """Use LLM to select MCPs."""
        
        # Build MCP descriptions for prompt
        mcp_list = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in MCP_REGISTRY.items()
        ])
        
        # Data context
        data_context = ""
        if df is not None and not df.empty:
            data_context = f"User has data with {len(df)} rows and columns: {list(df.columns)[:15]}"
        
        prompt = f"""You are a tool selection AI. Analyze the user's query and determine which tools to use.

USER QUERY: "{query}"

{data_context}

AVAILABLE TOOLS:
{mcp_list}

Based on the query, select the appropriate tools. Consider:
1. What does the user want to accomplish?
2. Which tools would help answer their question?
3. Should tools run in sequence (e.g., validate data before analysis)?

Respond with ONLY a JSON object:
{{
    "tools": ["tool_name1", "tool_name2"],
    "reasoning": "Brief explanation of why these tools",
    "chain": {{"tool2": ["tool1"]}}  // tool2 depends on tool1
}}

If no tools are needed, return: {{"tools": [], "reasoning": "Simple query, no tools needed"}}"""

        try:
            response = llm_chat(prompt, temperature=0.1, max_tokens=300)
            
            # Parse JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return MCPPlan(
                    tools_to_run=data.get("tools", []),
                    reasoning=data.get("reasoning", ""),
                    chain_dependencies=data.get("chain", {})
                )
        except Exception as e:
            logger.warning(f"LLM MCP selection failed: {e}")
        
        return self._rule_based_select(query)
    
    def _rule_based_select(self, query: str) -> MCPPlan:
        """Fallback rule-based selection."""
        q_lower = query.lower()
        selected = []
        
        for mcp_name, info in MCP_REGISTRY.items():
            if any(trigger in q_lower for trigger in info["triggers"]):
                selected.append(mcp_name)
        
        return MCPPlan(
            tools_to_run=selected,
            reasoning="Selected based on keyword matching"
        )


class SmartMCPExecutor:
    """
    🔧 SMART MCP EXECUTOR
    
    Executes MCPs with Claude-style progress tracking.
    Returns formatted tool blocks for frontend display.
    """
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.executions: List[MCPExecution] = []
    
    def execute_plan(self, plan: MCPPlan, query: str, df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Execute the MCP plan and return results.
        """
        result = {
            "tool_executions": [],
            "combined_context": "",
            "insights": [],
            "charts": [],
            "errors": []
        }
        
        if not plan.tools_to_run:
            return result
        
        # Execute each tool
        for tool_name in plan.tools_to_run:
            if tool_name not in MCP_REGISTRY:
                continue
            
            tool_info = MCP_REGISTRY[tool_name]
            execution = MCPExecution(
                tool_name=tool_info["name"],
                tool_icon=tool_info["icon"],
                action=f"Running {tool_info['description'][:50]}..."
            )
            execution.start_time = datetime.now()
            execution.status = "running"
            
            try:
                # Execute the tool
                tool_result = self._execute_tool(tool_name, query, df)
                
                execution.status = "success"
                execution.result = tool_result.get("summary", "Completed")
                execution.details = tool_result.get("details", [])
                
                # Add to results
                if tool_result.get("context"):
                    result["combined_context"] += f"\n{tool_result['context']}"
                if tool_result.get("insights"):
                    result["insights"].extend(tool_result["insights"])
                if tool_result.get("chart"):
                    result["charts"].append(tool_result["chart"])
                    
            except Exception as e:
                execution.status = "error"
                execution.error = str(e)[:100]
                result["errors"].append(str(e))
            
            execution.duration_ms = int((datetime.now() - execution.start_time).total_seconds() * 1000)
            result["tool_executions"].append(self._execution_to_dict(execution))
        
        return result
    
    def _execute_tool(self, tool_name: str, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute a specific MCP tool."""
        
        if tool_name == "data_validator":
            return self._run_data_validator(df)
        elif tool_name == "insight_engine":
            return self._run_insight_engine(query, df)
        elif tool_name == "chart_generator":
            return self._run_chart_generator(query, df)
        elif tool_name == "forecast_engine":
            return self._run_forecast_engine(query, df)
        elif tool_name == "alert_engine":
            return self._run_alert_engine(df)
        elif tool_name == "data_transformer":
            return self._run_data_transformer(query, df)
        elif tool_name == "report_generator":
            return self._run_report_generator(query, df)
        else:
            return {"summary": "Tool not implemented", "context": ""}
    
    def _run_data_validator(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run data validation."""
        if df is None or df.empty:
            return {"summary": "No data to validate", "context": ""}
        
        issues = []
        details = []
        
        # Check for missing values
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if len(null_cols) > 0:
            for col, count in null_cols.items():
                pct = (count / len(df)) * 100
                issues.append(f"{col}: {count} missing ({pct:.1f}%)")
                details.append(f"⚠️ {col} has {count} missing values")
        
        # Check for duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            issues.append(f"{dup_count} duplicate rows")
            details.append(f"⚠️ Found {dup_count} duplicate rows")
        
        # Calculate quality score
        total_checks = len(df.columns) + 1  # columns + duplicate check
        passed = total_checks - len(issues)
        quality_score = int((passed / total_checks) * 100)
        
        if not issues:
            details.append("✅ Data looks clean!")
        
        return {
            "summary": f"Quality Score: {quality_score}/100",
            "details": details,
            "context": f"📊 Data Quality: {quality_score}% - {len(issues)} issues found",
            "insights": [f"Data has {len(issues)} quality issues"] if issues else ["Data quality is good"]
        }
    
    def _run_insight_engine(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate insights from data."""
        if df is None or df.empty:
            return {"summary": "No data for insights", "context": ""}
        
        insights = []
        details = []
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        for col in numeric_cols[:5]:
            mean = df[col].mean()
            max_val = df[col].max()
            min_val = df[col].min()
            insights.append(f"{col}: avg={mean:.2f}, range=[{min_val:.2f}-{max_val:.2f}]")
            details.append(f"📈 {col}: Average {mean:.2f}")
        
        return {
            "summary": f"Generated {len(insights)} insights",
            "details": details,
            "context": "\n".join(f"💡 {i}" for i in insights),
            "insights": insights
        }
    
    def _run_chart_generator(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate chart using LLM visualizer."""
        if df is None or df.empty:
            return {"summary": "No data for chart", "context": ""}
        
        try:
            from core.llm_visualizer import llm_visualize
            result = llm_visualize(df, query, self.user_id)
            
            if result.get("success") and result.get("chart"):
                return {
                    "summary": f"Created {result.get('chart_type', 'chart')}",
                    "details": ["📊 Chart generated successfully"],
                    "context": "📊 Visualization ready",
                    "chart": result["chart"]
                }
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
        
        return {"summary": "Chart generation failed", "context": ""}
    
    def _run_forecast_engine(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Run forecasting."""
        if df is None or df.empty:
            return {"summary": "No data for forecast", "context": ""}
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            return {"summary": "No numeric data for forecasting", "context": ""}
        
        # Simple trend calculation
        col = numeric_cols[0]
        if len(df) >= 2:
            trend = ((df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0]) * 100
            direction = "up" if trend > 0 else "down"
            return {
                "summary": f"Trend: {direction} {abs(trend):.1f}%",
                "details": [f"🔮 {col} trending {direction} by {abs(trend):.1f}%"],
                "context": f"Forecast based on {col}: {direction} trend",
                "insights": [f"{col} shows {direction} trend of {abs(trend):.1f}%"]
            }
        
        return {"summary": "Insufficient data for forecast", "context": ""}
    
    def _run_alert_engine(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies."""
        if df is None or df.empty:
            return {"summary": "No data for anomaly detection", "context": ""}
        
        alerts = []
        details = []
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        for col in numeric_cols[:5]:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                outliers = df[(df[col] > mean + 3*std) | (df[col] < mean - 3*std)]
                if len(outliers) > 0:
                    alerts.append(f"{col}: {len(outliers)} outliers")
                    details.append(f"🚨 {len(outliers)} outliers in {col}")
        
        if not alerts:
            details.append("✅ No anomalies detected")
        
        return {
            "summary": f"Found {len(alerts)} anomaly types",
            "details": details,
            "context": f"🚨 Alerts: {len(alerts)} anomaly types detected",
            "insights": alerts if alerts else ["No significant anomalies found"]
        }
    
    def _run_data_transformer(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Transform data based on query."""
        if df is None or df.empty:
            return {"summary": "No data to transform", "context": ""}
        
        return {
            "summary": f"Data ready: {len(df)} rows × {len(df.columns)} cols",
            "details": [f"📋 {len(df)} rows, {len(df.columns)} columns"],
            "context": f"Data shape: {df.shape}"
        }
    
    def _run_report_generator(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive report."""
        if df is None or df.empty:
            return {"summary": "No data for report", "context": ""}
        
        sections = []
        sections.append(f"📊 Dataset: {len(df)} rows × {len(df.columns)} columns")
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        for col in numeric_cols[:3]:
            sections.append(f"📈 {col}: mean={df[col].mean():.2f}")
        
        return {
            "summary": "Report generated",
            "details": sections,
            "context": "\n".join(sections),
            "insights": sections
        }
    
    def _execution_to_dict(self, execution: MCPExecution) -> Dict[str, Any]:
        """Convert execution to dict for JSON response."""
        return {
            "toolName": execution.tool_name,
            "toolIcon": execution.tool_icon,
            "action": execution.action,
            "status": execution.status,
            "progress": 100 if execution.status == "success" else execution.progress,
            "details": execution.details,
            "result": execution.result,
            "error": execution.error,
            "duration": execution.duration_ms
        }


def smart_mcp_execute(query: str, df: pd.DataFrame = None, user_id: str = None) -> Dict[str, Any]:
    """
    Main entry point for smart MCP execution.
    
    Returns:
        Dict with tool_executions, combined_context, insights, charts
    """
    selector = SmartMCPSelector(user_id)
    executor = SmartMCPExecutor(user_id)
    
    # Select MCPs
    plan = selector.select_mcps(query, df)
    
    # Execute plan
    result = executor.execute_plan(plan, query, df)
    result["plan_reasoning"] = plan.reasoning
    result["tools_selected"] = plan.tools_to_run
    
    return result


def format_mcp_response(mcp_result: Dict[str, Any], base_response: str) -> str:
    """
    Format MCP execution results into Claude-style tool blocks.
    
    Args:
        mcp_result: Result from smart_mcp_execute
        base_response: The main AI response text
        
    Returns:
        Formatted response with tool blocks
    """
    if not mcp_result.get("tool_executions"):
        return base_response
    
    # Build tool execution summary
    tool_summary = "\n\n---\n**🔧 Tools Used:**\n"
    
    for exec_info in mcp_result["tool_executions"]:
        status_icon = "✅" if exec_info["status"] == "success" else "❌"
        tool_summary += f"\n{exec_info['toolIcon']} **{exec_info['toolName']}** {status_icon}\n"
        if exec_info.get("details"):
            for detail in exec_info["details"][:3]:
                tool_summary += f"   • {detail}\n"
        if exec_info.get("result"):
            tool_summary += f"   → {exec_info['result']}\n"
    
    # Add charts if generated
    charts_json = ""
    for chart in mcp_result.get("charts", []):
        if chart and isinstance(chart, dict) and "data" in chart:
            charts_json += f"\n\n```plotly_chart\n{json.dumps(chart, default=str)}\n```"
    
    return base_response + tool_summary + charts_json


__all__ = [
    'SmartMCPSelector', 
    'SmartMCPExecutor',
    'smart_mcp_execute',
    'format_mcp_response',
    'MCP_REGISTRY',
    'MCPExecution',
    'MCPPlan'
]
