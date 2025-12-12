# MCP Integration Layer
"""
Model Context Protocol (MCP) Integration for AI Business Analyst.

This module provides MCP-compatible tools for:
- Data cleaning and preprocessing
- Embedding generation
- Graph construction
- SQL execution
- Vision/OCR processing
- Forecasting engine (time-series prediction)
- Simulation engine (what-if scenarios)
- Insight engine (automated analysis)

Architecture:
- Internal Python modules (not external servers)
- Unified tool interface
- Async-ready design
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import json


class MCPToolType(Enum):
    """Types of MCP tools available"""
    DATA_CLEANER = "data_cleaner"
    VECTORIZER = "vectorizer"
    GRAPH_BUILDER = "graph_builder"
    SQL_EXECUTOR = "sql_executor"
    VISION_OCR = "vision_ocr"
    FORECAST_ENGINE = "forecast_engine"
    SIMULATION_ENGINE = "simulation_engine"
    INSIGHT_ENGINE = "insight_engine"
    PREDICTION_ENGINE = "prediction_engine"
    CHART_GENERATOR = "chart_generator"


@dataclass
class MCPToolResult:
    """Result from an MCP tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class MCPTool:
    """Definition of an MCP tool"""
    name: str
    description: str
    tool_type: MCPToolType
    parameters: Dict[str, Any]
    handler: Callable


class MCPRegistry:
    """
    Registry for MCP tools.
    
    Provides a unified interface for all MCP capabilities.
    """
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all MCP tools"""
        # Import tool handlers
        from mcp.data_cleaner import (
            clean_table,
            format_numbers,
            normalize_dates,
            deduplicate_rows
        )
        from mcp.vectorizer import (
            generate_embeddings,
            batch_embed,
            compute_similarity
        )
        from mcp.graph_builder import (
            extract_entities,
            build_graph_json,
            merge_graphs
        )
        from mcp.sql_executor import (
            execute_sql,
            create_table_from_df,
            query_to_dataframe
        )
        from mcp.vision_ocr import (
            extract_text_from_image,
            extract_tables_from_image,
            analyze_chart
        )
        from mcp.forecast_engine import (
            ForecastEngine,
            forecast_from_dataframe
        )
        from mcp.simulation_engine import (
            SimulationEngine,
            simulate_scenarios
        )
        from mcp.insight_engine import (
            InsightEngine,
            generate_insights
        )
        from mcp.prediction_engine import (
            PredictionEngine,
            predict_revenue,
            predict_sales,
            predict_churn,
            predict_demand
        )
        from mcp.chart_generator import (
            ChartGenerator,
            generate_forecast_chart,
            generate_scenario_chart
        )
        
        # Register Data Cleaner tools
        self._register_tool(MCPTool(
            name="clean_table",
            description="Clean and normalize tabular data",
            tool_type=MCPToolType.DATA_CLEANER,
            parameters={"data": "DataFrame or dict", "options": "CleaningOptions"},
            handler=clean_table
        ))
        
        self._register_tool(MCPTool(
            name="format_numbers",
            description="Format and standardize numeric columns",
            tool_type=MCPToolType.DATA_CLEANER,
            parameters={"data": "DataFrame", "columns": "List[str]", "format": "str"},
            handler=format_numbers
        ))
        
        self._register_tool(MCPTool(
            name="normalize_dates",
            description="Normalize date formats across data",
            tool_type=MCPToolType.DATA_CLEANER,
            parameters={"data": "DataFrame", "date_columns": "List[str]"},
            handler=normalize_dates
        ))
        
        self._register_tool(MCPTool(
            name="deduplicate_rows",
            description="Remove duplicate rows from data",
            tool_type=MCPToolType.DATA_CLEANER,
            parameters={"data": "DataFrame", "subset": "Optional[List[str]]"},
            handler=deduplicate_rows
        ))
        
        # Register Vectorizer tools
        self._register_tool(MCPTool(
            name="generate_embeddings",
            description="Generate embeddings for text",
            tool_type=MCPToolType.VECTORIZER,
            parameters={"text": "str"},
            handler=generate_embeddings
        ))
        
        self._register_tool(MCPTool(
            name="batch_embed",
            description="Generate embeddings for multiple texts",
            tool_type=MCPToolType.VECTORIZER,
            parameters={"texts": "List[str]", "batch_size": "int"},
            handler=batch_embed
        ))
        
        self._register_tool(MCPTool(
            name="compute_similarity",
            description="Compute similarity between embeddings",
            tool_type=MCPToolType.VECTORIZER,
            parameters={"embedding1": "List[float]", "embedding2": "List[float]"},
            handler=compute_similarity
        ))
        
        # Register Graph Builder tools
        self._register_tool(MCPTool(
            name="extract_entities",
            description="Extract entities from text or data",
            tool_type=MCPToolType.GRAPH_BUILDER,
            parameters={"data": "Any", "entity_types": "List[str]"},
            handler=extract_entities
        ))
        
        self._register_tool(MCPTool(
            name="build_graph_json",
            description="Build graph structure from entities",
            tool_type=MCPToolType.GRAPH_BUILDER,
            parameters={"entities": "List[Dict]", "relations": "List[Dict]"},
            handler=build_graph_json
        ))
        
        self._register_tool(MCPTool(
            name="merge_graphs",
            description="Merge multiple graphs into one",
            tool_type=MCPToolType.GRAPH_BUILDER,
            parameters={"graphs": "List[Dict]"},
            handler=merge_graphs
        ))
        
        # Register SQL Executor tools
        self._register_tool(MCPTool(
            name="execute_sql",
            description="Execute SQL query on data",
            tool_type=MCPToolType.SQL_EXECUTOR,
            parameters={"query": "str", "data": "Dict[str, DataFrame]"},
            handler=execute_sql
        ))
        
        self._register_tool(MCPTool(
            name="create_table_from_df",
            description="Create virtual table from DataFrame",
            tool_type=MCPToolType.SQL_EXECUTOR,
            parameters={"name": "str", "df": "DataFrame"},
            handler=create_table_from_df
        ))
        
        self._register_tool(MCPTool(
            name="query_to_dataframe",
            description="Execute query and return DataFrame",
            tool_type=MCPToolType.SQL_EXECUTOR,
            parameters={"query": "str"},
            handler=query_to_dataframe
        ))
        
        # Register Vision/OCR tools
        self._register_tool(MCPTool(
            name="extract_text_from_image",
            description="Extract text from image using OCR",
            tool_type=MCPToolType.VISION_OCR,
            parameters={"image_path": "str"},
            handler=extract_text_from_image
        ))
        
        self._register_tool(MCPTool(
            name="extract_tables_from_image",
            description="Extract tables from image",
            tool_type=MCPToolType.VISION_OCR,
            parameters={"image_path": "str"},
            handler=extract_tables_from_image
        ))
        
        self._register_tool(MCPTool(
            name="analyze_chart",
            description="Analyze chart image and extract data",
            tool_type=MCPToolType.VISION_OCR,
            parameters={"image_path": "str", "chart_type": "Optional[str]"},
            handler=analyze_chart
        ))
        
        # Register Forecast Engine tools
        forecast_engine = ForecastEngine()
        self._register_tool(MCPTool(
            name="forecast_timeseries",
            description="Generate time-series forecast with confidence intervals",
            tool_type=MCPToolType.FORECAST_ENGINE,
            parameters={"data": "List[Dict]", "periods": "int", "confidence": "float"},
            handler=forecast_engine.forecast
        ))
        
        self._register_tool(MCPTool(
            name="forecast_from_dataframe",
            description="Generate forecast from pandas DataFrame",
            tool_type=MCPToolType.FORECAST_ENGINE,
            parameters={"df": "DataFrame", "date_col": "str", "value_col": "str", "periods": "int"},
            handler=forecast_from_dataframe
        ))
        
        # Register Simulation Engine tools
        simulation_engine = SimulationEngine()
        self._register_tool(MCPTool(
            name="simulate_scenarios",
            description="Run what-if business scenarios (price, marketing, churn)",
            tool_type=MCPToolType.SIMULATION_ENGINE,
            parameters={"base_revenue": "float", "base_customers": "int", "modifiers": "Dict"},
            handler=simulate_scenarios
        ))
        
        self._register_tool(MCPTool(
            name="simulate_pricing",
            description="Simulate price change impact on revenue",
            tool_type=MCPToolType.SIMULATION_ENGINE,
            parameters={"base_revenue": "float", "price_change_pct": "List[float]"},
            handler=simulation_engine.simulate
        ))
        
        self._register_tool(MCPTool(
            name="monte_carlo",
            description="Run Monte Carlo simulation for revenue prediction",
            tool_type=MCPToolType.SIMULATION_ENGINE,
            parameters={"base_revenue": "float", "uncertainty": "float", "simulations": "int"},
            handler=simulation_engine.run_monte_carlo
        ))
        
        # Register Insight Engine tools
        insight_engine = InsightEngine()
        self._register_tool(MCPTool(
            name="generate_insights",
            description="Generate automated business insights from metrics",
            tool_type=MCPToolType.INSIGHT_ENGINE,
            parameters={"revenue": "float", "customers": "int", "churn_rate": "float"},
            handler=generate_insights
        ))
        
        self._register_tool(MCPTool(
            name="analyze_business",
            description="Full business analysis with trends, risks, and opportunities",
            tool_type=MCPToolType.INSIGHT_ENGINE,
            parameters={"revenue": "float", "revenue_previous": "float", "customers": "int", "orders": "int"},
            handler=insight_engine.analyze
        ))
    
    def _register_tool(self, tool: MCPTool):
        """Register a tool in the registry"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self, tool_type: Optional[MCPToolType] = None) -> List[MCPTool]:
        """List all tools, optionally filtered by type"""
        if tool_type:
            return [t for t in self._tools.values() if t.tool_type == tool_type]
        return list(self._tools.values())
    
    def execute(self, tool_name: str, **kwargs) -> MCPToolResult:
        """Execute a tool by name with given parameters"""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        try:
            result = tool.handler(**kwargs)
            return MCPToolResult(
                success=True,
                data=result,
                metadata={"tool": tool_name}
            )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"tool": tool_name}
            )
    
    def get_schema(self) -> Dict:
        """Get MCP-compatible schema for all tools"""
        schema = {
            "tools": []
        }
        
        for tool in self._tools.values():
            tool_schema = {
                "name": tool.name,
                "description": tool.description,
                "type": tool.tool_type.value,
                "parameters": tool.parameters
            }
            schema["tools"].append(tool_schema)
        
        return schema


# Lazy singleton
_registry = None

def get_mcp_registry() -> MCPRegistry:
    """Get or create the MCP registry singleton"""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
    return _registry


def execute_mcp_tool(tool_name: str, **kwargs) -> MCPToolResult:
    """Convenience function to execute an MCP tool"""
    registry = get_mcp_registry()
    return registry.execute(tool_name, **kwargs)
