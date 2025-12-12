"""
Report Agent - Generate weekly business reports
Creates comprehensive summaries of business performance
"""

from agents.base.agent_runner import AgentRunner, Insight
from graph.query import revenue_dataframe
import pandas as pd
import logging
from typing import List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReportAgent(AgentRunner):
    """Generates periodic business reports"""
    
    def __init__(self):
        super().__init__('ReportAgent')
    
    async def detect_insights(self, workspace_id: str) -> List[Insight]:
        """Generate weekly report insight"""
        insights = []
        
        try:
            df = revenue_dataframe(workspace_id)
            
            if df is None or df.empty:
                self.logger.warning(f"No data for workspace {workspace_id}")
                return []
            
            # Generate weekly summary
            report_data = await self._generate_weekly_summary(df)
            
            if report_data:
                insight = Insight(
                    title="📊 Weekly Business Report",
                    body=report_data['summary'],
                    severity='low',  # Reports are informational
                    score=100,  # Always send reports
                    metadata=report_data['metrics'],
                    chart_payload=None
                )
                insights.append(insight)
            
            self.logger.info(f"ReportAgent generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"ReportAgent failed: {e}", exc_info=True)
            return []
    
    async def _generate_weekly_summary(self, df) -> dict:
        """Generate weekly business summary"""
        try:
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            
            # Calculate key metrics
            total_revenue = df[amount_col].sum()
            total_orders = len(df)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            top_customers = []
            top_products = []
            
            if 'customer' in df.columns:
                customer_revenue = df.groupby('customer')[amount_col].sum().sort_values(ascending=False).head(5)
                top_customers = [{'name': k, 'revenue': v} for k, v in customer_revenue.items()]
            
            if 'product' in df.columns:
                product_revenue = df.groupby('product')[amount_col].sum().sort_values(ascending=False).head(5)
                top_products = [{'name': k, 'revenue': v} for k, v in product_revenue.items()]
            
            # Build summary text
            summary = f"Your business generated ₹{total_revenue:,.2f} from {total_orders} orders. "
            summary += f"Average order value: ₹{avg_order_value:,.2f}. "
            
            if top_customers:
                summary += f"Top customer: {top_customers[0]['name']} (₹{top_customers[0]['revenue']:,.2f}). "
            
            if top_products:
                summary += f"Best-selling product: {top_products[0]['name']}."
            
            return {
                'summary': summary,
                'metrics': {
                    'total_revenue': total_revenue,
                    'total_orders': total_orders,
                    'avg_order_value': avg_order_value,
                    'top_customers': top_customers,
                    'top_products': top_products
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            return None
