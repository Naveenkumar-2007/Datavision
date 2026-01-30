"""
Monitoring Agent - Continuous business monitoring
Detects anomalies, risks, and opportunities in real-time data
"""

from agents.base.agent_runner import AgentRunner, Insight
from services.mcp_client import mcp_client
from graph.query import revenue_dataframe
import logging
from typing import List

logger = logging.getLogger(__name__)


class MonitoringAgent(AgentRunner):
    """Monitors business metrics and detects anomalies"""
    
    def __init__(self):
        super().__init__('MonitoringAgent')
    
    async def detect_insights(self, workspace_id: str) -> List[Insight]:
        """Detect monitoring insights for workspace"""
        insights = []
        
        try:
            # Load workspace data
            df = revenue_dataframe(workspace_id)
            
            if df is None or df.empty:
                self.logger.warning(f"No data for workspace {workspace_id}")
                return []
            
            # Use MCP to detect insights
            mcp_insights = await mcp_client.detect_insights(workspace_id, {'dataframe': df})
            
            # Convert to Insight objects
            for insight_data in mcp_insights:
                insight = Insight(
                    title=insight_data.get('title', 'Monitoring Alert'),
                    body=insight_data.get('body', ''),
                    severity=insight_data.get('severity', 'medium'),
                    score=insight_data.get('score'),
                    metadata=insight_data.get('metadata', {}),
                    chart_payload=insight_data.get('chart_payload')
                )
                insights.append(insight)
            
            # Add custom monitoring checks
            custom_insights = await self._run_custom_checks(workspace_id, df)
            insights.extend(custom_insights)
            
            self.logger.info(f"MonitoringAgent detected {len(insights)} insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"MonitoringAgent failed: {e}", exc_info=True)
            return []
    
    async def _run_custom_checks(self, workspace_id: str, df) -> List[Insight]:
        """Run custom business logic checks"""
        insights = []
        
        try:
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            
            # Check for revenue drop
            if 'date' in df.columns:
                import pandas as pd
                df_temp = df.copy()
                df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
                df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
                
                if not df_dated.empty and len(df_dated) > 30:
                    # Get last 7 days vs previous 7 days
                    df_dated = df_dated.sort_values('date_parsed', ascending=False)
                    recent_7_days = df_dated.head(7)[amount_col].sum()
                    previous_7_days = df_dated.iloc[7:14][amount_col].sum()
                    
                    if previous_7_days > 0:
                        change_pct = ((recent_7_days - previous_7_days) / previous_7_days) * 100
                        
                        if change_pct < -15:  # 15% drop
                            insights.append(Insight(
                                title="⚠️ Revenue Drop Detected",
                                body=f"Revenue decreased by {abs(change_pct):.1f}% in the last 7 days compared to the previous week. Recent: ₹{recent_7_days:,.2f}, Previous: ₹{previous_7_days:,.2f}.",
                                severity='high',
                                score=95,
                                metadata={'change_pct': change_pct, 'recent': recent_7_days, 'previous': previous_7_days}
                            ))
            
            # Check for high-value customer churn risk
            if 'customer' in df.columns:
                customer_revenue = df.groupby('customer')[amount_col].sum().sort_values(ascending=False)
                top_customer_revenue = customer_revenue.iloc[0] if len(customer_revenue) > 0 else 0
                total_revenue = df[amount_col].sum()
                
                if total_revenue > 0 and top_customer_revenue / total_revenue > 0.25:  # > 25% concentration
                    insights.append(Insight(
                        title="📊 Customer Concentration Risk",
                        body=f"Your top customer accounts for {(top_customer_revenue/total_revenue*100):.1f}% of total revenue (₹{top_customer_revenue:,.2f}). Consider diversifying your customer base.",
                        severity='medium',
                        score=70,
                        metadata={'concentration': top_customer_revenue/total_revenue, 'top_customer_revenue': top_customer_revenue}
                    ))
            
        except Exception as e:
            self.logger.error(f"Custom checks failed: {e}")
        
        return insights
