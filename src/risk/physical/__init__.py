"""
Physical Risk Module Orchestrator

Integrates:
1. Hazard (Scenario data)
2. Exposure (Asset data)
3. Vulnerability (Damage functions)
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

# Export new submodules
from .hazard import HazardLoader, HazardData
from .exposure import ExposureMapper, AssetExposure
from .vulnerability import VulnerabilityModel, PhysicalImpact

# Legacy support for existing references
@dataclass
class PhysicalAdjustments:
    outage_rate: float
    capacity_derate: float
    efficiency_loss: float
    water_constrained_capacity: float = 1.0
    notes: str = ""

@dataclass
class YearlyPhysicalAdjustments:
    years: np.ndarray
    outage_rates: np.ndarray
    capacity_derates: np.ndarray
    efficiency_losses: np.ndarray
    water_constraints: np.ndarray
    scenario_name: str = ""

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        if year in self.years:
            idx = np.where(self.years == year)[0][0]
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[idx],
                capacity_derate=self.capacity_derates[idx],
                efficiency_loss=self.efficiency_losses[idx],
                water_constrained_capacity=self.water_constraints[idx],
                notes=f"{self.scenario_name} year {year}"
            )
        # Fallback/Interpolation logic could go here
        return PhysicalAdjustments(0, 0, 0, 1.0, "Out of range")

class PhysicalRiskEngine:
    def __init__(self):
        self.hazard_loader = HazardLoader()
        self.exposure_mapper = ExposureMapper()
        self.vulnerability_model = VulnerabilityModel()

    def calculate_adjustments(self, plant_params: Dict[str, Any], scenario_name: str, year: int = 2024) -> PhysicalAdjustments:
        # 1. Load Hazard
        hazard = self.hazard_loader.get_hazard(scenario_name, year)
        
        # 2. Map Exposure
        exposure = self.exposure_mapper.get_exposure(plant_params)
        
        # 3. Calculate Vulnerability/Impact
        impact = self.vulnerability_model.calculate_impact(hazard, exposure)
        
        return PhysicalAdjustments(
            outage_rate=impact.outage_rate,
            capacity_derate=impact.capacity_derate,
            efficiency_loss=impact.efficiency_loss,
            water_constrained_capacity=impact.water_constrained_capacity,
            notes=impact.description
        )

# Global instance for easier access
_ENGINE = PhysicalRiskEngine()

def get_physical_risk_engine() -> PhysicalRiskEngine:
    return _ENGINE

def apply_physical(
    plant_params: Dict[str, Any],
    scenario_name: str = "Baseline (Corrected)",
    year: int = 2024
) -> PhysicalAdjustments:
    """
    Apply physical risk assumptions using the new Hazard->Exposure->Vulnerability engine.
    """
    return _ENGINE.calculate_adjustments(plant_params, scenario_name, year)

def create_yearly_physical_adjustments(
    climada_hazards: Any, # Kept for signature compatibility but ignored
    scenario_prefix: str,
    start_year: int = 2024,
    end_year: int = 2060
) -> YearlyPhysicalAdjustments:
    """
    Create year-by-year physical adjustments using the new engine.
    """
    # Note: climada_hazards is ignored as we now load from CSV via HazardLoader
    # scenario_prefix maps to scenario_name
    
    # Simple mapping from old prefixes to new names if needed, or assume direct match
    scenario_map = {
        "baseline": "Baseline (Corrected)",
        "moderate_physical": "Moderate Physical Risk (Corrected)",
        "high_physical": "High Physical Risk (Corrected)",
        "extreme_physical": "Extreme Physical Risk (Corrected)"
    }
    name = scenario_map.get(scenario_prefix, scenario_prefix)
    
    years = np.arange(start_year, end_year + 1)
    n = len(years)
    
    outage_rates = np.zeros(n)
    capacity_derates = np.zeros(n)
    efficiency_losses = np.zeros(n)
    water_constraints = np.zeros(n)
    
    # We need plant params here for exposure, but the old signature didn't verify it.
    # We'll assume default plant params for now or update the signature if possible.
    # For backward partial compatibility, we default to generic plant params.
    default_plant = {"type": "Coal", "location": "Samcheok"}
    
    for i, year in enumerate(years):
        adj = _ENGINE.calculate_adjustments(default_plant, name, int(year))
        outage_rates[i] = adj.outage_rate
        capacity_derates[i] = adj.capacity_derate
        efficiency_losses[i] = adj.efficiency_loss
        water_constraints[i] = adj.water_constrained_capacity
        
    return YearlyPhysicalAdjustments(
        years=years,
        outage_rates=outage_rates,
        capacity_derates=capacity_derates,
        efficiency_losses=efficiency_losses,
        water_constraints=water_constraints,
        scenario_name=name
    )
