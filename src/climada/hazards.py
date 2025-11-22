"""
CLIMADA hazard data structures and loaders.
Integrates wildfire, flood, and sea level rise impacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import pandas as pd


@dataclass
class CLIMADAHazardData:
    """
    CLIMADA-derived physical hazard impacts.

    All rates and factors are annual values.

    Attributes:
        wildfire_outage_rate: Annual forced outage rate from wildfires (0-1)
        flood_outage_rate: Annual forced outage rate from floods (0-1)
        slr_capacity_derate: Capacity derating from sea level rise (0-1)
        compound_multiplier: Amplification factor for concurrent hazards (≥1.0)
        fwi_index: Fire Weather Index (CLIMADA metric)
        flood_return_period: Return period of design flood (years)
        slr_meters: Sea level rise above baseline (meters)
        data_source: Source of hazard data
        notes: Additional metadata
    """
    wildfire_outage_rate: float
    flood_outage_rate: float
    slr_capacity_derate: float
    compound_multiplier: float = 1.0
    fwi_index: float = 0.0
    flood_return_period: float = 100.0
    slr_meters: float = 0.0
    data_source: str = ""
    notes: str = ""

    @property
    def total_outage_rate(self) -> float:
        """
        Combined annual outage rate from all hazards.

        Outages are additive (wildfire OR flood causes shutdown).
        Compound multiplier accounts for hazard interactions.
        """
        base_outage = self.wildfire_outage_rate + self.flood_outage_rate
        return min(1.0, base_outage * self.compound_multiplier)

    @property
    def total_capacity_derate(self) -> float:
        """
        Total capacity derating from long-term hazards (primarily SLR).

        Derating is multiplicative (reduces effective capacity).
        """
        return min(1.0, self.slr_capacity_derate * self.compound_multiplier)

    @property
    def effective_capacity_factor_multiplier(self) -> float:
        """
        Combined effect on capacity factor.

        CF_effective = CF_baseline × (1 - derate) × (1 - outage_rate)
        """
        return (1 - self.total_capacity_derate) * (1 - self.total_outage_rate)

    def to_dict(self) -> Dict[str, float]:
        """Export as dictionary for CSV/analysis."""
        return {
            'wildfire_outage_rate': self.wildfire_outage_rate,
            'flood_outage_rate': self.flood_outage_rate,
            'slr_capacity_derate': self.slr_capacity_derate,
            'compound_multiplier': self.compound_multiplier,
            'total_outage_rate': self.total_outage_rate,
            'total_capacity_derate': self.total_capacity_derate,
            'effective_cf_multiplier': self.effective_capacity_factor_multiplier,
            'fwi_index': self.fwi_index,
            'flood_return_period': self.flood_return_period,
            'slr_meters': self.slr_meters,
        }


def load_climada_hazards(file_path: str, scenario_name: str = None) -> Dict[str, CLIMADAHazardData]:
    """
    Load CLIMADA hazard data from CSV file.

    Args:
        file_path: Path to climada_hazards.csv
        scenario_name: Optional filter for specific scenario

    Returns:
        Dict of scenario name -> CLIMADAHazardData
    """
    df = pd.read_csv(file_path)

    if scenario_name:
        df = df[df['scenario'] == scenario_name]

    hazards = {}

    for _, row in df.iterrows():
        scenario = row['scenario']
        hazards[scenario] = CLIMADAHazardData(
            wildfire_outage_rate=float(row['wildfire_outage_rate']),
            flood_outage_rate=float(row['flood_outage_rate']),
            slr_capacity_derate=float(row['slr_capacity_derate']),
            compound_multiplier=float(row['compound_multiplier']),
            fwi_index=float(row.get('fwi_index', 0)),
            flood_return_period=float(row.get('flood_return_period_yr', 100)),
            slr_meters=float(row.get('slr_meters', 0)),
            data_source=str(row.get('data_source', '')),
            notes=str(row.get('notes', ''))
        )

    return hazards


def calculate_compound_risk(
    wildfire_outage: float,
    flood_outage: float,
    slr_derate: float,
    interaction_factor: float = 1.2
) -> CLIMADAHazardData:
    """
    Calculate compound hazard risk with interaction effects.

    Compound events amplify impacts beyond simple addition:
    - Drought + wildfire → reduced firefighting capability
    - SLR + storm surge → amplified flood risk
    - Heat + SLR → combined cooling system stress

    Args:
        wildfire_outage: Base wildfire outage rate
        flood_outage: Base flood outage rate
        slr_derate: Base SLR capacity derating
        interaction_factor: Amplification from hazard interactions (default 1.2 = 20% increase)

    Returns:
        CLIMADAHazardData with compound effects
    """
    return CLIMADAHazardData(
        wildfire_outage_rate=wildfire_outage,
        flood_outage_rate=flood_outage,
        slr_capacity_derate=slr_derate,
        compound_multiplier=interaction_factor,
        notes=f"Compound risk with {interaction_factor:.1%} interaction amplification"
    )


def interpolate_hazard_by_year(
    hazards: Dict[str, CLIMADAHazardData],
    target_year: int,
    scenario_prefix: str = "high_physical"
) -> CLIMADAHazardData:
    """
    Interpolate CLIMADA hazard data for a specific year.

    Useful when hazard data is available for discrete years (2030, 2040, 2050)
    but analysis requires annual projections.

    Args:
        hazards: Dict of scenario -> hazard data (must include year in key)
        target_year: Year to interpolate for
        scenario_prefix: Scenario type (e.g., "high_physical", "moderate_physical")

    Returns:
        Interpolated CLIMADAHazardData

    Example:
        >>> hazards = load_climada_hazards('data/climada_hazards.csv')
        >>> hazard_2035 = interpolate_hazard_by_year(hazards, 2035, "high_physical")
    """
    # Extract scenarios with matching prefix and parse years
    relevant_scenarios = {
        key: value for key, value in hazards.items()
        if key.startswith(scenario_prefix)
    }

    if not relevant_scenarios:
        raise ValueError(f"No scenarios found with prefix '{scenario_prefix}'")

    # Parse years from scenario names (e.g., "high_physical_2040" -> 2040)
    years_data = []
    for key, hazard in relevant_scenarios.items():
        try:
            year = int(key.split('_')[-1])
            years_data.append((year, hazard))
        except ValueError:
            continue  # Skip scenarios without year suffix

    if not years_data:
        # Return first available if no year parsing possible
        return list(relevant_scenarios.values())[0]

    years_data.sort(key=lambda x: x[0])
    years = [y for y, _ in years_data]
    hazards_list = [h for _, h in years_data]

    # If target year is outside range, return nearest endpoint
    if target_year <= years[0]:
        return hazards_list[0]
    if target_year >= years[-1]:
        return hazards_list[-1]

    # Find bounding years for interpolation
    for i in range(len(years) - 1):
        if years[i] <= target_year <= years[i + 1]:
            y0, y1 = years[i], years[i + 1]
            h0, h1 = hazards_list[i], hazards_list[i + 1]

            # Linear interpolation weight
            weight = (target_year - y0) / (y1 - y0)

            # Interpolate each component
            return CLIMADAHazardData(
                wildfire_outage_rate=h0.wildfire_outage_rate + weight * (h1.wildfire_outage_rate - h0.wildfire_outage_rate),
                flood_outage_rate=h0.flood_outage_rate + weight * (h1.flood_outage_rate - h0.flood_outage_rate),
                slr_capacity_derate=h0.slr_capacity_derate + weight * (h1.slr_capacity_derate - h0.slr_capacity_derate),
                compound_multiplier=h0.compound_multiplier + weight * (h1.compound_multiplier - h0.compound_multiplier),
                fwi_index=h0.fwi_index + weight * (h1.fwi_index - h0.fwi_index),
                flood_return_period=h0.flood_return_period + weight * (h1.flood_return_period - h0.flood_return_period),
                slr_meters=h0.slr_meters + weight * (h1.slr_meters - h0.slr_meters),
                data_source=f"Interpolated between {y0} and {y1}",
                notes=f"Linear interpolation for year {target_year}"
            )

    # Fallback (should not reach)
    return hazards_list[0]


def calculate_economic_impact(
    hazard: CLIMADAHazardData,
    capacity_mw: float,
    power_price: float,
    annual_fixed_costs: float = 0.0
) -> Dict[str, float]:
    """
    Calculate economic impact of CLIMADA hazards.

    Args:
        hazard: CLIMADA hazard data
        capacity_mw: Plant capacity (MW)
        power_price: Electricity price ($/MWh)
        annual_fixed_costs: Fixed O&M costs ($/year)

    Returns:
        Dict with revenue_loss, generation_loss, cost_per_mwh_increase
    """
    # Annual generation loss from outages
    outage_generation_loss = capacity_mw * 8760 * hazard.total_outage_rate
    outage_revenue_loss = outage_generation_loss * power_price

    # Annual generation loss from capacity derating
    derate_generation_loss = capacity_mw * 8760 * hazard.total_capacity_derate
    derate_revenue_loss = derate_generation_loss * power_price

    # Total impact
    total_generation_loss = outage_generation_loss + derate_generation_loss
    total_revenue_loss = outage_revenue_loss + derate_revenue_loss

    # Effective generation after hazards
    effective_generation = capacity_mw * 8760 * hazard.effective_capacity_factor_multiplier

    # Cost increase per MWh (fixed costs spread over less generation)
    cost_per_mwh_increase = 0.0
    if effective_generation > 0 and annual_fixed_costs > 0:
        baseline_generation = capacity_mw * 8760
        baseline_cost_per_mwh = annual_fixed_costs / baseline_generation
        hazard_cost_per_mwh = annual_fixed_costs / effective_generation
        cost_per_mwh_increase = hazard_cost_per_mwh - baseline_cost_per_mwh

    return {
        'annual_generation_loss_mwh': total_generation_loss,
        'annual_revenue_loss': total_revenue_loss,
        'outage_generation_loss_mwh': outage_generation_loss,
        'derate_generation_loss_mwh': derate_generation_loss,
        'effective_generation_mwh': effective_generation,
        'cost_per_mwh_increase': cost_per_mwh_increase,
        'capacity_factor_reduction_pct': (1 - hazard.effective_capacity_factor_multiplier) * 100
    }
