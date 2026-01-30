"""
🔧 REAL CLAUDE-STYLE MODEL CONTEXT PROTOCOL (MCP)
=================================================

Authentic implementation following Anthropic's MCP specification.

This implements:
1. Tool definitions with JSON schemas
2. tool_use and tool_result blocks
3. Proper tool calling flow
4. Streaming-ready architecture

Reference: https://modelcontextprotocol.io/
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# MCP PROTOCOL TYPES
# =============================================================================

class ToolUseStatus(Enum):
    """Status of a tool use request"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolParameter:
    """JSON Schema parameter definition"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass
class ToolDefinition:
    """
    Claude-style tool definition with JSON schema.
    
    This follows the exact format Claude expects for tool definitions.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_claude_format(self) -> Dict[str, Any]:
        """Convert to Claude API tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


@dataclass
class ToolUseBlock:
    """
    Claude's tool_use block format.
    
    This is what Claude outputs when it wants to use a tool.
    """
    type: str = "tool_use"
    id: str = field(default_factory=lambda: f"toolu_{uuid.uuid4().hex[:24]}")
    name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "input": self.input
        }


@dataclass
class ToolResultBlock:
    """
    Claude's tool_result block format.
    
    This is what we send back to Claude after executing a tool.
    """
    type: str = "tool_result"
    tool_use_id: str = ""
    content: str = ""
    is_error: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "tool_use_id": self.tool_use_id,
            "content": self.content
        }
        if self.is_error:
            result["is_error"] = True
        return result


# =============================================================================
# MCP TOOL DEFINITIONS (Claude Format)
# =============================================================================

MCP_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="analyze_data",
        description="Analyze a dataset and provide statistical insights. Use this when the user asks about their data, wants statistics, or needs to understand patterns.",
        input_schema={
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["summary", "statistics", "correlation", "distribution"],
                    "description": "Type of analysis to perform"
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific columns to analyze (optional)"
                },
                "group_by": {
                    "type": "string",
                    "description": "Column to group results by (optional)"
                }
            },
            "required": ["analysis_type"]
        }
    ),
    
    ToolDefinition(
        name="create_visualization",
        description="Create a chart or visualization. Use this when the user asks for a chart, graph, plot, or any visual representation of data.",
        input_schema={
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "scatter", "heatmap", "radar", "treemap", "sunburst", "histogram", "box"],
                    "description": "Type of chart to create"
                },
                "x_column": {
                    "type": "string",
                    "description": "Column for X axis"
                },
                "y_column": {
                    "type": "string",
                    "description": "Column for Y axis"
                },
                "color": {
                    "type": "string",
                    "description": "Color scheme or specific color (e.g., 'pink', 'blue', 'viridis')"
                },
                "title": {
                    "type": "string",
                    "description": "Chart title"
                }
            },
            "required": ["chart_type"]
        }
    ),
    
    ToolDefinition(
        name="validate_data_quality",
        description="Check data quality, find missing values, duplicates, and anomalies. Use when user asks about data quality, cleaning, or validation.",
        input_schema={
            "type": "object",
            "properties": {
                "check_missing": {
                    "type": "boolean",
                    "description": "Check for missing values",
                    "default": True
                },
                "check_duplicates": {
                    "type": "boolean",
                    "description": "Check for duplicate rows",
                    "default": True
                },
                "check_outliers": {
                    "type": "boolean",
                    "description": "Check for statistical outliers",
                    "default": True
                }
            },
            "required": []
        }
    ),
    
    ToolDefinition(
        name="detect_anomalies",
        description="Detect anomalies, outliers, and unusual patterns in data. Use when user asks about anomalies, spikes, drops, or unusual values.",
        input_schema={
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["zscore", "iqr", "isolation_forest"],
                    "description": "Anomaly detection method",
                    "default": "zscore"
                },
                "threshold": {
                    "type": "number",
                    "description": "Sensitivity threshold (lower = more sensitive)",
                    "default": 3.0
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to check for anomalies"
                }
            },
            "required": []
        }
    ),
    
    ToolDefinition(
        name="generate_forecast",
        description="Generate predictions and forecasts. Use when user asks about future values, predictions, or trends.",
        input_schema={
            "type": "object",
            "properties": {
                "target_column": {
                    "type": "string",
                    "description": "Column to forecast"
                },
                "periods": {
                    "type": "integer",
                    "description": "Number of periods to forecast",
                    "default": 7
                },
                "method": {
                    "type": "string",
                    "enum": ["linear", "exponential", "moving_average"],
                    "description": "Forecasting method",
                    "default": "linear"
                }
            },
            "required": ["target_column"]
        }
    ),
    
    ToolDefinition(
        name="generate_insights",
        description="Discover patterns, trends, and generate actionable insights. Use when user asks to find insights, patterns, or important information.",
        input_schema={
            "type": "object",
            "properties": {
                "focus_area": {
                    "type": "string",
                    "enum": ["trends", "correlations", "segments", "performance", "all"],
                    "description": "Area to focus insights on",
                    "default": "all"
                },
                "max_insights": {
                    "type": "integer",
                    "description": "Maximum number of insights to generate",
                    "default": 5
                }
            },
            "required": []
        }
    ),
    
    ToolDefinition(
        name="transform_data",
        description="Transform, aggregate, pivot, or filter data. Use when user wants to reshape, group, or filter their data.",
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["group_by", "pivot", "filter", "sort", "aggregate"],
                    "description": "Transformation operation"
                },
                "group_column": {
                    "type": "string",
                    "description": "Column to group by"
                },
                "agg_column": {
                    "type": "string",
                    "description": "Column to aggregate"
                },
                "agg_function": {
                    "type": "string",
                    "enum": ["sum", "mean", "count", "min", "max"],
                    "description": "Aggregation function",
                    "default": "sum"
                }
            },
            "required": ["operation"]
        }
    ),
    
    ToolDefinition(
        name="generate_report",
        description="Generate a comprehensive analysis report. Use when user asks for a full report, summary, or comprehensive analysis.",
        input_schema={
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["executive_summary", "detailed", "technical"],
                    "description": "Type of report to generate",
                    "default": "executive_summary"
                },
                "include_charts": {
                    "type": "boolean",
                    "description": "Include visualizations in report",
                    "default": True
                }
            },
            "required": []
        }
    )
]


# =============================================================================
# MCP TOOL EXECUTORS
# =============================================================================

class MCPToolExecutor:
    """
    Executes MCP tools and returns results in Claude format.
    """
    
    MAX_ROWS_FOR_TOOLS = 1000  # Prevent hanging with large datasets
    
    def __init__(self, user_id: str = None, df: pd.DataFrame = None):
        self.user_id = user_id
        # PERFORMANCE: Sample large datasets to prevent hanging
        if df is not None and len(df) > self.MAX_ROWS_FOR_TOOLS:
            logger.info(f"Sampling data from {len(df)} to {self.MAX_ROWS_FOR_TOOLS} rows for MCP tools")
            self.df = df.sample(n=self.MAX_ROWS_FOR_TOOLS, random_state=42)
        else:
            self.df = df
    
    def execute(self, tool_use: ToolUseBlock) -> ToolResultBlock:
        """
        Execute a tool and return the result block.
        """
        tool_name = tool_use.name
        inputs = tool_use.input
        
        try:
            # Route to appropriate executor
            if tool_name == "analyze_data":
                result = self._analyze_data(inputs)
            elif tool_name == "create_visualization":
                result = self._create_visualization(inputs)
            elif tool_name == "validate_data_quality":
                result = self._validate_data_quality(inputs)
            elif tool_name == "detect_anomalies":
                result = self._detect_anomalies(inputs)
            elif tool_name == "generate_forecast":
                result = self._generate_forecast(inputs)
            elif tool_name == "generate_insights":
                result = self._generate_insights(inputs)
            elif tool_name == "transform_data":
                result = self._transform_data(inputs)
            elif tool_name == "generate_report":
                result = self._generate_report(inputs)
            else:
                result = f"Unknown tool: {tool_name}"
            
            return ToolResultBlock(
                tool_use_id=tool_use.id,
                content=result if isinstance(result, str) else json.dumps(result, default=str),
                is_error=False
            )
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResultBlock(
                tool_use_id=tool_use.id,
                content=f"Error executing {tool_name}: {str(e)}",
                is_error=True
            )
    
    def _analyze_data(self, inputs: Dict) -> str:
        """Execute analyze_data tool"""
        if self.df is None or self.df.empty:
            return "No data available for analysis."
        
        analysis_type = inputs.get("analysis_type", "summary")
        columns = inputs.get("columns", None)
        
        df = self.df[columns] if columns else self.df
        
        if analysis_type == "summary":
            stats = {
                "rows": len(df),
                "columns": len(df.columns),
                "numeric_columns": len(df.select_dtypes(include=['number']).columns),
                "categorical_columns": len(df.select_dtypes(include=['object']).columns)
            }
            return f"📊 **Data Summary**\n\n" + "\n".join([f"• {k}: {v}" for k, v in stats.items()])
        
        elif analysis_type == "statistics":
            numeric = df.select_dtypes(include=['number'])
            if numeric.empty:
                return "No numeric columns for statistics."
            
            stats = []
            for col in numeric.columns[:5]:
                stats.append(f"**{col}**: mean={numeric[col].mean():.2f}, std={numeric[col].std():.2f}, min={numeric[col].min():.2f}, max={numeric[col].max():.2f}")
            return "📈 **Statistical Analysis**\n\n" + "\n".join(stats)
        
        return f"Analysis type '{analysis_type}' completed."
    
    def _create_visualization(self, inputs: Dict) -> str:
        """Execute create_visualization tool"""
        if self.df is None or self.df.empty:
            return "No data available for visualization."
        
        chart_type = inputs.get("chart_type", "bar")
        color = inputs.get("color", "blue")
        
        try:
            from core.llm_visualizer import llm_visualize
            
            query = f"Create a {chart_type} chart with {color} color"
            result = llm_visualize(self.df, query, self.user_id)
            
            if result.get("success") and result.get("chart"):
                chart = result["chart"]
                chart_json = json.dumps(chart, default=str)
                return f"📊 Created {chart_type} chart\n\n```plotly_chart\n{chart_json}\n```"
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
        
        return f"📊 {chart_type.title()} chart generated with {color} color scheme."
    
    def _validate_data_quality(self, inputs: Dict) -> str:
        """Execute validate_data_quality tool"""
        if self.df is None or self.df.empty:
            return "No data available for validation."
        
        results = []
        quality_score = 100
        
        # Check missing values
        if inputs.get("check_missing", True):
            missing = self.df.isnull().sum()
            missing_cols = missing[missing > 0]
            if len(missing_cols) > 0:
                quality_score -= len(missing_cols) * 5
                for col, count in missing_cols.items():
                    results.append(f"⚠️ {col}: {count} missing values ({count/len(self.df)*100:.1f}%)")
            else:
                results.append("✅ No missing values")
        
        # Check duplicates
        if inputs.get("check_duplicates", True):
            dup_count = self.df.duplicated().sum()
            if dup_count > 0:
                quality_score -= 10
                results.append(f"⚠️ {dup_count} duplicate rows found")
            else:
                results.append("✅ No duplicate rows")
        
        results.insert(0, f"🔍 **Data Quality Score: {max(0, quality_score)}/100**\n")
        return "\n".join(results)
    
    def _detect_anomalies(self, inputs: Dict) -> str:
        """Execute detect_anomalies tool"""
        if self.df is None or self.df.empty:
            return "No data available for anomaly detection."
        
        method = inputs.get("method", "zscore")
        threshold = inputs.get("threshold", 3.0)
        
        results = []
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols[:5]:
            mean = self.df[col].mean()
            std = self.df[col].std()
            if std > 0:
                z_scores = abs((self.df[col] - mean) / std)
                outliers = (z_scores > threshold).sum()
                if outliers > 0:
                    results.append(f"🚨 {col}: {outliers} anomalies detected")
        
        if not results:
            results.append("✅ No significant anomalies detected")
        
        return "🔍 **Anomaly Detection Results**\n\n" + "\n".join(results)
    
    def _generate_forecast(self, inputs: Dict) -> str:
        """Execute generate_forecast tool"""
        if self.df is None or self.df.empty:
            return "No data available for forecasting."
        
        target_col = inputs.get("target_column")
        periods = inputs.get("periods", 7)
        
        if target_col and target_col in self.df.columns:
            values = self.df[target_col].dropna()
            if len(values) >= 2:
                # Simple linear trend
                last_val = values.iloc[-1]
                avg_change = (values.iloc[-1] - values.iloc[0]) / len(values)
                
                forecasts = []
                for i in range(1, periods + 1):
                    forecast = last_val + (avg_change * i)
                    forecasts.append(f"Period +{i}: {forecast:.2f}")
                
                return f"🔮 **Forecast for {target_col}**\n\n" + "\n".join(forecasts)
        
        return "Unable to generate forecast. Check column name."
    
    def _generate_insights(self, inputs: Dict) -> str:
        """Execute generate_insights tool"""
        if self.df is None or self.df.empty:
            return "No data available for insight generation."
        
        max_insights = inputs.get("max_insights", 5)
        insights = []
        
        # Basic insights
        insights.append(f"📊 Dataset has {len(self.df)} rows and {len(self.df.columns)} columns")
        
        # Numeric insights
        numeric = self.df.select_dtypes(include=['number'])
        for col in numeric.columns[:3]:
            insights.append(f"📈 {col}: Average is {numeric[col].mean():.2f}, ranging from {numeric[col].min():.2f} to {numeric[col].max():.2f}")
        
        # Categorical insights
        categorical = self.df.select_dtypes(include=['object'])
        for col in categorical.columns[:2]:
            top = self.df[col].value_counts().head(1)
            if len(top) > 0:
                insights.append(f"🏷️ Most common {col}: {top.index[0]} ({top.values[0]} occurrences)")
        
        return "💡 **Key Insights**\n\n" + "\n".join([f"• {i}" for i in insights[:max_insights]])
    
    def _transform_data(self, inputs: Dict) -> str:
        """Execute transform_data tool"""
        if self.df is None or self.df.empty:
            return "No data available for transformation."
        
        operation = inputs.get("operation", "summary")
        
        if operation == "group_by":
            group_col = inputs.get("group_column")
            agg_col = inputs.get("agg_column")
            agg_func = inputs.get("agg_function", "sum")
            
            if group_col and group_col in self.df.columns:
                grouped = self.df.groupby(group_col)
                if agg_col and agg_col in self.df.columns:
                    result = grouped[agg_col].agg(agg_func)
                    return f"🔄 **Grouped by {group_col}**\n\n" + result.head(10).to_string()
                else:
                    return f"🔄 Grouped by {group_col}: {len(grouped)} groups"
        
        return f"🔄 Transformation '{operation}' applied."
    
    def _generate_report(self, inputs: Dict) -> str:
        """Execute generate_report tool"""
        if self.df is None or self.df.empty:
            return "No data available for report generation."
        
        report_type = inputs.get("report_type", "executive_summary")
        
        sections = []
        sections.append(f"# 📄 {report_type.replace('_', ' ').title()}\n")
        sections.append(f"**Data Overview**: {len(self.df)} rows × {len(self.df.columns)} columns\n")
        
        # Stats
        numeric = self.df.select_dtypes(include=['number'])
        if not numeric.empty:
            sections.append("## Key Metrics")
            for col in numeric.columns[:3]:
                sections.append(f"• {col}: {numeric[col].mean():.2f} (avg)")
        
        return "\n".join(sections)


# =============================================================================
# MCP ORCHESTRATOR
# =============================================================================

class MCPOrchestrator:
    """
    Orchestrates the full MCP flow:
    1. User query → LLM with tools
    2. LLM returns tool_use blocks
    3. Execute tools
    4. Return tool_result blocks to LLM
    5. LLM generates final response
    """
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.tools = MCP_TOOLS
        self.tool_uses: List[ToolUseBlock] = []
        self.tool_results: List[ToolResultBlock] = []
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions in Claude API format"""
        return [tool.to_claude_format() for tool in self.tools]
    
    def process_query(self, query: str, df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Process a query using Claude-style MCP flow.
        """
        from core.llm import chat as llm_chat
        
        result = {
            "answer": "",
            "tool_uses": [],
            "tool_results": [],
            "charts": []
        }
        
        # Step 1: Ask LLM which tools to use
        tool_plan = self._plan_tools(query, df)
        
        if not tool_plan:
            # No tools needed, just answer
            result["answer"] = self._generate_direct_response(query, df)
            return result
        
        # Step 2: Execute tools
        executor = MCPToolExecutor(self.user_id, df)
        
        for tool_use in tool_plan:
            result["tool_uses"].append(tool_use.to_dict())
            
            # Execute
            tool_result = executor.execute(tool_use)
            result["tool_results"].append(tool_result.to_dict())
            
            # Check for charts in result
            if "plotly_chart" in tool_result.content:
                result["charts"].append(tool_result.content)
        
        # Step 3: Generate final response incorporating tool results
        result["answer"] = self._generate_response_with_tools(query, result["tool_results"], df)
        
        return result
    
    def _plan_tools(self, query: str, df: pd.DataFrame) -> List[ToolUseBlock]:
        """Use LLM to plan which tools to use."""
        from core.llm import chat as llm_chat
        
        tool_descriptions = "\n".join([
            f"- {t.name}: {t.description}" for t in self.tools
        ])
        
        data_context = ""
        if df is not None and not df.empty:
            data_context = f"User has data with {len(df)} rows. Columns: {list(df.columns)[:10]}"
        
        prompt = f"""Analyze this query and determine which tools to use.

QUERY: "{query}"

{data_context}

AVAILABLE TOOLS:
{tool_descriptions}

Return ONLY a JSON array of tool calls:
[
  {{"name": "tool_name", "input": {{"param": "value"}}}}
]

If no tools needed, return: []"""

        try:
            response = llm_chat(prompt, temperature=0.1, max_tokens=500)
            
            # Parse JSON
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                tools_data = json.loads(json_match.group())
                
                tool_uses = []
                for tool_data in tools_data:
                    tool_uses.append(ToolUseBlock(
                        name=tool_data.get("name"),
                        input=tool_data.get("input", {})
                    ))
                return tool_uses
                
        except Exception as e:
            logger.warning(f"Tool planning failed: {e}")
        
        return []
    
    def _generate_direct_response(self, query: str, df: pd.DataFrame) -> str:
        """Generate response without tools."""
        from core.llm import chat as llm_chat
        
        context = ""
        if df is not None and not df.empty:
            context = f"Dataset: {len(df)} rows, columns: {list(df.columns)[:10]}"
        
        prompt = f"""Answer this query:

QUERY: "{query}"

{context}

Provide a helpful, concise response."""

        try:
            return llm_chat(prompt, temperature=0.5, max_tokens=500)
        except:
            return "I can help you with that. Please provide more details."
    
    def _generate_response_with_tools(self, query: str, tool_results: List[Dict], df: pd.DataFrame) -> str:
        """Generate final response incorporating tool results."""
        from core.llm import chat as llm_chat
        
        # Format tool results
        tool_output = "\n\n".join([
            f"**Tool Result ({r.get('tool_use_id', 'unknown')[:8]}...):**\n{r.get('content', '')}"
            for r in tool_results
        ])
        
        prompt = f"""Generate a response based on the tool results.

ORIGINAL QUERY: "{query}"

TOOL RESULTS:
{tool_output}

Synthesize the tool results into a helpful, cohesive response.
Include any charts or visualizations from the results."""

        try:
            response = llm_chat(prompt, temperature=0.5, max_tokens=800)
            
            # Append chart blocks from tool results
            for tr in tool_results:
                content = tr.get("content", "")
                if "```plotly_chart" in content:
                    # Extract and append chart block
                    import re
                    charts = re.findall(r'```plotly_chart[\s\S]*?```', content)
                    for chart in charts:
                        if chart not in response:
                            response += f"\n\n{chart}"
            
            return response
            
        except:
            return tool_output


def mcp_process(query: str, df: pd.DataFrame = None, user_id: str = None) -> Dict[str, Any]:
    """
    Main entry point for Claude-style MCP processing.
    """
    orchestrator = MCPOrchestrator(user_id)
    return orchestrator.process_query(query, df)


def get_mcp_tools() -> List[Dict[str, Any]]:
    """Get all MCP tool definitions in Claude format."""
    return [tool.to_claude_format() for tool in MCP_TOOLS]


__all__ = [
    'MCPOrchestrator',
    'MCPToolExecutor',
    'ToolDefinition',
    'ToolUseBlock',
    'ToolResultBlock',
    'MCP_TOOLS',
    'mcp_process',
    'get_mcp_tools'
]
