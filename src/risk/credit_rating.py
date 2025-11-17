"""
Credit rating assessment based on KIS (Korea Investors Service) methodology.
Implements quantitative mapping grid for Private Power Generation (IPP) industry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class Rating(Enum):
    """Credit rating categories."""
    AAA = 1
    AA = 2
    A = 3
    BBB = 4
    BB = 5
    B = 6

    def __str__(self):
        return self.name

    def to_spread_bps(self) -> float:
        """Convert rating to typical spread over risk-free rate (bps)."""
        spread_map = {
            Rating.AAA: 50,
            Rating.AA: 100,
            Rating.A: 150,
            Rating.BBB: 250,
            Rating.BB: 400,
            Rating.B: 600,
        }
        return spread_map[self]

    @property
    def numeric_score(self) -> int:
        """Numeric score for rating (1=best, 6=worst)."""
        return self.value


@dataclass
class RatingMetrics:
    """Financial metrics used for credit rating assessment."""
    # Business Stability & Profitability
    capacity_mw: float
    ebitda_to_fixed_assets: float  # percentage

    # Coverage Ratios
    ebitda_to_interest: float  # times

    # Leverage Ratios
    net_debt_to_ebitda: float  # times
    debt_to_equity: float  # percentage
    debt_to_assets: float  # percentage


@dataclass
class RatingAssessment:
    """Credit rating assessment result."""
    overall_rating: Rating
    component_ratings: Dict[str, Rating]
    metrics: RatingMetrics
    rating_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_rating": str(self.overall_rating),
            "rating_numeric": self.overall_rating.numeric_score,
            "spread_bps": self.overall_rating.to_spread_bps(),
            "capacity_rating": str(self.component_ratings["capacity"]),
            "profitability_rating": str(self.component_ratings["profitability"]),
            "coverage_rating": str(self.component_ratings["coverage"]),
            "net_debt_leverage_rating": str(self.component_ratings["net_debt_leverage"]),
            "equity_leverage_rating": str(self.component_ratings["equity_leverage"]),
            "asset_leverage_rating": str(self.component_ratings["asset_leverage"]),
            "capacity_mw": self.metrics.capacity_mw,
            "ebitda_to_fixed_assets": self.metrics.ebitda_to_fixed_assets,
            "ebitda_to_interest": self.metrics.ebitda_to_interest,
            "net_debt_to_ebitda": self.metrics.net_debt_to_ebitda,
            "debt_to_equity": self.metrics.debt_to_equity,
            "debt_to_assets": self.metrics.debt_to_assets,
        }


def rate_capacity(capacity_mw: float) -> Rating:
    """Rate based on installed capacity (MW)."""
    if capacity_mw >= 2000:
        return Rating.AAA
    elif capacity_mw >= 800:
        return Rating.AA
    elif capacity_mw >= 400:
        return Rating.A
    elif capacity_mw >= 100:
        return Rating.BBB
    elif capacity_mw >= 20:
        return Rating.BB
    else:
        return Rating.B


def rate_profitability(ebitda_to_fixed_assets: float) -> Rating:
    """Rate based on EBITDA/Fixed Assets (%)."""
    if ebitda_to_fixed_assets >= 15:
        return Rating.AAA
    elif ebitda_to_fixed_assets >= 11:
        return Rating.AA
    elif ebitda_to_fixed_assets >= 8:
        return Rating.A
    elif ebitda_to_fixed_assets >= 4:
        return Rating.BBB
    elif ebitda_to_fixed_assets >= 1:
        return Rating.BB
    else:
        return Rating.B


def rate_coverage(ebitda_to_interest: float) -> Rating:
    """Rate based on EBITDA/Interest Expense (times)."""
    if ebitda_to_interest >= 12:
        return Rating.AAA
    elif ebitda_to_interest >= 6:
        return Rating.AA
    elif ebitda_to_interest >= 4:
        return Rating.A
    elif ebitda_to_interest >= 2:
        return Rating.BBB
    elif ebitda_to_interest >= 1:
        return Rating.BB
    else:
        return Rating.B


def rate_net_debt_leverage(net_debt_to_ebitda: float) -> Rating:
    """Rate based on Net Debt/EBITDA (times). Lower is better."""
    if net_debt_to_ebitda <= 1:
        return Rating.AAA
    elif net_debt_to_ebitda <= 4:
        return Rating.AA
    elif net_debt_to_ebitda <= 7:
        return Rating.A
    elif net_debt_to_ebitda <= 10:
        return Rating.BBB
    elif net_debt_to_ebitda <= 12:
        return Rating.BB
    else:
        return Rating.B


def rate_equity_leverage(debt_to_equity: float) -> Rating:
    """Rate based on Debt-to-Equity Ratio (%). Lower is better."""
    if debt_to_equity <= 80:
        return Rating.AAA
    elif debt_to_equity <= 150:
        return Rating.AA
    elif debt_to_equity <= 250:
        return Rating.A
    elif debt_to_equity <= 300:
        return Rating.BBB
    elif debt_to_equity <= 400:
        return Rating.BB
    else:
        return Rating.B


def rate_asset_leverage(debt_to_assets: float) -> Rating:
    """Rate based on Debt-to-Assets Ratio (%). Lower is better."""
    if debt_to_assets <= 20:
        return Rating.AAA
    elif debt_to_assets <= 40:
        return Rating.AA
    elif debt_to_assets <= 60:
        return Rating.A
    elif debt_to_assets <= 80:
        return Rating.BBB
    elif debt_to_assets <= 90:
        return Rating.BB
    else:
        return Rating.B


def assess_credit_rating(metrics: RatingMetrics) -> RatingAssessment:
    """
    Assess overall credit rating based on KIS methodology.

    Uses a conservative approach: overall rating is the worst of component ratings,
    with possible adjustments for balanced performance.
    """
    # Calculate component ratings
    component_ratings = {
        "capacity": rate_capacity(metrics.capacity_mw),
        "profitability": rate_profitability(metrics.ebitda_to_fixed_assets),
        "coverage": rate_coverage(metrics.ebitda_to_interest),
        "net_debt_leverage": rate_net_debt_leverage(metrics.net_debt_to_ebitda),
        "equity_leverage": rate_equity_leverage(metrics.debt_to_equity),
        "asset_leverage": rate_asset_leverage(metrics.debt_to_assets),
    }

    # Conservative approach: start with worst rating
    ratings_list = list(component_ratings.values())
    worst_rating = max(ratings_list, key=lambda r: r.value)

    # Count ratings at each level
    rating_counts = {rating: ratings_list.count(rating) for rating in set(ratings_list)}

    # If majority of metrics are better than worst, upgrade by one notch
    better_count = sum(1 for r in ratings_list if r.value < worst_rating.value)
    if better_count >= 4:  # Majority
        overall_value = max(1, worst_rating.value - 1)
        overall_rating = Rating(overall_value)
        rationale = f"Overall {overall_rating}: Conservative rating with majority upgrade (4+ metrics better than worst)"
    else:
        overall_rating = worst_rating
        rationale = f"Overall {overall_rating}: Conservative rating driven by weakest metrics"

    return RatingAssessment(
        overall_rating=overall_rating,
        component_ratings=component_ratings,
        metrics=metrics,
        rating_rationale=rationale,
    )


def calculate_rating_metrics_from_financials(
    capacity_mw: float,
    ebitda: float,
    fixed_assets: float,
    interest_expense: float,
    total_debt: float,
    cash_and_equivalents: float,
    total_equity: float,
    total_assets: float,
) -> RatingMetrics:
    """
    Calculate rating metrics from financial statement items.

    Args:
        capacity_mw: Installed capacity
        ebitda: Earnings before interest, taxes, depreciation, amortization
        fixed_assets: Property, plant & equipment
        interest_expense: Annual interest payments
        total_debt: Total debt outstanding
        cash_and_equivalents: Liquid assets
        total_equity: Total shareholder equity
        total_assets: Total assets
    """
    # Avoid division by zero
    ebitda_to_fixed_assets = (ebitda / fixed_assets * 100) if fixed_assets > 0 else 0
    ebitda_to_interest = (ebitda / interest_expense) if interest_expense > 0 else 999  # Very high if no interest

    net_debt = total_debt - cash_and_equivalents
    net_debt_to_ebitda = (net_debt / ebitda) if ebitda > 0 else 999

    debt_to_equity = (total_debt / total_equity * 100) if total_equity > 0 else 999
    debt_to_assets = (total_debt / total_assets * 100) if total_assets > 0 else 100

    return RatingMetrics(
        capacity_mw=capacity_mw,
        ebitda_to_fixed_assets=ebitda_to_fixed_assets,
        ebitda_to_interest=ebitda_to_interest,
        net_debt_to_ebitda=net_debt_to_ebitda,
        debt_to_equity=debt_to_equity,
        debt_to_assets=debt_to_assets,
    )


def rating_migration_analysis(
    baseline_rating: RatingAssessment,
    risk_rating: RatingAssessment,
) -> Dict[str, Any]:
    """
    Analyze credit rating migration from baseline to risk scenario.

    Returns dictionary with migration details and impact.
    """
    notch_change = risk_rating.overall_rating.value - baseline_rating.overall_rating.value
    spread_change = risk_rating.overall_rating.to_spread_bps() - baseline_rating.overall_rating.to_spread_bps()

    if notch_change == 0:
        migration = "No Change"
    elif notch_change > 0:
        migration = f"Downgrade by {notch_change} notch(es)"
    else:
        migration = f"Upgrade by {abs(notch_change)} notch(es)"

    # Identify which metrics deteriorated most
    metric_changes = {}
    for metric_name in baseline_rating.component_ratings.keys():
        baseline_val = baseline_rating.component_ratings[metric_name].value
        risk_val = risk_rating.component_ratings[metric_name].value
        metric_changes[metric_name] = risk_val - baseline_val

    worst_metric = max(metric_changes.items(), key=lambda x: x[1])

    return {
        "baseline_rating": str(baseline_rating.overall_rating),
        "risk_rating": str(risk_rating.overall_rating),
        "migration": migration,
        "notch_change": notch_change,
        "spread_increase_bps": spread_change,
        "worst_deteriorating_metric": worst_metric[0],
        "worst_deterioration_notches": worst_metric[1],
        "metric_changes": {k: v for k, v in metric_changes.items()},
    }
