# Report generation module
"""Weekly & Monthly business report generator."""

import pandas as pd
from datetime import datetime, timedelta
from core.llm import chat
from graph.query import revenue_dataframe


def generate_weekly_report(company_id: str) -> str:
    """
    Generate automated weekly business report
    """
    df = revenue_dataframe(company_id)
    
    if df.empty:
        return "No data available for weekly report. Please upload business data first."
    
    # Get last 7 days
    df['date'] = pd.to_datetime(df['date'])
    last_week = datetime.now() - timedelta(days=7)
    df_week = df[df['date'] >= last_week]
    
    # Calculate metrics
    total_revenue = df_week['amount'].sum()
    total_invoices = len(df_week)
    avg_invoice = df_week['amount'].mean() if total_invoices > 0 else 0
    top_customer = df_week.groupby('customer')['amount'].sum().idxmax() if total_invoices > 0 else "N/A"
    top_product = df_week.groupby('product')['amount'].sum().idxmax() if total_invoices > 0 else "N/A"
    
    # Create context for LLM
    context = f"""Weekly Business Data (Last 7 Days):
- Total Revenue: ₹{total_revenue:,.2f}
- Total Invoices: {total_invoices}
- Average Invoice Value: ₹{avg_invoice:,.2f}
- Top Customer: {top_customer}
- Top Product: {top_product}

Daily Breakdown:
{df_week.groupby('date')['amount'].sum().to_string()}

Top 5 Customers by Revenue:
{df_week.groupby('customer')['amount'].sum().nlargest(5).to_string()}

Top 5 Products by Revenue:
{df_week.groupby('product')['amount'].sum().nlargest(5).to_string()}"""

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
            <div>Total Revenue</div>
            <div class="metric-value">₹{total_revenue:,.2f}</div>
        </div>
        
        <div class="metric">
            <div>Total Transactions</div>
            <div class="metric-value">{total_invoices}</div>
        </div>
        
        <div class="metric">
            <div>Average Transaction Value</div>
            <div class="metric-value">₹{avg_invoice:,.2f}</div>
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


def generate_monthly_report(company_id: str) -> str:
    """
    Generate automated monthly business report
    """
    df = revenue_dataframe(company_id)
    
    if df.empty:
        return "No data available for monthly report. Please upload business data first."
    
    # Get last 30 days
    df['date'] = pd.to_datetime(df['date'])
    last_month = datetime.now() - timedelta(days=30)
    df_month = df[df['date'] >= last_month]
    
    # Calculate metrics
    total_revenue = df_month['amount'].sum()
    total_invoices = len(df_month)
    unique_customers = df_month['customer'].nunique()
    unique_products = df_month['product'].nunique()
    avg_invoice = df_month['amount'].mean() if total_invoices > 0 else 0
    
    # Growth comparison (compare to previous month)
    prev_month_start = last_month - timedelta(days=30)
    df_prev = df[(df['date'] >= prev_month_start) & (df['date'] < last_month)]
    prev_revenue = df_prev['amount'].sum()
    growth_rate = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    
    context = f"""Monthly Business Data (Last 30 Days):
- Total Revenue: ₹{total_revenue:,.2f}
- Growth Rate: {growth_rate:+.1f}% vs previous month
- Total Invoices: {total_invoices}
- Unique Customers: {unique_customers}
- Unique Products Sold: {unique_products}
- Average Invoice Value: ₹{avg_invoice:,.2f}

Weekly Breakdown:
{df_month.groupby(pd.Grouper(key='date', freq='W'))['amount'].sum().to_string()}

Top 10 Customers by Revenue:
{df_month.groupby('customer')['amount'].sum().nlargest(10).to_string()}

Top 10 Products by Revenue:
{df_month.groupby('product')['amount'].sum().nlargest(10).to_string()}"""

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
                <div class="metric-label">Total Revenue</div>
                <div class="metric-value">₹{total_revenue:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Transactions</div>
                <div class="metric-value">{total_invoices}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Transaction</div>
                <div class="metric-value">₹{avg_invoice:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Growth Rate</div>
                <div class="metric-value {'growth-positive' if growth_rate >= 0 else 'growth-negative'}">{growth_rate:+.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Unique Customers</div>
                <div class="metric-value">{unique_customers}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Products Sold</div>
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
