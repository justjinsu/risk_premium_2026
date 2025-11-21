"""
Scenario definitions for transition and physical risks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TransitionScenario:
    name: str
    dispatch_priority_penalty: float  # percentage point reduction to capacity factor
    retirement_years: int             # years until enforced retirement
    carbon_price_2025: float          # $/tCO2e in 2025
    carbon_price_2030: float          # $/tCO2e in 2030
    carbon_price_2040: float          # $/tCO2e in 2040
    carbon_price_2050: float          # $/tCO2e in 2050

    def get_carbon_price(self, year: int) -> float:
        """Interpolate carbon price for given year."""
        if year <= 2025:
            return self.carbon_price_2025
        elif year <= 2030:
            t = (year - 2025) / 5
            return self.carbon_price_2025 + t * (self.carbon_price_2030 - self.carbon_price_2025)
        elif year <= 2040:
            t = (year - 2030) / 10
            return self.carbon_price_2030 + t * (self.carbon_price_2040 - self.carbon_price_2030)
        elif year <= 2050:
            t = (year - 2040) / 10
            return self.carbon_price_2040 + t * (self.carbon_price_2050 - self.carbon_price_2040)
        else:
            return self.carbon_price_2050


@dataclass
class PhysicalScenario:
    name: str
    wildfire_outage_rate: float       # annual outage probability
    drought_derate: float             # capacity derate percentage
    cooling_temp_penalty: float       # efficiency loss percentage
    water_availability_pct: float = 100.0  # % of normal water supply available


@dataclass
class ScenarioSet:
    baseline_years: int
    transition: Optional[TransitionScenario]
    physical: Optional[PhysicalScenario]
