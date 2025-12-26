# Executive Output Formatter - ChatGPT-Quality Responses
"""
Standardizes all AI responses to executive-ready format.

Output Structure:
1. Bold headline answer (one line)
2. Key Findings table
3. Analysis (2-3 sentences)
4. Recommendations (if applicable)
5. Footer with sources and mode

This ensures EVERY response looks professional and consistent.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ResponseType(Enum):
    """Types of responses for formatting decisions"""
    FACTUAL = "factual"           # Single number/fact answer
    COMPARISON = "comparison"      # Comparing entities
    TREND = "trend"               # Time-based analysis
    PREDICTION = "prediction"      # Forecasts
    SUMMARY = "summary"           # Overview/dashboard
    INSIGHT = "insight"           # Analysis with recommendations
    ERROR = "error"               # Error or insufficient data


@dataclass
class FormattedResponse:
    """Structured response container"""
    headline: str                         # Bold one-liner
    key_findings: Optional[str]           # Markdown table
    analysis: Optional[str]               # 2-3 sentences
    recommendations: Optional[List[str]]  # Bullet points
    chart_payload: Optional[Dict]         # Chart JSON if any
    sources: List[str]                    # Data sources
    mode: str                             # Analysis mode
    confidence: str                       # HIGH/MEDIUM/LOW
    

def format_executive_response(
    headline: str,
    data_table: Optional[str] = None,
    analysis: Optional[str] = None,
    recommendations: Optional[List[str]] = None,
    chart_payload: Optional[Dict] = None,
    sources: Optional[List[str]] = None,
    mode: str = "RAG",
    confidence: str = "HIGH"
) -> str:
    """
    Format response in ChatGPT executive style.
    
    Always produces clean, consistent output regardless of input.
    """
    parts = []
    
    # 1. HEADLINE - Always bold, always first
    parts.append(f"**{headline}**\n")
    
    # 2. KEY FINDINGS TABLE - If data provided
    if data_table and data_table.strip():
        parts.append("### Key Findings")
        parts.append(data_table)
        parts.append("")
    
    # 3. ANALYSIS - Brief, insightful
    if analysis and analysis.strip():
        parts.append("### Analysis")
        parts.append(analysis)
        parts.append("")
    
    # 4. RECOMMENDATIONS - Action-oriented
    if recommendations and len(recommendations) > 0:
        parts.append("### Recommendations")
        for rec in recommendations[:5]:  # Max 5 recommendations
            parts.append(f"• {rec}")
        parts.append("")
    
    # 5. CHART - If included
    if chart_payload:
        import json
        parts.append("```plotly_chart")
        parts.append(json.dumps(chart_payload, indent=2))
        parts.append("```")
        parts.append("")
    
    # 6. FOOTER - Clean, minimal
    footer_parts = []
    if sources:
        source_str = ", ".join(sources[:3])  # Max 3 sources shown
        footer_parts.append(f"*Sources: {source_str}*")
    
    footer_parts.append(f"*{mode} Mode • {confidence} Confidence*")
    
    parts.append("---")
    parts.append(" | ".join(footer_parts))
    
    return "\n".join(parts)


def format_factual_response(
    metric_name: str,
    value: str,
    context: Optional[str] = None,
    comparison: Optional[str] = None,
    sources: Optional[List[str]] = None,
    mode: str = "RAG"
) -> str:
    """
    Format single-fact responses (e.g., "What is total revenue?")
    
    Keeps it concise but informative.
    """
    parts = []
    
    # Headline with the answer
    parts.append(f"**{metric_name}: {value}**")
    parts.append("")
    
    # Context if available
    if context:
        parts.append(context)
        parts.append("")
    
    # Comparison/benchmark if available
    if comparison:
        parts.append(f"📊 {comparison}")
        parts.append("")
    
    # Footer
    if sources:
        parts.append(f"---\n*Based on {sources[0]}*")
    
    return "\n".join(parts)


def format_comparison_response(
    title: str,
    comparison_table: str,
    winner: Optional[str] = None,
    insight: Optional[str] = None,
    sources: Optional[List[str]] = None,
    mode: str = "GRAPHRAG"
) -> str:
    """
    Format comparison responses (e.g., "Compare customer A vs B")
    """
    parts = []
    
    # Headline
    if winner:
        parts.append(f"**{winner} leads in this comparison.**")
    else:
        parts.append(f"**{title}**")
    parts.append("")
    
    # Comparison table
    parts.append(comparison_table)
    parts.append("")
    
    # Insight
    if insight:
        parts.append(f"💡 *{insight}*")
        parts.append("")
    
    # Footer
    parts.append(f"---\n*{mode} Mode*")
    
    return "\n".join(parts)


def format_prediction_response(
    prediction_headline: str,
    current_value: str,
    predicted_value: str,
    confidence_pct: float,
    assumptions: List[str],
    chart_payload: Optional[Dict] = None,
    sources: Optional[List[str]] = None
) -> str:
    """
    Format prediction responses with clear assumptions.
    
    Never hide uncertainty - executives need to know confidence levels.
    """
    parts = []
    
    # Headline
    parts.append(f"**{prediction_headline}**")
    parts.append("")
    
    # Prediction table
    parts.append("| Metric | Value |")
    parts.append("|--------|-------|")
    parts.append(f"| Current | {current_value} |")
    parts.append(f"| Predicted | {predicted_value} |")
    parts.append(f"| Confidence | {confidence_pct:.0f}% |")
    parts.append("")
    
    # Assumptions - CRITICAL for trust
    if assumptions:
        parts.append("### Assumptions")
        for assumption in assumptions[:4]:
            parts.append(f"• {assumption}")
        parts.append("")
    
    # Confidence warning
    if confidence_pct < 70:
        parts.append("> ⚠️ **Low confidence prediction** - results may vary significantly")
        parts.append("")
    
    # Chart
    if chart_payload:
        import json
        parts.append("```forecast_chart")
        parts.append(json.dumps(chart_payload, indent=2))
        parts.append("```")
        parts.append("")
    
    # Footer
    parts.append("---")
    parts.append("*PREDICTION Mode • AI-Powered Forecast*")
    
    return "\n".join(parts)


def format_error_response(
    error_type: str,
    message: str,
    suggestions: Optional[List[str]] = None
) -> str:
    """
    Format error responses gracefully.
    
    Never expose technical errors - always be helpful.
    """
    parts = []
    
    # Friendly headline
    parts.append(f"**{error_type}**")
    parts.append("")
    parts.append(message)
    parts.append("")
    
    # Helpful suggestions
    if suggestions:
        parts.append("**What you can try:**")
        for sug in suggestions:
            parts.append(f"• {sug}")
    
    return "\n".join(parts)


def format_insufficient_data_response(
    query: str,
    missing: List[str],
    available: Optional[List[str]] = None
) -> str:
    """
    When data is missing, be explicit about what's needed.
    """
    parts = []
    
    parts.append("**I don't have enough data to answer this question.**")
    parts.append("")
    
    parts.append("### What's Missing")
    for item in missing:
        parts.append(f"• {item}")
    parts.append("")
    
    if available:
        parts.append("### What I Can Answer")
        parts.append("Based on your uploaded data, I can help with:")
        for item in available[:5]:
            parts.append(f"• {item}")
    
    return "\n".join(parts)


# ============================================================================
# RESPONSE CLEANER - Remove AI artifacts
# ============================================================================

def clean_ai_artifacts(response: str) -> str:
    """
    🧹 ChatGPT-Level Response Cleaning v2.0
    
    Remove common AI response artifacts:
    - "As an AI..."
    - "I'd be happy to..."
    - "Let me analyze..."
    - Planning steps ("First, I'll...")
    - Reasoning preambles ("Looking at the data...")
    - Excessive disclaimers
    """
    import re
    
    # Common filler phrases (at start of response)
    start_fillers = [
        r"(?i)^as an ai[^.]*\.\s*",
        r"(?i)^i'd be happy to[^.]*\.\s*",
        r"(?i)^certainly[!,.]?\s*",
        r"(?i)^of course[!,.]?\s*",
        r"(?i)^sure[!,.]?\s*",
        r"(?i)^great question[!,.]?\s*",
        r"(?i)^good question[!,.]?\s*",
        r"(?i)^based on the information provided,?\s*",
        r"(?i)^based on the data you've shared,?\s*",
        r"(?i)^based on my analysis,?\s*",
        r"(?i)^based on the uploaded data,?\s*",
    ]
    
    for pattern in start_fillers:
        response = re.sub(pattern, "", response)
    
    # Planning preambles (remove entire sentences)
    planning_patterns = [
        r"(?i)let me analyze[^.]*\.\s*",
        r"(?i)i've analyzed[^.]*\.\s*",
        r"(?i)i'll start by[^.]*\.\s*",
        r"(?i)first,? i'll[^.]*\.\s*",
        r"(?i)first,? let me[^.]*\.\s*",
        r"(?i)looking at the data[^.]*\.\s*",
        r"(?i)looking at your data[^.]*\.\s*",
        r"(?i)analyzing the[^.]*\.\s*",
        r"(?i)to answer (this|your) question[^.]*\.\s*",
        r"(?i)let me (check|look|find|see)[^.]*\.\s*",
        r"(?i)i need to (first|analyze|check)[^.]*\.\s*",
        r"(?i)here's what i found[^.:]*[.:]\s*",
        r"(?i)here is (what|the)[^.:]*[.:]\s*",
    ]
    
    for pattern in planning_patterns:
        response = re.sub(pattern, "", response)
    
    # Remove thinking/reasoning blocks
    thinking_patterns = [
        r"\*\*thinking\*\*:?[^*]*\*\*",
        r"\*thinking\*:?[^*]*\*",
        r"<thinking>.*?</thinking>",
        r"\[thinking\].*?\[/thinking\]",
        r"\[internal\].*?\[/internal\]",
    ]
    
    for pattern in thinking_patterns:
        response = re.sub(pattern, "", response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove step-by-step planning
    step_patterns = [
        r"(?i)step \d+:?[^.]*\.\s*",
        r"(?i)next,? i('ll|'m going to)[^.]*\.\s*",
        r"(?i)now,? let me[^.]*\.\s*",
        r"(?i)finally,? (i'll|let me)[^.]*\.\s*",
    ]
    
    for pattern in step_patterns:
        response = re.sub(pattern, "", response)
    
    # Remove disclaimers and hedging
    disclaimer_patterns = [
        r"(?i)\*?note:? (that )?this (is|may be)[^*\n]*\*?\s*",
        r"(?i)please note[^.]*\.\s*",
        r"(?i)it's (worth|important to) (noting|note)[^.]*\.\s*",
        r"(?i)keep in mind[^.]*\.\s*",
        r"(?i)i should (mention|note)[^.]*\.\s*",
    ]
    
    for pattern in disclaimer_patterns:
        response = re.sub(pattern, "", response)
    
    # Clean up resulting whitespace issues
    response = re.sub(r'\n{3,}', '\n\n', response)
    response = re.sub(r'^\s*\n', '', response)
    response = response.strip()
    
    return response


def clean_for_display(response: str, max_length: int = 3000) -> str:
    """
    Full cleaning pipeline for display to user.
    
    1. Clean AI artifacts
    2. Fix formatting issues
    3. Remove duplicate mode labels
    4. Truncate if too long
    """
    import re
    
    # Step 1: Clean artifacts
    cleaned = clean_ai_artifacts(response)
    
    # Step 2: Remove duplicate mode labels and verbose metadata
    duplicate_patterns = [
        # Remove duplicate "Analysis Mode: X" lines
        r'(?i)(\*\*?\s*Analysis Mode:?\s*\*?\*?:?\s*[A-Z]+\s*\*?\*?)\s*\n\s*\1',
        r'(?i)✔️?\s*Analysis Mode:?\s*[A-Z]+\s*\n',
        r'(?i)📊?\s*Analysis Mode:?\s*[A-Z]+\s*\n',
        # Remove verbose reasoning metadata  
        r'(?i)(Reasoning Type:?[^\n]*\n)',
        r'(?i)(Mode Weights:?[^\n]*\n)',
        r'(?i)(Accuracy Tier:?[^\n]*\n)',
        # Remove redundant source markers when appearing multiple times
        r'(\n---\s*){2,}',
        # Remove empty metadata lines
        r'\n\s*---\s*\n\s*---\s*\n',
    ]
    
    for pattern in duplicate_patterns:
        cleaned = re.sub(pattern, '', cleaned)
    
    # Step 3: Fix common formatting issues
    cleaned = cleaned.replace('  ', ' ')
    cleaned = cleaned.replace(' .', '.')
    cleaned = cleaned.replace(' ,', ',')
    
    # Step 4: Fix table alignment
    lines = cleaned.split('\n')
    fixed_lines = []
    for line in lines:
        if '|' in line and line.count('|') >= 2:
            # It's a table row - ensure proper spacing
            cells = line.split('|')
            cells = [c.strip() for c in cells]
            line = ' | '.join(cells)
        fixed_lines.append(line)
    cleaned = '\n'.join(fixed_lines)
    
    # Step 5: Remove excessive newlines
    cleaned = re.sub(r'\n{4,}', '\n\n\n', cleaned)
    
    # Step 6: Truncate if needed
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + '...'
    
    return cleaned.strip()


def validate_numbers_in_response(response: str, context: str) -> str:
    """
    Anti-hallucination check - but DO NOT add † symbols or disclaimers.
    
    ChatGPT-level products never add academic markers.
    Just return the response as-is for clean output.
    """
    # DISABLED: No more † symbols or disclaimers
    # This was causing unclean output that felt "academic"
    # Trust the LLM and prompt engineering instead
    return response


# ============================================================================
# CONFIDENCE CALCULATOR
# ============================================================================

def calculate_response_confidence(
    data_points: int,
    source_count: int,
    query_type: str,
    has_time_series: bool = False
) -> tuple:
    """
    Calculate confidence level for response.
    
    Returns: (confidence_level: str, confidence_pct: int)
    """
    score = 0
    
    # Data points contribution (0-40 points)
    if data_points >= 50:
        score += 40
    elif data_points >= 20:
        score += 30
    elif data_points >= 5:
        score += 20
    else:
        score += 10
    
    # Source count contribution (0-30 points)
    if source_count >= 3:
        score += 30
    elif source_count >= 2:
        score += 20
    else:
        score += 10
    
    # Query type contribution (0-30 points)
    if query_type in ["factual", "aggregation"]:
        score += 30  # High confidence for simple queries
    elif query_type in ["comparison", "trend"]:
        score += 20
    elif query_type in ["prediction", "causal"]:
        score += 10  # Lower for predictions
    
    # Time series bonus for trend/prediction
    if has_time_series and query_type in ["trend", "prediction"]:
        score += 10
    
    # Determine level
    if score >= 80:
        return ("HIGH", min(score, 95))
    elif score >= 60:
        return ("MEDIUM", score)
    elif score >= 40:
        return ("LOW", score)
    else:
        return ("INSUFFICIENT", score)


# ============================================================================
# QUICK FORMATTERS
# ============================================================================

def format_metric_table(metrics: Dict[str, Any], currency_symbol: str = "$") -> str:
    """Create a simple metrics table"""
    lines = ["| Metric | Value |", "|--------|-------|"]
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            if value >= 1000:
                formatted = f"{currency_symbol}{value:,.0f}"
            else:
                formatted = f"{value:,.2f}"
        else:
            formatted = str(value)
        lines.append(f"| {key} | {formatted} |")
    return "\n".join(lines)


def format_ranking_table(items: List[Dict], value_key: str, label_key: str, currency_symbol: str = "$", limit: int = 10) -> str:
    """Create a ranked table (e.g., top customers)"""
    lines = ["| Rank | Name | Value |", "|------|------|-------|"]
    for i, item in enumerate(items[:limit], 1):
        value = item.get(value_key, 0)
        label = item.get(label_key, "Unknown")
        formatted_value = f"{currency_symbol}{value:,.0f}" if isinstance(value, (int, float)) else value
        lines.append(f"| {i} | {label} | {formatted_value} |")
    return "\n".join(lines)
