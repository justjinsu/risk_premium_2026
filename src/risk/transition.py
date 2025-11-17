"""
Transition risk adjustments (policy, dispatch, early retirement).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from src.scenarios import TransitionScenario


@dataclass
class TransitionAdjustments:
    capacity_factor: float
    operating_years: int


def apply_transition(plant_params: Dict[str, Any], scenario: TransitionScenario) -> TransitionAdjustments:
    """
    Apply transition assumptions to baseline plant parameters.
    Computes adjusted capacity factor and operating life.
    Note: Carbon price is accessed directly from scenario.get_carbon_price(year) in cash flow calculations.
    """
    baseline_cf = float(plant_params.get("capacity_factor", 0.5))
    adjusted_cf = max(0.0, baseline_cf - scenario.dispatch_priority_penalty)
    baseline_life = int(plant_params.get("operating_years", 40))
    adjusted_life = min(baseline_life, scenario.retirement_years)
    return TransitionAdjustments(
        capacity_factor=adjusted_cf,
        operating_years=adjusted_life,
    )
