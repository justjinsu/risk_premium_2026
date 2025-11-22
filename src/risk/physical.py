"""
Physical risk adjustments (wildfire, water stress, temperature).

Updated to integrate CLIMADA hazard data (wildfire, flood, sea level rise).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.scenarios import PhysicalScenario

# Conditional import for CLIMADA - allows backward compatibility
try:
    from src.climada import CLIMADAHazardData
    CLIMADA_AVAILABLE = True
except ImportError:
    CLIMADA_AVAILABLE = False
    CLIMADAHazardData = None


@dataclass
class PhysicalAdjustments:
    """
    Physical risk adjustments to plant operations.

    Attributes:
        outage_rate: Annual forced outage rate (0-1)
        capacity_derate: Capacity derating factor (0-1)
        efficiency_loss: Efficiency penalty (0-1)
        water_constrained_capacity: Max CF allowed by water (0-1)
        notes: Description of adjustments applied
    """
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0
    notes: str = ""


def apply_physical(
    plant_params: Dict[str, Any],
    scenario: PhysicalScenario,
    climada_hazard: Optional['CLIMADAHazardData'] = None
) -> PhysicalAdjustments:
    """
    Apply physical risk assumptions.

    Can use either traditional PhysicalScenario (simple parameters) or
    CLIMADA hazard data (spatially-explicit climate hazards).

    Args:
        plant_params: Plant design parameters
        scenario: Physical risk scenario (traditional)
        climada_hazard: Optional CLIMADA hazard data (overrides scenario if provided)

    Returns:
        PhysicalAdjustments with applied risk factors

    Priority order (if both provided):
        1. CLIMADA hazard data (most detailed)
        2. PhysicalScenario parameters (simple)
        3. Plant baseline parameters
    """
    # Use CLIMADA data if available
    if climada_hazard is not None and CLIMADA_AVAILABLE:
        return apply_climada_physical_risk(plant_params, climada_hazard)

    # Otherwise use traditional scenario-based approach
    base_outage = float(plant_params.get("base_outage_rate", 0.05))
    outage = max(0.0, base_outage + scenario.wildfire_outage_rate)

    # General derate (e.g., heat efficiency loss)
    derate = scenario.drought_derate
    eff_loss = scenario.cooling_temp_penalty

    # Water constraint (hard limit on capacity factor)
    # If water availability < required, capacity must be derated
    water_availability = getattr(scenario, "water_availability_pct", 100.0) / 100.0

    # Linear constraint: 80% water availability → max 80% capacity factor
    # (Assumes linear relationship between load and cooling water use)
    water_constrained_cap = min(1.0, water_availability)

    return PhysicalAdjustments(
        outage_rate=outage,
        capacity_derate=derate,
        efficiency_loss=eff_loss,
        water_constrained_capacity=water_constrained_cap,
        notes=f"Scenario-based: {scenario.name}"
    )


def apply_climada_physical_risk(
    plant_params: Dict[str, Any],
    climada_hazard: 'CLIMADAHazardData'
) -> PhysicalAdjustments:
    """
    Apply CLIMADA-based physical risk adjustments.

    CLIMADA provides spatially-explicit hazard modeling:
    - Wildfire: Fire Weather Index → transmission outages
    - Flood: Riverine + coastal flooding → equipment damage
    - Sea Level Rise: Cooling water intake disruption

    Args:
        plant_params: Plant design parameters
        climada_hazard: CLIMADA hazard data

    Returns:
        PhysicalAdjustments based on CLIMADA hazards
    """
    # CLIMADA outage rates (wildfire + flood)
    # These are already combined in climada_hazard.total_outage_rate
    outage_rate = climada_hazard.total_outage_rate

    # CLIMADA capacity derating (primarily from sea level rise)
    capacity_derate = climada_hazard.total_capacity_derate

    # Efficiency loss - can be added separately if heat wave data available
    # For now, included in capacity derate
    efficiency_loss = 0.0

    # Water constraint - CLIMADA SLR affects cooling water intake
    # If SLR exceeds design tolerance, cooling capacity is reduced
    # This is captured in capacity_derate, so water constraint remains 1.0
    # (Unless separate drought module is added to CLIMADA)
    water_constrained_capacity = 1.0

    notes = (
        f"CLIMADA-based: Wildfire {climada_hazard.wildfire_outage_rate:.2%}, "
        f"Flood {climada_hazard.flood_outage_rate:.2%}, "
        f"SLR {climada_hazard.slr_capacity_derate:.2%}, "
        f"Compound {climada_hazard.compound_multiplier:.2f}x | "
        f"{climada_hazard.data_source}"
    )

    return PhysicalAdjustments(
        outage_rate=outage_rate,
        capacity_derate=capacity_derate,
        efficiency_loss=efficiency_loss,
        water_constrained_capacity=water_constrained_capacity,
        notes=notes
    )


def get_physical_risk_scenario(level: str) -> PhysicalScenario:
    """
    Get physical risk scenario by severity level.

    Args:
        level: "Low", "Medium", "High", "Extreme"

    Returns:
        PhysicalScenario with appropriate water constraints
    """
    level = level.lower()
    
    if level == "low":
        return PhysicalScenario(
            name="Low Risk",
            wildfire_outage_rate=0.0,
            drought_derate=0.0,
            cooling_temp_penalty=0.0,
            water_availability_pct=100.0
        )
    elif level == "medium":
        return PhysicalScenario(
            name="Medium Risk",
            wildfire_outage_rate=0.01,
            drought_derate=0.02,
            cooling_temp_penalty=0.01,
            water_availability_pct=90.0
        )
    elif level == "high":
        return PhysicalScenario(
            name="High Risk",
            wildfire_outage_rate=0.03,
            drought_derate=0.05,
            cooling_temp_penalty=0.03,
            water_availability_pct=80.0
        )
    elif level == "extreme":
        return PhysicalScenario(
            name="Extreme Risk",
            wildfire_outage_rate=0.05,
            drought_derate=0.10,
            cooling_temp_penalty=0.05,
            water_availability_pct=60.0
        )
    else:
        # Default to Low
        return PhysicalScenario(
            name="Baseline (Low)",
            wildfire_outage_rate=0.0,
            drought_derate=0.0,
            cooling_temp_penalty=0.0,
            water_availability_pct=100.0
        )
