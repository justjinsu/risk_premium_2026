# Credit Rating Methodology - Enhanced for Climate Risk Analysis

## Overview

This document describes the enhanced credit rating methodology implemented for climate risk premium (CRP) calculation. The methodology has been updated to properly handle:

1. **Negative EBITDA scenarios** (common when carbon costs exceed revenue)
2. **Extended distressed rating scale** (CCC to D)
3. **DSCR-based assessment** (standard for project finance)
4. **Counterfactual baseline comparison** (for meaningful CRP calculation)

## Problem Statement

### Original Issue

The original credit rating module had a critical flaw: when carbon costs made EBITDA negative, ALL scenarios collapsed to the worst rating (B), resulting in:

| Scenario | Rating | CRP |
|----------|--------|-----|
| baseline | B | 0 |
| moderate_transition | B | 0 |
| aggressive_transition | B | 0 |

**Root Cause:** The rating thresholds were designed only for positive EBITDA:
- EBITDA/Interest < 1x → B (lowest rating)
- All negative values also fell into this bucket
- No differentiation = No spread differential = CRP = 0

### Impact

The "Credit Rating Death Spiral" - the core innovation of this model - was completely broken because there was no rating differentiation to create spread differentials.

## Solution: Extended Rating Scale

### New Rating Categories

| Rating | Numeric | Spread (bps) | Description |
|--------|---------|--------------|-------------|
| AAA | 1 | 50 | Prime |
| AA | 2 | 100 | High Grade |
| A | 3 | 150 | Upper Medium Grade |
| BBB | 4 | 250 | Lower Medium Grade (IG threshold) |
| BB | 5 | 400 | Non-Investment Speculative |
| B | 6 | 600 | Highly Speculative |
| **CCC** | 7 | 900 | Substantial Risk |
| **CC** | 8 | 1500 | Very High Risk |
| **C** | 9 | 2500 | Near Default |
| **D** | 10 | 5000 | In Default |

### DSCR-Based Rating Thresholds

DSCR (Debt Service Coverage Ratio) is the PRIMARY metric for project finance credit assessment:

| DSCR Range | Rating | Interpretation |
|------------|--------|----------------|
| < 0 | D | Cannot service debt - default |
| 0 - 0.5x | C | Severe shortfall |
| 0.5 - 0.8x | CC | Significant shortfall |
| 0.8 - 1.0x | CCC | Below breakeven |
| 1.0 - 1.1x | B | Marginal |
| 1.1 - 1.3x | BB | Weak but serviceable |
| 1.3 - 1.6x | BBB | Investment grade minimum |
| 1.6 - 2.0x | A | Good coverage |
| 2.0 - 2.5x | AA | Strong coverage |
| > 2.5x | AAA | Very strong coverage |

### Negative Coverage Handling

| EBITDA/Interest | Rating | Interpretation |
|-----------------|--------|----------------|
| < -5x | D | Severe - cannot cover interest |
| -5x to -2x | C | Near default |
| -2x to 0 | CC | Cannot cover from EBITDA |
| 0 to 0.5x | CCC | Barely any coverage |
| 0.5x to 1x | B | Below breakeven |
| > 1x | BB+ | Standard thresholds apply |

## Counterfactual Baseline Approach

### Concept

Instead of comparing climate scenarios to a "baseline with carbon costs" (which already has negative EBITDA), we compare to a **counterfactual no-carbon world**:

```
CRP = WACC(scenario with climate risks) - WACC(counterfactual without climate risks)
```

### Counterfactual Assumptions

For a 2100 MW coal plant like Samcheok in a no-carbon world:
- Expected Rating: **A** (upper medium grade)
- Rationale:
  - Large capacity (2100 MW → AAA on capacity metric)
  - Positive EBITDA (~$800M+ annually without carbon costs)
  - DSCR > 1.5x (typical for baseload power)
  - Moderate leverage (70% D/E typical for project finance)

### CRP Calculation

```python
CRP = (WACC_scenario - WACC_counterfactual) × 10,000 bps

Where:
WACC = 0.70 × (Rf + Spread) + 0.30 × (Re + Equity_Premium)
```

## Results After Fix

| Scenario | NEW Rating | NEW CRP (bps) | OLD CRP |
|----------|------------|---------------|---------|
| baseline | C | 1,735 | 0 |
| moderate_physical | C | 1,735 | 30 |
| high_physical | C | 1,735 | 56 |
| moderate_transition | D | 3,500 | 4,139 |
| aggressive_transition | D | 3,500 | 4,730 |
| combined_moderate | D | 3,500 | 4,057 |
| combined_aggressive | D | 3,500 | 4,547 |

### Key Observations

1. **Baseline now has meaningful CRP (1,735 bps)** - reflects climate transition risk even in "current policy" scenario
2. **Clear differentiation between scenario types:**
   - Physical-only scenarios: C rating (1,735 bps CRP)
   - Transition-heavy scenarios: D rating (3,500 bps CRP)
3. **Credit Rating Death Spiral working:**
   - Carbon costs → Negative EBITDA → Low DSCR → C/D Rating → High Spread → Higher Cost of Capital

## Implementation Details

### Files Modified

1. **`src/risk/credit_rating.py`** (393 → 643 lines)
   - Extended `Rating` enum with CCC, CC, C, D
   - Added `to_spread_bps()` for distressed ratings
   - Added `is_investment_grade` and `is_distressed` properties
   - New `rate_dscr()` function (primary metric)
   - Enhanced `rate_coverage()` for negative values
   - Enhanced `rate_net_debt_leverage()` for negative EBITDA
   - New weighted average approach in `assess_credit_rating()`
   - New `calculate_crp_from_ratings()` function
   - New `get_counterfactual_baseline_rating()` function
   - New `assess_rating_with_counterfactual()` function

2. **`src/risk/financing.py`** (175 → 249 lines)
   - New `calculate_financing_with_counterfactual()` function
   - Enhanced documentation

### Rating Assessment Algorithm

```python
# Weighted average approach (project finance standard)
weights = {
    "capacity": 0.05,        # Business scale
    "profitability": 0.10,   # Operating efficiency
    "coverage": 0.15,        # Interest coverage
    "dscr": 0.35,            # PRIMARY: Debt service coverage
    "net_debt_leverage": 0.15,  # Leverage
    "equity_leverage": 0.10,    # Capital structure
    "asset_leverage": 0.10,     # Balance sheet strength
}

# Distress override
if any critical metric in distress (CCC or worse):
    overall_rating = max(weighted_score, worst_distressed_metric)
```

## References

- **KIS Rating Methodology:** Power Generation Sector (2023)
- **Moody's Global Infrastructure Finance Rating Methodology** (2021)
- **S&P Project Finance Rating Criteria** (2022)
- **Bloomberg US Corporate Bond Index:** Historical spreads by rating (2020-2024)

## Usage Example

```python
from src.risk.credit_rating import (
    calculate_rating_metrics_from_financials,
    assess_rating_with_counterfactual
)

# Calculate metrics
metrics = calculate_rating_metrics_from_financials(
    capacity_mw=2100,
    ebitda=-100e6,  # Negative EBITDA
    fixed_assets=3200e6,
    interest_expense=92.5e6,
    total_debt=2240e6,
    cash_and_equivalents=100e6,
    total_equity=960e6,
    total_assets=3200e6,
    dscr=0.59,
)

# Get rating with counterfactual comparison
result = assess_rating_with_counterfactual(metrics)

print(f"Counterfactual: {result['counterfactual_rating']}")  # A
print(f"Scenario: {result['scenario_rating']}")              # CC
print(f"CRP: {result['crp_bps']:.0f} bps")                   # 1020
```

## Conclusion

The enhanced credit rating module now properly captures the "Credit Rating Death Spiral" that is central to climate risk pricing:

1. **Carbon costs reduce revenue** → Negative EBITDA
2. **Negative EBITDA reduces coverage ratios** → Low/Negative DSCR
3. **Poor coverage triggers distressed ratings** → CCC, CC, C, D
4. **Distressed ratings command high spreads** → 900-5000 bps
5. **High spreads increase cost of capital** → Higher CRP

This creates a non-linear feedback loop that properly prices climate transition risk into coal asset valuations.
