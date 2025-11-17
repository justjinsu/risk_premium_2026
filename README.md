# Quantifying Climate Risk Premium – Samcheok Power Plant

This repository hosts an open, modular financial analysis tool to quantify the Climate Risk Premium (CRP) for major infrastructure projects, starting with the Samcheok Power Plant case study. The structure separates data, analytics, and reporting so that CSV inputs/outputs, scenarios, and assumptions are easy to trace and update. Streamlit will later surface the results in an interactive UI.

## Repository layout
- `data/` raw CSV inputs, processed CSV outputs, and external reference data (kept out of git where possible)
- `docs/` research outline, methods, and project governance notes
- `notebooks/` exploratory calculations and visual prototypes
- `src/` Python package for reusable logic (CSV I/O, risk adjustments, cash-flow modeling, reporting, Streamlit UI hook)
- `tests/` unit tests for model components

## Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Analysis
```bash
# Quick command-line run
python run_analysis.py

# Or launch interactive Streamlit app
streamlit run src/app/streamlit_app.py

# Or explore in Jupyter
jupyter notebook notebooks/01_explore_crp_model.ipynb
```

### 3. Run Tests
```bash
pytest tests/ -v
```

## What's Included

The model is **fully functional** with:

**Data (in `data/raw/`):**
- ✅ Samcheok plant parameters (2,000 MW coal plant)
- ✅ 4 transition risk scenarios (baseline, moderate, aggressive, Korea NDC)
- ✅ 4 physical risk scenarios (baseline, moderate, high, extreme)
- ✅ Financing parameters (spreads, WACC assumptions)

**Analytics (in `src/`):**
- ✅ Time-series cash flow model (annual projections)
- ✅ NPV, IRR, DSCR, LLCR calculations
- ✅ Transition risk adjustments (dispatch penalties, early retirement, carbon pricing)
- ✅ Physical risk adjustments (wildfire outages, water stress, efficiency losses)
- ✅ Expected loss calculation from NPV differentials
- ✅ Climate Risk Premium (CRP) mapping to financing spreads & WACC

**Outputs:**
- ✅ Multi-scenario runner (7 default scenarios)
- ✅ CSV exports to `data/processed/`
- ✅ Interactive Streamlit dashboard
- ✅ Jupyter notebook for exploration
- ✅ Plotly visualizations (waterfall, capacity trajectories, NPV comparison, CRP spreads)

**Testing:**
- ✅ Unit tests for financials and risk modules

## Model Structure

```
Inputs (CSV) → Risk Adjustments → Cash Flows → Financial Metrics → CRP Calculation → Outputs
```

1. **Load plant & scenario data** from CSV
2. **Apply transition risks**: dispatch penalties, retirement schedules, carbon prices
3. **Apply physical risks**: outage rates, capacity derating, efficiency losses
4. **Generate time-series cash flows**: revenue, costs, EBITDA, FCF (annual)
5. **Calculate metrics**: NPV, IRR, DSCR, LLCR
6. **Compute expected loss**: (Baseline NPV - Risk NPV) / CAPEX
7. **Map to financing impacts**: debt spreads, equity premiums, WACC, CRP

## Scenarios

**Default Analysis Runs:**
1. Baseline (no climate risks)
2. Moderate transition (NDC-aligned)
3. Aggressive transition (Net Zero 2050)
4. Moderate physical (RCP 4.5)
5. High physical (RCP 8.5)
6. Combined moderate (transition + physical)
7. Combined aggressive (worst-case)

## Key Outputs

- `data/processed/scenario_comparison.csv`: Summary metrics for all scenarios
- `data/processed/cashflow_*.csv`: Annual cash flows for each scenario
- Interactive charts in Streamlit app showing NPV loss, CRP, and capacity trajectories

## Next Steps (Optional Enhancements)

- Calibrate carbon price trajectories to Korea policy updates
- Add Monte Carlo simulation for wildfire/water risk
- Incorporate more granular dispatch modeling
- Add sensitivity analysis for key parameters
- Extend to other coal plants or renewables comparison
