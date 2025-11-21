"""
Physical risk adjustments (wildfire, water stress, temperature).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from src.scenarios import PhysicalScenario


@dataclass
class PhysicalAdjustments:
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0  # Max capacity factor allowed by water (0.0-1.0)


def apply_physical(plant_params: Dict[str, Any], scenario: PhysicalScenario) -> PhysicalAdjustments:
    """
    Apply physical risk assumptions.
    Includes specific water constraint modeling.
    """
    base_outage = float(plant_params.get("base_outage_rate", 0.05))
    outage = max(0.0, base_outage + scenario.wildfire_outage_rate)
    
    # 1. General Derate (e.g. heat efficiency)
    derate = scenario.drought_derate
    eff_loss = scenario.cooling_temp_penalty
    
    # 2. Water Constraint (Hard Limit)
    # If water availability < required, we must derate capacity
    # Default to 100% availability if not specified
    water_availability = getattr(scenario, "water_availability_pct", 100.0) / 100.0
    
    # Simple linear constraint: If we have 80% water, we can only run at 80% load
    # (Assuming linear relationship between load and water use, which is roughly true for cooling)
    water_constrained_cap = min(1.0, water_availability)

    return PhysicalAdjustments(
        outage_rate=outage, 
        capacity_derate=derate, 
        efficiency_loss=eff_loss,
        water_constrained_capacity=water_constrained_cap
    )
