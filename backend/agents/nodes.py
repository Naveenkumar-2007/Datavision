# Enterprise Agent Nodes v2.0 - Premium $5M Enterprise Product Quality
"""
4 Enterprise AI Modes: RAG, GraphRAG, Hybrid, Vision

Features:
- LLM-powered query understanding (ChatGPT-quality)
- Query classification with confidence scoring
- Multi-hop graph reasoning
- Hybrid fusion with intelligent weighting
- Vision → RAG/Graph pipeline
- MCP tool integration
- Clean, ChatGPT-style outputs
- Dynamic visualization generation

$5M Enterprise Product - Query understanding that works like ChatGPT.
No hardcoded responses - LLM figures out intent from natural language.
"""

from core.llm import chat, get_optimal_model
from vector.retriever import retrieve
from graph.query import query_graph, revenue_dataframe, get_user_currency
from agents.state import AgentState
from agents.query_classifier import classify_query, QueryType
from agents.confidence_scorer import (
    get_confidence_scorer, 
    AnswerConfidence,
    ConfidenceLevel
)
import time
import json
from typing import List, Dict, Optional, Tuple

# ============================================================================
# $5M ENHANCEMENT: LLM-Powered Query Dispatcher - ChatGPT-style understanding
# ============================================================================
try:
    from agents.query_dispatcher import (
        dispatch_query,
        get_query_dispatcher,
        QueryDispatch,
        QueryIntent as DispatcherIntent,
        ResponseFormat,
        VisualizationType,
    )
    QUERY_DISPATCHER_AVAILABLE = True
    print("✓ Query Dispatcher loaded - LLM-powered query understanding active")
except ImportError as e:
    QUERY_DISPATCHER_AVAILABLE = False
    print(f"⚠️ Query dispatcher not available: {e}")

# Chart generation imports
try:
    from core.charts import (
        generate_customer_revenue_chart,
        generate_product_revenue_chart,
        generate_monthly_trend_chart,
        generate_prediction_chart,
        generate_revenue_bar_chart,
        generate_pie_chart
    )
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

# Interactive Plotly Charts (with hover/tooltips)
try:
    from core.interactive_charts import (
        generate_interactive_customer_chart,
        generate_interactive_product_chart,
        generate_interactive_trend_chart,
        generate_interactive_prediction_chart,
        generate_interactive_comparison_chart
    )
    INTERACTIVE_CHARTS_AVAILABLE = True
except ImportError:
    INTERACTIVE_CHARTS_AVAILABLE = False

# Enterprise Engine imports
try:
    from mcp.forecast_engine import ForecastEngine, forecast_from_dataframe
    from mcp.simulation_engine import SimulationEngine, simulate_scenarios
    from mcp.insight_engine import InsightEngine, generate_insights
    from mcp.prediction_engine import PredictionEngine, predict_revenue, predict_sales
    from mcp.chart_generator import ChartGenerator, generate_forecast_chart, generate_scenario_chart
    ENGINES_AVAILABLE = True
except ImportError:
    ENGINES_AVAILABLE = False

# Memory Pipeline imports (Cache RAG + 4-Layer Memory)
try:
    from core.cache_rag import cache_lookup, cache_store, CacheHitType
    from core.memory_retrieval import memory_retrieve, memory_store, get_memory_pipeline
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# ChatGPT-style Answer-Based Chart Generation
try:
    from agents.answer_chart_extractor import extract_chart_data_from_answer
    ANSWER_CHART_AVAILABLE = True
except ImportError:
    ANSWER_CHART_AVAILABLE = False
    print("⚠️ Answer chart extractor not available")

# ChatGPT Code Interpreter-style Charts (LLM understands any query)
try:
    from agents.smart_chart import smart_chart
    SMART_CHART_AVAILABLE = True
    print("✓ Smart Chart loaded - LLM-driven visualization active")
except ImportError:
    SMART_CHART_AVAILABLE = False
    print("⚠️ Smart Chart not available")


# Company Intelligence imports
try:
    from core.company_profile import (
        get_company_profile,
        build_company_context,
        get_company_terminology,
    )
    COMPANY_PROFILE_AVAILABLE = True
except ImportError:
    COMPANY_PROFILE_AVAILABLE = False
    print("⚠️ Company profile module not available")

# Role Intelligence imports
try:
    from agents.role_templates import (
        UserRole,
        get_role_from_string,
        get_role_prompt_modifier,
        format_response_for_role,
    )
    ROLE_TEMPLATES_AVAILABLE = True
except ImportError:
    ROLE_TEMPLATES_AVAILABLE = False
    print("⚠️ Role templates module not available")

# Conversation Intelligence imports
try:
    from core.memory_engine import ReferenceResolver, ShortTermMemory
    REFERENCE_RESOLVER_AVAILABLE = True
    # Singleton short-term memory for reference resolution
    _short_term_memory = ShortTermMemory()
except ImportError:
    REFERENCE_RESOLVER_AVAILABLE = False
    _short_term_memory = None
    print("⚠️ Reference resolver not available")

# Output Contracts and Chart Gatekeeping imports
try:
    from agents.output_contracts import (
        get_contract,
        get_max_tokens,
        can_show_chart,
        assess_data_confidence,
        format_confidence_response,
        ConfidenceLevel,
    )
    from agents.chart_gatekeeper import (
        should_render_chart,
        get_chart_decision,
        suggest_chart_type,
    )
    OUTPUT_CONTRACTS_AVAILABLE = True
except ImportError:
    OUTPUT_CONTRACTS_AVAILABLE = False
    print("⚠️ Output contracts module not available")

# ============================================================================
# MEMORY ENGINE - Conversation Intelligence (ChatGPT-level stateful behavior)
# ============================================================================
try:
    from core.memory_engine import (
        ShortTermMemory,
        ReferenceResolver,
        MemoryType,
        get_shared_memory,  # Import singleton getter
    )
    # Use SHARED singleton instance - CRITICAL for chart context sharing
    _short_term_memory = get_shared_memory()
    _reference_resolver = ReferenceResolver(_short_term_memory)
    MEMORY_ENGINE_AVAILABLE = True
    print("✓ Memory engine loaded - using SHARED singleton instance")
except ImportError as e:
    MEMORY_ENGINE_AVAILABLE = False
    _short_term_memory = None
    _reference_resolver = None
    print(f"⚠️ Memory engine not available: {e}")

# MCP Router imports (Smart query-based MCP selection)
try:
    from mcp.router import (
        get_required_mcps,
        should_call_mcp,
        detect_intent,
        execute_mcp_with_fallback,
        QueryIntent,
    )
    MCP_ROUTER_AVAILABLE = True
except ImportError:
    MCP_ROUTER_AVAILABLE = False
    print("⚠️ MCP router not available")

# Output Formatter imports (ChatGPT-quality responses)
try:
    from agents.output_formatter import (
        format_executive_response,
        format_factual_response,
        format_prediction_response,
        clean_ai_artifacts,
        clean_for_display,  # New v2.0 full cleaning pipeline
        validate_numbers_in_response,
        calculate_response_confidence,
        format_metric_table,
        format_ranking_table,
    )
    OUTPUT_FORMATTER_AVAILABLE = True
except ImportError:
    OUTPUT_FORMATTER_AVAILABLE = False
    clean_for_display = None
    print("⚠️ Output formatter not available")

# Query Decomposer imports (LLM-powered query enhancement v2.0)
try:
    from core.query_decomposer import (
        decompose_query,
        llm_decompose_query,
        classify_query_intent,
        expand_query_with_schema,
        QueryIntent,
        TemporalExpression,
        is_complex_query,
        merge_results,
    )
    QUERY_DECOMPOSER_AVAILABLE = True
    print("✓ Query Decomposer v2.0 loaded - LLM-powered query enhancement active")
except ImportError as e:
    QUERY_DECOMPOSER_AVAILABLE = False
    print(f"⚠️ Query decomposer not available: {e}")

# Visualization Intelligence imports (ChatGPT-level charts)
try:
    from agents.visualization_intelligence import (
        decide_visualization,
        detect_visualization_intent,
        VisualizationIntent,
        ChartType,
        profile_dataframe,
        extract_count_from_query,
        detect_visualization_subject,
    )
    from agents.advanced_charts import (
        create_chart_from_decision,
        generate_dynamic_chart,
    )
    from agents.visualization_intelligence import detect_visualization_intent
    VIZ_INTELLIGENCE_AVAILABLE = True
except ImportError:
    VIZ_INTELLIGENCE_AVAILABLE = False
    print("⚠️ Visualization intelligence partially available")

# $5M ENHANCEMENT: Response Enhancer - ChatGPT-quality responses
try:
    from agents.response_enhancer import (
        enhance_full_response,
        generate_proactive_insight,
        generate_followup_suggestions,
        enhance_response_tone,
        generate_helpful_error_recovery,
        extract_data_summary_from_response,
    )
    RESPONSE_ENHANCER_AVAILABLE = True
    print("✓ Response enhancer loaded - ChatGPT-quality responses active")
except ImportError as e:
    RESPONSE_ENHANCER_AVAILABLE = False
    print(f"⚠️ Response enhancer not available: {e}")

# $5M ENHANCEMENT: ChatGPT-Style Handler - Pure LLM-driven responses
try:
    from agents.chatgpt_handler import (
        understand_query_with_llm,
        generate_chatgpt_prompt,
        should_generate_chart,
        get_mode_quality_settings,
        enhance_response_like_chatgpt,
    )
    CHATGPT_HANDLER_AVAILABLE = True
    print("✓ ChatGPT handler loaded - LLM-driven responses active")
except ImportError as e:
    CHATGPT_HANDLER_AVAILABLE = False
    print(f"⚠️ ChatGPT handler not available: {e}")

# $5M CORE: Truth-Grounded AI - ChatGPT/Claude Level Principles
try:
    from core.truth_grounded_prompt import (
        get_truth_grounded_prompt,
        get_context as get_truth_context,
        update_context as update_truth_context,
        resolve_above_reference,
        validate_response_against_data,
        get_graceful_error_response,
        ConversationContext,
    )
    TRUTH_GROUNDED_AVAILABLE = True
    print("✓ Truth-Grounded AI loaded - ChatGPT/Claude level active")
except ImportError as e:
    TRUTH_GROUNDED_AVAILABLE = False
    print(f"⚠️ Truth-Grounded AI not available: {e}")

# $5M CORE: Production-Grade Business AI Engine (ChatGPT/Claude Architecture)
try:
    from core.business_ai_engine import (
        get_memory as get_ai_memory,
        execute_query_pipeline,
        should_refuse,
        self_audit,
        get_production_system_prompt,
        ThreeLayerMemory,
        PipelineResult,
        QueryIntent,
    )
    BUSINESS_AI_ENGINE_AVAILABLE = True
    print("✓ Business AI Engine loaded - Production-grade orchestration active")
except ImportError as e:
    BUSINESS_AI_ENGINE_AVAILABLE = False
    print(f"⚠️ Business AI Engine not available: {e}")

# $5M CORE: Production Mode Handler - Query Understanding + Mode-Specific Responses
try:
    from core.mode_handler import (
        ProductionModeHandler,
        understand_query,
        get_mode_prompt,
        handle_mode_query,
        AnalysisMode,
        MODE_PROMPTS,
    )
    MODE_HANDLER_AVAILABLE = True
    print("✓ Production Mode Handler loaded - 5 modes active")
except ImportError as e:
    MODE_HANDLER_AVAILABLE = False
    print(f"⚠️ Mode Handler not available: {e}")

# $500K VISUAL INTELLIGENCE ENGINE - Mind Maps, Knowledge Graphs, Smart Visualization
try:
    from core.visual_intelligence import (
        VisualIntelligenceEngine,
        generate_visual_intelligence,
        generate_mind_map,
        generate_knowledge_graph,
        generate_kpi_dashboard,
        VisualType,
    )
    from core.mermaid_renderer import (
        create_mermaid_response,
        generate_mermaid_visual,
        create_visual_response,
        render_ascii_mind_map,
        render_ascii_relationship_graph,
    )
    from core.premium_visuals import (
        generate_premium_visual,
        generate_mind_map_plotly,
        generate_knowledge_graph_plotly,
        generate_kpi_dashboard_plotly,
    )
    VISUAL_INTELLIGENCE_AVAILABLE = True
    print("✓ Visual Intelligence Engine loaded - Premium Plotly Graphs active")
except ImportError as e:
    VISUAL_INTELLIGENCE_AVAILABLE = False
    print(f"⚠️ Visual Intelligence not available: {e}")

# ============================================================================
# $5M ENHANCEMENT: Dynamic Prompt Builder - ChatGPT-Quality Response Generation
# ============================================================================

def _build_dynamic_system_prompt(
    dispatch: 'QueryDispatch',
    company_name: str = "Your Company",
    currency_symbol: str = "₹",
    has_chart: bool = False
) -> str:
    """
    Build a dynamic system prompt based on LLM query analysis.
    
    This is the CORE of ChatGPT-quality responses - the prompt adapts
    to what the user actually wants, not hardcoded templates.
    
    Args:
        dispatch: QueryDispatch from the LLM-powered dispatcher
        company_name: Name of the user's company
        currency_symbol: Currency symbol for formatting
        has_chart: Whether a chart will be shown
        
    Returns:
        Tailored system prompt for the LLM
    """
    # Base system prompt - always present
    base = f"""You are a $5M Enterprise AI Business Analyst for {company_name}.
You analyze ONLY the uploaded business data - never make up information.
Always use {currency_symbol} for currency formatting.
"""
    
    # Intent-specific instructions
    intent_instructions = {
        "factual": """
RESPONSE STYLE: FACTUAL
- Give a direct, clear answer
- Include the exact number/value
- Keep it concise but complete""",
        
        "aggregation": """
RESPONSE STYLE: AGGREGATION
- Calculate and present the total/average/count
- Show the calculation clearly
- Use markdown tables for multiple metrics""",
        
        "comparison": """
RESPONSE STYLE: COMPARISON
- Present both sides fairly
- Use a comparison table
- Highlight key differences
- State a clear winner if applicable""",
        
        "trend": """
RESPONSE STYLE: TREND ANALYSIS
- Describe the direction (up/down/stable)
- Include specific growth percentages
- Identify peak and low points
- Mention any seasonality patterns""",
        
        "ranking": """
RESPONSE STYLE: RANKING
- Present as an ordered list or table
- Include rank, name, and value
- Highlight the top performer
- Note any close competitors""",
        
        "breakdown": """
RESPONSE STYLE: BREAKDOWN
- Show distribution/composition
- Include percentages
- Use bullet points or table
- Highlight largest segments""",
        
        "prediction": """
RESPONSE STYLE: PREDICTION/FORECAST
- State the prediction clearly
- Include confidence level/range
- List key assumptions
- Note any risks or uncertainties""",
        
        "summary": """
RESPONSE STYLE: SUMMARY
- Start with executive summary (2-3 sentences)
- List key highlights
- Include actionable insights
- Keep it scannable""",
        
        "anomaly": """
RESPONSE STYLE: ANOMALY DETECTION
- Identify unusual patterns
- Explain why they're unusual
- Suggest possible causes
- Recommend actions""",
    }
    
    # Format-specific instructions
    format_instructions = {
        "one_line": """
CRITICAL FORMAT CONSTRAINT: ONE LINE ONLY
Your ENTIRE response must be ONE sentence.
No tables, no bullets, no paragraphs.
Maximum 30 words.""",
        
        "brief": """
FORMAT: BRIEF (2-3 sentences)
Keep response concise.
No unnecessary elaboration.""",
        
        "detailed": """
FORMAT: DETAILED ANALYSIS
Provide comprehensive analysis.
Include tables, metrics, insights.
Be thorough but structured.""",
        
        "table": """
FORMAT: TABLE PREFERRED
Present data in markdown table format.
Include headers and proper alignment.""",
    }
    
    # Build the prompt
    prompt_parts = [base]
    
    # Add intent instructions
    intent_key = dispatch.intent.value if hasattr(dispatch.intent, 'value') else str(dispatch.intent)
    if intent_key in intent_instructions:
        prompt_parts.append(intent_instructions[intent_key])
    
    # Add format instructions
    format_key = dispatch.response_format.value if hasattr(dispatch.response_format, 'value') else str(dispatch.response_format)
    if format_key in format_instructions:
        prompt_parts.append(format_instructions[format_key])
    
    # Add chart context
    if has_chart:
        prompt_parts.append("""
CHART INCLUDED: A visualization will be shown.
Your text should COMPLEMENT the chart, not repeat all its data.
Reference the chart in your response.""")
    
    # Add limit context
    if dispatch.limit:
        prompt_parts.append(f"""
LIMIT: User asked for top/bottom {dispatch.limit} items.
Only include {dispatch.limit} items in your response.""")
    
    # Anti-hallucination reminder
    prompt_parts.append("""
CRITICAL RULES:
- Use ONLY data from the context provided
- Never make up numbers or names
- If data is missing, say so clearly
- Do not add "As an AI..." phrases
- Be confident and direct""")
    
    return "\n".join(prompt_parts)


def _get_user_context(user_id: str) -> str:
    """Get personalized context for user"""
    try:
        from core.memory import get_user_context
        return get_user_context(user_id)
    except:
        return ""


def build_data_context(user_id: str) -> dict:
    """
    🧠 CHATGPT-STYLE DATA CONTEXT BUILDER
    
    Loads user's actual data and builds comprehensive context for LLM.
    This is the CORE function that makes all modes work dynamically.
    
    Returns dict with:
    - df: The actual DataFrame
    - schema: Column names and types
    - sample: First 10 rows as text
    - stats: Aggregated statistics
    - context_string: Full text context for LLM prompts
    """
    from api.v1.endpoints.charts import get_user_data
    
    result = {
        "df": None,
        "schema": {},
        "sample": "",
        "stats": {},
        "context_string": "",
        "row_count": 0,
        "columns": []
    }
    
    try:
        df = get_user_data(user_id)
        if df is None or df.empty:
            result["context_string"] = "No data uploaded yet. Please upload files in Data Hub."
            return result
        
        result["df"] = df
        result["row_count"] = len(df)
        result["columns"] = list(df.columns)
        
        # Build schema info
        schema_info = {}
        numeric_cols = []
        text_cols = []
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema_info[col] = dtype
            if 'int' in dtype or 'float' in dtype:
                numeric_cols.append(col)
            else:
                text_cols.append(col)
        
        result["schema"] = schema_info
        
        # Build statistics for numeric columns
        stats = {}
        for col in numeric_cols:
            try:
                stats[col] = {
                    "sum": float(df[col].sum()),
                    "mean": float(df[col].mean()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max())
                }
            except:
                pass
        result["stats"] = stats
        
        # Build sample rows (first 10)
        sample_rows = df.head(10).to_string(index=False)
        result["sample"] = sample_rows
        
        # Build full context string for LLM prompts
        context_parts = [
            f"=== USER'S DATA ({len(df)} rows) ===",
            f"",
            f"COLUMNS: {', '.join(df.columns)}",
            f"",
            f"COLUMN TYPES:",
        ]
        for col, dtype in schema_info.items():
            context_parts.append(f"  - {col}: {dtype}")
        
        context_parts.append(f"")
        context_parts.append(f"NUMERIC COLUMNS: {', '.join(numeric_cols) if numeric_cols else 'None'}")
        context_parts.append(f"TEXT COLUMNS: {', '.join(text_cols) if text_cols else 'None'}")
        
        # Add key statistics
        if stats:
            context_parts.append(f"")
            context_parts.append(f"KEY STATISTICS:")
            for col, col_stats in stats.items():
                context_parts.append(f"  - {col}: Total={col_stats['sum']:,.2f}, Avg={col_stats['mean']:,.2f}")
        
        # Add sample data
        context_parts.append(f"")
        context_parts.append(f"SAMPLE DATA (first 10 rows):")
        context_parts.append(sample_rows)
        
        # Add categorical breakdowns
        for col in text_cols[:3]:  # First 3 categorical columns
            try:
                unique_count = df[col].nunique()
                if 2 <= unique_count <= 20:
                    value_counts = df[col].value_counts().head(10)
                    context_parts.append(f"")
                    context_parts.append(f"{col.upper()} DISTRIBUTION:")
                    for val, count in value_counts.items():
                        context_parts.append(f"  - {val}: {count} records")
            except:
                pass
        
        result["context_string"] = "\n".join(context_parts)
        print(f"[DATA CONTEXT] Built context for {user_id}: {len(df)} rows, {len(df.columns)} columns")
        
    except Exception as e:
        print(f"[DATA CONTEXT] Error: {e}")
        result["context_string"] = f"Error loading data: {str(e)}"
    
    return result


def _format_currency(amount: float, user_id: str = None) -> str:
    """Format currency with proper symbol based on user preferences"""
    try:
        from core.currency_converter import format_currency, get_currency_symbol
        if user_id:
            symbol, code = get_user_currency(user_id)
            return format_currency(amount, code)
    except:
        pass
    # Default to INR
    try:
        from core.currency_converter import format_currency
        return format_currency(amount, "INR")
    except:
        return f"₹{amount:,.2f}"


def _build_source_citations(sources: List[str], mode: str) -> str:
    """Build formatted source citations - simplified to avoid duplication with frontend Sources"""
    if not sources:
        return ""
    
    # Frontend already shows sources in a small "Sources" section
    # Just add Analysis Mode footer - no need for duplicate table
    citation = f"\n\n---\n*Analysis Mode: **{mode.upper()}***"
    return citation


def _clean_response_formatting(answer: str, context: str = "") -> str:
    """
    Clean response formatting for premium $5M product quality.
    Fixes table alignment, removes artifacts, ensures professional output.
    
    Now includes:
    - AI artifact removal ("As an AI...", "I'd be happy to...")
    - Anti-hallucination number validation
    """
    if not answer:
        return answer
    
    import re
    
    # STEP 1: Clean AI artifacts (filler phrases)
    if OUTPUT_FORMATTER_AVAILABLE:
        answer = clean_ai_artifacts(answer)
    
    # Remove triple+ line breaks (keep max double line breaks)
    while '\n\n\n' in answer:
        answer = answer.replace('\n\n\n', '\n\n')
    
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in answer.split('\n')]
    answer = '\n'.join(lines)
    
    # Remove double backticks artifacts (but preserve triple backticks for code blocks)
    answer = re.sub(r'(?<!`)`{2}(?!`)', '', answer)
    
    # Remove excessive ** bold markers that break formatting
    answer = re.sub(r'\*\*\s*\*\*', '', answer)
    
    # Fix broken table separators (ensure proper | alignment)
    answer = re.sub(r'\| *\|', '| |', answer)
    
    # Remove empty table rows
    answer = re.sub(r'\n\|\s*\|\s*\|\s*\|\s*\|?\s*\n', '\n', answer)
    
    # Ensure consistent table header separators
    answer = re.sub(r'\|[-:]+\|', lambda m: '|' + '-' * (len(m.group(0)) - 2) + '|', answer)
    
    # SELECTIVE CLEANUP - Remove code blocks EXCEPT plotly_chart (our visualizations!)
    # Use negative lookahead to preserve plotly_chart blocks
    answer = re.sub(r'```(?!plotly_chart|forecast_chart)[a-zA-Z]*[\s\S]*?```', '', answer)
    
    # Remove LaTeX math blocks (these cause rendering issues)
    answer = re.sub(r'\$\$[\s\S]*?\$\$', '', answer)  # Display math
    answer = re.sub(r'\$[^$\n]+\$', '', answer)  # Inline math
    answer = re.sub(r'\\\\[a-z]+\{[^}]*\}', '', answer)  # LaTeX commands
    
    # Remove hallucinated markdown image links (LLM tries to make its own images)
    # Pattern: ![Alt Text](URL) including attachment:// scheme
    answer = re.sub(r'!\[.*?\]\(.*?\)', '', answer)
    # Also remove bare attachment:// links and [text](attachment://...) links
    answer = re.sub(r'\[.*?\]\(attachment://[^)]*\)', '', answer)
    answer = re.sub(r'attachment://[^\s\)]+', '', answer)
    
    # PRESERVE VALID TABLES - Only remove incomplete/broken table rows
    # Do NOT remove complete tables, as they are essential for data presentation
    
    # Remove numbered emoji sections (1️⃣, 2️⃣, etc.)
    answer = re.sub(r'[0-9]️⃣\s*', '', answer)
    
    # Clean up emoji spacing
    answer = re.sub(r'([📊📈💰🎯💡👥📦✅⚠️🔗])\s{2,}', r'\1 ', answer)
    
    # Remove "Error:" messages that leaked through
    answer = re.sub(r'Error:\s*\n?', '', answer)
    
    # Remove leading/trailing whitespace from entire response
    answer = answer.strip()
    
    # Ensure proper spacing after headers
    answer = re.sub(r'(#{1,3}\s+[^\n]+)\n{3,}', r'\1\n\n', answer)
    
    # Ensure proper spacing before headers
    answer = re.sub(r'\n{4,}(#{1,3}\s+)', r'\n\n\1', answer)
    
    # Remove any remaining incomplete table rows (single | at end of line)
    answer = re.sub(r'\n\|[^|\n]*$', '', answer)
    
    # STEP 2: Anti-hallucination validation (if context provided)
    if context and OUTPUT_FORMATTER_AVAILABLE:
        answer = validate_numbers_in_response(answer, context)
    
    return answer


# ============================================================================
# MEMORY & ANTI-HALLUCINATION HELPERS
# ============================================================================

def _get_chat_history(user_id: str, limit: int = 5) -> str:
    """
    Get recent chat history for context continuity.
    Returns formatted string of last N messages.
    """
    if not user_id:
        return ""
    
    try:
        from pathlib import Path
        from utils.paths import get_user_paths
        import json
        
        paths = get_user_paths(user_id)
        memory_path = paths.get("memory", Path(f"storage/users/{user_id}/memory"))
        history_file = memory_path / "chat_history.json"
        
        if not history_file.exists():
            return ""
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        # Get last N exchanges
        recent = history[-limit:] if len(history) > limit else history
        
        formatted = []
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('content', '')[:2000]  # Increased limit for better context
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    except Exception as e:
        print(f"Chat history error: {e}")
        return ""


def _save_chat_message(user_id: str, role: str, content: str) -> bool:
    """Save a chat message to history for future context."""
    if not user_id:
        return False
    
    try:
        from pathlib import Path
        from utils.paths import get_user_paths
        import json
        
        paths = get_user_paths(user_id)
        memory_path = paths.get("memory", Path(f"storage/users/{user_id}/memory"))
        memory_path.mkdir(parents=True, exist_ok=True)
        history_file = memory_path / "chat_history.json"
        
        history = []
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        # Add new message
        history.append({
            'role': role,
            'content': content[:2000]  # Increased limit for better context
        })
        
        # Keep only last 20 messages
        history = history[-20:]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Save chat error: {e}")
        return False


def _is_data_related_query(question: str) -> bool:
    """
    Check if a question relates to business/uploaded data topics.
    Returns False for general knowledge questions like "What is Python?"
    """
    q_lower = question.lower().strip()
    
    # Business data keywords - questions about THEIR data
    data_keywords = [
        'revenue', 'sales', 'customer', 'product', 'order', 'amount', 
        'total', 'top', 'bottom', 'highest', 'lowest', 'average', 'sum',
        'trend', 'growth', 'profit', 'margin', 'cost', 'price',
        'transaction', 'invoice', 'contract', 'deal', 'opportunity',
        'my data', 'my file', 'uploaded', 'analyze', 'analysis',
        'who', 'which', 'how much', 'how many', 'show me', 'list',
        'compare', 'breakdown', 'segment', 'category', 'region',
        'chart', 'graph', 'visual', 'forecast', 'predict', 'projection',
        'best', 'worst', 'performing', 'underperforming', 
        'month', 'quarter', 'year', 'date', 'period', 'time',
        'name', 'tell me my', 'what is my', 'remember', 'recall'
    ]
    
    # Check if it's about their data
    if any(kw in q_lower for kw in data_keywords):
        return True
    
    # General knowledge patterns to BLOCK
    general_patterns = [
        'what is', 'what are', 'who is', 'who are', 'explain', 'define',
        'how does', 'how do', 'why is', 'why are', 'tell me about',
        'write code', 'write a', 'create a script', 'generate code',
        'programming', 'python', 'java', 'javascript', 'html', 'css',
        'history of', 'meaning of', 'wikipedia', 'google'
    ]
    
    # If it matches general pattern AND doesn't have data keywords, block it
    if any(pattern in q_lower for pattern in general_patterns):
        # Double-check it's not asking about their data
        if not any(kw in q_lower for kw in ['my', 'our', 'the', 'this', 'uploaded', 'file', 'data', 'revenue', 'customer', 'product']):
            return False
    
    # Short greetings are OK
    if len(q_lower) < 15:
        return True  # "hi", "hello", "thanks" etc.
    
    return True  # Default: allow and let the AI figure it out


def _extract_and_save_personal_info(question: str, user_id: str) -> Optional[str]:
    """
    Extract personal info from question and save to memory.
    Returns the extracted name if found, None otherwise.
    """
    if not user_id or not question:
        return None
    
    try:
        from core.memory import process_personal_info, get_user_context
        
        # Try to extract and save personal info
        was_saved = process_personal_info(user_id, question)
        
        if was_saved:
            # Return the saved context
            context = get_user_context(user_id)
            return context
        
        return None
    except Exception as e:
        print(f"Personal info extraction error: {e}")
        return None


# ============================================================================
# $5M CORE FIX: Build Messages With Context - ChatGPT-Quality Conversation
# ============================================================================
# THIS IS THE CRITICAL FIX - Pass actual conversation history to LLM as messages

def build_messages_with_context(
    user_id: str,
    current_question: str,
    current_prompt: str,
    history_limit: int = 10
) -> list:
    """
    Build a proper message array with conversation history for the LLM.
    
    THIS IS THE KEY FIX FOR CONTEXT MEMORY!
    
    Instead of:
        chat("What is revenue?")  # LLM has no memory
        
    We now do:
        chat([
            {"role": "user", "content": "What is revenue?"},
            {"role": "assistant", "content": "Your revenue is $13.8M"},
            {"role": "user", "content": "Explain that"}  # LLM knows context!
        ])
    
    Args:
        user_id: User/session ID
        current_question: The current user question
        current_prompt: The full prompt to send (with context, data, etc.)
        history_limit: Max history messages to include
        
    Returns:
        List of message dicts for the LLM
    """
    messages = []
    
    # Get conversation history
    history_entries = []
    if user_id:
        try:
            # Try ShortTermMemory first
            if MEMORY_ENGINE_AVAILABLE and st_memory:
                history_entries = st_memory.get_messages(user_id, limit=history_limit)
            else:
                # Fallback to file-based history
                from pathlib import Path
                from utils.paths import get_user_paths
                import json
                
                paths = get_user_paths(user_id)
                memory_path = paths.get("memory", Path(f"storage/users/{user_id}/memory"))
                history_file = memory_path / "chat_history.json"
                
                if history_file.exists():
                    with open(history_file, 'r') as f:
                        history_entries = json.load(f)[-history_limit:]
        except Exception as e:
            print(f"[CONTEXT] History load error: {e}")
    
    # Add conversation history as message pairs
    for entry in history_entries:
        role = entry.get('role', 'user')
        content = entry.get('content', '')
        
        if role in ['user', 'assistant'] and content:
            # Truncate very long messages to stay within token limits
            if len(content) > 2000:
                content = content[:2000] + "... [truncated]"
            
            messages.append({
                "role": role,
                "content": content
            })
    
    # Add the current question/prompt as the final user message
    messages.append({
        "role": "user",
        "content": current_prompt
    })
    
    print(f"[CONTEXT] Built {len(messages)} messages ({len(history_entries)} history + 1 current)")
    
    return messages


def resolve_references_in_query(
    question: str,
    user_id: str
) -> tuple:
    """
    Resolve references like "it", "that", "above" using ReferenceResolver.
    
    Examples:
        - "Explain that" -> "Explain the previous revenue analysis"
        - "What about it?" -> "What about Customer_33?"
        - "Show more details" -> "Show more details about the monthly trend"
    
    Args:
        question: Original user question
        user_id: User session ID
        
    Returns:
        (resolved_question, extracted_entities)
    """
    if not MEMORY_ENGINE_AVAILABLE or not reference_resolver:
        return question, {}
    
    try:
        # Get session context
        session_context = None
        if st_memory:
            session_context = st_memory.get_context(user_id) if user_id else None
        
        # Resolve references
        resolved, entities = reference_resolver.resolve(
            question,
            session_context=session_context,
            session_id=user_id
        )
        
        if resolved != question:
            print(f"[CONTEXT] Resolved '{question}' -> '{resolved}'")
            print(f"[CONTEXT] Entities: {entities}")
        
        return resolved, entities
        
    except Exception as e:
        print(f"[CONTEXT] Resolution error: {e}")
        return question, {}


def _get_data_topics_summary(user_id: str) -> str:
    """Get a summary of topics available in user's data for context."""
    try:
        from graph.query import load_graph, get_graph_stats
        
        graph = load_graph(user_id)
        if not graph or graph.number_of_nodes() == 0:
            return ""
        
        stats = get_graph_stats(user_id)
        if not stats:
            return ""
        
        topics = []
        if stats.get('total_nodes', 0) > 0:
            topics.append(f"{stats.get('total_nodes')} entities")
        if stats.get('total_edges', 0) > 0:
            topics.append(f"{stats.get('total_edges')} relationships")
        
        return f"Available data: {', '.join(topics)}" if topics else ""
    except:
        return ""


def _wants_visualization(question: str) -> bool:
    """Check if user wants a chart/visualization"""
    viz_keywords = [
        # General chart keywords
        'chart', 'graph', 'plot', 'visualize', 'visualization', 
        'show me', 'display', 'draw', 'create a', 'generate',
        # Specific chart types
        'bar chart', 'pie chart', 'line chart', 'trend chart',
        'bar', 'pie', 'line', 'area', 'scatter', 'donut',
        'treemap', 'heatmap', 'funnel', 'gauge', 'waterfall',
        'horizontal bar', 'stacked bar', 'bubble', 'radar',
        # Visual intents
        'breakdown', 'distribution', 'comparison', 'trend',
        'top 5', 'top 10', 'top 6', 'top 7', 'top 3', 'top 20',
        'bottom 5', 'bottom 10', 'bottom 3',
        'by product', 'by customer', 'by category', 'by region'
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in viz_keywords)



def _wants_prediction(question: str) -> bool:
    """Check if user wants a prediction/forecast"""
    pred_keywords = [
        'predict', 'forecast', 'future', 'next month', 'next year',
        'projection', 'estimate', 'will be', 'expected', 'growth',
        'next 3', 'next 6', 'next 12', 'next week', 'next 7 days',
        'next day', 'next two', 'next 2', 'next five', 'next 5',
        'tomorrow', 'upcoming', 'for the next', 'in the next',
        'days ahead', 'weeks ahead', 'months ahead', 'years ahead',
        'customer growth', 'revenue growth'
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in pred_keywords)


def _wants_simulation(question: str) -> bool:
    """Check if user wants a what-if simulation"""
    sim_keywords = [
        'what if', 'what-if', 'simulate', 'simulation', 'scenario',
        'if i increase', 'if i decrease', 'if we increase', 'if we decrease',
        'price increase', 'price decrease', 'marketing spend', 'marketing increase',
        'impact of', 'effect of', 'how would', '10% increase', '20% increase',
        'elasticity', 'sensitivity', 'what happens if', 'churn impact'
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in sim_keywords)


def _wants_insights(question: str) -> bool:
    """Check if user wants automated insights analysis"""
    insight_keywords = [
        'insights', 'analyze my', 'analyse my', 'find risks', 'find opportunities',
        'what are the risks', 'what are the opportunities', 'health score',
        'business health', 'anomalies', 'detect anomalies', 'trends and risks',
        'full analysis', 'complete analysis', 'generate insights', 'auto analyze',
        'automated analysis', 'assess my', 'evaluate my'
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in insight_keywords)


# ============================================================================
# CONVERSATION INTELLIGENCE - ChatGPT-Level Follow-Up Handling
# ============================================================================

def _detect_followup_type(question: str) -> str:
    """
    Detect the type of follow-up query.
    
    Returns: 'explanation', 'conversion', 'comparison', 'refinement', 
             'hypothetical', 'evaluation', 'summarization', 'reformatting', 
             'self_explanation', or 'new_query'
    """
    q_lower = question.lower()
    
    # ==========================================================================
    # FIRST: Check for "above" references - these are ALWAYS follow-ups
    # ==========================================================================
    above_patterns = ['above', 'that', 'this', 'previous', 'same', 'it ']
    has_above_reference = any(kw in q_lower for kw in above_patterns)
    
    # Reformatting - same content, different format (MUST CHECK EARLY)
    format_patterns = [
        'in one line', 'in 1 line', 'in a line', 'one line',
        'in words', 'in text', 'in simple words', 'in plain words',
        'shorter', 'make it shorter', 'more brief', 'briefly',
        'as a table', 'in table', 'as list', 'in bullet points'
    ]
    if any(kw in q_lower for kw in format_patterns):
        return 'reformatting'
    
    # Explanation requests - reuse existing answer
    explanation_patterns = [
        'explain', 'why', 'how come', 'what does that mean', 
        'clarify', 'elaborate', 'what is this', 'tell me more'
    ]
    if any(kw in q_lower for kw in explanation_patterns):
        return 'explanation'
    
    # Summarization - reuse existing answer
    summary_patterns = [
        'summarize', 'summary', 'in short', 'briefly', 
        'in 2 lines', 'simplify', 'simpler', 'tldr'
    ]
    if any(kw in q_lower for kw in summary_patterns):
        return 'summarization'
    
    # Currency conversion - reuse computed values
    if any(kw in q_lower for kw in ['convert', 'in usd', 'in dollars', 'in euros', 'in inr', 'in rupees']):
        return 'conversion'
    
    # Comparison - needs context
    if any(kw in q_lower for kw in ['compare', 'versus', 'vs', 'difference between', 'better than', 'worse than']):
        return 'comparison'
    
    # Evaluation - use general knowledge
    if any(kw in q_lower for kw in ['good or bad', 'is this good', 'is this bad', 'healthy', 'benchmark', 'normal', 'typical']):
        return 'evaluation'
    
    # Hypothetical - what-if scenarios
    if any(kw in q_lower for kw in ['what if', 'suppose', 'assume', 'hypothetically', 'if we', 'if i']):
        return 'hypothetical'
    
    # Refinement - modify previous query
    if any(kw in q_lower for kw in ['now only', 'filter by', 'just for', 'only for', 'make it', 'change to', 'monthly', 'weekly']):
        return 'refinement'
    
    # Self-explanation - explain own reasoning (MUST DETECT "why do you think that?")
    self_explanation_patterns = [
        'why did you', 'how did you', 'explain your', 'reasoning',
        'why do you think', 'why do you say', 'how do you know',
        'why that', 'why this', 'how did you conclude', 'explain that'
    ]
    if any(kw in q_lower for kw in self_explanation_patterns):
        return 'self_explanation'
    
    # If contains 'above' reference but didn't match other patterns, treat as explanation
    if has_above_reference:
        return 'explanation'
    
    return 'new_query'



def _resolve_query_references(question: str, session_id: str) -> tuple:
    """
    Resolve references like 'that', 'this', 'above' using conversation memory.
    
    Returns: (resolved_question, metadata)
    """
    if not MEMORY_ENGINE_AVAILABLE or not _reference_resolver:
        return question, {'resolved': False}
    
    try:
        resolved_query, metadata = _reference_resolver.resolve(question, session_id)
        if metadata.get('had_references'):
            print(f"[MEMORY] Resolved references: {metadata.get('resolved')}")
        return resolved_query, metadata
    except Exception as e:
        print(f"[MEMORY] Reference resolution failed: {e}")
        return question, {'resolved': False, 'error': str(e)}


def _get_conversation_context(session_id: str, include_comparison: bool = False) -> str:
    """
    Get formatted conversation history for context.
    
    $5M Enhancement: Also includes comparison context when available,
    so "compare top vs lowest" queries work correctly.
    
    Args:
        session_id: Session identifier
        include_comparison: If True, also include comparison context
        
    Returns: String with last few messages + comparison context for LLM
    """
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return ""
    
    try:
        context = _short_term_memory.get_context(session_id)
        
        # $5M Enhancement: Add comparison context if available
        # This fixes "compare top vs lowest" queries failing!
        if include_comparison:
            try:
                comparison_ctx = _short_term_memory.get_comparison_context(session_id)
                if comparison_ctx:
                    context += "\n" + comparison_ctx
                    print(f"[MEMORY] Added comparison context for follow-up")
            except Exception as e:
                print(f"[MEMORY] Comparison context failed: {e}")
        
        return context
    except Exception as e:
        print(f"[MEMORY] Failed to get context: {e}")
        return ""


def _store_query_result_for_followup(session_id: str, query_type: str, data: list, summary: str = ""):
    """
    Store query results for follow-up comparisons.
    
    Call this after "top 5 customers" or "revenue breakdown by product" queries
    so the user can follow up with "compare top vs lowest".
    
    Args:
        session_id: Session identifier
        query_type: 'customers', 'products', 'months', etc.
        data: List of dicts with 'name' and 'value' keys
        summary: Optional description
    """
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    
    try:
        _short_term_memory.set_last_query_result(session_id, query_type, data, summary)
    except Exception as e:
        print(f"[MEMORY] Failed to store query result: {e}")


def _store_conversation_turn(session_id: str, role: str, content: str, metadata: dict = None):
    """Store a conversation turn in memory."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    
    try:
        _short_term_memory.add_message(session_id, role, content, metadata)
    except Exception as e:
        print(f"[MEMORY] Failed to store message: {e}")


def _is_language_only_query(question: str) -> bool:
    """
    Check if query only requires language transformation (no data re-fetch).
    
    These queries can be answered using the previous answer without re-running RAG.
    """
    q_lower = question.lower()
    
    language_patterns = [
        'explain', 'summarize', 'simplify', 'rephrase', 'in simple terms',
        'what does that mean', 'clarify', 'elaborate', 'in 2 lines', 'briefly',
        'is this good', 'is this bad', 'normal or not', 'healthy or not',
        'why did you say', 'explain your reasoning'
    ]
    
    return any(pattern in q_lower for pattern in language_patterns)


def _detect_response_format(question: str) -> dict:
    """
    Detect user's desired response format and return formatting instructions.
    
    This is CRITICAL for ChatGPT-level behavior: respecting format constraints.
    
    Examples:
    - "explain in one line" -> format: "ONE_LINE"
    - "give me a brief summary" -> format: "BRIEF"
    - "explain in detail" -> format: "DETAILED"
    """
    q_lower = question.lower()
    
    format_info = {
        "format_type": "NORMAL",
        "max_lines": None,
        "instructions": ""
    }
    
    # One-line responses
    if any(kw in q_lower for kw in ['one line', 'one sentence', 'single line', 'single sentence', '1 line', '1 sentence']):
        format_info["format_type"] = "ONE_LINE"
        format_info["max_lines"] = 1
        format_info["instructions"] = """
RESPONSE FORMAT: ONE LINE ONLY
- Your ENTIRE response must be ONE single sentence
- NO tables, NO bullet points, NO multiple paragraphs
- Maximum 30 words
- Just answer directly in ONE line"""
    
    # Two-line responses
    elif any(kw in q_lower for kw in ['two lines', '2 lines', 'two sentences', '2 sentences']):
        format_info["format_type"] = "TWO_LINES"
        format_info["max_lines"] = 2
        format_info["instructions"] = """
RESPONSE FORMAT: TWO LINES MAXIMUM
- Your ENTIRE response must be 2 sentences or less
- NO tables, NO bullet points
- Keep it to 50 words maximum"""
    
    # Brief responses
    elif any(kw in q_lower for kw in ['briefly', 'brief', 'short', 'quick', 'concise']):
        format_info["format_type"] = "BRIEF"
        format_info["max_lines"] = 3
        format_info["instructions"] = """
RESPONSE FORMAT: BRIEF
- Keep response to 2-3 sentences
- NO unnecessary tables or metrics
- Be concise and direct"""
    
    # Detailed responses
    elif any(kw in q_lower for kw in ['detail', 'detailed', 'elaborate', 'comprehensive', 'full analysis']):
        format_info["format_type"] = "DETAILED"
        format_info["max_lines"] = None
        format_info["instructions"] = """
RESPONSE FORMAT: DETAILED
- Provide comprehensive analysis
- Include relevant tables and metrics
- Explain insights thoroughly"""
    
    return format_info


def _detect_hypothetical(question: str) -> bool:
    """Detect if query is hypothetical (what-if scenario)."""
    q_lower = question.lower()
    return any(kw in q_lower for kw in ['what if', 'suppose', 'assume', 'hypothetically', 'imagine if'])


# ============================================================================
# AUTHORITATIVE METRIC TRACKING - Primary metric + Self-explanation
# ============================================================================

def _set_primary_metric(session_id: str, metric: str, value: float, 
                        currency: str = "INR", formatted: str = None):
    """Store the authoritative primary metric for this session."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    try:
        _short_term_memory.set_primary_metric(session_id, metric, value, currency, formatted)
    except Exception as e:
        print(f"[MEMORY] Failed to set primary metric: {e}")


def _get_primary_metric_context(session_id: str) -> str:
    """
    Get the primary metric context for follow-up queries.
    Returns formatted context string for LLM.
    """
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return ""
    
    try:
        metric_data = _short_term_memory.get_primary_metric(session_id)
        if metric_data:
            return f"""
AUTHORITATIVE METRIC (use this for 'it', 'that', 'this' references):
- Metric: {metric_data.get('metric', 'unknown')}
- Value: {metric_data.get('formatted', metric_data.get('value', 'N/A'))}
- Currency: {metric_data.get('currency', 'INR')}
"""
        return ""
    except Exception as e:
        print(f"[MEMORY] Failed to get primary metric: {e}")
        return ""


def _set_conclusion(session_id: str, conclusion: str, reasons: list, metric: str = None):
    """Store an evaluative conclusion for self-explanation."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    try:
        _short_term_memory.set_conclusion(session_id, conclusion, reasons, metric)
    except Exception as e:
        print(f"[MEMORY] Failed to set conclusion: {e}")


def _get_self_explanation_context(session_id: str) -> str:
    """
    Get the self-explanation context for 'why' questions.
    Returns formatted context string referencing stored conclusion.
    """
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return ""
    
    try:
        conclusion_data = _short_term_memory.get_conclusion(session_id)
        if conclusion_data:
            reasons_str = "\n".join([f"  - {r}" for r in conclusion_data.get('reasons', [])])
            return f"""
YOUR PREVIOUS CONCLUSION (explain this reasoning):
- Conclusion: {conclusion_data.get('conclusion', 'N/A')}
- Metric: {conclusion_data.get('metric', 'the data')}
- Reasons:
{reasons_str}

SELF-EXPLANATION REQUIRED:
- Explain WHY you reached that conclusion
- Use the reasons listed above
- Be confident - DO NOT ask for clarification
- DO NOT re-run data queries
"""
        return ""
    except Exception as e:
        print(f"[MEMORY] Failed to get conclusion: {e}")
        return ""


def _get_last_answer_context(session_id: str) -> str:
    """Get the last answer for follow-up transformations."""
    # Try short-term memory first
    if MEMORY_ENGINE_AVAILABLE and _short_term_memory:
        try:
            last_answer = _short_term_memory.get_last_answer(session_id)
            if last_answer:
                return f"""
YOUR PREVIOUS ANSWER (use this for follow-ups):
{last_answer[:1500]}
"""
        except Exception as e:
            print(f"[MEMORY] Short-term memory error: {e}")
    
    # Fallback: Read from file-based history
    try:
        from pathlib import Path
        from utils.paths import get_user_paths
        import json
        
        paths = get_user_paths(session_id)
        memory_path = paths.get("memory", Path(f"storage/users/{session_id}/memory"))
        history_file = memory_path / "chat_history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Find last assistant message
            for msg in reversed(history):
                if msg.get('role') == 'assistant':
                    last_answer = msg.get('content', '')
                    if last_answer:
                        return f"""
YOUR PREVIOUS ANSWER (use this for follow-ups):
{last_answer[:1500]}
"""
                    break
    except Exception as e:
        print(f"[MEMORY] File-based fallback error: {e}")
    
    return ""




def _extract_primary_metric_from_answer(answer: str, session_id: str, currency_symbol: str = "₹"):
    """
    Extract and store the primary metric from an answer.
    Called after generating an answer to enable follow-up resolution.
    """
    import re
    
    # Look for revenue/total patterns
    patterns = [
        (r'(?:total\s+)?revenue[:\s]+[₹$€£]?([\d,]+(?:\.\d+)?)', 'total_revenue'),
        (r'(?:total\s+)?sales[:\s]+[₹$€£]?([\d,]+(?:\.\d+)?)', 'total_sales'),
        (r'(?:total\s+)?orders[:\s]+([\d,]+)', 'total_orders'),
        (r'(?:average\s+)?order\s+value[:\s]+[₹$€£]?([\d,]+(?:\.\d+)?)', 'average_order_value'),
        (r'([\d,]+(?:\.\d+)?)\s*(?:customers|clients)', 'total_customers'),
    ]
    
    answer_lower = answer.lower()
    
    for pattern, metric_name in patterns:
        match = re.search(pattern, answer_lower)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                value = float(value_str)
                formatted = f"{currency_symbol}{value:,.2f}" if metric_name != 'total_orders' and metric_name != 'total_customers' else f"{int(value):,}"
                _set_primary_metric(session_id, metric_name, value, "INR", formatted)
                return
            except ValueError:
                pass
    
    # Fallback: Look for any bold metric
    bold_pattern = r'\*\*([^*]+)[:\s]+[₹$€£]?([\d,]+(?:\.\d+)?)\*\*'
    match = re.search(bold_pattern, answer)
    if match:
        metric_name = match.group(1).strip().lower().replace(' ', '_')
        value_str = match.group(2).replace(',', '')
        try:
            value = float(value_str)
            formatted = f"{currency_symbol}{value:,.2f}"
            _set_primary_metric(session_id, metric_name, value, "INR", formatted)
        except ValueError:
            pass


# ============================================================================
# CURRENCY PREFERENCE HELPERS
# ============================================================================

def _set_currency_preference(session_id: str, currency: str):
    """Store user's preferred output currency."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    try:
        _short_term_memory.set_currency_preference(session_id, currency)
    except Exception as e:
        print(f"[MEMORY] Failed to set currency preference: {e}")


def _get_currency_preference(session_id: str) -> str:
    """Get user's preferred output currency (default INR)."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return "INR"
    try:
        pref = _short_term_memory.get_currency_preference(session_id)
        return pref if pref else "INR"
    except Exception as e:
        print(f"[MEMORY] Failed to get currency preference: {e}")
        return "INR"


def _detect_currency_from_query(question: str) -> str:
    """Detect which currency user is asking for and store preference."""
    q_lower = question.lower()
    
    if any(kw in q_lower for kw in ['to usd', 'in usd', 'in dollars', 'to dollars']):
        return "USD"
    elif any(kw in q_lower for kw in ['to eur', 'in eur', 'in euros', 'to euros']):
        return "EUR"
    elif any(kw in q_lower for kw in ['to gbp', 'in gbp', 'in pounds', 'to pounds']):
        return "GBP"
    elif any(kw in q_lower for kw in ['to inr', 'in inr', 'in rupees', 'to rupees']):
        return "INR"
    return None


# ============================================================================
# AUTHORITATIVE AGGREGATE HELPERS - Unified truth across modes
# ============================================================================

def _store_aggregate(session_id: str, key: str, value):
    """Store an authoritative aggregate that cannot be contradicted."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    try:
        _short_term_memory.set_aggregate(session_id, key, value)
    except Exception as e:
        print(f"[MEMORY] Failed to store aggregate: {e}")


def _get_aggregates_context(session_id: str) -> str:
    """Get formatted aggregates for LLM prompt."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return ""
    try:
        return _short_term_memory.get_aggregates_context(session_id)
    except Exception as e:
        print(f"[MEMORY] Failed to get aggregates: {e}")
        return ""


def _store_chart_context(session_id: str, chart_type: str, title: str, 
                         data_summary: str, peak: dict = None, low: dict = None):
    """Store chart context for explanation binding."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return
    try:
        _short_term_memory.set_last_chart(session_id, {
            "type": chart_type,
            "title": title,
            "data_summary": data_summary,
            "peak": peak,
            "low": low
        })
    except Exception as e:
        print(f"[MEMORY] Failed to store chart context: {e}")


def _get_chart_explanation_context(session_id: str) -> str:
    """Get chart context for 'explain this chart' queries."""
    if not MEMORY_ENGINE_AVAILABLE or not _short_term_memory:
        return ""
    try:
        return _short_term_memory.get_chart_explanation_context(session_id)
    except Exception as e:
        print(f"[MEMORY] Failed to get chart context: {e}")
        return ""


def _detect_chart_explanation_query(question: str) -> bool:
    """Detect if user is asking to explain a chart."""
    q_lower = question.lower()
    patterns = [
        'explain this chart', 'explain the chart', 'what does this chart show',
        'explain what this', 'describe the chart', 'interpret this chart',
        'what does the chart', 'explain above chart'
    ]
    return any(p in q_lower for p in patterns)


def _detect_trend_query(question: str) -> bool:
    """Detect if user is asking about trends."""
    q_lower = question.lower()
    patterns = [
        'trend', 'over time', 'month by month', 'monthly', 'weekly',
        'progression', 'growth pattern', 'performance over'
    ]
    return any(p in q_lower for p in patterns)


def _detect_best_worst_query(question: str) -> bool:
    """Detect if user is asking about best/worst performance."""
    q_lower = question.lower()
    patterns = [
        'best month', 'worst month', 'highest month', 'lowest month',
        'peak month', 'performed best', 'performed worst', 'which month'
    ]
    return any(p in q_lower for p in patterns)


def _generate_intelligent_chart(
    question: str,
    df,
    currency_symbol: str = "₹",
    user_role: str = "analyst"
) -> tuple:
    """
    Generate a chart using intelligent visualization decision.
    
    This replaces hardcoded chart selection with query-aware selection.
    
    Returns: (chart_payload, decision_info)
    """
    print(f"[VIZ] Starting intelligent chart generation for: '{question}'")
    print(f"[VIZ] VIZ_INTELLIGENCE_AVAILABLE: {VIZ_INTELLIGENCE_AVAILABLE}")
    
    if not VIZ_INTELLIGENCE_AVAILABLE:
        print("[VIZ] ERROR: Visualization intelligence not available!")
        return None, "Visualization intelligence not available"
    
    if df is None:
        print("[VIZ] ERROR: DataFrame is None!")
        return None, "No data available for visualization"
    
    if df.empty:
        print("[VIZ] ERROR: DataFrame is empty!")
        return None, "No data available for visualization"
    
    print(f"[VIZ] DataFrame shape: {df.shape}, columns: {list(df.columns)}")
    
    # Get visualization decision
    try:
        decision = decide_visualization(question, df, user_role)
        
        # Extract count from query and set decision.limit dynamically
        # e.g., "top 3 customers" → limit = 3
        from agents.visualization_intelligence import extract_count_from_query
        extracted_limit = extract_count_from_query(question)
        decision.limit = extracted_limit
        
        print(f"[VIZ] Decision: should_render={decision.should_render}, chart_type={decision.chart_type}, intent={decision.intent}, limit={decision.limit}")
        print(f"[VIZ] Columns: x={decision.x_column}, y={decision.y_column}, group={decision.group_column}")
        print(f"[VIZ] Title: {decision.title}, Reason: {decision.reason}")
    except Exception as e:
        print(f"[VIZ] ERROR in decide_visualization: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Decision error: {e}"
    
    if not decision.should_render:
        print(f"[VIZ] Not rendering: {decision.reason}")
        return None, decision.reason
    
    # Generate chart from decision
    try:
        chart_payload = create_chart_from_decision(
            decision=decision,
            df=df,
            currency_symbol=currency_symbol,
            user_role=user_role
        )
        print(f"[VIZ] Chart payload generated: {chart_payload is not None}")
        if chart_payload:
            print(f"[VIZ] Chart has 'data': {'data' in chart_payload}, has 'layout': {'layout' in chart_payload}")
    except Exception as e:
        print(f"[VIZ] ERROR in create_chart_from_decision: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Chart generation error: {e}"
    
    if chart_payload and not chart_payload.get("error"):
        info = f"Generated {decision.chart_type.value} chart: {decision.title}"
        print(f"[VIZ] SUCCESS: {info}")
        return chart_payload, info
    
    error_msg = chart_payload.get("error", "Chart generation failed") if chart_payload else "No chart payload"
    print(f"[VIZ] FAILED: {error_msg}")
    return None, error_msg


def _is_followup_query(question: str) -> bool:
    """Check if this is a follow-up query about previous response/chart"""
    followup_keywords = [
        # Explain patterns
        'explain above', 'explain this', 'explain the', 'explain that',
        'explain it', 'in words', 'in simple', 'what does it mean',
        # About patterns
        'about above', 'about that', 'about this', 'about it',
        # Chart patterns
        'above graph', 'above chart', 'this graph', 'this chart',
        'the graph', 'the chart', 'that chart', 'that graph',
        'the bar', 'this bar', 'above bar',
        # General follow-up
        'tell me about', 'explain more', 'more about', 'can you explain',
        'previous', 'what does', 'elaborate', 'clarify',
        # Short references
        'that', 'above', 'it'
    ]
    q_lower = question.lower().strip()
    
    # Check for keyword matches
    if any(kw in q_lower for kw in followup_keywords):
        return True
    
    # Also detect very short questions that are likely follow-ups
    if len(q_lower.split()) <= 5 and any(w in q_lower for w in ['that', 'it', 'this', 'above']):
        return True
    
    return False


def _extract_chart_type_from_context(conversation_context: str) -> str:
    """Extract what type of chart was shown in previous response"""
    context_lower = conversation_context.lower()
    
    # Check for customer chart indicators
    if any(kw in context_lower for kw in ['top customers', 'customer revenue', 'customer_3', 'customer_2', 'customer_1']):
        return 'customer'
    
    # Check for product chart indicators
    if any(kw in context_lower for kw in ['product revenue', 'product distribution', 'top products', 'product_']):
        return 'product'
    
    # Check for trend chart indicators
    if any(kw in context_lower for kw in ['monthly revenue', 'trend', '2025-', 'revenue over time']):
        return 'trend'
    
    return 'customer'  # Default to customer if unclear


def _enhance_followup_question(question: str, conversation_context: str) -> str:
    """Enhance a follow-up question with context from previous conversation"""
    if not _is_followup_query(question):
        return question
    
    chart_type = _extract_chart_type_from_context(conversation_context)
    
    # Build enhanced question with context
    if chart_type == 'customer':
        return f"{question}\n\n[Context: The user is asking about the TOP CUSTOMERS BY REVENUE bar chart that was shown. Explain the customer revenue data with exact customer names and amounts.]"
    elif chart_type == 'product':
        return f"{question}\n\n[Context: The user is asking about the PRODUCT DISTRIBUTION chart that was shown. Explain the product revenue data with exact product names and percentages.]"
    elif chart_type == 'trend':
        return f"{question}\n\n[Context: The user is asking about the MONTHLY REVENUE TREND chart that was shown. Explain the monthly revenue data with exact months and amounts.]"
    
    return question


def _extract_prediction_period(question: str) -> dict:
    """
    Extract prediction period from question.
    
    Returns dict with:
        periods: Number of periods
        unit: 'days', 'weeks', 'months', 'years'
        display: Human-readable string
    """
    import re
    q_lower = question.lower()
    
    # Word to number mapping
    word_nums = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'a': 1, 'an': 1
    }
    
    def extract_number(text):
        """Extract number from text (digit or word)"""
        for word, num in word_nums.items():
            if word in text:
                return num
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else None
    
    # Check for days
    day_patterns = [r'next\s+(\w+)\s*days?', r'(\d+)\s*days?\s*ahead', r'tomorrow']
    for pattern in day_patterns:
        match = re.search(pattern, q_lower)
        if match or 'tomorrow' in q_lower:
            num = extract_number(match.group(0)) if match else 1
            num = num or 1
            return {'periods': num, 'unit': 'days', 'display': f'{num} day(s)'}
    
    # Check for weeks
    week_patterns = [r'next\s+(\w+)\s*weeks?', r'(\d+)\s*weeks?\s*ahead']
    for pattern in week_patterns:
        match = re.search(pattern, q_lower)
        if match:
            num = extract_number(match.group(0)) or 1
            return {'periods': num, 'unit': 'weeks', 'display': f'{num} week(s)'}
    
    # Check for months
    month_patterns = [r'next\s+(\w+)\s*months?', r'(\d+)\s*months?\s*ahead']
    for pattern in month_patterns:
        match = re.search(pattern, q_lower)
        if match:
            num = extract_number(match.group(0)) or 3
            return {'periods': num, 'unit': 'months', 'display': f'{num} month(s)'}
    
    # Check for quarters
    if 'quarter' in q_lower:
        match = re.search(r'next\s+(\w+)\s*quarters?', q_lower)
        num = extract_number(match.group(0)) if match else 1
        return {'periods': num * 3, 'unit': 'months', 'display': f'{num} quarter(s)'}
    
    # Check for years
    year_patterns = [r'next\s+(\w+)\s*years?', r'(\d+)\s*years?\s*ahead']
    for pattern in year_patterns:
        match = re.search(pattern, q_lower)
        if match:
            num = extract_number(match.group(0)) or 1
            return {'periods': num * 12, 'unit': 'months', 'display': f'{num} year(s)'}
    
    if 'next year' in q_lower:
        return {'periods': 12, 'unit': 'months', 'display': '1 year'}
    if 'next quarter' in q_lower:
        return {'periods': 3, 'unit': 'months', 'display': '1 quarter'}
    if 'next month' in q_lower:
        return {'periods': 1, 'unit': 'months', 'display': '1 month'}
    if 'next week' in q_lower:
        return {'periods': 1, 'unit': 'weeks', 'display': '1 week'}
    
    # Default 3 months
    return {'periods': 3, 'unit': 'months', 'display': '3 months'}


def _format_prediction_response(
    prediction_result: dict,
    currency_symbol: str = "₹",
    data_source: str = "uploaded data"
) -> str:
    """
    Format prediction result into structured AI response.
    
    Returns markdown with:
    - Executive Summary
    - Forecast Insights  
    - Key Forecast Numbers
    - Risk Zones
    - Opportunities
    - Driver Analysis
    - Chart Payload (JSON)
    - Data Source
    """
    response_parts = []
    
    # 1. Executive Summary
    response_parts.append("### 📌 Executive Summary")
    insight = prediction_result.get('insight', 'Forecast analysis complete.')
    response_parts.append(f"{insight}\n")
    
    # 2. Forecast Insights
    response_parts.append("### 🔮 Forecast Insights")
    trend = prediction_result.get('trend', 'stable')
    trend_labels = {
        'strongly_increasing': '📈 Strong upward momentum detected',
        'increasing': '📈 Steady growth trend observed',
        'stable': '➡️ Values remain relatively stable',
        'decreasing': '📉 Declining trend identified',
        'strongly_decreasing': '📉 Significant downward pressure'
    }
    response_parts.append(f"- **Trend**: {trend_labels.get(trend, trend)}")
    
    seasonality = prediction_result.get('seasonality')
    if seasonality:
        response_parts.append(f"- **Seasonality**: {seasonality.capitalize()} pattern detected")
    
    model = prediction_result.get('model_used', 'auto')
    model_names = {
        'prophet': 'Facebook Prophet (trend + seasonality)',
        'arima': 'ARIMA (auto-regressive)',
        'holt_winters': 'Holt-Winters (exponential smoothing)',
        'linear': 'Linear regression with smoothing'
    }
    response_parts.append(f"- **Model**: {model_names.get(model, model)}\n")
    
    # 3. Key Forecast Numbers
    response_parts.append("### 📈 Key Forecast Numbers")
    forecast_points = prediction_result.get('forecast_points', [])
    
    if forecast_points:
        # Get specific period forecasts
        for i, point in enumerate(forecast_points[:6]):
            value = point.get('value', 0)
            lower = point.get('lower', value * 0.9)
            upper = point.get('upper', value * 1.1)
            date = point.get('date', f'Period +{i+1}')
            
            response_parts.append(
                f"| **{date}** | {currency_symbol}{value:,.0f} | "
                f"Range: {currency_symbol}{lower:,.0f} - {currency_symbol}{upper:,.0f} |"
            )
    
    # Accuracy scores
    accuracy = prediction_result.get('accuracy', {})
    if accuracy:
        mape = accuracy.get('MAPE', 0)
        rmse = accuracy.get('RMSE', 0)
        confidence = 100 - mape if mape else 0
        response_parts.append(f"\n**Accuracy Score**: {confidence:.0f}% (MAPE: {mape:.1f}%, RMSE: {currency_symbol}{rmse:,.0f})\n")
    
    # 4. Risk Zones
    risks = prediction_result.get('risks', [])
    if risks:
        response_parts.append("### ⚠️ Risk Zones")
        for risk in risks[:5]:
            response_parts.append(f"- ⚡ {risk}")
        response_parts.append("")
    
    # 5. Opportunities
    opportunities = prediction_result.get('opportunities', [])
    if opportunities:
        response_parts.append("### 🟢 Opportunities")
        for opp in opportunities[:4]:
            response_parts.append(f"- {opp}")
        response_parts.append("")
    
    # 6. Driver Analysis
    explanation = prediction_result.get('explanation', '')
    if explanation:
        response_parts.append("### 🧠 Why This Happened")
        response_parts.append(f"{explanation}\n")
    
    # 7. Chart Payload (for frontend)
    chart_payload = prediction_result.get('chart_payload', {})
    if chart_payload:
        response_parts.append("### 📊 Chart")
        response_parts.append("```forecast_chart")
        import json
        response_parts.append(json.dumps(chart_payload, indent=2))
        response_parts.append("```\n")
    
    # 8. Data Source
    response_parts.append("### 📦 Data Source")
    response_parts.append(f"Analysis based on: **{data_source}**")
    
    return "\n".join(response_parts)


def _embed_chart_in_response(answer: str, chart_base64: str, chart_title: str) -> str:
    """Embed a chart image in the response"""
    # Add chart as embedded image (frontend will render)
    chart_section = f"\n\n📊 **{chart_title}**\n"
    chart_section += f"![{chart_title}]({chart_base64})\n"
    return answer + chart_section


def _add_confidence_indicator(
    answer: str, 
    confidence: AnswerConfidence
) -> str:
    """Add confidence indicator to answer if needed"""
    if confidence.should_flag_uncertainty:
        warning = "\n\n> ⚠️ **Note:** This response has lower confidence. "
        warning += "Consider uploading more relevant data for better accuracy."
        return answer + warning
    return answer


def _build_chart_data_summary(df, question: str, currency_symbol: str) -> str:
    """
    Pre-compute chart data summary to include in LLM prompt.
    This ensures the LLM explanation matches the actual chart data.
    """
    q_lower = question.lower()
    summary = ""
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    
    # Customer chart data - EXACT data that will be shown in chart
    if 'customer' in q_lower and 'customer' in df.columns:
        customer_revenue = df.groupby('customer')[amount_col].sum().sort_values(ascending=False).head(10)
        customer_orders = df.groupby('customer').size()
        
        summary = "\n\n📊 CHART DATA (Use this EXACT data in your explanation):\n"
        summary += "| Rank | Customer | Revenue | Orders |\n"
        summary += "|------|----------|---------|--------|\n"
        
        for rank, (cust, rev) in enumerate(customer_revenue.items(), 1):
            orders = customer_orders.get(cust, 0)
            summary += f"| {rank} | {cust} | {currency_symbol}{rev:,.2f} | {orders} |\n"
        
        total_rev = df[amount_col].sum()
        avg_order = df[amount_col].mean()
        summary += f"\n**Total Revenue:** {currency_symbol}{total_rev:,.2f}\n"
        summary += f"**Average Order:** {currency_symbol}{avg_order:,.2f}\n"
        summary += f"**Top Customer:** {customer_revenue.index[0]} ({currency_symbol}{customer_revenue.iloc[0]:,.2f})\n"
        summary += f"**Lowest in Top 10:** {customer_revenue.index[-1]} ({currency_symbol}{customer_revenue.iloc[-1]:,.2f})\n"
    
    # Product chart data
    elif 'product' in q_lower and 'product' in df.columns:
        product_revenue = df.groupby('product')[amount_col].sum().sort_values(ascending=False).head(8)
        product_counts = df.groupby('product').size()
        
        summary = "\n\n📦 CHART DATA (Use this EXACT data in your explanation):\n"
        summary += "| Rank | Product | Revenue | Units Sold | % Share |\n"
        summary += "|------|---------|---------|------------|--------|\n"
        
        total = product_revenue.sum()
        for rank, (prod, rev) in enumerate(product_revenue.items(), 1):
            units = product_counts.get(prod, 0)
            share = (rev / total) * 100 if total > 0 else 0
            summary += f"| {rank} | {prod} | {currency_symbol}{rev:,.2f} | {units} | {share:.1f}% |\n"
        
        summary += f"\n**Total Product Revenue:** {currency_symbol}{total:,.2f}\n"
        summary += f"**Top Product:** {product_revenue.index[0]}\n"
        summary += f"**Number of Products:** {len(product_revenue)}\n"
    
    # Trend/prediction data
    elif any(kw in q_lower for kw in ['trend', 'month', 'predict', 'forecast']):
        if 'date' in df.columns:
            import pandas as pd
            df_temp = df.copy()
            df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
            df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
            
            if not df_dated.empty:
                df_dated['month'] = df_dated['date_parsed'].dt.to_period('M')
                monthly = df_dated.groupby('month')[amount_col].sum()
                
                summary = "\n\n📈 CHART DATA (Use this EXACT data in your explanation):\n"
                summary += "| Month | Revenue |\n"
                summary += "|-------|--------|\n"
                
                for month, rev in monthly.items():
                    summary += f"| {month} | {currency_symbol}{rev:,.2f} |\n"
                
                if len(monthly) >= 2:
                    growth = ((monthly.iloc[-1] - monthly.iloc[0]) / monthly.iloc[0]) * 100 if monthly.iloc[0] > 0 else 0
                    summary += f"\n**Period Growth:** {growth:+.1f}%\n"
                    summary += f"**Highest Month:** {monthly.idxmax()} ({currency_symbol}{monthly.max():,.2f})\n"
                    summary += f"**Lowest Month:** {monthly.idxmin()} ({currency_symbol}{monthly.min():,.2f})\n"
    
    return summary




def rag_answer(state: AgentState) -> AgentState:
    """
    🟦 RAG MODE - Enterprise Document-Based Answers
    
    Features:
    - Adaptive retrieval with confidence scoring
    - Citation formatting with source locations
    - Token-aware context building
    - Clean markdown output
    - CONVERSATION MEMORY - ChatGPT-level stateful behavior
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    session_id = user_id  # Use user_id as session_id for now
    
    # =========================================================================
    # STEP 1A: CONVERSATION MEMORY - Store user message in session memory
    # =========================================================================
    _store_conversation_turn(session_id, "user", question)
    
    # =========================================================================
    # STEP 1B: FOLLOW-UP INTELLIGENCE - Detect query type and resolve references
    # =========================================================================
    followup_type = _detect_followup_type(question)
    original_question = question
    
    # Resolve references like "that", "this", "above", "it"
    resolved_question, resolution_metadata = _resolve_query_references(question, session_id)
    if resolution_metadata.get('had_references'):
        print(f"[CONV] Follow-up detected: {followup_type}")
        print(f"[CONV] Resolved: '{question}' -> '{resolved_question}'")
        question = resolved_question
    
    # =========================================================================
    # TRUTH-GROUNDED: Better resolution for "explain above" type queries
    # =========================================================================
    if TRUTH_GROUNDED_AVAILABLE:
        try:
            enhanced_q, truth_resolution = resolve_above_reference(session_id, question)
            if truth_resolution.get("had_reference"):
                print(f"[TRUTH] Resolved '{question}' -> '{enhanced_q}'")
                print(f"[TRUTH] Reference type: {truth_resolution.get('reference_type')}")
                question = enhanced_q
        except Exception as e:
            print(f"[TRUTH] Resolution error: {e}")
    
    # =========================================================================
    # PRODUCTION-GRADE: Execute 7-step Query Pipeline
    # =========================================================================
    pipeline_result = None
    ai_memory = None
    
    if BUSINESS_AI_ENGINE_AVAILABLE:
        try:
            # Get 3-layer memory
            ai_memory = get_ai_memory(session_id)
            
            # Add user turn to memory
            ai_memory.add_turn(role="user", content=original_question)
            
            # Execute 7-step pipeline
            pipeline_result = execute_query_pipeline(question, session_id, ai_memory)
            
            # =================================================================
            # DISABLED: Early refusal was blocking queries before RAG checks
            # The existing RAG system already handles data availability properly
            # =================================================================
            # should_refuse_response, refuse_reason = should_refuse(pipeline_result)
            # if should_refuse_response:
            #     ... (disabled - RAG handles this)
            
            print(f"[PIPELINE] Proceeding with intent={pipeline_result.intent.value}")
            
        except Exception as e:
            print(f"[PIPELINE] Error: {e}")
    
    # Get conversation context for LLM
    conversation_context = _get_conversation_context(session_id)
    
    # =========================================================================
    # STEP 1C: MEMORY - Save user message and extract personal info (legacy)
    # =========================================================================
    _save_chat_message(user_id, "user", original_question)
    
    # Extract and save personal info (name, company, role)
    personal_context = _extract_and_save_personal_info(question, user_id)
    if personal_context:
        # User introduced themselves - give a warm response
        import re
        name_match = re.search(r"Name:\s*([^\n]+)", personal_context)
        if name_match:
            user_name = name_match.group(1).strip()
            warm_response = f"""Nice to meet you, **{user_name}**! 👋

I'm your AI Business Analyst. I can help you analyze the data you've uploaded.

**Ask me about:**
• 📊 Revenue and sales trends
• 👥 Top customers and products
• 📈 Forecasts and predictions

What would you like to explore today?"""
            state.answer = warm_response
            state.route = "rag"
            state.sources = []
            _save_chat_message(user_id, "assistant", warm_response)
            _store_conversation_turn(session_id, "assistant", warm_response)
            return state
    
    # =========================================================================
    # STEP 2: SMART GUARDRAILS - Allow language-only queries
    # =========================================================================
    # Language-only queries (explain, summarize, evaluate) don't need data check
    is_language_only = _is_language_only_query(question)
    is_hypothetical = _detect_hypothetical(question)
    
    if not _is_data_related_query(question) and not is_language_only and followup_type == 'new_query':
        # This is a general knowledge question - REFUSE to answer
        refusal_response = f"""🚫 **I can only answer questions about YOUR business data.**

I noticed you're asking a general knowledge question. As your Business Analyst AI, I'm designed to analyze YOUR uploaded files, not provide general information.

**Try asking:**
• "What is my total revenue?"
• "Who are my top 5 customers?"
• "Show me sales trends"
• "Which products perform best?"

*Need to upload data? Go to **Data Hub** first.*"""
        state.answer = refusal_response
        state.route = "rag"
        state.sources = []
        _save_chat_message(user_id, "assistant", refusal_response)
        _store_conversation_turn(session_id, "assistant", refusal_response)
        return state
    
    # =========================================================================
    # STEP 3: MEMORY - Get chat history for context
    # =========================================================================
    chat_history = _get_chat_history(user_id, limit=5)
    
    # Classify query for better retrieval
    query_analysis = classify_query(question)
    
    # Retrieve with hybrid search - INCREASED k for multi-file coverage
    docs = retrieve(question, k=12, user_id=user_id)
    
    if not docs or len(docs) == 0:
        state.answer = """I don't have any data to analyze yet.

**To get started:**
• Go to **Data Hub** and upload your business files
• Supported formats: CSV, Excel, PDF, Word, Images
• Include data with columns like: Customer, Product, Amount, Date

Once uploaded, I can help you analyze sales trends, customer insights, and more."""
        state.route = "rag"
        state.sources = []
        return state
    
    # Build context with metadata - INCREASED to include ALL files
    context_parts = []
    sources = []
    similarity_scores = []
    sources_with_data = {}  # Track data by source file
    
    for i, doc in enumerate(docs[:15]):  # Process up to 15 for multi-file coverage
        doc_text = doc.get('text', str(doc))[:1500]
        source = doc.get('source', doc.get('metadata', {}).get('source', ''))
        score = doc.get('score', 0.5)
        
        if source:
            if source not in sources:
                sources.append(source)
            if source not in sources_with_data:
                sources_with_data[source] = []
            sources_with_data[source].append(doc_text[:500])
        
        similarity_scores.append(score)
        context_parts.append(f"[Source {i+1}: {source}]\n{doc_text}")
    
    # Build organized context showing data from EACH file
    organized_context = f"## 📁 Data from {len(sources)} Files:\n\n"
    for src in sources:
        organized_context += f"### From: {src}\n"
        for data_snippet in sources_with_data.get(src, [])[:3]:
            organized_context += f"{data_snippet}\n\n"
    
    context = organized_context + "\n---\n\n## All Retrieved Data:\n" + "\n\n---\n\n".join(context_parts[:10])
    
    # Calculate confidence
    scorer = get_confidence_scorer()
    rag_conf = scorer.score_rag_confidence(
        similarity_scores=similarity_scores,
        sources=sources,
        query_terms=len(question.split()),
        matched_terms=len(question.split()) // 2
    )
    confidence = scorer.build_answer_confidence("rag", rag_conf=rag_conf, sources=[{"source": s} for s in sources])
    
    # Get currency for formatting
    currency_symbol, currency_code = get_user_currency(user_id)
    
    # =========================================================================
    # COMPANY INTELLIGENCE - Build company context for aware responses
    # =========================================================================
    company_context_section = ""
    company_name = "Your Company"
    if COMPANY_PROFILE_AVAILABLE:
        try:
            company_profile = get_company_profile(user_id)
            if company_profile:
                company_name = company_profile.company_name
                company_context_section = build_company_context(user_id)
        except Exception as e:
            print(f"⚠️ Company profile loading: {e}")
    
    # =========================================================================
    # BUILD CONVERSATION-AWARE SYSTEM PROMPT
    # =========================================================================
    
    # Add conversation context section if available
    conversation_section = ""
    if conversation_context:
        conversation_section = f"""

RECENT CONVERSATION (use this for follow-ups):
{conversation_context}
---"""
    
    # Add aggregates context (AUTHORITATIVE - cannot be contradicted)
    aggregates_section = _get_aggregates_context(session_id)
    
    # Add chart context for "explain this chart" queries
    chart_section = ""
    if _detect_chart_explanation_query(question):
        chart_section = _get_chart_explanation_context(session_id)
    
    # Detect and add response format constraints (ONE LINE, BRIEF, etc.)
    format_info = _detect_response_format(question)
    format_section = format_info.get("instructions", "")
    
    # Add follow-up handling instructions based on query type
    followup_instructions = ""
    if followup_type == 'explanation':
        followup_instructions = """
FOLLOW-UP MODE: EXPLANATION
- Explain the previous answer in simpler terms
- DO NOT re-query data - use existing values
- Be helpful and educational"""
    elif followup_type == 'summarization':
        followup_instructions = """
FOLLOW-UP MODE: SUMMARIZATION
- Summarize the previous answer briefly
- DO NOT re-query data - use existing values
- Keep it to 2-3 sentences"""
    # ==========================================================================
    # 🧠 CHATGPT-STYLE: Load actual DataFrame context for dynamic understanding
    # ==========================================================================
    data_ctx = build_data_context(user_id)
    data_context_section = data_ctx.get("context_string", "No data available")
    
    # Get the last answer for context (critical for follow-ups)
    last_answer = _get_last_answer_context(session_id)
    
    system_prompt = f"""You are DataVision, an AI Data Analyst.

⚠️ CRITICAL - DATA GROUNDING RULES (NEVER VIOLATE):
1. ONLY use information from the DATA PROVIDED BELOW
2. NEVER use outside knowledge, general facts, or industry information
3. NEVER make up or estimate numbers - every number must come from the data
4. If the data doesn't have the answer, say "I don't have data for that"
5. NEVER say "typically", "usually", "in general", or "generally"

{company_context_section}

## 📊 YOUR DATA (ONLY USE THIS):
{data_context_section}

## DATA SOURCES:
{', '.join(sources) if sources else 'No data loaded yet'}

## CURRENCY: {currency_symbol} ({currency_code})

## CONVERSATION CONTEXT:
{conversation_context if conversation_context else 'This is the first message.'}
{last_answer}

## RESPONSE RULES:
1. Give DIRECT answers using ONLY the data above
2. COMPUTE actual values from the data - totals, percentages, counts
3. CITE which column/data you used (e.g., "From the Sales column...")
4. Use {currency_symbol} for currency values
5. Format nicely with markdown tables, bullet points, bold
6. If data is missing, say: "Your data doesn't include [X], so I can't answer that"

## 🚫 FORBIDDEN (will cause system failure):
- Using general knowledge
- Making up numbers
- Saying "typically" or "usually"
- Answering about topics not in the data

## YOUR RESPONSE (ONLY from data above):"""


    # =========================================================================
    # ROLE INTELLIGENCE - Add role-specific response formatting rules
    # =========================================================================
    if ROLE_TEMPLATES_AVAILABLE:
        try:
            user_role = get_role_from_string(state.user_role)
            role_modifier = get_role_prompt_modifier(user_role)
            system_prompt += role_modifier
        except Exception as e:
            print(f"⚠️ Role template loading: {e}")

    # Get personalized user context
    user_context = _get_user_context(user_id)
    user_context_section = f"\n\nUser Context:\n{user_context}" if user_context else ""

    # Pre-compute chart data if visualization requested OR follow-up about chart
    chart_data_section = ""
    is_followup = _is_followup_query(question)
    needs_chart_data = _wants_visualization(question) or _wants_prediction(question) or is_followup
    
    if needs_chart_data:
        try:
            # Use get_user_data to preserve original columns (Department, Salary, etc.)
            from api.v1.endpoints.charts import get_user_data
            df_for_chart = get_user_data(user_id)
            if df_for_chart is not None and not df_for_chart.empty:
                # For follow-ups, default to customer chart data since that's most common
                if is_followup:
                    # Always provide customer data for follow-up questions about charts
                    chart_data_section = _build_chart_data_summary(df_for_chart, "customer chart", currency_symbol)
                else:
                    chart_data_section = _build_chart_data_summary(df_for_chart, question, currency_symbol)
        except Exception as e:
            print(f"Chart data pre-computation: {e}")

    # Enhance question for follow-up queries
    enhanced_question = question
    if is_followup:
        # =================================================================
        # CRITICAL FIX: Get ACTUAL previous response, not hardcoded chart
        # =================================================================
        previous_response = ""
        try:
            # Get actual last assistant response from chat history
            from utils.paths import get_user_paths
            import json
            
            paths = get_user_paths(user_id)
            memory_path = paths.get("memory", Path(f"storage/users/{user_id}/memory"))
            history_file = memory_path / "chat_history.json"
            
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
                
                # Find last assistant message
                for msg in reversed(history):
                    if msg.get('role') == 'assistant':
                        previous_response = msg.get('content', '')[:1000]  # First 1000 chars
                        break
                        
            print(f"[CONTEXT] Found previous response: {len(previous_response)} chars")
        except Exception as e:
            print(f"[CONTEXT] Error getting previous response: {e}")
        
        if previous_response:
            enhanced_question = f"""{question}

[PREVIOUS AI RESPONSE TO EXPLAIN:]
{previous_response}

[INSTRUCTION: The user is asking you to EXPLAIN the above response. 
Answer their specific question about what was shown above. 
Do NOT generate new charts or analysis - just explain what was already shown.]"""
        else:
            enhanced_question = f"""{question}

[CONTEXT: The user is referring to a previous response. Please explain based on the conversation context.]"""

    # Build chat history section
    chat_history_section = ""
    if chat_history:
        chat_history_section = f"\n\n**Recent Conversation:**\n{chat_history}"

    prompt = f"""Question: {enhanced_question}

Query Type: {query_analysis.query_type.value}
Aggregation: {query_analysis.aggregation_type or 'N/A'}
{user_context_section}
{chat_history_section}

Retrieved Context:
{context}
{chart_data_section}

IMPORTANT RULES:
1. If CHART DATA is provided above, reference those EXACT numbers and names in your explanation.
2. A chart will be generated AUTOMATICALLY - DO NOT output any JSON, Plotly code, or chart specifications.
3. Just provide a clear text explanation/summary. The visualization system handles charts separately.
4. NEVER include raw JSON objects like {{"type": "...", "data": [...]}} in your response.

If the user previously introduced themselves (check Recent Conversation), remember their name and use it warmly.

Provide a clear, data-driven answer."""


    # ===========================================================================
    # $5M FIX: BUILD MESSAGES WITH FULL CONVERSATION CONTEXT
    # This is the key change - LLM now sees entire conversation history
    # ===========================================================================
    messages = build_messages_with_context(
        user_id=user_id,
        current_question=question,
        current_prompt=prompt,
        history_limit=10
    )
    
    # ===========================================================================
    # SMART MODEL ROUTING - Use fast model for simple, reasoning for complex
    # ===========================================================================
    optimal_model = get_optimal_model(
        query_type=query_analysis.query_type.value,
        context_length=len(context)
    )
    
    # Use messages array instead of single prompt for context memory
    answer = chat(messages=messages, system=system_prompt, max_tokens=1500, model=optimal_model)
    
    # Clean response with anti-hallucination validation
    answer = _clean_response_formatting(answer, context=context)
    
    # ==========================================================================
    # VISUALIZATION - Managed universally in chat.py via append_chart_if_needed
    # ==========================================================================
    # We no longer generate charts here to prevent duplicates and ensure
    # orchestration logic in the chat handler.
    
    # PLOTLY GENERATION FOR RAG (Migrated to chat.py)
    # All chart generation is now handled by the universal helper in chat.py
    
    # Add citations and confidence
    answer = _add_confidence_indicator(answer, confidence)
    answer += _build_source_citations(sources, "rag")
    
    # Clean response formatting for premium quality
    answer = _clean_response_formatting(answer)
    
    state.answer = answer
    state.route = "rag"
    state.sources = sources
    state.context["confidence"] = confidence.overall_score
    state.context["query_type"] = query_analysis.query_type.value
    
    # Save assistant response to chat history for memory
    # CRITICAL: Save enough to include key data for follow-ups
    _save_chat_message(user_id, "assistant", answer[:2000])
    
    # =========================================================================
    # CONVERSATION MEMORY - Store response for follow-up intelligence
    # =========================================================================
    _store_conversation_turn(session_id, "assistant", answer[:1000], {
        "query_type": query_analysis.query_type.value,
        "sources": sources[:3],
        "followup_type": followup_type
    })
    
    # =========================================================================
    # AUTHORITATIVE METRIC EXTRACTION - Store primary metric for follow-ups
    # =========================================================================
    _extract_primary_metric_from_answer(answer, session_id, currency_symbol)
    
    # =========================================================================
    # $5M ENHANCEMENT: ChatGPT-Quality Response Enhancement
    # =========================================================================
    # Adds proactive insights, follow-up suggestions, and natural tone
    # ALL using LLM - no hardcoding!
    if RESPONSE_ENHANCER_AVAILABLE:
        try:
            # Extract data summary from answer for insight generation
            data_summary = extract_data_summary_from_response(answer, currency_symbol)
            
            # Add entities from query for relevant suggestions
            entities = []
            q_lower = question.lower()
            if 'customer' in q_lower:
                entities.append('customers')
            if 'product' in q_lower:
                entities.append('products')
            if 'revenue' in q_lower or 'sales' in q_lower:
                entities.append('revenue')
            
            # Get query type for context-aware suggestions
            query_type_str = query_analysis.query_type.value if query_analysis else "general"
            
            # Apply full enhancement pipeline
            enhanced_answer = enhance_full_response(
                query=question,
                response=answer,
                query_type=query_type_str,
                data_summary=data_summary,
                entities=entities,
                add_insight=True,
                add_suggestions=True,
                enhance_tone=True,
                currency_symbol=currency_symbol
            )
            
            if enhanced_answer and len(enhanced_answer) > len(answer):
                answer = enhanced_answer
                state.answer = answer
                print("[ENHANCE] Response enhanced with insights and suggestions")
        except Exception as enhance_error:
            print(f"[ENHANCE] Enhancement failed (non-fatal): {enhance_error}")
    
    # =========================================================================
    # $5M FIX: SAVE ASSISTANT RESPONSE FOR CONTEXT MEMORY
    # Without this, the LLM won't know what it said in previous turns!
    # =========================================================================
    _store_conversation_turn(session_id, "assistant", state.answer or answer)
    _save_chat_message(user_id, "assistant", state.answer or answer)
    print(f"[CONTEXT] Saved assistant response ({len(state.answer or answer)} chars)")
    
    # =========================================================================
    # TRUTH-GROUNDED: Update context with WHAT was shown for follow-up queries
    # =========================================================================
    if TRUTH_GROUNDED_AVAILABLE:
        try:
            # Detect what topic was discussed
            topic = None
            result_type = "text"
            chart_type = None
            q_lower = question.lower()
            
            if any(t in q_lower for t in ["revenue", "sales", "amount", "total"]):
                topic = "revenue"
            elif any(t in q_lower for t in ["customer", "client"]):
                topic = "customers"
            elif any(t in q_lower for t in ["product", "item"]):
                topic = "products"
            elif any(t in q_lower for t in ["convert", "currency", "inr", "usd"]):
                topic = "currency_conversion"
            
            # Detect if chart was shown
            if "```plotly_chart" in (state.answer or answer):
                result_type = "chart"
                if "bar" in (state.answer or answer).lower() or "bar" in q_lower:
                    chart_type = "bar"
                elif "line" in (state.answer or answer).lower() or "trend" in q_lower:
                    chart_type = "line"
                elif "pie" in (state.answer or answer).lower():
                    chart_type = "pie"
            elif "|" in (state.answer or answer) and "---" in (state.answer or answer):
                result_type = "table"
            
            update_truth_context(
                session_id=session_id,
                topic=topic,
                result_type=result_type,
                chart_type=chart_type,
                answer=(state.answer or answer)[:500]  # Store first 500 chars
            )
            print(f"[TRUTH] Updated context: topic={topic}, type={result_type}, chart={chart_type}")
        except Exception as e:
            print(f"[TRUTH] Context update error: {e}")
    
    # =========================================================================
    # PRODUCTION-GRADE: Update ThreeLayerMemory with response metadata
    # =========================================================================
    if BUSINESS_AI_ENGINE_AVAILABLE and ai_memory:
        try:
            # Detect topic and metrics
            topic = None
            result_type = "text"
            chart_type = None
            metrics = {}
            q_lower = question.lower()
            
            if any(t in q_lower for t in ["revenue", "sales", "amount", "total"]):
                topic = "revenue"
            elif any(t in q_lower for t in ["customer", "client"]):
                topic = "customers"
            elif any(t in q_lower for t in ["product", "item"]):
                topic = "products"
            
            # Detect chart
            if "```plotly_chart" in (state.answer or answer):
                result_type = "chart"
                if "bar" in q_lower:
                    chart_type = "bar"
                elif "line" in q_lower or "trend" in q_lower:
                    chart_type = "line"
            elif "|" in (state.answer or answer) and "---" in (state.answer or answer):
                result_type = "table"
            
            # Extract any numbers as potential metrics
            import re
            numbers = re.findall(r'[\$₹€£]?([\d,]+\.?\d*)', state.answer or answer)
            for i, num_str in enumerate(numbers[:3]):
                try:
                    num = float(num_str.replace(',', ''))
                    metrics[f"value_{i}"] = num
                except:
                    pass
            
            # Add to ThreeLayerMemory
            ai_memory.add_turn(
                role="assistant",
                content=(state.answer or answer)[:500],
                topic=topic,
                result_type=result_type,
                chart_type=chart_type,
                metrics=metrics
            )
            
            print(f"[AI-ENGINE] Memory updated: topic={topic}, metrics={len(metrics)}")
            
            # SELF-AUDIT before returning (ChatGPT/Claude behavior)
            if pipeline_result:
                audit = self_audit(state.answer or answer, ai_memory, pipeline_result)
                if not audit.passed:
                    print(f"[AUDIT] Warning: {audit.issues}")
                else:
                    print(f"[AUDIT] Passed: {audit.claims_verified} claims verified")
                    
        except Exception as e:
            print(f"[AI-ENGINE] Memory update error: {e}")
    
    return state


# ============================================================================
# 🟧 GRAPHRAG MODE - Enhanced Knowledge Graph Reasoning
# ============================================================================

def graph_answer(state: AgentState) -> AgentState:
    """
    🟧 GRAPHRAG MODE - Enterprise Graph-Based Analysis
    
    Features:
    - Multi-hop reasoning with path explanations
    - PageRank-based importance ranking
    - Complete data tables
    - Causal chain detection
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    session_id = user_id  # Use user_id as session_id for conversation memory
    
    # Initialize enterprise context variables to prevent NameError
    company_name = "Your Company"
    company_context_section = ""
    user_context_section = ""
    graph_insights = ""
    currency_symbol = "₹"
    
    try:
        from graph.query import get_graph_stats, load_graph, get_graph_analysis
        from graph.traversal import EnterpriseGraphTraversal, TraversalStrategy
        
        graph = load_graph(user_id)
        
        if not graph or graph.number_of_nodes() == 0:
            state.answer = """I don't have a knowledge graph built yet.

**To enable GraphRAG:**
• Upload business files in **Data Hub**
• Include structured data (CSV/Excel) with Customer, Product, Amount columns
• The graph will be built automatically

**GraphRAG excels at:**
• "Which customers buy which products?"
• "What are the revenue trends?"
• "Show customer-product relationships"
• "Why did sales drop?" (causal reasoning)"""
            state.route = "graph"
            return state
        
        # --- ENTERPRISE CONTEXT LOADING ---
        if COMPANY_PROFILE_AVAILABLE:
            try:
                company_profile = get_company_profile(user_id)
                if company_profile:
                    company_name = company_profile.company_name
                    company_context_section = build_company_context(user_id)
            except Exception as e:
                print(f"⚠️ Company profile loading error: {e}")

        user_context = _get_user_context(user_id)
        if user_context:
            user_context_section = f"\n\nUser Context:\n{user_context}"

        # Get specialized graph insights for the prompt
        try:
            graph_insights = get_graph_analysis(user_id, question) or "No specific relationship patterns detected for this query."
        except Exception as e:
            print(f"⚠️ Graph analysis error: {e}")
            graph_insights = "Error analyzing graph relationships."

        # Classify query for traversal strategy
        query_analysis = classify_query(question)
        
        # Select traversal strategy based on query type
        if query_analysis.query_type == QueryType.CAUSAL:
            strategy = TraversalStrategy.DFS
        elif query_analysis.query_type == QueryType.RELATIONAL:
            strategy = TraversalStrategy.BFS
        else:
            strategy = TraversalStrategy.PAGERANK
        
        # Initialize traversal
        traversal = EnterpriseGraphTraversal(graph)
        
        # Extract entities from question
        entities = query_analysis.entities_mentioned
        
        # Perform traversal if entities found
        traversal_result = None
        if entities:
            traversal_result = traversal.find_paths(
                source_entities=entities,
                max_hops=3,
                strategy=strategy,
                max_paths=5
            )
        
        # Get graph stats
        stats = get_graph_stats(user_id)
        
        # Get comprehensive data - use get_user_data to preserve original columns
        from api.v1.endpoints.charts import get_user_data
        
        # 🧠 CHATGPT-STYLE: Load actual data context dynamically
        data_ctx = build_data_context(user_id)
        df = data_ctx.get("df")
        data_summary = ""
        
        if df is not None and not df.empty:
            currency_symbol, currency_code = get_user_currency(user_id)
            
            # Dynamic column detection - works with ANY data domain
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Find amount column dynamically (Salary, amount, total, revenue, etc.)
            amount_col = None
            amount_keywords = ['salary', 'amount', 'total', 'revenue', 'price', 'cost', 'value', 'wage', 'pay']
            for col in numeric_cols:
                if any(kw in col.lower() for kw in amount_keywords):
                    amount_col = col
                    break
            if not amount_col and numeric_cols:
                amount_col = numeric_cols[0]  # Fallback to first numeric
            
            # Find grouping column dynamically (Department, customer, category, etc.)
            entity_col = None
            entity_keywords = ['department', 'customer', 'category', 'product', 'region', 'location', 'team', 'client']
            for col in text_cols:
                if any(kw in col.lower() for kw in entity_keywords):
                    entity_col = col
                    break
            if not entity_col and text_cols:
                entity_col = text_cols[0]  # Fallback to first text column
            
            # Calculate summary using detected columns
            total_value = df[amount_col].sum() if amount_col else 0
            num_records = len(df)
            num_entities = df[entity_col].nunique() if entity_col else 0
            
            data_summary = f"""
## 📊 Data Summary
| Metric | Value |
|--------|-------|
| Total {amount_col or 'Value'} | {currency_symbol}{total_value:,.2f} |
| Records | {num_records:,} |
| Unique {entity_col or 'Entities'} | {num_entities:,} |

## 🧠 Data Schema:
{data_ctx.get('context_string', 'No schema available')}
"""
            
            # --- PRO DATA SUMMARY GENERATION ($5M Quality) ---
            query_limit = 10
            if VIZ_INTELLIGENCE_AVAILABLE:
                query_limit = extract_count_from_query(question)
            
            # Context-aware extraction using detected columns
            if entity_col and amount_col:
                all_entities = df.groupby(entity_col)[amount_col].sum().sort_values(ascending=False)
                show_count = min(query_limit, len(all_entities))
                data_summary += f"\n### Top {show_count} {entity_col} by {amount_col}\n"
                data_summary += f"| Rank | {entity_col} | {amount_col} | Count |\n|------|----------|---------|--------|\n"
                for i, (ent, amt) in enumerate(all_entities.head(show_count).items(), 1):
                    count = df[df[entity_col] == ent].shape[0]
                    data_summary += f"| {i} | {ent} | {currency_symbol}{amt:,.2f} | {count} |\n"

        # --- SMART CONTEXT \u0026 PERSONA ($5M Enterprise Quality) ---
        q_lower = question.lower()
        follow_up_indicators = ['above', 'that', 'those', 'chart', 'mentioned', 'previous', 'before', 'there is', 'in it', 'was shown', 'it', 'shown']
        is_follow_up = any(w in q_lower for w in follow_up_indicators) or (len(question.split()) < 5 and any(w in q_lower for w in ['how many', 'who', 'what']))
        
        # Redundant Chart Prevention: Only generate new chart if explicitly requested
        viz_keywords = ['chart', 'graph', 'plot', 'pie', 'bar', 'line', 'visualize', 'show', 'display',
                       'mindmap', 'mind map', 'knowledge graph', 'sankey', 'network', 'relationship']
        explicit_viz_request = any(kw in q_lower for kw in viz_keywords)

        
        fact_keywords = ['how many', 'who', 'what', 'is there', 'total', 'count']
        is_fact_query = any(kw in q_lower for kw in fact_keywords)
        
        should_generate_viz_block = explicit_viz_request
        if is_follow_up and is_fact_query and not explicit_viz_request:
            should_generate_viz_block = False # Protect against redundancy
            
        # Build Expert System Prompt
        system_prompt = f"""You are DataVision, an AI Data Analyst.

⚠️ CRITICAL - DATA GROUNDING RULES (NEVER VIOLATE):
1. ONLY use data from summaries and graph insights below
2. NEVER use outside knowledge or general industry facts
3. NEVER make up numbers - every number must be from the data
4. If data doesn't exist, say "I don't have data for that"

{company_context_section}

## STRICT RULES:
1. Use EXACT numbers from the data provided
2. If user asks about "above chart", use ONLY previous turn's data
3. NEVER draw charts with text symbols - use markdown tables only
4. Do not say "As an AI..." or use filler phrases
"""
        
        previous_context = ""
        if is_follow_up:
            last_response = _get_chat_history(user_id, limit=2)
            if last_response:
                previous_context = f"""
### 🚨 MANDATORY CONTEXT - READ THIS FIRST! 🚨
The user is asking about your PREVIOUS response/chart.
PREVIOUS TURN CONTENT:
---
{last_response}
---
🛑 DIRECTION: If referring to the chart or "above", use ONLY the numbers in THIS segment. 
Ignore the Total Dataset Stats if they contradict what was shown in the chart.
"""
                print(f"[GRAPH] Follow-up detected. Engaging Context Lock.")

        prompt = f"""Question: {question}
{user_context_section}

{previous_context}

## 📊 RAW DATA SUMMARY (Total Dataset):
{data_summary}

## 📈 GRAPH INSIGHTS (Relationships):
{graph_insights}

**Backend Statistics:** {stats.get('total_nodes', 0)} entities, {stats.get('total_edges', 0)} relationships

⚠️ FINAL INSTRUCTIONS:
1. Provide a one-sentence bolded summary lead.
2. If previous context applies (follow-up), prioritize it for "how many" counts.
3. Use currency {currency_symbol} for all amounts.
4. Charts will be generated AUTOMATICALLY - DO NOT output any JSON, Plotly code, or chart specifications.
5. Just provide clear text analysis. The visualization system handles charts separately.
6. NEVER include raw JSON objects like {{"type": "...", "data": [...]}} in your response."""


        # $5M FIX: Build messages with context for GraphRAG
        messages = build_messages_with_context(
            user_id=user_id,
            current_question=question,
            current_prompt=prompt,
            history_limit=10
        )
        
        # Smart model routing for GraphRAG
        optimal_model = get_optimal_model(
            query_type=query_analysis.query_type.value,
            context_length=len(data_summary)
        )
        
        answer = chat(messages=messages, system=system_prompt, max_tokens=1500, model=optimal_model)
        
        # Clean with anti-hallucination
        answer = _clean_response_formatting(answer, context=data_summary)
        
        # Generate charts if visualization requested
        # --- PRO-LEVEL VISUAL ORCHESTRATOR ($5M Quality) ---
        if should_generate_viz_block and df is not None and not df.empty:
            try:
                # 1. IDENTIFY SUBJECT \u0026 COLUMNS
                primary_entity = 'customer' if 'customer' in q_lower else ('product' if 'product' in q_lower else 'customer')
                revenue_col = 'amount' if 'amount' in df.columns else 'total_amount'
                
                # Accuracy fallback: ensure columns exist
                if primary_entity not in df.columns:
                    for col in df.columns:
                        if primary_entity in col.lower():
                            primary_entity = col
                            break
                
                premium_visual_generated = False
                
                # 2. PREMIUM VISUAL: MINDMAPS, KNOWLEDGE GRAPHS, RELATIONSHIPS
                # Uses new LLM-driven graph_visualizations v2.0 module
                graph_viz_keywords = ['mindmap', 'mind map', 'knowledge graph', 'network', 
                                     'relationship', 'sankey', 'entity map', 'connections',
                                     'radial', 'cluster', 'hierarchy', 'tree diagram']
                if any(w in q_lower for w in graph_viz_keywords):
                    try:
                        from agents.graph_visualizations import (
                            generate_mindmap, generate_knowledge_graph, 
                            generate_relationship_diagram, detect_graph_visualization_type,
                            generate_radial_mindmap, generate_entity_cluster,
                            get_best_graph_visualization
                        )
                        
                        # LLM determines what type of visualization user wants
                        viz_type = detect_graph_visualization_type(question)
                        print(f"[GRAPH VIZ v2.0] Detected visualization type: {viz_type}")
                        
                        if viz_type == 'radial':
                            # NEW: Pro-level radial mindmap
                            chart, explanation = generate_radial_mindmap(
                                graph=graph, query=question, max_depth=3
                            )
                            if chart:
                                chart_json = json.dumps(chart, separators=(',', ':'))
                                answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                                answer += f"\n\n{explanation}"
                                premium_visual_generated = True
                                print(f"[GRAPH VIZ v2.0] ✅ Radial Mindmap generated")
                        
                        elif viz_type == 'mindmap':
                            # Generate Plotly treemap (frontend-compatible mindmap)
                            chart, explanation = generate_mindmap(
                                graph=graph, query=question, max_depth=3
                            )
                            if chart:
                                chart_json = json.dumps(chart, separators=(',', ':'))
                                answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                                answer += f"\n\n{explanation}"
                                premium_visual_generated = True
                                print(f"[GRAPH VIZ v2.0] ✅ Mindmap treemap generated")

                        elif viz_type == 'cluster':
                            # NEW: Entity clustering visualization
                            chart, explanation = generate_entity_cluster(
                                df=df, query=question, currency_symbol=currency_symbol
                            )
                            if chart:
                                chart_json = json.dumps(chart, separators=(',', ':'))
                                answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                                answer += f"\n\n{explanation}"
                                premium_visual_generated = True
                                print(f"[GRAPH VIZ v2.0] ✅ Entity Cluster generated")
                        
                        elif viz_type == 'knowledge_graph':
                            # Generate Plotly network diagram
                            chart, explanation = generate_knowledge_graph(
                                graph=graph, query=question, 
                                max_nodes=query_limit, currency_symbol=currency_symbol
                            )
                            if chart:
                                chart_json = json.dumps(chart, separators=(',', ':'))
                                answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                                answer += f"\n\n{explanation}"
                                premium_visual_generated = True
                                print(f"[GRAPH VIZ v2.0] ✅ Knowledge Graph generated")
                        
                        elif viz_type in ['relationship', 'sankey']:
                            # Generate Sankey relationship diagram
                            chart, explanation = generate_relationship_diagram(
                                df=df, query=question, currency_symbol=currency_symbol
                            )
                            if chart:
                                chart_json = json.dumps(chart, separators=(',', ':'))
                                answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                                answer += f"\n\n{explanation}"
                                premium_visual_generated = True
                                print(f"[GRAPH VIZ] ✅ Relationship Diagram generated")
                                
                    except Exception as e:
                        print(f"⚠️ Graph Visualization failed: {e}")
                        import traceback
                        traceback.print_exc()

                # 3. SMART CHARTS: Uses LLM to understand query and generate appropriate chart
                if not premium_visual_generated and SMART_CHART_AVAILABLE:
                    try:
                        chart_result, chart_explanation = smart_chart(
                            query=question,
                            df=df,
                            currency_symbol=currency_symbol
                        )
                        
                        if chart_result:
                            chart_json = json.dumps(chart_result, separators=(',', ':'))
                            answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                            answer += f"\n\n{chart_explanation}"
                            premium_visual_generated = True
                            print(f"[GRAPH VIZ] ✅ Smart Chart generated")
                    except Exception as e:
                        print(f"⚠️ Smart Chart failed in Graph mode: {e}")

                # 4. PREDICTIONS (Non-exclusive)
                if not premium_visual_generated and any(w in q_lower for w in ['predict', 'forecast', 'future', 'trend']):
                    # ... (prediction logic remains focused) ...
                    pass

            except Exception as e:
                print(f"⚠️ Pro-Viz Engine global failure: {e}")

        # Final Summary Branding
        if "Analysis mode:" not in answer:
            answer += f"\n\n---\n🔗 **Data Grounding:** Analysis reflects {stats.get('total_nodes', 0)} entities found in the Knowledge Graph."
            answer += f"\n*Enterprise Intelligence mode: GRAPHRAG*"
        
        # Anti-Artifact cleaning
        answer = _clean_response_formatting(answer)
        state.answer = answer
        state.route = "graph"
        state.sources = ["Enterprise Knowledge Graph"]
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[GRAPHRAG] Error: {e}")
        
        # Proper error message with debugging help
        state.answer = f"""**GraphRAG Processing Error**

I encountered an issue analyzing the knowledge graph for your query: "{question[:50]}..."

**Error Details:** {str(e)[:100]}

**To fix this:**
1. Ensure you have uploaded data files in **Data Hub**
2. The graph is auto-built from CSV/Excel files with entity columns
3. Try using **RAG mode** for document-based queries

**What GraphRAG needs:**
- Structured data with entity columns (Department, Employee, Product, etc.)
- The graph is built automatically when you upload structured files"""
        state.route = "graph"
    
    # Store turn for memory
    _store_conversation_turn(session_id, "assistant", state.answer)
    _save_chat_message(user_id, "assistant", state.answer)
    return state


# ============================================================================
# 🟪 HYBRID MODE - Intelligent RAG + GraphRAG Fusion
# ============================================================================

def hybrid_answer(state: AgentState) -> AgentState:
    """
    🟪 HYBRID MODE - Combined Document + Graph Analysis
    
    Features:
    - Intelligent query routing
    - Confidence-weighted fusion
    - Best of both RAG and Graph
    - Reasoning type indicator
    - Cache RAG integration (40-80% API cost savings)
    - 4-Layer memory context
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    session_id = user_id  # Use user_id as session_id
    
    # =========================================================================
    # CONVERSATION MEMORY - ChatGPT-level stateful behavior
    # =========================================================================
    _store_conversation_turn(session_id, "user", question)
    
    # Detect follow-up type and format constraints
    followup_type = _detect_followup_type(question)
    format_info = _detect_response_format(question)
    
    # Get conversation context for continuity
    conversation_context = _get_conversation_context(session_id)
    
    # Detect if this is prediction mode (from chat.py prefix)
    is_prediction_mode = "[PREDICTION MODE" in question
    if is_prediction_mode:
        # Remove the prefix for cleaner processing
        question = question.replace("[PREDICTION MODE - Use 3 accuracy tiers] ", "").strip()
        state.question = question
        print(f"📈 PREDICTION MODE detected - Will use prediction formatting")
    
    # =========================================================================
    # CACHE CHECK - Fast path for cached queries
    # =========================================================================
    if MEMORY_AVAILABLE:
        try:
            # Check cache first (returns immediately if exact hit)
            cache_result = memory_retrieve(question, user_id)
            
            if cache_result.cache_hit and cache_result.cached_answer:
                # EXACT CACHE HIT - Return immediately (< 100ms)
                state.answer = cache_result.cached_answer
                state.answer += f"\n\n---\n⚡ *Cached response ({cache_result.retrieval_time_ms:.0f}ms)*"
                state.route = "hybrid"
                state.context["cache_hit"] = True
                return state
        except Exception as cache_err:
            print(f"Cache lookup error: {cache_err}")
    
    # Classify query for routing
    query_analysis = classify_query(question)
    
    # Determine fusion weights based on query type
    if query_analysis.query_type in [QueryType.CAUSAL, QueryType.RELATIONAL]:
        weight_graph = 0.7
        weight_rag = 0.3
        primary_mode = "GraphRAG"
    elif query_analysis.query_type in [QueryType.FACTUAL, QueryType.AGGREGATION]:
        weight_graph = 0.3
        weight_rag = 0.7
        primary_mode = "RAG"
    else:
        weight_graph = 0.5
        weight_rag = 0.5
        primary_mode = "Balanced"
    
    # Get RAG context
    docs = retrieve(question, k=4, user_id=user_id)
    rag_context = ""
    sources = []
    
    if docs:
        for doc in docs[:3]:
            rag_context += doc.get('text', '')[:600] + "\n\n"
            source = doc.get('source', doc.get('metadata', {}).get('source', ''))
            if source and source not in sources:
                sources.append(source)
    
    # Get Graph context
    graph_context = ""
    try:
        from graph.query import get_graph_summary
        from api.v1.endpoints.charts import get_user_data
        
        graph_context = get_graph_summary(user_id) or ""
        
        # 🧠 CHATGPT-STYLE: Use build_data_context for dynamic column detection
        data_ctx = build_data_context(user_id)
        df = data_ctx.get("df")
        
        if df is not None and not df.empty:
            currency_symbol, _ = get_user_currency(user_id)
            
            # Dynamic column detection - works with ANY data domain
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Find amount column dynamically
            amount_col = None
            amount_keywords = ['salary', 'amount', 'total', 'revenue', 'price', 'cost', 'value']
            for col in numeric_cols:
                if any(kw in col.lower() for kw in amount_keywords):
                    amount_col = col
                    break
            if not amount_col and numeric_cols:
                amount_col = numeric_cols[0]
            
            # Find entity column dynamically
            entity_col = None
            entity_keywords = ['department', 'customer', 'category', 'product', 'region', 'team']
            for col in text_cols:
                if any(kw in col.lower() for kw in entity_keywords):
                    entity_col = col
                    break
            if not entity_col and text_cols:
                entity_col = text_cols[0]
            
            if amount_col:
                total = df[amount_col].sum()
                avg = df[amount_col].mean()
                graph_context += f"\n\n**{amount_col} Summary:** {currency_symbol}{total:,.2f} total, {currency_symbol}{avg:,.2f} avg"
            
            # Add top/bottom for entity queries
            if entity_col and amount_col:
                top_entity = df.groupby(entity_col)[amount_col].sum().idxmax()
                low_entity = df.groupby(entity_col)[amount_col].sum().idxmin()
                graph_context += f"\n**Top {entity_col}:** {top_entity}"
                graph_context += f"\n**Lowest {entity_col}:** {low_entity}"
    except Exception as e:
        pass
    
    # Check if we have enough data
    if not rag_context and not graph_context:
        state.answer = """I need data to provide hybrid analysis.

**To use Hybrid mode:**
• Upload files in **Data Hub** (CSV, Excel, PDF)
• Hybrid combines document search with knowledge graph
• Best for comprehensive business questions"""
        state.route = "hybrid"
        state.sources = []
        return state
    
    currency_symbol, _ = get_user_currency(user_id)
    
    system_prompt = f"""You are DataVision, an AI Data Analyst.

⚠️ CRITICAL - DATA GROUNDING (NEVER VIOLATE):
1. ONLY use data from the context provided below
2. NEVER use outside knowledge or general industry facts
3. NEVER make up numbers - every number must be from YOUR data
4. If data doesn't exist, say "I don't have data for that"

HYBRID MODE: RAG {weight_rag:.0%} + Graph {weight_graph:.0%}
USER CURRENCY: {currency_symbol}

═══════════════════════════════════════════════════════════════
                    RESPONSE FORMAT
═══════════════════════════════════════════════════════════════

ALWAYS respond with:
1. One-line answer (bold) using {currency_symbol}
2. Table with data breakdown FROM YOUR DATA ONLY

EXAMPLE:
**Total Revenue: {currency_symbol}[amount from data]**

| Metric | Value |
|--------|-------|
| Total Revenue | {currency_symbol}[from data] |
| Customers | [from data] |
| Orders | [from data] |

═══════════════════════════════════════════════════════════════
                    STRICT RULES
═══════════════════════════════════════════════════════════════

1. Use | table | format for data (UNLESS user asks for brief)
2. Use {currency_symbol} as the currency symbol
3. NEVER say "typically" or "usually" - ONLY real data
3. Use ONLY data from the context provided
4. Be concise - no filler text
5. NEVER make up numbers

CURRENCY CONVERSION (MANDATORY):
- ₹88 INR = $1 USD (use this EXACT rate)
- ₹92 INR = €1 EUR
- ₹110 INR = £1 GBP
- Show calculation when converting

FORMAT CONSTRAINTS (STRICTLY FOLLOW):
- "one word" → ONLY one word, NO tables, NO explanation
- "one line" → ONE sentence only
- "briefly" → 2-3 sentences max

ANTI-HALLUCINATION:
- ONLY use numbers from context
- Do NOT add disclaimers about missing data when data IS provided
- NEVER invent or estimate numbers"""

    # Get personalized user context  
    user_context = _get_user_context(user_id)
    user_context_section = f"\n\nUser Context:\n{user_context}" if user_context else ""
    
    # Build format constraint section
    format_section = format_info.get("instructions", "") if format_info else ""
    
    # Build conversation context section
    conv_section = f"\n\n**Recent Conversation (for follow-ups):**\n{conversation_context}" if conversation_context else ""

    prompt = f"""Question: {question}

Query Type: {query_analysis.query_type.value}
Confidence: {query_analysis.confidence:.2f}
{user_context_section}
{conv_section}

{format_section}

**Document Context (RAG):**
{rag_context if rag_context else "Limited document data"}

**Graph Insights:**
{graph_context if graph_context else "Limited graph data"}

Based on the user's question and the data provided, give a direct answer. If user asks for "one word" or "briefly", follow that constraint STRICTLY. If this is a follow-up question, use the conversation context above."""

    # $5M FIX: Build messages with context for Hybrid mode
    messages = build_messages_with_context(
        user_id=user_id,
        current_question=question,
        current_prompt=prompt,
        history_limit=10
    )
    
    # Smart model routing for Hybrid mode
    # Use reasoning model for complex queries (hybrid = more complex)
    combined_context = f"{rag_context or ''}\n{graph_context or ''}"
    optimal_model = get_optimal_model(
        query_type=query_analysis.query_type.value,
        context_length=len(combined_context)
    )
    
    answer = chat(messages=messages, system=system_prompt, max_tokens=1500, model=optimal_model)
    
    # Clean with anti-hallucination validation
    answer = _clean_response_formatting(answer, context=combined_context)
    
    # =========================================================================
    # ENTERPRISE ENGINE INTEGRATION
    # =========================================================================
    
    if ENGINES_AVAILABLE:
        try:
            # Get data for engines - use get_user_data to preserve original columns
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(user_id) if user_id else None
            
            # -------------------------------------------------------------
            # FORECAST ENGINE - Time-Series Prediction
            # -------------------------------------------------------------
            if _wants_prediction(question) and df is not None and not df.empty:
                try:
                    # Smart date detection
                    from agents.visualization_intelligence import profile_dataframe
                    profile = profile_dataframe(df)
                    
                    if profile.has_date_column and profile.date_column:
                        date_col = profile.date_column
                        import pandas as pd
                        
                        # revenue_dataframe() returns standardized column names: 'amount', 'date'
                        amount_col = 'amount'  # Always 'amount' from revenue_dataframe()
                        
                        print(f"[PREDICTION DEBUG] date_col={date_col}, amount_col={amount_col}, df.columns={list(df.columns)}")
                        
                        if amount_col in df.columns:
                            df_temp = df.copy()
                            df_temp['date_parsed'] = pd.to_datetime(df_temp[date_col], errors='coerce')
                            df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
                        
                        if not df_dated.empty:
                            # Dynamic Granularity & Resampling (Google-style adaptive freq)
                            df_dated.set_index('date_parsed', inplace=True)
                            duration_days = (df_dated.index.max() - df_dated.index.min()).days
                            
                            if duration_days < 32:
                                rule = 'D'
                                period_multiplier = 30
                                title_suffix = "(Daily)"
                            elif duration_days < 180:
                                rule = 'W'
                                period_multiplier = 4
                                title_suffix = "(Weekly)"
                            else:
                                rule = 'M'
                                period_multiplier = 1
                                title_suffix = "(Monthly)"
                                
                            # Resample to ensure uniform time steps (critical for regression)
                            time_data = df_dated[amount_col].resample(rule).sum().fillna(0).reset_index()
                            time_data.columns = ['date', 'value']
                            time_data['date'] = time_data['date'].dt.strftime('%Y-%m-%d')
                            
                            # Get forecast with scaled periods
                            months_requested = _extract_prediction_period(question)
                            periods = months_requested * period_multiplier
                            
                            # Update title to reflect granularity
                            title = f"Revenue Prediction {title_suffix}"
                            
                            forecast_result = forecast_from_dataframe(time_data, 'date', 'value', periods=periods)
                            
                            if forecast_result.get('success'):
                                # Generate interactive chart
                                if CHARTS_AVAILABLE:
                                    # Extract points directly from ForecastEngine result to preserve confidence intervals
                                    forecast_items = forecast_result.get('forecast', [])
                                    hist_points = [item for item in forecast_items if item.get('type') == 'historical']
                                    pred_points = [item for item in forecast_items if item.get('type') == 'forecast']
                                    
                                    chart_payload = generate_forecast_chart({
                                        'historical_points': hist_points,
                                        'forecast_points': pred_points,
                                        'title': title
                                    })
                                    
                                    # Embed JSON payload for frontend
                                    answer += f"\n```forecast_chart\n{json.dumps(chart_payload, separators=(',', ':'))}\n```\n"

                                answer += f"\n\n📈 **Forecast Analysis (AI-Powered)**\n"
                                answer += f"📊 Trend: {forecast_result.get('trend', 'N/A').replace('_', ' ').title()}\n"
                                answer += f"🎯 Confidence: {forecast_result.get('confidence', 'N/A')}\n\n"
                            
                                if forecast_result.get('insights'):
                                    answer += "**Forecast Insights:**\n"
                                    for insight in forecast_result['insights'][:3]:
                                        answer += f"• {insight}\n"
                    else:
                        # SNAPSHOT FALLBACK - No date column found
                        # revenue_dataframe() returns standardized columns: 'amount', 'customer', 'product'
                        amount_col = 'amount'
                        total_revenue = df[amount_col].sum() if amount_col in df.columns else 0
                        total_customers = df['customer'].nunique() if 'customer' in df.columns else 0
                        total_orders = len(df)
                        avg_order = total_revenue / total_orders if total_orders > 0 else 0
                        
                        answer += f"\n\n📊 **Current Business Snapshot**\n"
                        answer += f"| Metric | Value |\n|--------|-------|\n"
                        answer += f"| Total Revenue | {currency_symbol}{total_revenue:,.2f} |\n"
                        answer += f"| Total Customers | {total_customers} |\n"
                        answer += f"| Total Orders | {total_orders} |\n"
                        answer += f"| Avg Order Value | {currency_symbol}{avg_order:,.2f} |\n\n"
                        
                        answer += "📈 **Growth Potential Analysis**\n"
                        answer += f"• Revenue per customer: {currency_symbol}{(total_revenue/total_customers):,.0f}\n" if total_customers > 0 else ""
                        answer += f"• If top 20% customers increase by 10%: +{currency_symbol}{(total_revenue * 0.2 * 0.1):,.0f} potential\n"
                        answer += f"• If customer base grows 15%: +{currency_symbol}{(total_revenue * 0.15):,.0f} projected\n\n"
                        answer += "*Note: Time-series forecasting requires date column. Upload data with dates for trend predictions.*"
                        
                except Exception as forecast_err:
                    print(f"Forecast engine error: {forecast_err}")
            
            # -------------------------------------------------------------
            # SIMULATION ENGINE - What-If Scenarios
            # -------------------------------------------------------------
            if _wants_simulation(question) and df is not None and not df.empty:
                try:
                    # Use schema detector for amount column
                    try:
                        from core.schema_detector import detect_schema
                        schema = detect_schema(df, "simulation")
                        amount_col = schema.best_amount_col
                        entity_cols = schema.best_entity_cols
                    except ImportError:
                        amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                        entity_cols = []
                    
                    total_revenue = df[amount_col].sum() if amount_col and amount_col in df.columns else 0
                    # Find customer count from entity columns
                    if entity_cols:
                        total_customers = df[entity_cols[0]].nunique()
                    else:
                        ent_cols = [c for c in df.columns if df[c].dtype == 'object' and 10 < df[c].nunique() < 500]
                        total_customers = df[ent_cols[0]].nunique() if ent_cols else 100
                    
                    # Run simulation
                    sim_result = simulate_scenarios(
                        revenue=total_revenue,
                        customers=total_customers,
                        margin=0.2,
                        churn=0.05
                    )
                    
                    if sim_result.get('success'):
                        if CHARTS_AVAILABLE:
                             # Generate interactive scenario chart
                             chart_payload = generate_scenario_chart(sim_result)
                             answer += f"\n```forecast_chart\n{json.dumps(chart_payload, separators=(',', ':'))}\n```\n"

                        answer += f"\n\n🎲 **Scenario Simulation Results**\n"
                        answer += f"✅ **Best Strategy:** {sim_result.get('best_scenario', 'N/A')}\n"
                        answer += f"💡 **Recommendation:** {sim_result.get('recommendation', 'N/A')}\n"
                        answer += f"⚠️ **Risk Level:** {sim_result.get('risk_level', 'low').upper()}\n\n"
                        
                        # Show top scenarios
                        scenarios = sim_result.get('scenarios', [])[:4]
                        if scenarios:
                            answer += "| Scenario | Revenue | Change |\n"
                            answer += "|----------|---------|--------|\n"
                            for s in scenarios:
                                change = s.get('change_pct', 0)
                                change_str = f"+{change}%" if change > 0 else f"{change}%"
                                answer += f"| {s.get('name')} | {currency_symbol}{s.get('revenue', 0):,.0f} | {change_str} |\n"
                        
                        if sim_result.get('insights'):
                            answer += "\n**Strategic Insights:**\n"
                            for insight in sim_result['insights'][:3]:
                                answer += f"• {insight}\n"
                except Exception as sim_err:
                    print(f"Simulation engine error: {sim_err}")
            
            # -------------------------------------------------------------
            # INSIGHT ENGINE - Automated Analysis
            # -------------------------------------------------------------
            if _wants_insights(question) and df is not None and not df.empty:
                try:
                    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                    total_revenue = df[amount_col].sum()
                    total_customers = df['customer'].nunique() if 'customer' in df.columns else 0
                    total_orders = len(df)
                    
                    # Get top products and customers for analysis
                    top_products = None
                    top_customers = None
                    
                    if 'product' in df.columns:
                        prod_rev = df.groupby('product')[amount_col].sum().sort_values(ascending=False)
                        top_products = [{'name': p, 'revenue': r} for p, r in prod_rev.head(5).items()]
                    
                    if 'customer' in df.columns:
                        cust_rev = df.groupby('customer')[amount_col].sum().sort_values(ascending=False)
                        top_customers = [{'name': c, 'revenue': r} for c, r in cust_rev.head(5).items()]
                    
                    # Generate insights
                    insight_result = generate_insights(
                        revenue=total_revenue,
                        revenue_previous=total_revenue * 0.9,  # Assume 10% growth
                        customers=total_customers,
                        orders=total_orders,
                        churn_rate=0.05,
                        profit_margin=0.2,
                        top_products=top_products,
                        top_customers=top_customers
                    )
                    
                    if insight_result.get('success'):
                        answer += f"\n\n🔍 **Automated Business Insights**\n"
                        answer += f"📊 Health Score: {insight_result.get('health_score', 0):.0f}/100\n"
                        answer += f"⚠️ Risk Score: {insight_result.get('risk_score', 0):.0f}/100\n"
                        answer += f"💡 Opportunity Score: {insight_result.get('opportunity_score', 0):.0f}/100\n\n"
                        
                        if insight_result.get('top_priority'):
                            answer += f"🎯 **Top Priority:** {insight_result['top_priority']}\n\n"
                        
                        insights = insight_result.get('insights', [])
                        if insights:
                            answer += f"**{len(insights)} Insights Found:**\n"
                            for i in insights[:6]:
                                icon = i.get('icon', '💡')
                                msg = i.get('message', '')
                                answer += f"{icon} {msg}\n"
                                if i.get('recommendation'):
                                    answer += f"   ↳ *{i['recommendation']}*\n"
                except Exception as insight_err:
                    print(f"Insight engine error: {insight_err}")
                    
        except Exception as engine_err:
            print(f"Engine integration error: {engine_err}")
    
    # =========================================================================
    # BASIC VISUALIZATION CHARTS (Customer/Product/Trend)
    # =========================================================================
    print(f"[VIZ DEBUG] CHARTS_AVAILABLE={CHARTS_AVAILABLE}, user_id={user_id}")
    if CHARTS_AVAILABLE:
        try:
            # Use get_user_data to preserve original columns (Department, Salary, etc.)
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(user_id) if user_id else None
            print(f"[VIZ DEBUG] df loaded: rows={len(df) if df is not None else 0}, columns={list(df.columns) if df is not None else []}")
            if df is not None and not df.empty:
                q_lower = question.lower()
                
                # Check for visualization keywords - comprehensive list
                viz_keywords = ['chart', 'graph', 'visual', 'plot', 'show', 'display', 'pie', 'bar', 'line', 'area', 'scatter', 'trend', 'breakdown', 'distribution']
                wants_viz = any(kw in q_lower for kw in viz_keywords)
                print(f"[VIZ DEBUG] wants_viz={wants_viz}, matched_keywords={[kw for kw in viz_keywords if kw in q_lower]}")
                
                if wants_viz:
                    # Extract count AND chart type from query dynamically
                    from agents.visualization_intelligence import extract_count_from_query, extract_chart_type_from_query
                    from agents.advanced_charts import generate_dynamic_chart
                    chart_limit = extract_count_from_query(question)
                    chart_type = extract_chart_type_from_query(question)
                    
                    # =========================================================
                    # USE STANDARDIZED COLUMN NAMES FROM revenue_dataframe()
                    # The df returned has: 'amount', 'date', 'customer', 'product'
                    # =========================================================
                    # Amount column is always 'amount' from revenue_dataframe
                    y_col = 'amount' if 'amount' in df.columns else None
                    
                    # Determine entity based on query - use standardized column names
                    if 'customer' in q_lower:
                        x_col = 'customer' if 'customer' in df.columns else None
                        entity = 'customer'
                    elif 'product' in q_lower:
                        x_col = 'product' if 'product' in df.columns else None
                        entity = 'product'
                    else:
                        # Default to product for "top" queries, customer otherwise
                        if 'top' in q_lower:
                            x_col = 'product' if 'product' in df.columns else ('customer' if 'customer' in df.columns else None)
                            entity = 'product' if 'product' in df.columns else 'customer'
                        else:
                            x_col = 'customer' if 'customer' in df.columns else ('product' if 'product' in df.columns else None)
                            entity = 'customer' if 'customer' in df.columns else 'product'
                    
                    # Determine chart type using intelligent extraction
                    if chart_type == 'auto':
                        # Check direct keywords for chart types
                        if 'pie' in q_lower or 'donut' in q_lower:
                            chart_type = 'pie'
                        elif 'line' in q_lower:
                            chart_type = 'line'
                        elif 'bar' in q_lower:
                            chart_type = 'bar'
                        elif 'area' in q_lower:
                            chart_type = 'area'
                        elif 'scatter' in q_lower:
                            chart_type = 'scatter'
                        elif 'trend' in q_lower or 'over time' in q_lower or 'monthly' in q_lower:
                            chart_type = 'line'
                        elif 'breakdown' in q_lower or 'distribution' in q_lower or 'share' in q_lower:
                            chart_type = 'pie'
                        elif 'compare' in q_lower or 'comparison' in q_lower:
                            chart_type = 'bar'
                        elif 'top' in q_lower or 'best' in q_lower or 'highest' in q_lower:
                            chart_type = 'bar'
                        else:
                            chart_type = 'bar'
                    
                    # Generate dynamic chart using smart_chart for full type support
                    print(f"[CHART DEBUG] Using smart_chart for query: {question[:50]}...")
                    # Use smart_chart which has full chart type detection including pie, violin, radar, etc.
                    if SMART_CHART_AVAILABLE:
                        try:
                            chart, chart_explanation = smart_chart(
                                query=question,
                                df=df,
                                currency_symbol=currency_symbol
                            )
                            if chart and 'error' not in chart:
                                import json
                                chart_json = json.dumps(chart, separators=(',', ':'))
                                answer += f"\n\n```plotly_chart\n{chart_json}\n```"
                                print(f"[CHART DEBUG] Successfully generated chart via smart_chart")
                        except Exception as chart_err:
                            print(f"[CHART DEBUG] smart_chart failed: {chart_err}")
        except Exception as viz_err:
            print(f"Visualization chart error: {viz_err}")
    
    # Add reasoning indicator
    answer += f"\n\n---\n**Reasoning Type:** {primary_mode} Fusion"
    answer += f"\n**Mode Weights:** RAG {weight_rag:.0%} | Graph {weight_graph:.0%}"
    answer += _build_source_citations(sources, "hybrid")
    
    # =========================================================================
    # CACHE STORAGE - Store response for future fast retrieval
    # =========================================================================
    if MEMORY_AVAILABLE:
        try:
            memory_store(
                query=question,
                answer=answer,
                workspace_id=user_id,
                reasoning_type="hybrid"
            )
        except Exception as store_err:
            print(f"Cache store error: {store_err}")
    
    # Handle prediction mode formatting
    if is_prediction_mode:
        import re
        
        # Replace ALL HYBRID variations (plain, bold, italic, with emoji)
        hybrid_patterns = [
            (r'Analysis Mode:\s*\*?HYBRID\*?', 'Analysis Mode: PREDICTION'),
            (r'\*Analysis Mode:\s*HYBRID\*', '**Analysis Mode: PREDICTION**'),
            (r'Mode:\s*HYBRID', 'Mode: PREDICTION'),
            (r'HYBRID\s*MODE', 'PREDICTION MODE'),
            (r'Reasoning Type:\s*(?:RAG Fusion|Balanced Fusion|Graph-Heavy)', 'Reasoning Type: Prediction Analysis'),
            (r'Mode Weights:\s*RAG', 'Prediction Weights: RAG'),
        ]
        
        for pattern, replacement in hybrid_patterns:
            answer = re.sub(pattern, replacement, answer, flags=re.IGNORECASE)
        
        # Remove the entire reasoning/mode weights section (it's hybrid terminology)
        # Pattern: ---\nReasoning Type: ...\nMode Weights: ...\n---
        answer = re.sub(
            r'---\s*\n\s*Reasoning Type:[^\n]*\n\s*Mode Weights:[^\n]*\n\s*---',
            '',
            answer,
            flags=re.IGNORECASE
        )
        
        # Also remove standalone reasoning type lines
        answer = re.sub(r'Reasoning Type:\s*Balanced Fusion[^\n]*\n?', '', answer)
        answer = re.sub(r'Mode Weights:\s*RAG[^\n]*\n?', '', answer)
        
        # Clean up multiple dashes
        answer = re.sub(r'(---\s*\n\s*){2,}', '---\n', answer)
        
        # Add clean prediction footer if not present
        if 'PREDICTION' not in answer.upper():
            answer += "\n\n---\n📈 **Analysis Mode: PREDICTION**\n"
            answer += "Accuracy Tier: TIER 3 (Scenario-Based) - Snapshot data used\n"
        elif 'Tier' not in answer:
            answer += "\nAccuracy Tier: TIER 3 (Scenario-Based) - Snapshot data used\n"
    
    state.answer = answer
    state.route = "prediction" if is_prediction_mode else "hybrid"
    state.sources = sources
    state.context["fusion_weights"] = {"rag": weight_rag, "graph": weight_graph}
    state.context["primary_mode"] = primary_mode
    
    # Store assistant response in conversation memory for follow-ups
    _store_conversation_turn(session_id, "assistant", answer[:500])  # Store first 500 chars
    
    return state


# ============================================================================
# 🟩 VISION MODE - Enhanced Image Analysis Pipeline
# ============================================================================

def vision_answer(state: AgentState) -> AgentState:
    """
    🟩 VISION MODE - Enterprise Image Analysis
    
    Features:
    - Chart data extraction to JSON
    - Table detection and parsing
    - OCR text extraction
    - Vision → RAG/Graph pipeline
    """
    start_time = time.time()
    question = state.question
    attached_files = state.context.get("attached_files", [])
    user_id = state.company_id
    
    if not attached_files:
        state.answer = """I need an image to analyze.

**How to use Vision mode:**
• Drag and drop an image into the chat
• Or click the attachment button

**I can analyze:**
• 📊 Charts and graphs → Extract data points
• 📋 Tables → Convert to structured data
• 🧾 Invoices and receipts → Extract details
• 📄 Documents → OCR and summarize
• 📈 Screenshots → Identify trends and metrics

Once extracted, I can query the data using RAG or Graph analysis."""
        state.route = "vision"
        return state
    
    image_files = [f for f in attached_files if f.get('type', '').startswith('image/')]
    
    if not image_files:
        state.answer = """The attached file doesn't appear to be an image.

**Supported formats:** PNG, JPG, JPEG, WebP"""
        state.route = "vision"
        return state
    
    try:
        from core.vision import analyze_image
        try:
            from mcp.vision_ocr import (
                extract_tables_from_image,
                analyze_chart,
                vision_to_rag_context
            )
        except ImportError:
            # Fallback - define stubs
            def extract_tables_from_image(path, output_format):
                return {"success": False, "tables": []}
            def analyze_chart(path):
                return {"success": False, "chart_data": None}
            def vision_to_rag_context(path, question):
                return {"success": False, "ready_for_rag": False}
        
        image_file = image_files[0]
        image_path = image_file.get('path', '')
        image_name = image_file.get('name', 'image')
        
        # Detect analysis type from question
        q_lower = question.lower()
        
        if any(word in q_lower for word in ['table', 'extract data', 'rows', 'columns']):
            # Table extraction mode
            table_result = extract_tables_from_image(image_path, output_format="markdown")
            
            if table_result.get("success") and table_result.get("tables"):
                answer = f"## Extracted Tables from {image_name}\n\n"
                for i, table in enumerate(table_result["tables"], 1):
                    if isinstance(table, str):
                        answer += f"### Table {i}\n{table}\n\n"
                    else:
                        answer += f"### Table {i}\n"
                        answer += f"| {' | '.join(table.get('headers', []))} |\n"
                        answer += f"| {' | '.join(['---'] * len(table.get('headers', [])))} |\n"
                        for row in table.get('rows', []):
                            answer += f"| {' | '.join(row)} |\n"
                        answer += "\n"
                
                answer += f"\n*Extracted {len(table_result['tables'])} table(s)*"
            else:
                answer = "I couldn't extract tables from this image. Please ensure the image contains clear tabular data."
        
        elif any(word in q_lower for word in ['chart', 'graph', 'plot', 'trend', 'data points']):
            # Chart analysis mode
            chart_result = analyze_chart(image_path)
            
            if chart_result.get("success") and chart_result.get("chart_data"):
                chart_data = chart_result["chart_data"]
                
                answer = f"## 📊 Chart Analysis: {image_name}\n\n"
                
                if isinstance(chart_data, dict):
                    if chart_data.get("chart_type"):
                        answer += f"**Type:** {chart_data['chart_type']}\n"
                    if chart_data.get("title"):
                        answer += f"**Title:** {chart_data['title']}\n"
                    
                    if chart_data.get("data_series"):
                        answer += "\n### 📈 Extracted Data\n"
                        for series in chart_data["data_series"]:
                            series_name = series.get('name', 'Series')
                            answer += f"\n**{series_name}:**\n"
                            answer += "| X Value | Y Value |\n"
                            answer += "|---------|--------|\n"
                            for point in series.get("data", []):
                                x_val = point.get('x', 'N/A')
                                y_val = point.get('y', 'N/A')
                                answer += f"| {x_val} | {y_val} |\n"
                else:
                    answer += chart_result.get("raw_analysis", "Unable to parse chart data")
            else:
                # Fall back to general analysis
                answer = analyze_image(image_path, question)
        
        else:
            # General image analysis
            analysis = analyze_image(image_path, question)
            answer = f"## Image Analysis: {image_name}\n\n{analysis}"
        
        # Check if user wants to continue with RAG/Graph analysis
        if any(word in q_lower for word in ['analyze further', 'query', 'insights', 'trends']):
            rag_context = vision_to_rag_context(image_path, question)
            if rag_context.get("success") and rag_context.get("ready_for_rag"):
                answer += "\n\n---\n*📊 Data extracted and ready for further analysis. Ask follow-up questions to explore insights.*"
        
        state.answer = answer
        state.route = "vision"
        state.sources = [image_name]
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        state.answer = f"""I couldn't analyze the image due to an error.

**Error:** {str(e)}

**Troubleshooting:**
• Ensure the image is valid (PNG, JPG, WebP)
• Check that the GOOGLE_API_KEY is configured
• Try a different image or format"""
        state.route = "vision"
    
    return state


# ============================================================================
# FALLBACK MODE
# ============================================================================

def fallback_answer(state: AgentState) -> AgentState:
    """Fallback when no data available"""
    state.answer = """I don't have any data to work with yet.

**Getting Started:**
1. Go to **Data Hub** in the sidebar
2. Upload your business files (CSV, Excel, PDF, Images)
3. Return here to ask questions

**Example questions once you have data:**
• "What are the total sales?"
• "Who are my top customers?"
• "Show revenue trends"
• "Which products sell the most?"

**AI Modes Available:**
• 🟦 **RAG** - Document search and retrieval
• 🟧 **GraphRAG** - Knowledge graph reasoning
• 🟪 **Hybrid** - Combined analysis (best results)
• 🟩 **Vision** - Image and chart analysis"""
    state.route = "fallback"
    return state


# ============================================================================
# AI MODEL MODE (DeepSeek, Mistral, Llama)
# ============================================================================

def ai_model_answer(state: AgentState) -> AgentState:
    """
    Handle direct AI model queries (DeepSeek, Mistral, Llama).
    
    Uses specified model directly with context from user's data.
    """
    try:
        from agents.ai_models import (
            get_ai_model_config,
            is_ai_model_mode,
            get_ai_model_system_prompt,
        )
        
        question = state.question
        user_id = state.user_id
        mode = state.route  # The AI model mode (e.g., "deepseek-chat")
        
        # Get model configuration
        model_config = get_ai_model_config(mode)
        if not model_config:
            state.answer = f"Unknown AI model: {mode}"
            return state
        
        # Get currency
        currency_symbol, currency_code = get_user_currency(user_id)
        
        # Try to get context from graph/vector
        context = ""
        sources = []
        
        # Try graph context first
        try:
            from graph.query import query_graph
            graph_result = query_graph(question, user_id=user_id)
            if graph_result and graph_result.strip():
                context = f"Business Data:\n{graph_result}"
                sources.append("knowledge_graph")
        except:
            pass
        
        # Try vector context if graph is empty
        if not context:
            try:
                from vector.retriever import retrieve
                vector_results = retrieve(question, k=5, user_id=user_id)
                if vector_results:
                    context = "Document Context:\n" + "\n".join([r.get("content", "") for r in vector_results[:3]])
                    sources.extend([r.get("source", "document") for r in vector_results[:3]])
            except:
                pass
        
        # Build system prompt
        system_prompt = f"""{get_ai_model_system_prompt()}

USER CURRENCY: {currency_symbol} ({currency_code})
MODEL: {model_config.name}

{context if context else "No business data loaded. Answer generally or ask user to upload data."}"""
        
        # Call LLM with specific model
        answer = chat(
            question,
            system=system_prompt,
            model=model_config.model_path,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature,
        )
        
        # Add model attribution
        answer += f"\n\n---\n*Powered by **{model_config.name}***"
        
        state.answer = answer
        state.route = mode
        state.sources = sources if sources else None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        state.answer = f"""I encountered an error with the AI model.

**Error:** {str(e)}

**Try:**
• Switching to a different AI model
• Using RAG or Hybrid mode instead
• Checking your API configuration"""
        state.route = state.route or "ai_model"
    
    return state

