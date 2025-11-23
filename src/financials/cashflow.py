"""
Cash-flow engine for baseline vs risk-adjusted scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np

from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.scenarios import TransitionScenario, MarketScenario
# Import locally to avoid circular import if possible, or refactor. 
# metrics.py imports cashflow.py, so importing metrics here causes circular import.
# We should move calculate_debt_service to a separate module or implement simple logic here.
# Let's implement simple debt logic here to avoid circular dependency.
import numpy_financial as npf


@dataclass
class CashFlowTimeSeries:
    """Time-series cash flow projections."""
    years: np.ndarray
    revenue: np.ndarray
    fuel_costs: np.ndarray
    variable_opex: np.ndarray
    fixed_opex: np.ndarray
    carbon_costs: np.ndarray
    outage_costs: np.ndarray
    total_costs: np.ndarray
    ebitda: np.ndarray
    depreciation: np.ndarray
    ebit: np.ndarray
    interest_expense: np.ndarray
    tax_expense: np.ndarray
    net_income: np.ndarray
    capex: np.ndarray
    free_cash_flow: np.ndarray
    capacity_factor: np.ndarray

    def to_dict(self) -> Dict[str, List[float]]:
        """Convert to dict for CSV export."""
        return {
            "year": self.years.tolist(),
            "revenue": self.revenue.tolist(),
            "fuel_costs": self.fuel_costs.tolist(),
            "variable_opex": self.variable_opex.tolist(),
            "fixed_opex": self.fixed_opex.tolist(),
            "carbon_costs": self.carbon_costs.tolist(),
            "outage_costs": self.outage_costs.tolist(),
            "total_costs": self.total_costs.tolist(),
            "ebitda": self.ebitda.tolist(),
            "depreciation": self.depreciation.tolist(),
            "ebit": self.ebit.tolist(),
            "interest_expense": self.interest_expense.tolist(),
            "tax_expense": self.tax_expense.tolist(),
            "net_income": self.net_income.tolist(),
            "capex": self.capex.tolist(),
            "free_cash_flow": self.free_cash_flow.tolist(),
            "capacity_factor": self.capacity_factor.tolist(),
        }


def compute_cashflows_timeseries(
    plant_params: Dict[str, Any],
    transition_scenario: TransitionScenario,
    transition_adj: TransitionAdjustments,
    physical_adj: PhysicalAdjustments,
    market_scenario: MarketScenario | None = None,
    start_year: int = 2025,
) -> CashFlowTimeSeries:
    """
    Compute annual cash flows over the plant's operating life.
    """
    # Extract plant parameters
    capacity_mw = float(plant_params.get("capacity_mw", 2000))
    price = float(plant_params.get("power_price_per_mwh", 80))
    heat_rate = float(plant_params.get("heat_rate_mmbtu_mwh", 9.5))
    fuel_price = float(plant_params.get("fuel_price_per_mmbtu", 3.2))
    fixed_opex_per_kw = float(plant_params.get("fixed_opex_per_kw_year", 42))
    variable_opex_per_mwh = float(plant_params.get("variable_opex_per_mwh", 4.5))
    emissions_rate = float(plant_params.get("emissions_tCO2_per_mwh", 0.95))
    
    # Financial params for concretization
    total_capex = float(plant_params.get("total_capex_million", 3200)) * 1e6
    useful_life = int(plant_params.get("useful_life", 30))
    tax_rate = float(plant_params.get("tax_rate", 0.24)) # Korean Corporate Tax ~24%
    debt_fraction = float(plant_params.get("debt_fraction", 0.70))
    debt_interest = float(plant_params.get("debt_interest_rate", 0.05))
    debt_tenor = int(plant_params.get("debt_tenor_years", 20))

    # Operating years
    n_years = transition_adj.operating_years
    years = np.arange(start_year, start_year + n_years)

    # Capacity factor adjusted for both transition and physical risks
    base_cf = transition_adj.capacity_factor
    
    # Apply Market Demand factor to Base CF if market scenario exists
    if market_scenario:
        # Demand growth affects utilization
        demand_factors = np.array([market_scenario.get_demand_factor(year, start_year) for year in years])
        # Assume 1:1 relationship between demand growth and CF for simplicity, capped at 1.0
        base_cf_series = np.minimum(1.0, base_cf * demand_factors)
    else:
        base_cf_series = np.full(n_years, base_cf)

    # Apply Physical Constraints (Derates + Water Constraints)
    # 1. Subtract derates (efficiency loss)
    cf_series = base_cf_series * (1 - physical_adj.capacity_derate)
    
    # 2. Apply Water Constraint (Hard Cap)
    # If water is constrained, we cannot exceed the water_constrained_capacity
    water_cap = getattr(physical_adj, "water_constrained_capacity", 1.0)
    cf_series = np.minimum(cf_series, water_cap)
    
    cf_series = np.maximum(cf_series, 0.0)

    # Annual generation
    annual_mwh = capacity_mw * 8760 * cf_series

    # Revenue
    # Apply Market Price if scenario exists
    if market_scenario:
        prices = np.array([market_scenario.get_power_price(year, start_year) for year in years])
    else:
        prices = np.full(n_years, price)
        
    revenue = annual_mwh * prices

    # Carbon price trajectory
    carbon_prices = np.array([transition_scenario.get_carbon_price(year) for year in years])

    # Costs
    fuel_costs = annual_mwh * heat_rate * fuel_price
    variable_opex = annual_mwh * variable_opex_per_mwh
    fixed_opex = np.full(n_years, capacity_mw * 1000 * fixed_opex_per_kw)
    carbon_costs = annual_mwh * emissions_rate * carbon_prices
    outage_costs = annual_mwh * physical_adj.outage_rate * price

    total_costs = fuel_costs + variable_opex + fixed_opex + carbon_costs + outage_costs

    # --- Financial Calculations ---

    # 1. EBITDA Calculation
    # EBITDA = Revenue - Total Costs (Fuel + O&M + Carbon + Outage)
    ebitda = revenue - total_costs

    # 2. Depreciation (Non-cash expense)
    # Straight-line depreciation over useful life
    # Assumption: Capex is fully depreciable, no salvage value
    annual_depreciation = total_capex / useful_life
    depreciation = np.full(n_years, annual_depreciation)
    
    # 3. EBIT (Earnings Before Interest and Taxes)
    # EBIT = EBITDA - Depreciation
    ebit = ebitda - depreciation
    
    # 4. Debt Service (Interest & Principal)
    # Calculate amortization schedule for the debt portion
    debt_amount = total_capex * debt_fraction
    interest_expense = np.zeros(n_years)
    balance = debt_amount
    
    if debt_interest > 0 and debt_tenor > 0:
        # Calculate level annual payment (Annuity)
        annual_ds = -npf.pmt(debt_interest, debt_tenor, debt_amount)
        
        for i in range(min(n_years, debt_tenor)):
            # Interest component
            interest = balance * debt_interest
            # Principal component
            principal = annual_ds - interest
            
            interest_expense[i] = interest
            
            # Update balance
            balance -= principal
            if balance < 0: balance = 0

    # 5. Tax Calculation
    # Corporate Tax is applied to Earnings Before Tax (EBT)
    # EBT = EBIT - Interest Expense
    # Tax Shield: Interest expense reduces taxable income
    taxable_income = ebit - interest_expense
    # Tax cannot be negative (no carry-forward modeled for simplicity)
    tax_expense = np.maximum(0.0, taxable_income * tax_rate)
    
    # 6. Net Income
    # Net Income = EBT - Tax
    net_income = ebit - interest_expense - tax_expense

    # 7. Free Cash Flow (FCFF - Free Cash Flow to Firm)
    # FCFF represents cash available to all capital providers (Debt + Equity)
    # Formula: FCFF = EBIT * (1 - Tax Rate) + Depreciation - Capex - Change in WC
    # Note: Interest tax shield is captured in WACC for NPV, so we use EBIT*(1-t)
    # However, for consistency with the previous model which might have used a different definition,
    # let's stick to the standard FCFF definition:
    # FCFF = NOPAT + Depreciation - Capex
    # NOPAT = EBIT * (1 - Tax Rate)
    nopat = ebit * (1 - tax_rate)
    
    # Capex (sustaining capex only, construction already completed)
    capex = np.zeros(n_years)
    
    fcf = nopat + depreciation - capex

    return CashFlowTimeSeries(
        years=years,
        revenue=revenue,
        fuel_costs=fuel_costs,
        variable_opex=variable_opex,
        fixed_opex=fixed_opex,
        carbon_costs=carbon_costs,
        outage_costs=outage_costs,
        total_costs=total_costs,
        ebitda=ebitda,
        depreciation=depreciation,
        ebit=ebit,
        interest_expense=interest_expense,
        tax_expense=tax_expense,
        net_income=net_income,
        capex=capex,
        free_cash_flow=fcf,
        capacity_factor=cf_series,
    )


# Keep old function for backward compatibility
@dataclass
class CashFlowResult:
    annual_revenue: float
    annual_costs: float
    ebitda: float
    free_cash_flow: float
    notes: str


def compute_cashflows(
    plant_params: Dict[str, Any],
    transition: TransitionAdjustments,
    physical: PhysicalAdjustments,
) -> CashFlowResult:
    """
    Legacy single-period calculator. Use compute_cashflows_timeseries instead.
    """
    capacity_mw = float(plant_params.get("capacity_mw", 2000))
    price = float(plant_params.get("power_price_per_mwh", 80))
    heat_rate = float(plant_params.get("heat_rate_mmbtu_mwh", 9.5))
    fuel_price = float(plant_params.get("fuel_price_per_mmbtu", 3.2))
    fixed_opex = float(plant_params.get("fixed_opex_per_kw_year", 42))
    variable_opex = float(plant_params.get("variable_opex_per_mwh", 4.5))
    cf = max(0.0, transition.capacity_factor * (1 - physical.capacity_derate))

    annual_mwh = capacity_mw * 8760 * cf
    fuel_cost = annual_mwh * heat_rate * fuel_price
    variable_costs = annual_mwh * variable_opex
    fixed_costs = capacity_mw * 1000 * fixed_opex
    carbon_costs = annual_mwh * 0.95 * 50  # placeholder carbon price
    outage_penalty = annual_mwh * physical.outage_rate * price

    revenue = annual_mwh * price
    costs = fuel_cost + variable_costs + fixed_costs + carbon_costs + outage_penalty
    ebitda = revenue - costs
    fcf = ebitda
    notes = "Legacy single-period; use compute_cashflows_timeseries instead."
    return CashFlowResult(
        annual_revenue=revenue,
        annual_costs=costs,
        ebitda=ebitda,
        free_cash_flow=fcf,
        notes=notes,
    )
