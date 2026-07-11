# Report generation module
"""Weekly & Monthly business report generator with multi-currency support.
Uses dynamic column detection — works with ANY dataset, not just sales data."""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional
from core.llm import chat
from graph.query import revenue_dataframe, get_user_currency
from utils.currency import (
    format_currency,
    get_currency_symbol,
    calculate_currency_breakdown,
    convert_to_usd,
    CURRENCY_CONFIG
)

logger = logging.getLogger(__name__)


# =============================================================================
# Dynamic Column Detection
# =============================================================================

def _detect_amount_col(df: pd.DataFrame) -> Optional[str]:
    """Find the primary numeric amount column."""
    candidates = [
        'amount', 'total_amount', 'revenue', 'sales', 'total', 'price',
        'value', 'total_price', 'net_amount', 'gross_amount', 'invoice_amount',
    ]
    for col in candidates:
        if col in df.columns:
            return col
    # Fallback: first non-negative numeric column
    for col in df.select_dtypes(include='number').columns:
        if df[col].min() >= 0 and df[col].max() > 0:
            return col
    return None


def _detect_category_col(df: pd.DataFrame, role: str) -> Optional[str]:
    """Find a categorical column by role name."""
    role_candidates = {
        'customer': ['customer', 'customer_name', 'client', 'account', 'buyer', 'company'],
        'product': ['product', 'product_name', 'item', 'item_name', 'sku', 'service', 'category'],
    }
    for col in role_candidates.get(role, [role]):
        if col in df.columns:
            return col
    return None


def _detect_date_col(df: pd.DataFrame) -> Optional[str]:
    """Find the primary date column."""
    candidates = ['date', 'created_at', 'order_date', 'timestamp', 'invoice_date', 'transaction_date']
    for col in candidates:
        if col in df.columns:
            return col
    dt_cols = df.select_dtypes(include='datetime').columns.tolist()
    return dt_cols[0] if dt_cols else None


def _safe_groupby_top(df: pd.DataFrame, group_col: str, amount_col: str, n: int = 5) -> str:
    """Safely generate a 'top N by amount' string. Returns empty string if columns missing."""
    if group_col not in df.columns or amount_col not in df.columns:
        return "(column not available)"
    try:
        return df.groupby(group_col)[amount_col].sum().nlargest(n).to_string()
    except Exception:
        return "(unable to compute)"


# =============================================================================
# Weekly Report
# =============================================================================

def generate_weekly_report(company_id: str) -> str:
    """
    Generate automated weekly business report.
    Dynamically detects columns — no longer requires 'amount', 'customer', 'product'.
    """
    df = revenue_dataframe(company_id)

    if df is None or df.empty:
        return "No data available for weekly report. Please upload business data first."

    # Detect columns
    amount_col = _detect_amount_col(df)
    customer_col = _detect_category_col(df, 'customer')
    product_col = _detect_category_col(df, 'product')
    date_col = _detect_date_col(df)

    # Filter to last 7 days if date column exists
    last_week = datetime.now() - timedelta(days=7)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df_week = df[df[date_col] >= last_week]
        if df_week.empty:
            df_week = df  # Fallback to all data
    else:
        df_week = df

    # Detect user's currency
    currency_symbol, currency_code = get_user_currency(company_id)

    # Calculate metrics
    total_invoices = len(df_week)

    if amount_col:
        has_currency_col = 'currency' in df_week.columns

        if has_currency_col:
            currency_totals = df_week.groupby('currency')[amount_col].sum().to_dict()
            currency_breakdown = calculate_currency_breakdown(currency_totals)
            total_revenue_usd = currency_breakdown['total_usd_equivalent']
            currency_summary = "\n".join([
                f"• {item['currency']}: {item['formatted']} (≈ ${item['usd_equivalent']:,.2f} USD)"
                for item in currency_breakdown['breakdown']
            ])
        else:
            total_revenue = df_week[amount_col].sum()
            total_revenue_usd = convert_to_usd(total_revenue, currency_code)
            currency_summary = f"• {currency_code}: {currency_symbol}{total_revenue:,.2f}"

        avg_invoice = df_week[amount_col].mean() if total_invoices > 0 else 0
    else:
        total_revenue_usd = 0
        avg_invoice = 0
        currency_summary = "• No numeric amount column detected"

    # Dimension analysis
    top_customer = "N/A"
    if customer_col and amount_col and total_invoices > 0:
        try:
            top_customer = str(df_week.groupby(customer_col)[amount_col].sum().idxmax())
        except Exception:
            pass

    top_product = "N/A"
    if product_col and amount_col and total_invoices > 0:
        try:
            top_product = str(df_week.groupby(product_col)[amount_col].sum().idxmax())
        except Exception:
            pass

    # Build LLM context
    amount_label = (amount_col or "value").replace("_", " ").title()
    customer_label = (customer_col or "entity").replace("_", " ").title()
    product_label = (product_col or "category").replace("_", " ").title()

    context = f"""Weekly Business Data (Last 7 Days):

💰 Revenue by Currency:
{currency_summary}
📊 Total USD Equivalent: ${total_revenue_usd:,.2f}

📈 Key Metrics:
- Total Records: {total_invoices}
- Average {amount_label}: {currency_symbol}{avg_invoice:,.2f}
- Top {customer_label}: {top_customer}
- Top {product_label}: {top_product}
"""

    if customer_col and amount_col:
        context += f"\nTop 5 {customer_label}s by {amount_label}:\n{_safe_groupby_top(df_week, customer_col, amount_col)}\n"
    if product_col and amount_col:
        context += f"\nTop 5 {product_label}s by {amount_label}:\n{_safe_groupby_top(df_week, product_col, amount_col)}\n"

    system_prompt = """You are a senior business analyst preparing an executive weekly report.
Write a professional, actionable report with:
1. Executive Summary (2-3 sentences)
2. Key Metrics
3. Trends & Insights
4. Recommendations (3 actionable items)

Use clear business language and focus on actionable insights."""

    prompt = f"""{context}

Generate a comprehensive weekly business report for the executive team."""

    report = chat(prompt, system=system_prompt, max_tokens=1500)

    # Format as HTML for better presentation
    html_report = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Business Report</h1>
        <p><strong>Period:</strong> {last_week.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}</p>
        <p><strong>Company ID:</strong> {company_id}</p>

        <div class="metric">
            <div>Total Revenue (USD Equivalent)</div>
            <div class="metric-value">${total_revenue_usd:,.2f}</div>
        </div>

        <div class="metric">
            <div>Total Transactions</div>
            <div class="metric-value">{total_invoices}</div>
        </div>

        <div class="metric">
            <div>Average Transaction Value</div>
            <div class="metric-value">{currency_symbol}{avg_invoice:,.2f}</div>
        </div>

        <h2>📈 Analysis & Insights</h2>
        <div style="white-space: pre-wrap;">{report}</div>

        <p style="margin-top: 40px; color: #7f8c8d; font-size: 12px;">
        Generated automatically by AI Business Analyst on {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </body>
    </html>
    """

    return html_report


# =============================================================================
# Monthly Report
# =============================================================================

def generate_monthly_report(company_id: str) -> str:
    """
    Generate automated monthly business report.
    Dynamically detects columns — no longer requires 'amount', 'customer', 'product'.
    """
    df = revenue_dataframe(company_id)

    if df is None or df.empty:
        return "No data available for monthly report. Please upload business data first."

    # Detect columns
    amount_col = _detect_amount_col(df)
    customer_col = _detect_category_col(df, 'customer')
    product_col = _detect_category_col(df, 'product')
    date_col = _detect_date_col(df)

    # Filter to last 30 days
    last_month = datetime.now() - timedelta(days=30)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df_month = df[df[date_col] >= last_month]
        if df_month.empty:
            df_month = df
    else:
        df_month = df

    # Detect user's currency
    currency_symbol, currency_code = get_user_currency(company_id)

    # Calculate metrics
    total_invoices = len(df_month)

    if amount_col:
        total_revenue = df_month[amount_col].sum()
        total_revenue_usd = convert_to_usd(total_revenue, currency_code)
        avg_invoice = df_month[amount_col].mean() if total_invoices > 0 else 0
    else:
        total_revenue = 0
        total_revenue_usd = 0
        avg_invoice = 0

    unique_customers = df_month[customer_col].nunique() if customer_col and customer_col in df_month.columns else 0
    unique_products = df_month[product_col].nunique() if product_col and product_col in df_month.columns else 0

    # Growth comparison (vs previous month)
    growth_rate = 0
    if date_col and amount_col:
        prev_month_start = last_month - timedelta(days=30)
        df_prev = df[(df[date_col] >= prev_month_start) & (df[date_col] < last_month)]
        prev_revenue = df_prev[amount_col].sum() if not df_prev.empty else 0
        growth_rate = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0

    amount_label = (amount_col or "value").replace("_", " ").title()
    customer_label = (customer_col or "entity").replace("_", " ").title()
    product_label = (product_col or "category").replace("_", " ").title()

    context = f"""Monthly Business Data (Last 30 Days):
- Total {amount_label}: {currency_symbol}{total_revenue:,.2f} (≈ ${total_revenue_usd:,.2f} USD)
- Growth Rate: {growth_rate:+.1f}% vs previous month
- Total Records: {total_invoices}
- Unique {customer_label}s: {unique_customers}
- Unique {product_label}s: {unique_products}
- Average {amount_label}: {currency_symbol}{avg_invoice:,.2f}
"""

    if date_col and amount_col:
        try:
            weekly_breakdown = df_month.groupby(pd.Grouper(key=date_col, freq='W'))[amount_col].sum().to_string()
            context += f"\nWeekly Breakdown:\n{weekly_breakdown}\n"
        except Exception:
            pass

    if customer_col and amount_col:
        context += f"\nTop 10 {customer_label}s by {amount_label}:\n{_safe_groupby_top(df_month, customer_col, amount_col, 10)}\n"
    if product_col and amount_col:
        context += f"\nTop 10 {product_label}s by {amount_label}:\n{_safe_groupby_top(df_month, product_col, amount_col, 10)}\n"

    system_prompt = """You are a senior business analyst preparing an executive monthly report.
Write a comprehensive, strategic report with:
1. Executive Summary (key highlights)
2. Performance Metrics
3. Trends Analysis (with growth insights)
4. Customer & Product Insights
5. Strategic Recommendations (5 actionable items)

Focus on strategic insights and actionable recommendations."""

    prompt = f"""{context}

Generate a comprehensive monthly business report for the executive team and board."""

    report = chat(prompt, system=system_prompt, max_tokens=2000)

    # Format as HTML
    html_report = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
            .metric {{ background: #ecf0f1; padding: 15px; border-radius: 5px; }}
            .metric-label {{ font-size: 14px; color: #7f8c8d; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #27ae60; margin-top: 5px; }}
            .growth-positive {{ color: #27ae60; }}
            .growth-negative {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>📊 Monthly Business Report</h1>
        <p><strong>Period:</strong> {last_month.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}</p>
        <p><strong>Company ID:</strong> {company_id}</p>

        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Total Revenue (USD)</div>
                <div class="metric-value">${total_revenue_usd:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Transactions</div>
                <div class="metric-value">{total_invoices}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Transaction</div>
                <div class="metric-value">{currency_symbol}{avg_invoice:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Growth Rate</div>
                <div class="metric-value {'growth-positive' if growth_rate >= 0 else 'growth-negative'}">{growth_rate:+.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Unique {customer_label}s</div>
                <div class="metric-value">{unique_customers}</div>
            </div>
            <div class="metric">
                <div class="metric-label">{product_label}s</div>
                <div class="metric-value">{unique_products}</div>
            </div>
        </div>

        <h2>📈 Comprehensive Analysis</h2>
        <div style="white-space: pre-wrap; line-height: 1.6;">{report}</div>

        <p style="margin-top: 40px; color: #7f8c8d; font-size: 12px;">
        Generated automatically by AI Business Analyst on {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </body>
    </html>
    """

    return html_report
