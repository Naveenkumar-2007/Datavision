from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random

router = APIRouter()

class ScenarioVariable(BaseModel):
    name: str
    current_value: float
    min_value: float
    max_value: float
    step: float
    unit: str

class SimulationRequest(BaseModel):
    variables: Dict[str, float]

class SimulationResult(BaseModel):
    baseline_metrics: Dict[str, str]
    simulated_metrics: Dict[str, str]
    impact_percentage: Dict[str, float]
    chart_data: List[Dict[str, Any]]

def get_default_variables() -> List[ScenarioVariable]:
    return [
        ScenarioVariable(name="Marketing Budget", current_value=50000, min_value=10000, max_value=200000, step=5000, unit="$"),
        ScenarioVariable(name="Product Price", current_value=199, min_value=49, max_value=499, step=10, unit="$"),
        ScenarioVariable(name="Discount Rate", current_value=15, min_value=0, max_value=50, step=1, unit="%"),
        ScenarioVariable(name="Customer Churn Rate", current_value=3.5, min_value=0.5, max_value=15.0, step=0.1, unit="%")
    ]

@router.get("/simulator/variables", response_model=List[ScenarioVariable])
async def get_simulator_variables():
    """
    Returns the available adjustable variables for the What-If simulation.
    """
    return get_default_variables()

@router.post("/simulator/run", response_model=SimulationResult)
async def run_simulation(request: SimulationRequest):
    """
    Runs a simulation based on the provided adjusted variables and returns the impact.
    """
    variables = request.variables
    
    # Simple mock simulation logic based on variables
    marketing_budget = variables.get("Marketing Budget", 50000)
    product_price = variables.get("Product Price", 199)
    discount = variables.get("Discount Rate", 15)
    churn = variables.get("Customer Churn Rate", 3.5)
    
    # Baseline calculations
    base_revenue = 1500000
    base_profit = 350000
    base_cac = 120
    
    # Simulation calculations (mock logic)
    # Higher marketing -> higher revenue but higher CAC
    # Higher price -> higher revenue per user but might increase churn
    
    marketing_multiplier = (marketing_budget / 50000) 
    price_multiplier = (product_price / 199)
    discount_impact = 1 - (discount / 100)
    churn_impact = 1 - (churn / 100)
    
    sim_revenue = base_revenue * marketing_multiplier * price_multiplier * churn_impact
    sim_profit = sim_revenue * discount_impact - marketing_budget - 800000  # fixed costs
    sim_cac = base_cac * (marketing_multiplier ** 0.5)
    
    # Generate Chart Data (next 6 months forecast)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    chart_data = []
    
    current_base = base_revenue / 6
    current_sim = sim_revenue / 6
    
    for month in months:
        # Add some random walk noise
        noise_base = random.uniform(0.9, 1.1)
        noise_sim = random.uniform(0.9, 1.1)
        
        chart_data.append({
            "month": month,
            "Baseline Revenue": round(current_base * noise_base, 2),
            "Simulated Revenue": round(current_sim * noise_sim, 2)
        })
        
        # Trend
        current_base *= 1.02
        current_sim *= 1.05
    
    return SimulationResult(
        baseline_metrics={
            "Revenue": f"${base_revenue:,.0f}",
            "Net Profit": f"${base_profit:,.0f}",
            "CAC": f"${base_cac:,.0f}"
        },
        simulated_metrics={
            "Revenue": f"${sim_revenue:,.0f}",
            "Net Profit": f"${sim_profit:,.0f}",
            "CAC": f"${sim_cac:,.0f}"
        },
        impact_percentage={
            "Revenue": round(((sim_revenue - base_revenue) / base_revenue) * 100, 1),
            "Net Profit": round(((sim_profit - base_profit) / base_profit) * 100, 1),
            "CAC": round(((sim_cac - base_cac) / base_cac) * 100, 1)
        },
        chart_data=chart_data
    )
