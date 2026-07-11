"""
Report Agent — Enterprise Business Intelligence Reports
=========================================================
Generates comprehensive, McKinsey-quality summaries of business performance.
Uses dynamic column detection — works with ANY dataset, not just sales data.
"""

from agents.base.agent_runner import AgentRunner, Insight
from graph.query import revenue_dataframe
import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# =============================================================================
# Dynamic Column Detection Helpers
# =============================================================================

def _detect_amount_column(df: pd.DataFrame) -> Optional[str]:
    """Find the primary numeric 'amount' column (revenue, sales, price, etc.)."""
    # Priority order of known column names
    candidates = [
        'amount', 'total_amount', 'revenue', 'sales', 'total', 'price',
        'value', 'total_price', 'net_amount', 'gross_amount', 'total_revenue',
        'invoice_amount', 'order_total', 'sum', 'cost',
    ]
    for col in candidates:
        if col in df.columns:
            return col

    # Fallback: pick the first numeric column that looks like money
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if numeric_cols:
        # Prefer columns with large ranges (likely monetary)
        for col in numeric_cols:
            if df[col].max() > 1 and df[col].min() >= 0:
                return col
        return numeric_cols[0]

    return None


def _detect_category_column(df: pd.DataFrame, role: str = 'customer') -> Optional[str]:
    """Find a categorical column by role (customer, product, region, etc.)."""
    role_candidates = {
        'customer': ['customer', 'customer_name', 'client', 'client_name', 'account', 'buyer', 'company', 'user'],
        'product': ['product', 'product_name', 'item', 'item_name', 'sku', 'service', 'category', 'product_category'],
        'region': ['region', 'country', 'city', 'state', 'location', 'territory', 'market', 'area'],
    }

    candidates = role_candidates.get(role, [role])
    for col in candidates:
        if col in df.columns:
            return col

    return None


def _detect_date_column(df: pd.DataFrame) -> Optional[str]:
    """Find the primary date/time column."""
    candidates = ['date', 'created_at', 'order_date', 'timestamp', 'datetime', 'invoice_date', 'transaction_date']
    for col in candidates:
        if col in df.columns:
            return col

    # Fallback: first datetime column
    dt_cols = df.select_dtypes(include='datetime').columns.tolist()
    if dt_cols:
        return dt_cols[0]

    return None


def _auto_detect_groupby_col(df: pd.DataFrame) -> Optional[str]:
    """Pick the best categorical groupby column automatically."""
    object_cols = df.select_dtypes(include='object').columns.tolist()
    if not object_cols:
        return None

    # Prefer columns with reasonable cardinality (2–500 unique values)
    scored = []
    for col in object_cols:
        nunique = df[col].nunique()
        if 2 <= nunique <= 500:
            scored.append((col, nunique))

    if scored:
        # Prefer lower cardinality (more groupable)
        scored.sort(key=lambda x: x[1])
        return scored[0][0]

    return object_cols[0] if object_cols else None


# =============================================================================
# Report Agent
# =============================================================================

class ReportAgent(AgentRunner):
    """Generates premium enterprise-grade business reports using dynamic column detection."""

    def __init__(self):
        super().__init__('ReportAgent')

    async def detect_insights(self, workspace_id: str) -> List[Insight]:
        """Generate report insight"""
        insights = []

        try:
            df = revenue_dataframe(workspace_id)

            if df is None or df.empty:
                self.logger.warning(f"No data for workspace {workspace_id}")
                return []

            # Generate comprehensive report
            report_data = await self._generate_enterprise_report(df)

            if report_data:
                insight = Insight(
                    title="📊 AI Business Intelligence Report",
                    body=report_data['summary'],
                    severity='info',
                    score=100,  # Always send reports
                    metadata=report_data['metrics'],
                    chart_payload=report_data.get('chart_data')
                )
                insights.append(insight)

            self.logger.info(f"ReportAgent generated {len(insights)} insights")
            return insights

        except Exception as e:
            self.logger.error(f"ReportAgent failed: {e}", exc_info=True)
            return []

    async def _generate_enterprise_report(self, df: pd.DataFrame) -> Optional[Dict]:
        """Generate enterprise-quality report using dynamic column detection."""
        try:
            # ============================================
            # DYNAMIC COLUMN DETECTION
            # ============================================
            amount_col = _detect_amount_column(df)
            customer_col = _detect_category_column(df, 'customer')
            product_col = _detect_category_column(df, 'product')
            date_col = _detect_date_column(df)

            total_rows = len(df)

            # ============================================
            # CORE METRICS (with fallbacks)
            # ============================================
            if amount_col:
                total_revenue = df[amount_col].sum()
                avg_order_value = total_revenue / total_rows if total_rows > 0 else 0
                min_value = df[amount_col].min()
                max_value = df[amount_col].max()
                median_value = df[amount_col].median()
            else:
                total_revenue = 0
                avg_order_value = 0
                min_value = 0
                max_value = 0
                median_value = 0

            # ============================================
            # CUSTOMER/DIMENSION ANALYSIS
            # ============================================
            top_customers = []
            customer_concentration = 0
            unique_customers = 0

            if customer_col and amount_col:
                unique_customers = df[customer_col].nunique()
                customer_revenue = df.groupby(customer_col)[amount_col].sum().sort_values(ascending=False)

                top_5_revenue = customer_revenue.head(5).sum()
                customer_concentration = (top_5_revenue / total_revenue * 100) if total_revenue > 0 else 0

                for name, revenue in customer_revenue.head(5).items():
                    orders = len(df[df[customer_col] == name])
                    pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                    top_customers.append({
                        'name': str(name),
                        'revenue': float(revenue),
                        'orders': int(orders),
                        'percentage': round(pct, 1)
                    })
            elif customer_col:
                unique_customers = df[customer_col].nunique()

            # ============================================
            # PRODUCT/CATEGORY ANALYSIS
            # ============================================
            top_products = []
            best_product = None
            unique_products = 0

            if product_col and amount_col:
                unique_products = df[product_col].nunique()
                product_revenue = df.groupby(product_col)[amount_col].sum().sort_values(ascending=False)

                best_product = str(product_revenue.index[0]) if len(product_revenue) > 0 else None

                for name, revenue in product_revenue.head(5).items():
                    units = len(df[df[product_col] == name])
                    pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                    top_products.append({
                        'name': str(name),
                        'revenue': float(revenue),
                        'units': int(units),
                        'percentage': round(pct, 1)
                    })
            elif product_col:
                unique_products = df[product_col].nunique()

            # ============================================
            # BUILD REPORT SUMMARY
            # ============================================
            currency = "₹"

            # Dynamic label based on detected column
            amount_label = (amount_col or "value").replace("_", " ").title()
            customer_label = (customer_col or "entity").replace("_", " ").title()
            product_label = (product_col or "category").replace("_", " ").title()

            summary = f"""
📈 **Executive Summary**

Your dataset contains **{total_rows:,}** records"""

            if amount_col:
                summary += f""" with total {amount_label} of **{currency}{total_revenue:,.2f}**.

---

💰 **Key Performance Indicators**

| Metric | Value |
|--------|-------|
| Total {amount_label} | {currency}{total_revenue:,.2f} |
| Total Records | {total_rows:,} |
| Average {amount_label} | {currency}{avg_order_value:,.2f} |
| Median {amount_label} | {currency}{median_value:,.2f} |
| Min {amount_label} | {currency}{min_value:,.2f} |
| Max {amount_label} | {currency}{max_value:,.2f} |"""
            else:
                summary += ".\n\n> ⚠️ No numeric amount column detected — showing row-count analysis only."

            if unique_customers:
                summary += f"\n| Unique {customer_label}s | {unique_customers} |"
            if unique_products:
                summary += f"\n| Unique {product_label}s | {unique_products} |"

            summary += "\n\n---\n"

            # Customer section
            if top_customers:
                summary += f"\n👥 **Top 5 {customer_label}s**\n\n"
                summary += f"| Rank | {customer_label} | {amount_label} | Records | Share |\n"
                summary += "|------|----------|---------|--------|-------|\n"
                for i, c in enumerate(top_customers, 1):
                    summary += f"| {i} | {c['name']} | {currency}{c['revenue']:,.2f} | {c['orders']} | {c['percentage']}% |\n"
                summary += f"\n⚠️ **Concentration Risk:** Top 5 = {customer_concentration:.1f}% of total\n\n---\n"

            # Product section
            if top_products:
                summary += f"\n📦 **Top 5 {product_label}s**\n\n"
                summary += f"| Rank | {product_label} | {amount_label} | Units | Share |\n"
                summary += "|------|---------|---------|-------|-------|\n"
                for i, p in enumerate(top_products, 1):
                    summary += f"| {i} | {p['name']} | {currency}{p['revenue']:,.2f} | {p['units']} | {p['percentage']}% |\n"
                summary += "\n---\n"

            # AI Recommendations
            summary += "\n💡 **AI Recommendations**\n\n"

            if customer_concentration > 50:
                summary += f"1. **🔴 High Concentration** - Top 5 {customer_label}s represent {customer_concentration:.0f}% of total. Diversify.\n"
            elif customer_concentration > 30:
                summary += f"1. **🟡 Moderate Concentration** - Consider expanding to new {customer_label} segments.\n"
            elif customer_col:
                summary += f"1. **🟢 Healthy Diversification** - {amount_label} is well-distributed across {customer_label}s.\n"

            if amount_col and avg_order_value < 1000:
                summary += f"2. **Increase Average** - Current {currency}{avg_order_value:,.2f} — consider bundling or upsells.\n"
            elif amount_col:
                summary += f"2. **Strong Average** - {currency}{avg_order_value:,.2f} indicates healthy transaction size.\n"

            if best_product:
                summary += f"3. **Focus on {best_product}** - Top performer. Consider expanding this line.\n"

            summary += "\n---\n\n*Report generated by AI Business Analyst Enterprise*"

            return {
                'summary': summary,
                'metrics': {
                    'total_revenue': float(total_revenue),
                    'total_records': total_rows,
                    'avg_order_value': float(avg_order_value),
                    'unique_customers': unique_customers,
                    'unique_products': unique_products,
                    'customer_concentration': float(customer_concentration),
                    'top_customers': top_customers,
                    'top_products': top_products,
                    'detected_columns': {
                        'amount': amount_col,
                        'customer': customer_col,
                        'product': product_col,
                        'date': date_col,
                    }
                },
                'chart_data': None
            }

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}", exc_info=True)
            return None


# =============================================================================
# Scheduler-callable functions
# =============================================================================

async def generate_daily_report(workspace_id: str) -> Dict:
    """Generate daily business report"""
    agent = ReportAgent()
    insights = await agent.detect_insights(workspace_id)

    if insights:
        return {
            'success': True,
            'title': insights[0].title,
            'body': insights[0].body,
            'metrics': insights[0].metadata
        }
    return {'success': False, 'error': 'No data available'}


async def generate_weekly_report(workspace_id: str) -> Dict:
    """Generate weekly business report with extended analysis"""
    agent = ReportAgent()
    insights = await agent.detect_insights(workspace_id)

    if insights:
        weekly_header = "📆 **Weekly Business Review**\n\n"
        weekly_header += f"Report Period: {(datetime.now() - timedelta(days=7)).strftime('%b %d')} - {datetime.now().strftime('%b %d, %Y')}\n\n"

        return {
            'success': True,
            'title': "📊 Weekly Business Intelligence Report",
            'body': weekly_header + insights[0].body,
            'metrics': insights[0].metadata
        }
    return {'success': False, 'error': 'No data available'}
