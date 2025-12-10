"""
Scenario definitions for transition and physical risks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .carbon_pricing import CarbonPricingScenario


@dataclass
class TransitionScenario:
    """
    Transition risk scenario combining dispatch constraints and carbon pricing.

    Attributes:
        name: Scenario identifier
        dispatch_priority_penalty: Percentage point reduction to capacity factor (0-1)
        retirement_years: Years until enforced retirement
        carbon_price_2025-2050: Legacy carbon price anchors (USD/tCO2)
        carbon_scenario_name: Name of linked CarbonPricingScenario (optional)
        _carbon_scenario: Cached CarbonPricingScenario object

    Carbon Pricing Priority:
        1. If _carbon_scenario is set, use its get_carbon_price() method
        2. Otherwise, interpolate from carbon_price_20XX anchors
    """
    name: str
    dispatch_priority_penalty: float  # percentage point reduction to capacity factor
    retirement_years: int             # years until enforced retirement
    carbon_price_2025: float          # $/tCO2e in 2025
    carbon_price_2030: float          # $/tCO2e in 2030
    carbon_price_2040: float          # $/tCO2e in 2040
    carbon_price_2050: float          # $/tCO2e in 2050
    carbon_scenario_name: Optional[str] = None  # Link to CarbonPricingScenario
    _carbon_scenario: Optional['CarbonPricingScenario'] = field(default=None, repr=False)

    def set_carbon_scenario(self, scenario: 'CarbonPricingScenario') -> None:
        """Set the carbon pricing scenario for detailed trajectory."""
        self._carbon_scenario = scenario

    def get_carbon_price(self, year: int) -> float:
        """
        Get carbon price for given year.

        Uses CarbonPricingScenario if available, otherwise interpolates
        from anchor points.
        """
        # Priority 1: Use detailed carbon scenario if available
        if self._carbon_scenario is not None:
            return self._carbon_scenario.get_carbon_price(year)

        # Priority 2: Interpolate from anchor points (legacy behavior)
        return self._interpolate_carbon_price(year)

    def _interpolate_carbon_price(self, year: int) -> float:
        """Legacy interpolation from 4 anchor points."""
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
            # Extrapolate beyond 2050 with last decade's growth rate
            if self.carbon_price_2040 > 0:
                annual_growth = (self.carbon_price_2050 / self.carbon_price_2040) ** 0.1 - 1
                years_beyond = year - 2050
                return self.carbon_price_2050 * (1 + annual_growth) ** years_beyond
            return self.carbon_price_2050

    def get_carbon_price_trajectory(self, start_year: int = 2024, end_year: int = 2050) -> dict:
        """Get full carbon price trajectory as dict."""
        return {year: self.get_carbon_price(year) for year in range(start_year, end_year + 1)}


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
