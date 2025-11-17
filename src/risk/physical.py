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


def apply_physical(plant_params: Dict[str, Any], scenario: PhysicalScenario) -> PhysicalAdjustments:
    """
    Apply physical risk assumptions.
    Placeholder linear logic; replace with Monte Carlo or hazard models as data arrives.
    """
    base_outage = float(plant_params.get("base_outage_rate", 0.05))
    outage = max(0.0, base_outage + scenario.wildfire_outage_rate)
    derate = scenario.drought_derate
    eff_loss = scenario.cooling_temp_penalty
    return PhysicalAdjustments(outage_rate=outage, capacity_derate=derate, efficiency_loss=eff_loss)
