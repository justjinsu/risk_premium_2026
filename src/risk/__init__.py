"""Risk adjustment modules."""

from .transition import TransitionAdjustments, apply_transition
from .physical import (
    PhysicalAdjustments,
    YearlyPhysicalAdjustments,
    apply_physical,
    create_yearly_physical_adjustments,
)
from .financing import (
    FinancingImpact,
    map_expected_loss_to_spreads,
    calculate_expected_loss,
    calculate_financing_from_rating
)
from .credit_rating import (
    Rating,
    RatingMetrics,
    RatingAssessment,
    assess_credit_rating,
    calculate_rating_metrics_from_financials,
    rating_migration_analysis,
)

__all__ = [
    "TransitionAdjustments",
    "apply_transition",
    "PhysicalAdjustments",
    "YearlyPhysicalAdjustments",
    "apply_physical",
    "create_yearly_physical_adjustments",
    "FinancingImpact",
    "map_expected_loss_to_spreads",
    "calculate_expected_loss",
    "calculate_financing_from_rating",
    "Rating",
    "RatingMetrics",
    "RatingAssessment",
    "assess_credit_rating",
    "calculate_rating_metrics_from_financials",
    "rating_migration_analysis",
]
