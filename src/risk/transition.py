"""
Transition risk adjustments (policy, dispatch, early retirement).

Updated to integrate Korea National Power Supply Plan (전력수급기본계획) dispatch trajectories.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.scenarios import TransitionScenario

# Conditional import for Korea Power Plan - allows backward compatibility
try:
    from src.scenarios.korea_power_plan import KoreaPowerPlanScenario
    KOREA_POWER_PLAN_AVAILABLE = True
except ImportError:
    KOREA_POWER_PLAN_AVAILABLE = False
    KoreaPowerPlanScenario = None


@dataclass
class TransitionAdjustments:
    """
    Transition risk adjustments to plant operations.

    Attributes:
        capacity_factor: Adjusted capacity factor after policy constraints (0-1)
        operating_years: Adjusted operating lifetime (years)
        notes: Description of adjustments applied
    """
    capacity_factor: float
    operating_years: int
    notes: str = ""


def apply_transition(
    plant_params: Dict[str, Any],
    scenario: TransitionScenario,
    korea_plan_scenario: Optional['KoreaPowerPlanScenario'] = None,
    current_year: Optional[int] = None
) -> TransitionAdjustments:
    """
    Apply transition assumptions to baseline plant parameters.

    Can use either generic TransitionScenario (simple dispatch penalty) or
    Korea Power Plan trajectory (year-by-year dispatch reductions from 전력수급계획).

    Args:
        plant_params: Plant design parameters
        scenario: Generic transition risk scenario
        korea_plan_scenario: Optional Korea Power Plan scenario (overrides if provided)
        current_year: Year for Korea Power Plan trajectory lookup

    Returns:
        TransitionAdjustments with capacity factor and operating years

    Priority order (if both provided):
        1. Korea Power Plan trajectory (most accurate for Korean plants)
        2. TransitionScenario dispatch penalty (generic approach)

    Note:
        Carbon price is accessed directly from scenario.get_carbon_price(year)
        in cash flow calculations, not stored in TransitionAdjustments.
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.5))
    baseline_life = int(plant_params.get("operating_years", 40))

    # Use Korea Power Plan trajectory if available
    if korea_plan_scenario is not None and KOREA_POWER_PLAN_AVAILABLE:
        if current_year is not None:
            # Year-specific capacity factor from power plan
            adjusted_cf = korea_plan_scenario.get_capacity_factor(current_year, baseline_cf)
        else:
            # Use average over lifetime if no specific year provided
            start_year = plant_params.get("cod_year", 2024)
            end_year = start_year + baseline_life
            total_cf = sum(
                korea_plan_scenario.get_capacity_factor(year, baseline_cf)
                for year in range(start_year, end_year)
            )
            adjusted_cf = total_cf / baseline_life

        # Operating years from power plan early retirement
        adjusted_life = korea_plan_scenario.get_operating_years(
            plant_params.get("cod_year", 2024),
            baseline_life
        )

        notes = f"Korea Power Plan: {korea_plan_scenario.name} | {korea_plan_scenario.policy_reference}"

    else:
        # Traditional approach: simple dispatch penalty
        adjusted_cf = max(0.0, baseline_cf - scenario.dispatch_priority_penalty)
        adjusted_life = min(baseline_life, scenario.retirement_years)
        notes = f"Generic transition: {scenario.name} | penalty={scenario.dispatch_priority_penalty:.1%}"

    return TransitionAdjustments(
        capacity_factor=adjusted_cf,
        operating_years=adjusted_life,
        notes=notes
    )


def apply_korea_power_plan_trajectory(
    plant_params: Dict[str, Any],
    korea_plan_scenario: 'KoreaPowerPlanScenario',
    start_year: int = 2024,
    end_year: int = 2050
) -> Dict[int, float]:
    """
    Generate year-by-year capacity factor trajectory from Korea Power Plan.

    This function returns annual capacity factors for use in time-series
    cash flow modeling, directly from 전력수급기본계획 data.

    Args:
        plant_params: Plant design parameters
        korea_plan_scenario: Korea Power Plan scenario
        start_year: Analysis start year
        end_year: Analysis end year

    Returns:
        Dict mapping year -> capacity factor

    Example:
        >>> from src.scenarios.korea_power_plan import load_korea_power_plan_scenarios
        >>> scenarios = load_korea_power_plan_scenarios('data/raw/korea_power_plan.csv')
        >>> plan = scenarios['official_10th_plan']
        >>> cf_trajectory = apply_korea_power_plan_trajectory(plant_params, plan, 2024, 2050)
        >>> print(cf_trajectory[2030])  # Capacity factor in 2030
        0.45
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.5))

    trajectory = {}
    for year in range(start_year, end_year + 1):
        trajectory[year] = korea_plan_scenario.get_capacity_factor(year, baseline_cf)

    return trajectory
