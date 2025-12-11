"""
CLIMADA Physical Risk Model for Samcheok Blue Power Plant.

Reads ALL inputs from CSV files:
- input/climada_data.csv: CLIMADA API outputs
- input/literature_data.csv: Verified literature values
- input/model_assumptions.csv: Modeling assumptions

Run:
    python -m src.climada.climada_physical_risk_model

Version: 2.0 (CSV-based pipeline)
"""

from .climada_physical_risk_model import (
    # Main functions
    run_full_analysis,
    calculate_physical_risk,
    calculate_temperature_impact,
    calculate_base_outage_rates,
    # Data loading
    load_climada_data,
    load_literature_data,
    load_assumptions,
    # Data classes
    PhysicalRiskSummary,
    HazardResult,
    TemperatureResult,
    # Constants
    SAMCHEOK_LAT,
    SAMCHEOK_LON,
)

__all__ = [
    'run_full_analysis',
    'calculate_physical_risk',
    'calculate_temperature_impact',
    'calculate_base_outage_rates',
    'load_climada_data',
    'load_literature_data',
    'load_assumptions',
    'PhysicalRiskSummary',
    'HazardResult',
    'TemperatureResult',
    'SAMCHEOK_LAT',
    'SAMCHEOK_LON',
]
