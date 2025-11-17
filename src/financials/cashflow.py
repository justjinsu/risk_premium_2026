"""
Cash-flow engine for baseline vs risk-adjusted scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np

from src.risk import TransitionAdjustments, PhysicalAdjustments
from src.scenarios import TransitionScenario


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
            "capex": self.capex.tolist(),
            "free_cash_flow": self.free_cash_flow.tolist(),
            "capacity_factor": self.capacity_factor.tolist(),
        }


def compute_cashflows_timeseries(
    plant_params: Dict[str, Any],
    transition_scenario: TransitionScenario,
    transition_adj: TransitionAdjustments,
    physical_adj: PhysicalAdjustments,
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

    # Operating years
    n_years = transition_adj.operating_years
    years = np.arange(start_year, start_year + n_years)

    # Capacity factor adjusted for both transition and physical risks
    base_cf = transition_adj.capacity_factor
    cf_series = np.full(n_years, base_cf * (1 - physical_adj.capacity_derate))
    cf_series = np.maximum(cf_series, 0.0)

    # Annual generation
    annual_mwh = capacity_mw * 8760 * cf_series

    # Revenue
    revenue = annual_mwh * price

    # Carbon price trajectory
    carbon_prices = np.array([transition_scenario.get_carbon_price(year) for year in years])

    # Costs
    fuel_costs = annual_mwh * heat_rate * fuel_price
    variable_opex = annual_mwh * variable_opex_per_mwh
    fixed_opex = np.full(n_years, capacity_mw * 1000 * fixed_opex_per_kw)
    carbon_costs = annual_mwh * emissions_rate * carbon_prices
    outage_costs = annual_mwh * physical_adj.outage_rate * price

    total_costs = fuel_costs + variable_opex + fixed_opex + carbon_costs + outage_costs

    # EBITDA
    ebitda = revenue - total_costs

    # Capex (sustaining capex only, construction already completed)
    capex = np.zeros(n_years)

    # Free cash flow
    fcf = ebitda - capex

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
