"""Risk adjustment modules."""

from .transition import TransitionAdjustments, apply_transition
from .physical import PhysicalAdjustments, apply_physical
from .financing import FinancingImpact, map_expected_loss_to_spreads, calculate_expected_loss
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
    "apply_physical",
    "FinancingImpact",
    "map_expected_loss_to_spreads",
    "calculate_expected_loss",
    "Rating",
    "RatingMetrics",
    "RatingAssessment",
    "assess_credit_rating",
    "calculate_rating_metrics_from_financials",
    "rating_migration_analysis",
]
