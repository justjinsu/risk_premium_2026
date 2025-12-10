"""
CLIMADA (Climate Adaptation) physical risk integration module.

This module provides functionality to incorporate CLIMADA hazard data
(wildfire, flood, sea level rise) into physical risk assessments.

Key Features:
- Literature-backed parameters (literature_parameters.py)
- Probabilistic risk framework (probabilistic_risk.py)
- CLIMADA hazard data structures (hazards.py)

All parameter values are derived from peer-reviewed literature.
See docs/physical_risk_methodology.md for full citations.
"""
from .hazards import (
    CLIMADAHazardData,
    load_climada_hazards,
    calculate_compound_risk,
    get_hazard_description,
    interpolate_hazard_by_year,
    calculate_economic_impact,
)

from .literature_parameters import (
    LiteratureSource,
    LiteratureParameter,
    THERMAL_EFFICIENCY_PARAMS,
    WILDFIRE_OUTAGE_PARAMS,
    FLOOD_DAMAGE_PARAMS,
    COMPOUND_RISK_PARAMS,
    SLR_PARAMS,
    KOREA_SPECIFIC_PARAMS,
    get_all_parameters,
    get_parameter_summary,
)

from .probabilistic_risk import (
    HazardType,
    HazardEvent,
    DamageFunction,
    ExposureAsset,
    AnnualRiskResult,
    CreditRiskImpact,
    ProbabilisticRiskEngine,
    create_samcheok_exposure,
)

__all__ = [
    # Hazards module
    'CLIMADAHazardData',
    'load_climada_hazards',
    'calculate_compound_risk',
    'get_hazard_description',
    'interpolate_hazard_by_year',
    'calculate_economic_impact',
    # Literature parameters
    'LiteratureSource',
    'LiteratureParameter',
    'THERMAL_EFFICIENCY_PARAMS',
    'WILDFIRE_OUTAGE_PARAMS',
    'FLOOD_DAMAGE_PARAMS',
    'COMPOUND_RISK_PARAMS',
    'SLR_PARAMS',
    'KOREA_SPECIFIC_PARAMS',
    'get_all_parameters',
    'get_parameter_summary',
    # Probabilistic risk
    'HazardType',
    'HazardEvent',
    'DamageFunction',
    'ExposureAsset',
    'AnnualRiskResult',
    'CreditRiskImpact',
    'ProbabilisticRiskEngine',
    'create_samcheok_exposure',
]
