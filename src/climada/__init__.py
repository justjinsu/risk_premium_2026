"""
CLIMADA Physical Risk Model for Samcheok Blue Power Plant.

Integrates:
1. CLIMADA API data (Wildfire, TC, River Flood)
2. Temperature efficiency derate (literature)
3. Sea level rise projections (CMIP6)

Run:
    python -m src.climada.climada_physical_risk_model

Output:
    data/physical_risk_steps/physical_risk_output.csv

Version: 1.0 (December 2024)
"""

from .climada_physical_risk_model import (
    # Main functions
    run_full_analysis,
    calculate_physical_risk,
    calculate_temperature_impact,
    analyze_climada_hazards,
    # Data classes
    PhysicalRiskSummary,
    HazardResult,
    TemperatureResult,
    # Constants
    SAMCHEOK_LAT,
    SAMCHEOK_LON,
    KOREA_TEMP_PROJECTIONS_RCP85,
    WILDFIRE_CLIMATE_FACTORS,
    TC_CLIMATE_FACTORS,
    SLR_PROJECTIONS_M,
)

__all__ = [
    'run_full_analysis',
    'calculate_physical_risk',
    'calculate_temperature_impact',
    'analyze_climada_hazards',
    'PhysicalRiskSummary',
    'HazardResult',
    'TemperatureResult',
    'SAMCHEOK_LAT',
    'SAMCHEOK_LON',
    'KOREA_TEMP_PROJECTIONS_RCP85',
    'WILDFIRE_CLIMATE_FACTORS',
    'TC_CLIMATE_FACTORS',
    'SLR_PROJECTIONS_M',
]
