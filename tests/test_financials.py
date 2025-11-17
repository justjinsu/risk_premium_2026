"""
Unit tests for financial calculations.
"""
import pytest
import numpy as np
from src.financials.cashflow import compute_cashflows_timeseries
from src.financials.metrics import calculate_metrics, calculate_debt_service
from src.scenarios import TransitionScenario, PhysicalScenario
from src.risk import apply_transition, apply_physical


@pytest.fixture
def plant_params():
    """Sample plant parameters."""
    return {
        'capacity_mw': 1000,
        'capacity_factor': 0.50,
        'operating_years': 30,
        'heat_rate_mmbtu_mwh': 9.5,
        'emissions_tCO2_per_mwh': 0.95,
        'power_price_per_mwh': 80,
        'fuel_price_per_mmbtu': 3.2,
        'fixed_opex_per_kw_year': 42,
        'variable_opex_per_mwh': 4.5,
        'total_capex_million': 1600,
        'discount_rate': 0.08,
        'debt_fraction': 0.70,
        'equity_fraction': 0.30,
        'debt_interest_rate': 0.05,
        'debt_tenor_years': 20,
    }


@pytest.fixture
def baseline_scenario():
    """Baseline transition scenario."""
    return TransitionScenario(
        name="baseline",
        dispatch_priority_penalty=0.0,
        retirement_years=30,
        carbon_price_2025=0,
        carbon_price_2030=0,
        carbon_price_2040=0,
        carbon_price_2050=0,
    )


@pytest.fixture
def baseline_physical():
    """Baseline physical scenario."""
    return PhysicalScenario(
        name="baseline",
        wildfire_outage_rate=0.0,
        drought_derate=0.0,
        cooling_temp_penalty=0.0,
    )


def test_cashflow_timeseries(plant_params, baseline_scenario, baseline_physical):
    """Test time-series cashflow calculation."""
    transition_adj = apply_transition(plant_params, baseline_scenario)
    physical_adj = apply_physical(plant_params, baseline_physical)

    cashflow = compute_cashflows_timeseries(
        plant_params,
        baseline_scenario,
        transition_adj,
        physical_adj,
        start_year=2025,
    )

    # Check structure
    assert len(cashflow.years) == 30
    assert len(cashflow.revenue) == 30
    assert len(cashflow.ebitda) == 30

    # Check values are positive
    assert np.all(cashflow.revenue > 0)
    assert np.all(cashflow.fuel_costs > 0)
    assert np.all(cashflow.fixed_opex > 0)

    # Check EBITDA = revenue - costs
    assert np.allclose(
        cashflow.ebitda,
        cashflow.revenue - cashflow.total_costs,
        rtol=1e-6
    )


def test_debt_service_calculation(plant_params):
    """Test debt service amortization."""
    total_capex = plant_params['total_capex_million'] * 1e6
    debt_fraction = plant_params['debt_fraction']
    interest_rate = plant_params['debt_interest_rate']
    tenor = plant_params['debt_tenor_years']

    debt_struct = calculate_debt_service(total_capex, debt_fraction, interest_rate, tenor)

    # Check debt amount
    assert debt_struct.debt_amount == total_capex * debt_fraction

    # Check schedule length
    assert len(debt_struct.principal_schedule) == tenor
    assert len(debt_struct.interest_schedule) == tenor

    # Check principal + interest = debt service
    for i in range(tenor):
        total_payment = debt_struct.principal_schedule[i] + debt_struct.interest_schedule[i]
        assert abs(total_payment - debt_struct.annual_debt_service) < 1.0


def test_financial_metrics(plant_params, baseline_scenario, baseline_physical):
    """Test NPV, IRR, DSCR, LLCR calculations."""
    transition_adj = apply_transition(plant_params, baseline_scenario)
    physical_adj = apply_physical(plant_params, baseline_physical)

    cashflow = compute_cashflows_timeseries(
        plant_params,
        baseline_scenario,
        transition_adj,
        physical_adj,
    )

    metrics = calculate_metrics(cashflow, plant_params)

    # NPV should be reasonable
    assert metrics.npv > -1e9  # Not hugely negative
    assert metrics.npv < 1e10  # Not unreasonably large

    # IRR should be between -50% and 50%
    assert -0.5 <= metrics.irr <= 0.5

    # DSCR should be positive
    assert metrics.avg_dscr > 0
    assert metrics.min_dscr > 0

    # LLCR should be positive
    assert metrics.llcr > 0


def test_carbon_price_impact(plant_params, baseline_physical):
    """Test that carbon pricing reduces NPV."""
    # Baseline scenario with no carbon price
    baseline = TransitionScenario(
        name="baseline",
        dispatch_priority_penalty=0.0,
        retirement_years=30,
        carbon_price_2025=0,
        carbon_price_2030=0,
        carbon_price_2040=0,
        carbon_price_2050=0,
    )

    # Scenario with carbon price
    carbon_scenario = TransitionScenario(
        name="carbon",
        dispatch_priority_penalty=0.0,
        retirement_years=30,
        carbon_price_2025=50,
        carbon_price_2030=100,
        carbon_price_2040=150,
        carbon_price_2050=200,
    )

    physical_adj = apply_physical(plant_params, baseline_physical)

    # Calculate NPVs
    baseline_adj = apply_transition(plant_params, baseline)
    cf_baseline = compute_cashflows_timeseries(plant_params, baseline, baseline_adj, physical_adj)
    metrics_baseline = calculate_metrics(cf_baseline, plant_params)

    carbon_adj = apply_transition(plant_params, carbon_scenario)
    cf_carbon = compute_cashflows_timeseries(plant_params, carbon_scenario, carbon_adj, physical_adj)
    metrics_carbon = calculate_metrics(cf_carbon, plant_params)

    # Carbon pricing should reduce NPV
    assert metrics_carbon.npv < metrics_baseline.npv
