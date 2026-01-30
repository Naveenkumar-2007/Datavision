# Mode Output Contracts - Strict Rules per Mode
"""
Defines output constraints for each mode to ensure consistent, professional responses.
ChatGPT quality comes from constraints, not freedom.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class OutputMode(Enum):
    """Available output modes"""
    RAG = "rag"
    GRAPHRAG = "graphrag"
    HYBRID = "hybrid"
    VISION = "vision"
    PREDICTION = "prediction"


@dataclass
class OutputContract:
    """Strict output rules for a mode"""
    mode: OutputMode
    max_tokens: int
    allow_tables: bool
    require_tables: bool  # Must include table for data queries
    allow_charts: bool
    max_sections: int
    allowed_sections: List[str]
    confidence_required: bool
    min_data_points_for_chart: int


# ============================================================================
# MODE CONTRACTS - Strict rules per mode
# ============================================================================

MODE_CONTRACTS = {
    OutputMode.RAG: OutputContract(
        mode=OutputMode.RAG,
        max_tokens=1200,
        allow_tables=True,
        require_tables=True,  # Data queries need tables
        allow_charts=True,
        max_sections=3,
        allowed_sections=["summary", "data_table", "sources"],
        confidence_required=True,
        min_data_points_for_chart=3,
    ),
    
    OutputMode.GRAPHRAG: OutputContract(
        mode=OutputMode.GRAPHRAG,
        max_tokens=1500,
        allow_tables=True,
        require_tables=True,
        allow_charts=True,
        max_sections=4,
        allowed_sections=["summary", "data_table", "graph_insights", "sources"],
        confidence_required=True,
        min_data_points_for_chart=3,
    ),
    
    OutputMode.HYBRID: OutputContract(
        mode=OutputMode.HYBRID,
        max_tokens=1500,
        allow_tables=True,
        require_tables=True,
        allow_charts=True,
        max_sections=4,
        allowed_sections=["summary", "data_table", "analysis", "sources"],
        confidence_required=True,
        min_data_points_for_chart=3,
    ),
    
    OutputMode.VISION: OutputContract(
        mode=OutputMode.VISION,
        max_tokens=1000,
        allow_tables=True,
        require_tables=False,  # Vision may not have tabular data
        allow_charts=False,  # Vision analyzes existing charts
        max_sections=3,
        allowed_sections=["summary", "findings", "interpretation"],
        confidence_required=True,
        min_data_points_for_chart=0,
    ),
    
    OutputMode.PREDICTION: OutputContract(
        mode=OutputMode.PREDICTION,
        max_tokens=1500,
        allow_tables=True,
        require_tables=True,
        allow_charts=True,
        max_sections=4,
        allowed_sections=["summary", "forecast_table", "trend_analysis", "confidence"],
        confidence_required=True,
        min_data_points_for_chart=5,  # Need more data for predictions
    ),
}


def get_contract(mode: str) -> OutputContract:
    """Get the output contract for a mode"""
    try:
        output_mode = OutputMode(mode.lower())
        return MODE_CONTRACTS.get(output_mode, MODE_CONTRACTS[OutputMode.RAG])
    except (ValueError, KeyError):
        return MODE_CONTRACTS[OutputMode.RAG]


def get_max_tokens(mode: str) -> int:
    """Get max tokens for a mode"""
    return get_contract(mode).max_tokens


def should_require_table(mode: str, query_type: str) -> bool:
    """Check if table is required for this query"""
    contract = get_contract(mode)
    
    # Data queries always need tables
    data_query_types = {"factual", "aggregation", "comparison", "list", "ranking"}
    if query_type.lower() in data_query_types:
        return contract.require_tables
    
    return False


def can_show_chart(mode: str, data_points: int) -> bool:
    """Check if chart is allowed for this mode with this data"""
    contract = get_contract(mode)
    
    if not contract.allow_charts:
        return False
    
    if data_points < contract.min_data_points_for_chart:
        return False
    
    return True


# ============================================================================
# CONFIDENCE SIGNALING
# ============================================================================

class ConfidenceLevel(Enum):
    """Confidence levels for responses"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


def get_confidence_prefix(level: ConfidenceLevel) -> str:
    """Get appropriate prefix for confidence level"""
    prefixes = {
        ConfidenceLevel.HIGH: "",  # No prefix needed for high confidence
        ConfidenceLevel.MEDIUM: "Based on available data, ",
        ConfidenceLevel.LOW: "With limited data available, ",
        ConfidenceLevel.INSUFFICIENT: "**Note: Insufficient data for a complete answer.** ",
    }
    return prefixes.get(level, "")


def get_confidence_suffix(level: ConfidenceLevel) -> str:
    """Get appropriate suffix/disclaimer for confidence level"""
    suffixes = {
        ConfidenceLevel.HIGH: "",
        ConfidenceLevel.MEDIUM: "\n\n*Analysis based on partial data.*",
        ConfidenceLevel.LOW: "\n\n*⚠️ Limited data available. Results may be incomplete.*",
        ConfidenceLevel.INSUFFICIENT: "\n\n*❌ Data is insufficient to provide a reliable answer. Please upload more data.*",
    }
    return suffixes.get(level, "")


def assess_data_confidence(
    data_points: int,
    sources_count: int,
    has_null_values: bool = False
) -> ConfidenceLevel:
    """Assess confidence level based on data quality"""
    
    # Insufficient data
    if data_points == 0 or sources_count == 0:
        return ConfidenceLevel.INSUFFICIENT
    
    # Low confidence
    if data_points < 3 or sources_count < 1:
        return ConfidenceLevel.LOW
    
    # Medium confidence (some issues)
    if has_null_values or data_points < 10:
        return ConfidenceLevel.MEDIUM
    
    # High confidence
    return ConfidenceLevel.HIGH


def format_confidence_response(
    answer: str,
    confidence: ConfidenceLevel
) -> str:
    """Format response with appropriate confidence signaling"""
    
    if confidence == ConfidenceLevel.HIGH:
        return answer  # No modification needed
    
    prefix = get_confidence_prefix(confidence)
    suffix = get_confidence_suffix(confidence)
    
    # Don't add prefix to bolded summary lines
    lines = answer.split('\n')
    if lines and lines[0].startswith('**'):
        # Insert prefix after first line
        lines.insert(1, f"\n{prefix.strip()}")
        return '\n'.join(lines) + suffix
    else:
        return prefix + answer + suffix
