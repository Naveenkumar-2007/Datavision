"""
Forecast Agent - Revenue and trend prediction
Generates forecasts and predictive insights
"""

from agents.base.agent_runner import AgentRunner, Insight
from services.mcp_client import mcp_client
from graph.query import revenue_dataframe
import logging
from typing import List

logger = logging.getLogger(__name__)


class ForecastAgent(AgentRunner):
    """Generates revenue forecasts and predictions"""
    
    def __init__(self):
        super().__init__('ForecastAgent')
    
    async def detect_insights(self, workspace_id: str) -> List[Insight]:
        """Generate forecast insights"""
        insights = []
        
        try:
            df = revenue_dataframe(workspace_id)
            
            if df is None or df.empty:
                self.logger.warning(f"No data for workspace {workspace_id}")
                return []
            
            # Check if we have date column for forecasting
            if 'date' not in df.columns:
                self.logger.warning(f"No date column in data for workspace {workspace_id}")
                return []
            
            # Run forecast for next 3 months
            forecast_result = await mcp_client.run_forecast(workspace_id, periods=3)
            
            if not forecast_result:
                return []
            
            # Create insight from forecast
            trend = forecast_result.get('trend', 'stable')
            forecast_points = forecast_result.get('forecast_points', [])
            
            if forecast_points and len(forecast_points) > 0:
                next_period_value = forecast_points[0].get('value', 0)
                upper_bound = forecast_points[0].get('upper', next_period_value * 1.1)
                lower_bound = forecast_points[0].get('lower', next_period_value * 0.9)
                
                # Determine severity based on trend
                severity = 'low'
                if trend in ['strongly_increasing', 'strongly_decreasing']:
                    severity = 'high'
                elif trend in ['increasing', 'decreasing']:
                    severity = 'medium'
                
                insight = Insight(
                    title=f"📈 Revenue Forecast: {trend.replace('_', ' ').title()}",
                    body=f"Based on historical data, revenue is projected to be ₹{next_period_value:,.2f} next period (range: ₹{lower_bound:,.2f} - ₹{upper_bound:,.2f}). Trend: {trend.replace('_', ' ')}.",
                    severity=severity,
                    score=forecast_result.get('accuracy', {}).get('confidence', 75),
                    metadata={
                        'forecast_result': forecast_result,
                        'trend': trend,
                        'periods': 3
                    },
                    chart_payload=forecast_result.get('chart_payload')
                )
                
                insights.append(insight)
            
            self.logger.info(f"ForecastAgent generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            self.logger.error(f"ForecastAgent failed: {e}", exc_info=True)
            return []
