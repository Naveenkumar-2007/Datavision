"""
Report Agent - $500K Enterprise Daily & Weekly Business Reports
Generates comprehensive, McKinsey-quality summaries of business performance
"""

from agents.base.agent_runner import AgentRunner, Insight
from graph.query import revenue_dataframe
import pandas as pd
import logging
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReportAgent(AgentRunner):
    """Generates premium enterprise-grade business reports"""
    
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
    
    async def _generate_enterprise_report(self, df) -> Dict:
        """Generate $500K quality business report"""
        try:
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            
            # ============================================
            # CORE METRICS
            # ============================================
            total_revenue = df[amount_col].sum()
            total_orders = len(df)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # ============================================
            # CUSTOMER ANALYSIS
            # ============================================
            top_customers = []
            customer_concentration = 0
            if 'customer' in df.columns:
                unique_customers = df['customer'].nunique()
                customer_revenue = df.groupby('customer')[amount_col].sum().sort_values(ascending=False)
                
                top_5_revenue = customer_revenue.head(5).sum()
                customer_concentration = (top_5_revenue / total_revenue * 100) if total_revenue > 0 else 0
                
                for name, revenue in customer_revenue.head(5).items():
                    orders = len(df[df['customer'] == name])
                    pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                    top_customers.append({
                        'name': name,
                        'revenue': revenue,
                        'orders': orders,
                        'percentage': round(pct, 1)
                    })
            else:
                unique_customers = 0
            
            # ============================================
            # PRODUCT ANALYSIS
            # ============================================
            top_products = []
            best_product = None
            if 'product' in df.columns:
                unique_products = df['product'].nunique()
                product_revenue = df.groupby('product')[amount_col].sum().sort_values(ascending=False)
                
                best_product = product_revenue.index[0] if len(product_revenue) > 0 else None
                
                for name, revenue in product_revenue.head(5).items():
                    units = len(df[df['product'] == name])
                    pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                    top_products.append({
                        'name': name,
                        'revenue': revenue,
                        'units': units,
                        'percentage': round(pct, 1)
                    })
            else:
                unique_products = 0
            
            # ============================================
            # BUILD PREMIUM REPORT SUMMARY
            # ============================================
            currency = "₹"
            
            summary = f"""
📈 **Executive Summary**

Your business generated **{currency}{total_revenue:,.2f}** in total revenue from **{total_orders:,}** orders.

---

💰 **Key Performance Indicators**

| Metric | Value |
|--------|-------|
| Total Revenue | {currency}{total_revenue:,.2f} |
| Total Orders | {total_orders:,} |
| Average Order Value | {currency}{avg_order_value:,.2f} |
| Unique Customers | {unique_customers} |
| Unique Products | {unique_products} |

---

👥 **Top 5 Customers**

"""
            # Add customer table
            if top_customers:
                summary += "| Rank | Customer | Revenue | Orders | Share |\n"
                summary += "|------|----------|---------|--------|-------|\n"
                for i, c in enumerate(top_customers, 1):
                    summary += f"| {i} | {c['name']} | {currency}{c['revenue']:,.2f} | {c['orders']} | {c['percentage']}% |\n"
                
                summary += f"\n⚠️ **Concentration Risk:** Top 5 customers = {customer_concentration:.1f}% of revenue\n\n"
            
            summary += "---\n\n📦 **Top 5 Products**\n\n"
            
            if top_products:
                summary += "| Rank | Product | Revenue | Units | Share |\n"
                summary += "|------|---------|---------|-------|-------|\n"
                for i, p in enumerate(top_products, 1):
                    summary += f"| {i} | {p['name']} | {currency}{p['revenue']:,.2f} | {p['units']} | {p['percentage']}% |\n"
            
            # Add recommendations
            summary += """
---

💡 **AI Recommendations**

"""
            # Generate smart recommendations
            if customer_concentration > 50:
                summary += "1. **🔴 High Customer Concentration** - Top 5 customers represent over 50% of revenue. Diversify your customer base.\n"
            elif customer_concentration > 30:
                summary += "1. **🟡 Moderate Concentration** - Consider expanding to new customer segments.\n"
            else:
                summary += "1. **🟢 Healthy Diversification** - Revenue is well-distributed across customers.\n"
            
            if avg_order_value < 1000:
                summary += f"2. **Increase AOV** - Current ₹{avg_order_value:,.2f} is below ₹1,000. Bundle products or add upsells.\n"
            else:
                summary += f"2. **Strong AOV** - Average order of ₹{avg_order_value:,.2f} indicates healthy basket size.\n"
            
            if best_product:
                summary += f"3. **Focus on {best_product}** - Your best performer. Consider expanding this product line.\n"
            
            summary += "\n---\n\n*Report generated by AI Business Analyst Enterprise*"
            
            return {
                'summary': summary,
                'metrics': {
                    'total_revenue': total_revenue,
                    'total_orders': total_orders,
                    'avg_order_value': avg_order_value,
                    'unique_customers': unique_customers,
                    'unique_products': unique_products,
                    'customer_concentration': customer_concentration,
                    'top_customers': top_customers,
                    'top_products': top_products
                },
                'chart_data': None  # Can add chart payload here
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return None


# Daily report function for scheduler
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


# Weekly report function for scheduler
async def generate_weekly_report(workspace_id: str) -> Dict:
    """Generate weekly business report with extended analysis"""
    agent = ReportAgent()
    insights = await agent.detect_insights(workspace_id)
    
    if insights:
        # Add weekly header
        weekly_header = "📆 **Weekly Business Review**\n\n"
        weekly_header += f"Report Period: {(datetime.now() - timedelta(days=7)).strftime('%b %d')} - {datetime.now().strftime('%b %d, %Y')}\n\n"
        
        return {
            'success': True,
            'title': "📊 Weekly Business Intelligence Report",
            'body': weekly_header + insights[0].body,
            'metrics': insights[0].metadata
        }
    return {'success': False, 'error': 'No data available'}
