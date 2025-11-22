"""
CLIMADA (Climate Adaptation) physical risk integration module.

This module provides functionality to incorporate CLIMADA hazard data
(wildfire, flood, sea level rise) into physical risk assessments.
"""
from .hazards import (
    CLIMADAHazardData,
    load_climada_hazards,
    calculate_compound_risk,
)

__all__ = [
    'CLIMADAHazardData',
    'load_climada_hazards',
    'calculate_compound_risk',
]
