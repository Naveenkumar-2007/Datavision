# Enterprise Agent Nodes v2.0 - Premium $50K Product Quality
"""
4 Enterprise AI Modes: RAG, GraphRAG, Hybrid, Vision

Features:
- Query classification with confidence scoring
- Multi-hop graph reasoning
- Hybrid fusion with intelligent weighting
- Vision → RAG/Graph pipeline
- MCP tool integration
- Clean, ChatGPT-style outputs
"""

from core.llm import chat
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


def _get_user_context(user_id: str) -> str:
    """Get personalized context for user"""
    try:
        from core.memory import get_user_context
        return get_user_context(user_id)
    except:
        return ""


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
    """Build formatted source citations as a clean table"""
    if not sources:
        return ""
    
    citation = "\n\n---\n\n### 📚 Data Sources\n\n"
    citation += "| # | Source File |\n"
    citation += "|---|---|\n"
    for i, src in enumerate(sources[:5], 1):
        citation += f"| {i} | {src} |\n"
    citation += f"\n*Analysis Mode: **{mode.upper()}***"
    return citation


def _clean_response_formatting(answer: str) -> str:
    """
    Clean response formatting for premium $50K product quality.
    Fixes table alignment, removes artifacts, ensures professional output.
    """
    if not answer:
        return answer
    
    import re
    
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
    
    # AGGRESSIVE CLEANUP - Remove code blocks EXCEPT plotly_chart (our visualizations!)
    # Use negative lookahead to preserve plotly_chart blocks
    answer = re.sub(r'```(?!plotly_chart)[a-zA-Z]*[\s\S]*?```', '', answer)
    
    # Remove LaTeX math blocks
    answer = re.sub(r'\$\$[\s\S]*?\$\$', '', answer)  # Display math
    answer = re.sub(r'\$[^$\n]+\$', '', answer)  # Inline math
    answer = re.sub(r'\\\\[a-z]+\{[^}]*\}', '', answer)  # LaTeX commands
    
    # Remove markdown tables completely
    # Match lines that start with | and have multiple |
    lines = answer.split('\n')
    cleaned_lines = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        # Detect table rows
        if stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 2:
            in_table = True
            continue  # Skip table lines
        elif in_table and (stripped.startswith('|') or stripped.startswith('|-')):
            continue  # Still in table
        else:
            in_table = False
            cleaned_lines.append(line)
    answer = '\n'.join(cleaned_lines)
    
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
    
    # Remove any remaining incomplete table rows
    answer = re.sub(r'\n\|[^|\n]*$', '', answer)
    
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
            content = msg.get('content', '')[:200]  # Truncate for context
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
            'content': content[:500]  # Limit size
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
        'chart', 'graph', 'plot', 'visualize', 'visualization', 
        'show me', 'display', 'draw', 'create a', 'generate',
        'bar chart', 'pie chart', 'line chart', 'trend chart'
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in viz_keywords)


def _wants_prediction(question: str) -> bool:
    """Check if user wants a prediction/forecast"""
    pred_keywords = [
        'predict', 'forecast', 'future', 'next month', 'next year',
        'projection', 'estimate', 'will be', 'expected', 'growth',
        'next 3', 'next 6', 'next 12', 'next week', 'next 7 days'
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


def _is_followup_query(question: str) -> bool:
    """Check if this is a follow-up query about previous response/chart"""
    followup_keywords = [
        'explain above', 'explain this', 'explain the', 'about above',
        'above graph', 'above chart', 'this graph', 'this chart',
        'the graph', 'the chart', 'what does', 'tell me about',
        'explain more', 'more about', 'can you explain', 'previous',
        'that chart', 'that graph', 'the bar', 'this bar', 'above bar'
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in followup_keywords)


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


def _extract_prediction_period(question: str) -> int:
    """Extract prediction period from question (in months)"""
    import re
    q_lower = question.lower()
    
    # Look for patterns like "next 3 months", "3 months", "next year"
    month_match = re.search(r'next\s+(\d+)\s*months?', q_lower)
    if month_match:
        return int(month_match.group(1))
    
    year_match = re.search(r'next\s+(\d+)\s*years?', q_lower)
    if year_match:
        return int(year_match.group(1)) * 12
    
    if 'next year' in q_lower:
        return 12
    if 'next quarter' in q_lower:
        return 3
    
    return 3  # Default 3 months


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
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    
    # =========================================================================
    # STEP 1: MEMORY - Save user message and extract personal info
    # =========================================================================
    _save_chat_message(user_id, "user", question)
    
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
            return state
    
    # =========================================================================
    # STEP 2: ANTI-HALLUCINATION - Block non-data questions
    # =========================================================================
    if not _is_data_related_query(question):
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
    
    system_prompt = f"""You are an AI Business Analyst. $500,000 enterprise quality. Real-time answers.

DATA FILES: {', '.join(sources) if sources else 'None'}
USER CURRENCY: {currency_symbol} ({currency_code})

═══════════════════════════════════════════════════════════════
                    CURRENCY RULES
═══════════════════════════════════════════════════════════════
1. Use {currency_symbol} as the DEFAULT currency (from user's Settings)
2. Conversion rates (only when explicitly asked):
   - $1 USD = ₹83 INR = €0.92 EUR = £0.79 GBP
3. Only convert to other currencies when user asks

═══════════════════════════════════════════════════════════════
                    RESPONSE FORMAT
═══════════════════════════════════════════════════════════════

ALWAYS respond with:
1. One-line answer (bold) using {currency_symbol}
2. Table with data breakdown

EXAMPLE:
**Total Revenue: {currency_symbol}[amount from data]**

| Metric | Value |
|--------|-------|
| Total Revenue | {currency_symbol}[from data] |
| Customers | [from data] |
| Orders | [from data] |

═══════════════════════════════════════════════════════════════
                    RULES
═══════════════════════════════════════════════════════════════

1. ALWAYS use | table | format for data
2. Use {currency_symbol} as the currency symbol
3. Use ONLY data from the Retrieved Context below
4. Be concise - no filler text
5. NEVER make up numbers

ANTI-HALLUCINATION:
- ONLY use numbers from Retrieved Context
- If missing, say "This data is not in your uploaded files"
- NEVER invent or estimate numbers"""

    # Get personalized user context
    user_context = _get_user_context(user_id)
    user_context_section = f"\n\nUser Context:\n{user_context}" if user_context else ""

    # Pre-compute chart data if visualization requested OR follow-up about chart
    chart_data_section = ""
    is_followup = _is_followup_query(question)
    needs_chart_data = _wants_visualization(question) or _wants_prediction(question) or is_followup
    
    if needs_chart_data:
        try:
            from graph.query import revenue_dataframe
            df_for_chart = revenue_dataframe(user_id)
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
        enhanced_question = f"""{question}

[CONTEXT: The user is asking about a CUSTOMER REVENUE BAR CHART that was previously shown. 
Please explain the chart data above. List the TOP 10 customers by revenue with their exact amounts.
Do NOT generate a new trend chart - explain the BAR CHART data for customers.]"""

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

IMPORTANT: If CHART DATA is provided above, your explanation MUST reference those EXACT numbers and names. A chart will be generated showing this data - your explanation should match it precisely.

If the user previously introduced themselves (check Recent Conversation), remember their name and use it warmly.

Provide a clear, data-driven answer."""

    answer = chat(prompt, system=system_prompt, max_tokens=1500)
    
    # Generate charts if visualization requested (works in any mode)
    if CHARTS_AVAILABLE and (_wants_visualization(question) or _wants_prediction(question)):
        try:
            from graph.query import revenue_dataframe
            df = revenue_dataframe(user_id)
            
            if df is not None and not df.empty:
                if _wants_visualization(question):
                    q_lower = question.lower()
                    if 'customer' in q_lower:
                        chart = generate_customer_revenue_chart(df, currency_symbol)
                        answer = _embed_chart_in_response(answer, chart, "Customer Revenue")
                    elif 'product' in q_lower:
                        chart = generate_product_revenue_chart(df, currency_symbol)
                        answer = _embed_chart_in_response(answer, chart, "Product Distribution")
                    else:
                        chart = generate_monthly_trend_chart(df, currency_symbol, show_prediction=False)
                        if chart:
                            answer = _embed_chart_in_response(answer, chart, "Revenue Trend")
                            
                elif _wants_prediction(question):
                    prediction_months = _extract_prediction_period(question)
                    if 'date' in df.columns:
                        import pandas as pd
                        amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                        df_temp = df.copy()
                        df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
                        df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
                        
                        if not df_dated.empty:
                            df_dated['month'] = df_dated['date_parsed'].dt.strftime('%Y-%m')
                            monthly = df_dated.groupby('month')[amount_col].sum().to_dict()
                            
                            if monthly:
                                chart, pred_data = generate_prediction_chart(
                                    monthly, 
                                    prediction_months=prediction_months,
                                    currency_symbol=currency_symbol
                                )
                                answer = _embed_chart_in_response(answer, chart, "Prediction Chart")
                                answer += f"\n\n🔮 Predicted Growth: {pred_data['total_predicted_growth']:.1f}%"
        except Exception as chart_error:
            print(f"RAG chart error: {chart_error}")
    
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
    _save_chat_message(user_id, "assistant", answer[:300])
    
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
        
        # Get comprehensive data
        df = revenue_dataframe(user_id)
        data_summary = ""
        
        if df is not None and not df.empty:
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            currency_symbol, currency_code = get_user_currency(user_id)
            
            total_rev = df[amount_col].sum()
            num_trans = len(df)
            num_cust = df['customer'].nunique() if 'customer' in df.columns else 0
            num_prod = df['product'].nunique() if 'product' in df.columns else 0
            
            data_summary = f"""
## 📊 Business Metrics
| Metric | Value |
|--------|-------|
| Total Revenue | {currency_symbol}{total_rev:,.2f} |
| Transactions | {num_trans:,} |
| Unique Customers | {num_cust:,} |
| Unique Products | {num_prod:,} |
"""
            
            # Add customer analysis
            if 'customer' in df.columns:
                all_customers = df.groupby('customer')[amount_col].sum().sort_values(ascending=False)
                customer_orders = df.groupby('customer').size()
                
                data_summary += f"\n## 👥 Customer Analysis\n"
                data_summary += f"| Rank | Customer | Revenue | Orders | Avg Order |\n"
                data_summary += f"|------|----------|---------|--------|----------|\n"
                
                for i, (cust, amt) in enumerate(all_customers.items(), 1):
                    orders = customer_orders.get(cust, 0)
                    avg_order = amt / orders if orders > 0 else 0
                    data_summary += f"| {i} | {cust} | {currency_symbol}{amt:,.2f} | {orders} | {currency_symbol}{avg_order:,.2f} |\n"
                
                # Highlight top and bottom
                top_customer = all_customers.index[0]
                bottom_customer = all_customers.index[-1]
                data_summary += f"\n⭐ **Top:** {top_customer} ({currency_symbol}{all_customers.iloc[0]:,.2f})\n"
            
            # Add product analysis
            if 'product' in df.columns:
                all_products = df.groupby('product')[amount_col].sum().sort_values(ascending=False)
                product_counts = df.groupby('product').size()
                
                data_summary += f"\n## 📦 Product Analysis\n"
                
                for i, (prod, amt) in enumerate(all_products.items(), 1):
                    count = product_counts.get(prod, 0)
                    avg_price = amt / count if count > 0 else 0
                    data_summary += f"{i}. **{prod}**: {currency_symbol}{amt:,.2f} ({count} units, avg {currency_symbol}{avg_price:,.2f})\n"
        
        # Add traversal insights if available
        graph_insights = ""
        if traversal_result and traversal_result.paths:
            graph_insights = "\n## Graph Reasoning\n"
            for i, path in enumerate(traversal_result.paths[:3], 1):
                graph_insights += f"• **Path {i}:** {path.explanation}\n"
            graph_insights += f"\n*Traversed {len(traversal_result.visited_nodes)} entities*\n"
        
        # Build LLM prompt
        system_prompt = f"""You are an AI Business Analyst. $500,000 enterprise quality responses only.

GRAPH MODE: Knowledge Graph Intelligence
CURRENCY: {currency_symbol}

═══════════════════════════════════════════════════════════════
                    STRICT TABLE FORMAT RULE
═══════════════════════════════════════════════════════════════

WRONG FORMAT (never do this):
• Revenue: $433M
• Customers: 650
1. Customer_33 - $29,752

CORRECT FORMAT (always do this):
| Metric | Value |
|--------|-------|
| Revenue | $433M |
| Customers | 650 |

| Rank | Customer | Revenue | Orders |
|------|----------|---------|--------|
| 1 | Customer_33 | $29,752 | 9 |
| 2 | Customer_25 | $28,500 | 8 |
| 3 | Customer_39 | $27,200 | 7 |

═══════════════════════════════════════════════════════════════
                    RESPONSE EXAMPLES
═══════════════════════════════════════════════════════════════

QUERY: "Total revenue?"
RESPONSE:
**Total Revenue: {currency_symbol}433,394,115**

| Source | Revenue |
|--------|---------|
| Enterprise (USD) | $433,387,500 |
| New Customers (INR) | ₹548,765 → $6,615 |
| **TOTAL** | **$433,394,115** |

---

QUERY: "Top customers?"
RESPONSE:
| Rank | Customer | Revenue | Orders | Status |
|------|----------|---------|--------|--------|
| 1 | Glovo Ltd | $1,150,000 | 12 | ⭐ Top |
| 2 | Just Eat Ltd | $980,000 | 9 | ⭐ Top |
| 3 | Delivery Hero | $875,000 | 8 | 📈 High |

═══════════════════════════════════════════════════════════════
                    RULES
═══════════════════════════════════════════════════════════════

1. ALWAYS use | table | format for data
2. NEVER use bullet points or numbered lists for data
3. Convert currencies automatically (₹83 = $1)
4. Be concise - no filler or verbose explanations
5. Simple question = simple answer + table
6. Every table needs header row and 3+ data rows

ANTI-HALLUCINATION:
Only use data from graph context. If missing, say so."""

        # Get personalized user context
        user_context = _get_user_context(user_id)
        user_context_section = f"\n\nUser Context:\n{user_context}" if user_context else ""

        prompt = f"""Question: {question}

Query Type: {query_analysis.query_type.value}
Reasoning Depth: {query_analysis.reasoning_depth.value}
{user_context_section}

{data_summary}

{graph_insights}

**Graph Stats:** {stats.get('total_nodes', 0)} entities, {stats.get('total_edges', 0)} relationships

IMPORTANT: Your explanation MUST reference the EXACT customer names, product names, and revenue numbers from the data above. If a chart is generated, your explanation should match those exact values.

Provide a comprehensive, data-driven answer with insights. Reference specific customers and products by name with their exact revenue amounts."""

        answer = chat(prompt, system=system_prompt, max_tokens=1500)
        
        # Generate charts if visualization requested
        if CHARTS_AVAILABLE and df is not None and not df.empty:
            try:
                # Check for visualization request
                if _wants_visualization(question):
                    q_lower = question.lower()
                    
                    if 'customer' in q_lower:
                        chart = generate_customer_revenue_chart(df, currency_symbol)
                        answer = _embed_chart_in_response(answer, chart, "Customer Revenue Chart")
                    elif 'product' in q_lower:
                        chart = generate_product_revenue_chart(df, currency_symbol)
                        answer = _embed_chart_in_response(answer, chart, "Product Distribution")
                    elif 'trend' in q_lower or 'month' in q_lower:
                        chart = generate_monthly_trend_chart(df, currency_symbol, show_prediction=False)
                        if chart:
                            answer = _embed_chart_in_response(answer, chart, "Revenue Trend")
                    else:
                        # Default: customer revenue chart
                        if 'customer' in df.columns:
                            chart = generate_customer_revenue_chart(df, currency_symbol)
                            answer = _embed_chart_in_response(answer, chart, "Revenue Overview")
                
                # Check for prediction request
                elif _wants_prediction(question):
                    prediction_months = _extract_prediction_period(question)
                    
                    # Get monthly data for prediction
                    if 'date' in df.columns:
                        import pandas as pd
                        amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                        df_temp = df.copy()
                        df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
                        df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
                        
                        if not df_dated.empty:
                            df_dated['month'] = df_dated['date_parsed'].dt.strftime('%Y-%m')
                            monthly = df_dated.groupby('month')[amount_col].sum().to_dict()
                            
                            if monthly:
                                chart, pred_data = generate_prediction_chart(
                                    monthly, 
                                    prediction_months=prediction_months,
                                    title=f"📈 Revenue Prediction ({prediction_months} months)",
                                    currency_symbol=currency_symbol
                                )
                                answer = _embed_chart_in_response(answer, chart, "Revenue Prediction")
                                
                                # Add prediction summary
                                answer += f"\n\n🔮 **Prediction Summary:**\n"
                                answer += f"• Scenario: {pred_data['scenario'].title()}\n"
                                answer += f"• Expected Growth: {pred_data['total_predicted_growth']:.1f}%\n"
                                for period, value in pred_data['predictions'].items():
                                    answer += f"• {period}: {currency_symbol}{value:,.2f}\n"
            except Exception as chart_error:
                print(f"Chart generation error: {chart_error}")
        
        # Add graph summary
        answer += f"\n\n---\n🔗 **Graph Summary:** {stats.get('total_nodes', 0)} entities, {stats.get('total_edges', 0)} relationships\n"
        answer += f"*Analysis mode: GRAPHRAG*"
        
        # Clean response formatting for premium quality
        answer = _clean_response_formatting(answer)
        
        state.answer = answer
        state.route = "graph"
        state.sources = ["Knowledge Graph Analysis"]
        state.context["traversal_paths"] = len(traversal_result.paths) if traversal_result else 0
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Log to server console only
        # Don't expose internal error details to user
        state.answer = (
            "**ANALYSIS ERROR**\n\n"
            "Unable to complete the graph analysis. Please try:\n"
            "- Uploading your data files in Data Hub\n"
            "- Asking a more specific question\n"
            "- Using RAG mode instead"
        )
        state.route = "graph"
    
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
        from graph.query import get_graph_summary, revenue_dataframe
        
        graph_context = get_graph_summary(user_id) or ""
        
        df = revenue_dataframe(user_id)
        if df is not None and not df.empty:
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            currency_symbol, _ = get_user_currency(user_id)
            
            total = df[amount_col].sum()
            avg = df[amount_col].mean()
            
            graph_context += f"\n\n**Revenue Summary:** {currency_symbol}{total:,.2f} total, {currency_symbol}{avg:,.2f} avg order"
            
            # Add top/bottom for relevant queries
            if 'customer' in df.columns:
                top_cust = df.groupby('customer')[amount_col].sum().idxmax()
                low_cust = df.groupby('customer')[amount_col].sum().idxmin()
                graph_context += f"\n**Top Customer:** {top_cust}"
                graph_context += f"\n**Lowest Customer:** {low_cust}"
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
    
    system_prompt = f"""You are an AI Business Analyst. $500,000 enterprise quality. Real-time answers.

HYBRID MODE: RAG {weight_rag:.0%} + Graph {weight_graph:.0%}
USER CURRENCY: {currency_symbol}

═══════════════════════════════════════════════════════════════
                    CURRENCY RULES
═══════════════════════════════════════════════════════════════
1. Use {currency_symbol} as the DEFAULT currency (from user's Settings)
2. Conversion rates (only when explicitly asked):
   - $1 USD = ₹83 INR = €0.92 EUR = £0.79 GBP
3. Only convert to other currencies when user asks

═══════════════════════════════════════════════════════════════
                    RESPONSE FORMAT
═══════════════════════════════════════════════════════════════

ALWAYS respond with:
1. One-line answer (bold) using {currency_symbol}
2. Table with data breakdown

EXAMPLE:
**Total Revenue: {currency_symbol}[amount from data]**

| Metric | Value |
|--------|-------|
| Total Revenue | {currency_symbol}[from data] |
| Customers | [from data] |
| Orders | [from data] |

═══════════════════════════════════════════════════════════════
                    RULES
═══════════════════════════════════════════════════════════════

1. ALWAYS use | table | format for data
2. Use {currency_symbol} as the currency symbol
3. Use ONLY data from the context provided
4. Be concise - no filler text
5. NEVER make up numbers

ANTI-HALLUCINATION:
- ONLY use numbers from context
- If missing, say "This data is not in your uploaded files"
- NEVER invent or estimate numbers"""

    # Get personalized user context  
    user_context = _get_user_context(user_id)
    user_context_section = f"\n\nUser Context:\n{user_context}" if user_context else ""

    prompt = f"""Question: {question}

Query Type: {query_analysis.query_type.value}
Confidence: {query_analysis.confidence:.2f}
{user_context_section}

**Document Context (RAG):**
{rag_context if rag_context else "Limited document data"}

**Graph Insights:**
{graph_context if graph_context else "Limited graph data"}

Provide a comprehensive answer using the most relevant information from both sources. If the user introduced themselves, acknowledge their name warmly."""

    answer = chat(prompt, system=system_prompt, max_tokens=1500)
    
    # =========================================================================
    # ENTERPRISE ENGINE INTEGRATION
    # =========================================================================
    
    if ENGINES_AVAILABLE:
        try:
            # Get data for engines
            df = revenue_dataframe(user_id) if user_id else None
            
            # -------------------------------------------------------------
            # FORECAST ENGINE - Time-Series Prediction
            # -------------------------------------------------------------
            if _wants_prediction(question) and df is not None and not df.empty:
                try:
                    if 'date' in df.columns:
                        import pandas as pd
                        amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                        df_temp = df.copy()
                        df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
                        df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
                        
                        if not df_dated.empty:
                            df_dated['month'] = df_dated['date_parsed'].dt.strftime('%Y-%m')
                            monthly = df_dated.groupby('month')[amount_col].sum().reset_index()
                            monthly.columns = ['date', 'value']
                            
                            # Get forecast
                            periods = _extract_prediction_period(question)
                            forecast_result = forecast_from_dataframe(monthly, 'date', 'value', periods=periods)
                            
                            if forecast_result.get('success'):
                                # Generate interactive chart
                                if CHARTS_AVAILABLE:
                                    # Extract points directly from ForecastEngine result to preserve confidence intervals
                                    forecast_items = forecast_result.get('forecast', [])
                                    hist_points = [item for item in forecast_items if item.get('type') == 'historical']
                                    pred_points = [item for item in forecast_items if item.get('type') == 'forecast']
                                    
                                    chart_payload = generate_forecast_chart({
                                        'historical_points': hist_points,
                                        'forecast_points': pred_points
                                    })
                                    
                                    # Embed JSON payload for frontend
                                    answer += f"\n```forecast_chart\n{json.dumps(chart_payload, indent=2)}\n```\n"

                                answer += f"\n\n📈 **Forecast Analysis (AI-Powered)**\n"
                                answer += f"📊 Trend: {forecast_result.get('trend', 'N/A').replace('_', ' ').title()}\n"
                                answer += f"🎯 Confidence: {forecast_result.get('confidence', 'N/A')}\n\n"
                            
                                if forecast_result.get('insights'):
                                    answer += "**Forecast Insights:**\n"
                                    for insight in forecast_result['insights'][:3]:
                                        answer += f"• {insight}\n"
                except Exception as forecast_err:
                    print(f"Forecast engine error: {forecast_err}")
            
            # -------------------------------------------------------------
            # SIMULATION ENGINE - What-If Scenarios
            # -------------------------------------------------------------
            if _wants_simulation(question) and df is not None and not df.empty:
                try:
                    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
                    total_revenue = df[amount_col].sum()
                    total_customers = df['customer'].nunique() if 'customer' in df.columns else 100
                    
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
                             answer += f"\n```forecast_chart\n{json.dumps(chart_payload, indent=2)}\n```\n"

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
    if CHARTS_AVAILABLE:
        try:
            df = revenue_dataframe(user_id) if user_id else None
            if df is not None and not df.empty:
                q_lower = question.lower()
                
                # Check for visualization keywords
                viz_keywords = ['chart', 'graph', 'visual', 'plot', 'show', 'display', 'pie', 'bar']
                wants_viz = any(kw in q_lower for kw in viz_keywords)
                
                if wants_viz:
                    if 'customer' in q_lower:
                        chart = generate_customer_revenue_chart(df, currency_symbol)
                        if chart:
                            answer = _embed_chart_in_response(answer, chart, "Customer Revenue Chart")
                    elif 'product' in q_lower or 'pie' in q_lower:
                        chart = generate_product_revenue_chart(df, currency_symbol)
                        if chart:
                            answer = _embed_chart_in_response(answer, chart, "Product Distribution Chart")
                    elif 'trend' in q_lower or 'monthly' in q_lower:
                        chart = generate_monthly_trend_chart(df, currency_symbol, show_prediction=True)
                        if chart:
                            answer = _embed_chart_in_response(answer, chart, "Revenue Trend Chart")
                    else:
                        # Default: show customer chart for general visualization requests
                        chart = generate_customer_revenue_chart(df, currency_symbol)
                        if chart:
                            answer = _embed_chart_in_response(answer, chart, "Revenue Analysis Chart")
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
