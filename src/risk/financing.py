"""
Translate expected losses into financing spreads and Climate Risk Premium (CRP).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FinancingImpact:
    expected_loss_pct: float
    npv_loss_million: float
    debt_spread_bps: float
    equity_premium_pct: float
    crp_bps: float
    wacc_baseline_pct: float
    wacc_adjusted_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_loss_pct": self.expected_loss_pct,
            "npv_loss_million": self.npv_loss_million,
            "debt_spread_bps": self.debt_spread_bps,
            "equity_premium_pct": self.equity_premium_pct,
            "crp_bps": self.crp_bps,
            "wacc_baseline_pct": self.wacc_baseline_pct,
            "wacc_adjusted_pct": self.wacc_adjusted_pct,
        }


def calculate_expected_loss(
    baseline_npv: float,
    risk_adjusted_npv: float,
    total_capex: float,
) -> float:
    """
    Calculate expected loss as percentage of capital at risk.
    Expected Loss % = (Baseline NPV - Risk-Adjusted NPV) / Total CAPEX * 100
    """
    npv_loss = baseline_npv - risk_adjusted_npv
    if total_capex <= 0:
        return 0.0
    expected_loss_pct = (npv_loss / total_capex) * 100
    return max(0.0, expected_loss_pct)  # Floor at zero


def map_expected_loss_to_spreads(
    expected_loss_pct: float,
    npv_loss: float,
    params: Dict[str, Any]
) -> FinancingImpact:
    """
    Map expected loss to financing cost impacts (debt spreads, equity premiums).
    Calculate Climate Risk Premium (CRP) and adjusted WACC.
    """
    # Extract parameters
    spread_slope = float(params.get("spread_slope_bps_per_pct", 50))
    equity_slope = float(params.get("equity_slope_pct_per_pct", 0.8))
    baseline_spread = float(params.get("baseline_spread_bps", 150))
    risk_free_rate = float(params.get("risk_free_rate", 0.03))
    debt_fraction = float(params.get("debt_fraction", 0.70))
    equity_fraction = float(params.get("equity_fraction", 0.30))

    # Baseline debt cost
    baseline_debt_rate = risk_free_rate + (baseline_spread / 10000)

    # Risk-adjusted debt spread
    debt_spread = baseline_spread + expected_loss_pct * spread_slope
    adjusted_debt_rate = risk_free_rate + (debt_spread / 10000)

    # Equity cost (baseline equity return ~12%, adjusted by risk premium)
    baseline_equity_rate = 0.12
    equity_premium_pct = expected_loss_pct * equity_slope
    adjusted_equity_rate = baseline_equity_rate + (equity_premium_pct / 100)

    # WACC calculations
    # Tax shield ignored for simplicity
    wacc_baseline = debt_fraction * baseline_debt_rate + equity_fraction * baseline_equity_rate
    wacc_adjusted = debt_fraction * adjusted_debt_rate + equity_fraction * adjusted_equity_rate

    # Climate Risk Premium (increase in total cost of capital)
    crp = (wacc_adjusted - wacc_baseline) * 10000  # in bps

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=debt_spread,
        equity_premium_pct=equity_premium_pct,
        crp_bps=crp,
        wacc_baseline_pct=wacc_baseline * 100,
        wacc_adjusted_pct=wacc_adjusted * 100,
    )


def calculate_financing_from_rating(
    rating_spread_bps: float,
    baseline_spread_bps: float,
    npv_loss: float,
    total_capex: float,
    params: Dict[str, Any]
) -> FinancingImpact:
    """
    Calculate financing impact based on a specific credit rating spread.
    
    Args:
        rating_spread_bps: The spread associated with the scenario's credit rating (e.g., 250 for BBB)
        baseline_spread_bps: The spread associated with the baseline scenario
        npv_loss: Absolute NPV loss (Baseline NPV - Scenario NPV)
        total_capex: Total CAPEX for expected loss % calculation
        params: Financing parameters
    """
    # Extract parameters
    equity_slope = float(params.get("equity_slope_pct_per_pct", 0.8))
    risk_free_rate = float(params.get("risk_free_rate", 0.03))
    debt_fraction = float(params.get("debt_fraction", 0.70))
    equity_fraction = float(params.get("equity_fraction", 0.30))

    # Calculate Expected Loss % (for reporting purposes, even if not driving spread)
    expected_loss_pct = 0.0
    if total_capex > 0:
        expected_loss_pct = max(0.0, (npv_loss / total_capex) * 100)

    # 1. Debt Cost
    # Use the explicit rating spread
    debt_spread = rating_spread_bps
    adjusted_debt_rate = risk_free_rate + (debt_spread / 10000)
    
    # Baseline debt cost (for comparison)
    baseline_debt_rate = risk_free_rate + (baseline_spread_bps / 10000)

    # 2. Equity Cost
    # We still use the linear model for equity premium as we don't have a "Credit Rating for Equity"
    # Alternatively, we could scale it by the spread increase ratio, but sticking to the slope is safer for now.
    baseline_equity_rate = 0.12
    equity_premium_pct = expected_loss_pct * equity_slope
    adjusted_equity_rate = baseline_equity_rate + (equity_premium_pct / 100)

    # 3. WACC
    wacc_baseline = debt_fraction * baseline_debt_rate + equity_fraction * baseline_equity_rate
    wacc_adjusted = debt_fraction * adjusted_debt_rate + equity_fraction * adjusted_equity_rate

    # 4. Climate Risk Premium (CRP)
    crp = (wacc_adjusted - wacc_baseline) * 10000  # in bps

    return FinancingImpact(
        expected_loss_pct=expected_loss_pct,
        npv_loss_million=npv_loss / 1e6,
        debt_spread_bps=debt_spread,
        equity_premium_pct=equity_premium_pct,
        crp_bps=crp,
        wacc_baseline_pct=wacc_baseline * 100,
        wacc_adjusted_pct=wacc_adjusted * 100,
    )
