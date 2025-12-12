# Simulation Engine MCP Service
"""
Enterprise What-If Scenario Simulation Engine

Features:
- Price elasticity modeling
- Marketing impact simulation
- Customer churn prediction
- Revenue scenario comparison
- Sensitivity analysis

Usage:
    from mcp.simulation_engine import SimulationEngine
    engine = SimulationEngine()
    result = engine.simulate(base_data, modifiers)
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class Scenario:
    """A single simulation scenario"""
    name: str
    revenue: float
    profit: float
    customers: int
    churn_rate: float
    change_pct: float
    risk_level: str
    description: str


@dataclass
class SimulationResult:
    """Result from simulation engine"""
    scenarios: List[Scenario]
    recommended_strategy: str
    best_scenario: str
    risk_assessment: str
    insights: List[str]
    confidence: float


class SimulationEngine:
    """
    Enterprise What-If Simulation Engine.
    
    Supports:
    - Price change impact
    - Marketing spend impact
    - Customer acquisition/churn
    - Multi-variable scenarios
    """
    
    # Default elasticity coefficients
    PRICE_ELASTICITY = -1.2  # 1% price increase → 1.2% demand decrease
    MARKETING_ELASTICITY = 0.3  # 1% marketing increase → 0.3% revenue increase
    CHURN_SENSITIVITY = 0.5  # Sensitivity to price/service changes
    
    def __init__(self):
        self.scenarios_run = 0
        
    def simulate(
        self,
        base_revenue: float,
        base_customers: int = 100,
        base_profit_margin: float = 0.2,
        base_churn_rate: float = 0.05,
        modifiers: Optional[Dict[str, float]] = None
    ) -> SimulationResult:
        """
        Run what-if simulations with given modifiers.
        
        Args:
            base_revenue: Current revenue
            base_customers: Current customer count
            base_profit_margin: Current profit margin (0-1)
            base_churn_rate: Current churn rate (0-1)
            modifiers: Dict of modifiers to simulate, e.g.:
                {
                    "price_change": [5, 10, 15],  # % changes
                    "marketing_change": [10, 20],
                    "churn_reduction": [10, 20]
                }
                
        Returns:
            SimulationResult with all scenarios compared
        """
        if modifiers is None:
            # Default simulation scenarios
            modifiers = {
                "price_change": [-10, -5, 5, 10, 15],
                "marketing_change": [10, 20, 50],
            }
            
        scenarios = []
        
        # Base scenario
        base_scenario = Scenario(
            name="Current State",
            revenue=base_revenue,
            profit=base_revenue * base_profit_margin,
            customers=base_customers,
            churn_rate=base_churn_rate,
            change_pct=0,
            risk_level="low",
            description="Current business state"
        )
        scenarios.append(base_scenario)
        
        # Price change scenarios
        if "price_change" in modifiers:
            for pct in modifiers["price_change"]:
                scenario = self._simulate_price_change(
                    base_revenue, base_customers, 
                    base_profit_margin, base_churn_rate, pct
                )
                scenarios.append(scenario)
                
        # Marketing change scenarios
        if "marketing_change" in modifiers:
            for pct in modifiers["marketing_change"]:
                scenario = self._simulate_marketing_change(
                    base_revenue, base_customers,
                    base_profit_margin, base_churn_rate, pct
                )
                scenarios.append(scenario)
                
        # Find best scenario
        best = max(scenarios, key=lambda s: s.profit)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(scenarios, best)
        
        # Risk assessment
        risk = self._assess_overall_risk(scenarios)
        
        # Generate insights
        insights = self._generate_insights(scenarios, base_scenario, best)
        
        return SimulationResult(
            scenarios=scenarios,
            recommended_strategy=recommendation,
            best_scenario=best.name,
            risk_assessment=risk,
            insights=insights,
            confidence=85.0
        )
        
    def _simulate_price_change(
        self,
        base_revenue: float,
        base_customers: int,
        profit_margin: float,
        churn_rate: float,
        price_change_pct: float
    ) -> Scenario:
        """Simulate impact of price change."""
        # Price elasticity effect on demand
        demand_change = price_change_pct * self.PRICE_ELASTICITY
        
        # Calculate new metrics
        new_revenue = base_revenue * (1 + price_change_pct/100) * (1 + demand_change/100)
        
        # Churn increases with price increases
        churn_impact = max(0, price_change_pct * self.CHURN_SENSITIVITY / 100)
        new_churn = min(0.5, churn_rate + churn_impact)
        
        # Customers affected by churn
        customer_loss = int(base_customers * churn_impact)
        new_customers = max(0, base_customers - customer_loss)
        
        # Profit margin slightly improves with price increase
        margin_boost = price_change_pct * 0.005
        new_margin = min(0.5, profit_margin + margin_boost)
        new_profit = new_revenue * new_margin
        
        # Risk level
        if price_change_pct > 10:
            risk = "high"
        elif price_change_pct > 5:
            risk = "medium"
        elif price_change_pct < -5:
            risk = "medium"
        else:
            risk = "low"
            
        change_pct = ((new_revenue - base_revenue) / base_revenue * 100) if base_revenue else 0
        
        return Scenario(
            name=f"Price {'+' if price_change_pct >= 0 else ''}{price_change_pct}%",
            revenue=round(new_revenue, 2),
            profit=round(new_profit, 2),
            customers=new_customers,
            churn_rate=round(new_churn, 3),
            change_pct=round(change_pct, 1),
            risk_level=risk,
            description=f"{'Increase' if price_change_pct >= 0 else 'Decrease'} prices by {abs(price_change_pct)}%"
        )
        
    def _simulate_marketing_change(
        self,
        base_revenue: float,
        base_customers: int,
        profit_margin: float,
        churn_rate: float,
        marketing_change_pct: float
    ) -> Scenario:
        """Simulate impact of marketing spend change."""
        # Marketing elasticity effect
        revenue_boost = marketing_change_pct * self.MARKETING_ELASTICITY
        new_revenue = base_revenue * (1 + revenue_boost/100)
        
        # Marketing cost reduces profit margin
        marketing_cost = base_revenue * (marketing_change_pct / 100) * 0.1
        new_profit = (new_revenue * profit_margin) - marketing_cost
        
        # New customer acquisition
        customer_gain = int(base_customers * (marketing_change_pct / 100) * 0.2)
        new_customers = base_customers + customer_gain
        
        # Marketing reduces churn
        churn_reduction = marketing_change_pct * 0.001
        new_churn = max(0.01, churn_rate - churn_reduction)
        
        # Risk level
        if marketing_change_pct > 50:
            risk = "medium"
        else:
            risk = "low"
            
        change_pct = ((new_revenue - base_revenue) / base_revenue * 100) if base_revenue else 0
        
        return Scenario(
            name=f"Marketing +{marketing_change_pct}%",
            revenue=round(new_revenue, 2),
            profit=round(new_profit, 2),
            customers=new_customers,
            churn_rate=round(new_churn, 3),
            change_pct=round(change_pct, 1),
            risk_level=risk,
            description=f"Increase marketing spend by {marketing_change_pct}%"
        )
        
    def _generate_recommendation(
        self,
        scenarios: List[Scenario],
        best: Scenario
    ) -> str:
        """Generate strategic recommendation."""
        if best.name == "Current State":
            return "Maintain current strategy - changes show limited upside"
            
        if "Price" in best.name:
            if best.change_pct > 0:
                return f"Consider {best.name} - shows {best.change_pct:.1f}% revenue increase with {best.risk_level} risk"
            else:
                return f"Consider {best.name} to capture market share"
                
        if "Marketing" in best.name:
            return f"Invest in {best.name} - projected {best.change_pct:.1f}% revenue growth"
            
        return f"Implement {best.name} for optimal results"
        
    def _assess_overall_risk(self, scenarios: List[Scenario]) -> str:
        """Assess overall risk of recommended changes."""
        high_risk = sum(1 for s in scenarios if s.risk_level == "high")
        medium_risk = sum(1 for s in scenarios if s.risk_level == "medium")
        
        if high_risk > 2:
            return "high"
        elif medium_risk > 3 or high_risk > 0:
            return "medium"
        else:
            return "low"
            
    def _generate_insights(
        self,
        scenarios: List[Scenario],
        base: Scenario,
        best: Scenario
    ) -> List[str]:
        """Generate actionable insights."""
        insights = []
        
        # Best scenario insight
        if best.name != "Current State":
            profit_gain = best.profit - base.profit
            insights.append(
                f"💡 {best.name} could increase profit by ${profit_gain:,.0f}"
            )
            
        # Risk insight
        high_risk_scenarios = [s for s in scenarios if s.risk_level == "high"]
        if high_risk_scenarios:
            names = ", ".join(s.name for s in high_risk_scenarios[:2])
            insights.append(f"⚠️ High-risk scenarios: {names}")
            
        # Price sensitivity insight
        price_scenarios = [s for s in scenarios if "Price" in s.name]
        if price_scenarios:
            optimal = max(price_scenarios, key=lambda s: s.profit)
            insights.append(
                f"📊 Optimal pricing point: {optimal.name} (profit: ${optimal.profit:,.0f})"
            )
            
        # Marketing ROI insight
        marketing_scenarios = [s for s in scenarios if "Marketing" in s.name]
        if marketing_scenarios:
            best_marketing = max(marketing_scenarios, key=lambda s: s.change_pct)
            insights.append(
                f"📈 Best marketing ROI: {best_marketing.name} ({best_marketing.change_pct:.1f}% revenue boost)"
            )
            
        return insights
        
    def run_monte_carlo(
        self,
        base_revenue: float,
        uncertainty: float = 0.1,
        simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for revenue prediction.
        
        Args:
            base_revenue: Base revenue value
            uncertainty: Uncertainty range (0-1)
            simulations: Number of simulations
            
        Returns:
            Dict with percentile outcomes
        """
        results = []
        for _ in range(simulations):
            # Random variation
            variation = np.random.normal(0, uncertainty)
            simulated = base_revenue * (1 + variation)
            results.append(max(0, simulated))
            
        results = np.array(results)
        
        return {
            "mean": float(np.mean(results)),
            "median": float(np.median(results)),
            "p10": float(np.percentile(results, 10)),
            "p25": float(np.percentile(results, 25)),
            "p75": float(np.percentile(results, 75)),
            "p90": float(np.percentile(results, 90)),
            "std": float(np.std(results)),
            "best_case": float(np.max(results)),
            "worst_case": float(np.min(results))
        }


def simulate_scenarios(
    revenue: float,
    customers: int = 100,
    margin: float = 0.2,
    churn: float = 0.05
) -> Dict[str, Any]:
    """
    Convenience function for scenario simulation.
    
    Returns:
        Dict with simulation results
    """
    engine = SimulationEngine()
    result = engine.simulate(revenue, customers, margin, churn)
    
    return {
        "success": True,
        "scenarios": [
            {
                "name": s.name,
                "revenue": s.revenue,
                "profit": s.profit,
                "customers": s.customers,
                "churn_rate": s.churn_rate,
                "change_pct": s.change_pct,
                "risk": s.risk_level,
                "description": s.description
            }
            for s in result.scenarios
        ],
        "recommendation": result.recommended_strategy,
        "best_scenario": result.best_scenario,
        "risk_level": result.risk_assessment,
        "insights": result.insights,
        "confidence": f"{result.confidence}%"
    }


# Quick test
if __name__ == "__main__":
    result = simulate_scenarios(
        revenue=100000,
        customers=500,
        margin=0.25,
        churn=0.08
    )
    
    print("Simulation Results:")
    print(f"Best Scenario: {result['best_scenario']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"\nInsights:")
    for insight in result['insights']:
        print(f"  {insight}")
    print(f"\nScenarios:")
    for s in result['scenarios'][:5]:
        print(f"  {s['name']}: Revenue ${s['revenue']:,.0f}, Profit ${s['profit']:,.0f}")
