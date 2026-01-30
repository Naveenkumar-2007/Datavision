# Insight Engine MCP Service
"""
Enterprise Automated Insight Generation Engine

Features:
- Trend detection (MoM, YoY)
- Anomaly detection (Z-score)
- Top/bottom performer analysis
- Risk identification
- Opportunity scoring
- Customer segmentation insights
- Automated recommendations

Usage:
    from mcp.insight_engine import InsightEngine
    engine = InsightEngine()
    result = engine.analyze(data)
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class InsightType(Enum):
    TREND = "trend"
    ANOMALY = "anomaly"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    PERFORMANCE = "performance"
    RECOMMENDATION = "recommendation"


class InsightSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Insight:
    """A single business insight"""
    type: InsightType
    message: str
    severity: InsightSeverity
    metric: str
    value: Optional[float] = None
    change_pct: Optional[float] = None
    recommendation: Optional[str] = None
    icon: str = "💡"


@dataclass
class InsightResult:
    """Result from insight engine"""
    insights: List[Insight]
    summary: str
    risk_score: float
    opportunity_score: float
    health_score: float
    top_priority: str


class InsightEngine:
    """
    Enterprise Automated Insight Generation Engine.
    
    Analyzes business data and generates:
    - Trend insights (growth/decline patterns)
    - Anomaly alerts (unusual values)
    - Risk warnings
    - Opportunity identification
    - Actionable recommendations
    """
    
    # Thresholds for analysis
    GROWTH_THRESHOLD = 5  # % for significant growth
    DECLINE_THRESHOLD = -5  # % for significant decline
    ANOMALY_Z_SCORE = 2  # Z-score threshold for anomalies
    
    def __init__(self):
        self.insights_generated = 0
        
    def analyze(
        self,
        revenue: float = 0,
        revenue_previous: float = 0,
        customers: int = 0,
        customers_previous: int = 0,
        orders: int = 0,
        orders_previous: int = 0,
        top_products: Optional[List[Dict]] = None,
        top_customers: Optional[List[Dict]] = None,
        time_series: Optional[List[Dict]] = None,
        churn_rate: float = 0,
        profit_margin: float = 0
    ) -> InsightResult:
        """
        Analyze business metrics and generate insights.
        
        Args:
            revenue: Current period revenue
            revenue_previous: Previous period revenue
            customers: Current customer count
            customers_previous: Previous customer count
            orders: Current order count
            orders_previous: Previous order count
            top_products: List of top products with revenue
            top_customers: List of top customers with revenue
            time_series: Time series data for trend analysis
            churn_rate: Customer churn rate
            profit_margin: Profit margin (0-1)
            
        Returns:
            InsightResult with all generated insights
        """
        insights = []
        
        # Revenue trends
        if revenue and revenue_previous:
            insights.extend(self._analyze_revenue_trend(revenue, revenue_previous))
            
        # Customer trends
        if customers and customers_previous:
            insights.extend(self._analyze_customer_trend(customers, customers_previous))
            
        # Order trends
        if orders and orders_previous:
            insights.extend(self._analyze_order_trend(orders, orders_previous))
            
        # Product performance
        if top_products:
            insights.extend(self._analyze_product_performance(top_products))
            
        # Customer concentration
        if top_customers and revenue:
            insights.extend(self._analyze_customer_concentration(top_customers, revenue))
            
        # Time series anomalies
        if time_series:
            insights.extend(self._detect_anomalies(time_series))
            insights.extend(self._detect_time_trends(time_series))
            
        # Risk analysis
        insights.extend(self._analyze_risks(churn_rate, profit_margin, revenue, revenue_previous))
        
        # Opportunity identification
        insights.extend(self._identify_opportunities(
            revenue, customers, orders, top_products, profit_margin
        ))
        
        # Calculate scores
        risk_score = self._calculate_risk_score(insights)
        opp_score = self._calculate_opportunity_score(insights)
        health_score = self._calculate_health_score(insights, risk_score, opp_score)
        
        # Generate summary
        summary = self._generate_summary(insights, risk_score, opp_score)
        
        # Find top priority
        priority = self._find_top_priority(insights)
        
        return InsightResult(
            insights=insights,
            summary=summary,
            risk_score=risk_score,
            opportunity_score=opp_score,
            health_score=health_score,
            top_priority=priority
        )
        
    def _analyze_revenue_trend(self, current: float, previous: float) -> List[Insight]:
        """Analyze revenue trend."""
        insights = []
        change_pct = ((current - previous) / previous * 100) if previous else 0
        
        if change_pct > 20:
            insights.append(Insight(
                type=InsightType.TREND,
                message=f"Revenue grew {change_pct:.1f}% - exceptional performance!",
                severity=InsightSeverity.HIGH,
                metric="revenue",
                value=current,
                change_pct=change_pct,
                icon="🚀"
            ))
        elif change_pct > self.GROWTH_THRESHOLD:
            insights.append(Insight(
                type=InsightType.TREND,
                message=f"Revenue increased {change_pct:.1f}% period-over-period",
                severity=InsightSeverity.MEDIUM,
                metric="revenue",
                value=current,
                change_pct=change_pct,
                icon="📈"
            ))
        elif change_pct < -20:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Revenue dropped {abs(change_pct):.1f}% - requires immediate attention",
                severity=InsightSeverity.CRITICAL,
                metric="revenue",
                value=current,
                change_pct=change_pct,
                recommendation="Analyze root causes: pricing, churn, or market conditions",
                icon="🚨"
            ))
        elif change_pct < self.DECLINE_THRESHOLD:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Revenue decreased {abs(change_pct):.1f}% - monitor closely",
                severity=InsightSeverity.HIGH,
                metric="revenue",
                value=current,
                change_pct=change_pct,
                recommendation="Review sales pipeline and customer retention",
                icon="⚠️"
            ))
            
        return insights
        
    def _analyze_customer_trend(self, current: int, previous: int) -> List[Insight]:
        """Analyze customer trend."""
        insights = []
        change_pct = ((current - previous) / previous * 100) if previous else 0
        
        if change_pct > 10:
            insights.append(Insight(
                type=InsightType.TREND,
                message=f"Customer base grew {change_pct:.1f}%",
                severity=InsightSeverity.MEDIUM,
                metric="customers",
                value=current,
                change_pct=change_pct,
                icon="👥"
            ))
        elif change_pct < -10:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Customer base declined {abs(change_pct):.1f}%",
                severity=InsightSeverity.HIGH,
                metric="customers",
                value=current,
                change_pct=change_pct,
                recommendation="Implement customer retention programs",
                icon="⚠️"
            ))
            
        return insights
        
    def _analyze_order_trend(self, current: int, previous: int) -> List[Insight]:
        """Analyze order volume trend."""
        insights = []
        change_pct = ((current - previous) / previous * 100) if previous else 0
        
        if change_pct > 15:
            insights.append(Insight(
                type=InsightType.TREND,
                message=f"Order volume up {change_pct:.1f}% - strong demand",
                severity=InsightSeverity.MEDIUM,
                metric="orders",
                value=current,
                change_pct=change_pct,
                icon="📦"
            ))
        elif change_pct < -15:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Order volume down {abs(change_pct):.1f}%",
                severity=InsightSeverity.HIGH,
                metric="orders",
                value=current,
                change_pct=change_pct,
                recommendation="Review product catalog and pricing strategy",
                icon="📉"
            ))
            
        return insights
        
    def _analyze_product_performance(self, products: List[Dict]) -> List[Insight]:
        """Analyze product performance."""
        insights = []
        
        if not products:
            return insights
            
        # Top performer
        top = products[0] if products else None
        if top:
            insights.append(Insight(
                type=InsightType.PERFORMANCE,
                message=f"Top product: {top.get('name', 'Unknown')} - ${top.get('revenue', 0):,.0f}",
                severity=InsightSeverity.LOW,
                metric="product_revenue",
                value=top.get('revenue', 0),
                icon="🏆"
            ))
            
        # Product concentration risk
        if len(products) >= 2:
            total = sum(p.get('revenue', 0) for p in products)
            top_share = (products[0].get('revenue', 0) / total * 100) if total else 0
            
            if top_share > 50:
                insights.append(Insight(
                    type=InsightType.RISK,
                    message=f"High product concentration: top product = {top_share:.0f}% of revenue",
                    severity=InsightSeverity.MEDIUM,
                    metric="product_concentration",
                    value=top_share,
                    recommendation="Diversify product portfolio to reduce risk",
                    icon="⚠️"
                ))
                
        return insights
        
    def _analyze_customer_concentration(self, customers: List[Dict], total_revenue: float) -> List[Insight]:
        """Analyze customer concentration risk."""
        insights = []
        
        if not customers or not total_revenue:
            return insights
            
        # Top customer concentration
        top_5_revenue = sum(c.get('revenue', 0) for c in customers[:5])
        concentration = (top_5_revenue / total_revenue * 100) if total_revenue else 0
        
        if concentration > 60:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"High customer concentration: top 5 = {concentration:.0f}% of revenue",
                severity=InsightSeverity.HIGH,
                metric="customer_concentration",
                value=concentration,
                recommendation="Expand customer base to reduce dependency",
                icon="🚨"
            ))
        elif concentration > 40:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Moderate customer concentration: top 5 = {concentration:.0f}% of revenue",
                severity=InsightSeverity.MEDIUM,
                metric="customer_concentration",
                value=concentration,
                icon="⚠️"
            ))
            
        return insights
        
    def _detect_anomalies(self, time_series: List[Dict]) -> List[Insight]:
        """Detect anomalies in time series data."""
        insights = []
        
        if len(time_series) < 5:
            return insights
            
        values = [item.get('value', item.get('revenue', 0)) for item in time_series]
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return insights
            
        # Check for anomalies
        for i, (item, val) in enumerate(zip(time_series, values)):
            z_score = (val - mean) / std
            
            if abs(z_score) > self.ANOMALY_Z_SCORE:
                date = item.get('date', f'Period {i+1}')
                direction = "spike" if z_score > 0 else "drop"
                
                insights.append(Insight(
                    type=InsightType.ANOMALY,
                    message=f"Unusual {direction} detected on {date}",
                    severity=InsightSeverity.HIGH,
                    metric="anomaly",
                    value=val,
                    recommendation=f"Investigate cause of {direction}",
                    icon="🔍"
                ))
                
        return insights
        
    def _detect_time_trends(self, time_series: List[Dict]) -> List[Insight]:
        """Detect trends in time series."""
        insights = []
        
        if len(time_series) < 3:
            return insights
            
        values = [item.get('value', item.get('revenue', 0)) for item in time_series]
        
        # Simple trend detection
        first_half = np.mean(values[:len(values)//2])
        second_half = np.mean(values[len(values)//2:])
        
        change = ((second_half - first_half) / first_half * 100) if first_half else 0
        
        if change > 10:
            insights.append(Insight(
                type=InsightType.TREND,
                message=f"Accelerating growth trend detected (+{change:.1f}%)",
                severity=InsightSeverity.MEDIUM,
                metric="trend",
                change_pct=change,
                icon="📈"
            ))
        elif change < -10:
            insights.append(Insight(
                type=InsightType.TREND,
                message=f"Declining trend detected ({change:.1f}%)",
                severity=InsightSeverity.HIGH,
                metric="trend",
                change_pct=change,
                recommendation="Address root causes of decline",
                icon="📉"
            ))
            
        return insights
        
    def _analyze_risks(
        self,
        churn_rate: float,
        profit_margin: float,
        revenue: float,
        revenue_previous: float
    ) -> List[Insight]:
        """Identify business risks."""
        insights = []
        
        # Churn risk
        if churn_rate > 0.15:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"High churn rate: {churn_rate*100:.1f}%",
                severity=InsightSeverity.CRITICAL,
                metric="churn",
                value=churn_rate * 100,
                recommendation="Implement immediate retention initiatives",
                icon="🚨"
            ))
        elif churn_rate > 0.08:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Elevated churn rate: {churn_rate*100:.1f}%",
                severity=InsightSeverity.HIGH,
                metric="churn",
                value=churn_rate * 100,
                recommendation="Review customer satisfaction and support",
                icon="⚠️"
            ))
            
        # Margin risk
        if profit_margin > 0 and profit_margin < 0.1:
            insights.append(Insight(
                type=InsightType.RISK,
                message=f"Low profit margin: {profit_margin*100:.1f}%",
                severity=InsightSeverity.HIGH,
                metric="margin",
                value=profit_margin * 100,
                recommendation="Optimize costs or adjust pricing",
                icon="⚠️"
            ))
            
        return insights
        
    def _identify_opportunities(
        self,
        revenue: float,
        customers: int,
        orders: int,
        products: Optional[List[Dict]],
        margin: float
    ) -> List[Insight]:
        """Identify growth opportunities."""
        insights = []
        
        # Cross-sell opportunity
        if customers and orders:
            orders_per_customer = orders / customers
            if orders_per_customer < 2:
                insights.append(Insight(
                    type=InsightType.OPPORTUNITY,
                    message=f"Cross-sell opportunity: {orders_per_customer:.1f} orders/customer",
                    severity=InsightSeverity.MEDIUM,
                    metric="orders_per_customer",
                    value=orders_per_customer,
                    recommendation="Implement cross-sell campaigns to increase order frequency",
                    icon="💡"
                ))
                
        # Upsell opportunity
        if revenue and customers:
            avg_value = revenue / customers
            insights.append(Insight(
                type=InsightType.OPPORTUNITY,
                message=f"Current customer value: ${avg_value:,.0f} - potential for upselling",
                severity=InsightSeverity.LOW,
                metric="customer_value",
                value=avg_value,
                recommendation="Target high-value customers with premium offerings",
                icon="💎"
            ))
            
        # Margin improvement opportunity
        if margin and margin < 0.3:
            potential = revenue * 0.05  # 5% margin improvement
            insights.append(Insight(
                type=InsightType.OPPORTUNITY,
                message=f"Margin improvement could add ${potential:,.0f} to profit",
                severity=InsightSeverity.MEDIUM,
                metric="margin_opportunity",
                value=potential,
                recommendation="Review cost structure and pricing strategy",
                icon="💰"
            ))
            
        return insights
        
    def _calculate_risk_score(self, insights: List[Insight]) -> float:
        """Calculate overall risk score (0-100)."""
        risk_insights = [i for i in insights if i.type == InsightType.RISK]
        
        if not risk_insights:
            return 10  # Low baseline risk
            
        score = 0
        for insight in risk_insights:
            if insight.severity == InsightSeverity.CRITICAL:
                score += 30
            elif insight.severity == InsightSeverity.HIGH:
                score += 20
            elif insight.severity == InsightSeverity.MEDIUM:
                score += 10
            else:
                score += 5
                
        return min(100, score)
        
    def _calculate_opportunity_score(self, insights: List[Insight]) -> float:
        """Calculate opportunity score (0-100)."""
        opp_insights = [i for i in insights if i.type == InsightType.OPPORTUNITY]
        
        base_score = len(opp_insights) * 15
        return min(100, base_score + 20)  # Base opportunity exists
        
    def _calculate_health_score(
        self,
        insights: List[Insight],
        risk_score: float,
        opp_score: float
    ) -> float:
        """Calculate overall business health score."""
        # Start at 70
        health = 70
        
        # Adjust for risks
        health -= risk_score * 0.3
        
        # Boost for opportunities
        health += opp_score * 0.1
        
        # Boost for positive trends
        positive_trends = sum(1 for i in insights 
                            if i.type == InsightType.TREND 
                            and i.change_pct and i.change_pct > 0)
        health += positive_trends * 5
        
        return max(0, min(100, health))
        
    def _generate_summary(
        self,
        insights: List[Insight],
        risk_score: float,
        opp_score: float
    ) -> str:
        """Generate executive summary."""
        risk_count = sum(1 for i in insights if i.type == InsightType.RISK)
        opp_count = sum(1 for i in insights if i.type == InsightType.OPPORTUNITY)
        trend_count = sum(1 for i in insights if i.type == InsightType.TREND)
        
        parts = []
        
        if risk_score > 50:
            parts.append(f"⚠️ {risk_count} risks need attention")
        elif risk_count > 0:
            parts.append(f"ℹ️ {risk_count} risk(s) identified")
            
        if opp_count > 0:
            parts.append(f"💡 {opp_count} growth opportunities found")
            
        if trend_count > 0:
            parts.append(f"📈 {trend_count} trend insights detected")
            
        return " | ".join(parts) if parts else "Analysis complete - no major findings"
        
    def _find_top_priority(self, insights: List[Insight]) -> str:
        """Find the highest priority insight."""
        # Critical risks first
        critical = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
        if critical:
            return critical[0].message
            
        # High severity next
        high = [i for i in insights if i.severity == InsightSeverity.HIGH]
        if high:
            return high[0].message
            
        # Opportunities
        opps = [i for i in insights if i.type == InsightType.OPPORTUNITY]
        if opps:
            return opps[0].message
            
        return "No immediate priorities"


def generate_insights(
    revenue: float = 0,
    revenue_previous: float = 0,
    customers: int = 0,
    orders: int = 0,
    churn_rate: float = 0.05,
    profit_margin: float = 0.2,
    time_series: Optional[List[Dict]] = None,
    top_products: Optional[List[Dict]] = None,
    top_customers: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate insights.
    
    Returns:
        Dict with all insights and scores
    """
    engine = InsightEngine()
    result = engine.analyze(
        revenue=revenue,
        revenue_previous=revenue_previous,
        customers=customers,
        customers_previous=int(customers * 0.95),  # Assume 5% growth if not provided
        orders=orders,
        orders_previous=int(orders * 0.9),
        top_products=top_products,
        top_customers=top_customers,
        time_series=time_series,
        churn_rate=churn_rate,
        profit_margin=profit_margin
    )
    
    return {
        "success": True,
        "insights": [
            {
                "type": i.type.value,
                "message": i.message,
                "severity": i.severity.value,
                "metric": i.metric,
                "value": i.value,
                "change_pct": i.change_pct,
                "recommendation": i.recommendation,
                "icon": i.icon
            }
            for i in result.insights
        ],
        "summary": result.summary,
        "risk_score": result.risk_score,
        "opportunity_score": result.opportunity_score,
        "health_score": result.health_score,
        "top_priority": result.top_priority
    }


# Quick test
if __name__ == "__main__":
    result = generate_insights(
        revenue=500000,
        revenue_previous=450000,
        customers=250,
        orders=1200,
        churn_rate=0.12,
        profit_margin=0.18,
        top_products=[
            {"name": "AI Starter Kit", "revenue": 150000},
            {"name": "Pro Pack", "revenue": 100000},
            {"name": "Enterprise", "revenue": 80000}
        ],
        top_customers=[
            {"name": "Acme Corp", "revenue": 120000},
            {"name": "TechStart", "revenue": 80000},
            {"name": "DataCo", "revenue": 60000}
        ]
    )
    
    print("Insight Analysis:")
    print(f"Summary: {result['summary']}")
    print(f"Health Score: {result['health_score']:.0f}/100")
    print(f"Risk Score: {result['risk_score']:.0f}/100")
    print(f"\nTop Priority: {result['top_priority']}")
    print(f"\nInsights ({len(result['insights'])}):")
    for i in result['insights'][:5]:
        print(f"  {i['icon']} [{i['type']}] {i['message']}")
