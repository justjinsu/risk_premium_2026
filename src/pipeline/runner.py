"""
Class-based orchestration for CRP runs using CSV inputs and CSV/plot outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

from src.data import load_inputs, get_param_value
from src.scenarios import TransitionScenario, PhysicalScenario, MarketScenario
from src.scenarios.carbon_pricing import (
    CarbonPricingScenario,
    get_all_carbon_scenarios,
    load_carbon_scenarios_from_csv,
)
from src.risk import (
    apply_transition, apply_physical, map_expected_loss_to_spreads, calculate_expected_loss, FinancingImpact,
    assess_credit_rating, calculate_rating_metrics_from_financials, RatingAssessment,
    calculate_financing_from_rating
)
from src.risk.credit_rating import (
    assess_rating_with_counterfactual,
    get_counterfactual_baseline_rating,
    Rating
)
from src.risk.financing import calculate_financing_with_counterfactual
from src.financials import compute_cashflows_timeseries, calculate_metrics, CashFlowTimeSeries, FinancialMetrics
from src.scenarios.korea_power_plan import load_korea_power_plan_scenarios
from src.risk.physical import get_physical_risk_scenario
from src.climada.hazards import load_climada_hazards, CLIMADAHazardData


@dataclass
class ScenarioResult:
    """Results for a single scenario."""
    scenario_name: str
    cashflow: CashFlowTimeSeries
    metrics: FinancialMetrics
    financing: FinancingImpact | None = None  # Only for risk scenarios
    credit_rating: RatingAssessment | None = None  # Credit rating assessment
    counterfactual_crp: Dict[str, Any] | None = None  # Counterfactual-based CRP analysis


class CRPModelRunner:
    """
    Orchestrates loading CSV inputs, applying risk adjustments, and exporting outputs.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.dataset = load_inputs(self.base_dir)
        self.power_plans = load_korea_power_plan_scenarios(self.base_dir / "data/raw/korea_power_plan.csv")
        self.climada_hazards = load_climada_hazards(self.base_dir / "data/raw/climada_hazards.csv")
        self.carbon_scenarios = self._load_carbon_scenarios()

    def _load_carbon_scenarios(self) -> Dict[str, CarbonPricingScenario]:
        """Load carbon pricing scenarios from CSV or use defaults."""
        carbon_csv_path = self.base_dir / "data/raw/carbon_prices.csv"
        if carbon_csv_path.exists():
            try:
                return load_carbon_scenarios_from_csv(str(carbon_csv_path))
            except Exception as e:
                print(f"Warning: Could not load carbon_prices.csv: {e}")
                return get_all_carbon_scenarios()
        else:
            # Use built-in scenarios
            return get_all_carbon_scenarios()

    def _get_plant_params(self) -> Dict[str, Any]:
        """Extract plant parameters as a flat dict."""
        return {k: get_param_value(self.dataset.plant_params, k) for k in self.dataset.plant_params.keys()}

    def _get_financing_params(self) -> Dict[str, Any]:
        """Extract financing parameters."""
        params = {}
        for k in self.dataset.financing_params.keys():
            params[k] = get_param_value(self.dataset.financing_params, k)
        # Also add plant finance params
        plant_params = self._get_plant_params()
        params['debt_fraction'] = plant_params.get('debt_fraction', 0.70)
        params['equity_fraction'] = plant_params.get('equity_fraction', 0.30)
        return params

    def _load_transition_scenario(self, scenario_name: str) -> TransitionScenario:
        """
        Load transition scenario from CSV and link carbon pricing scenario.

        Carbon pricing is linked in this priority:
        1. If 'carbon_scenario' column exists in policy.csv, link that scenario
        2. Otherwise, use the carbon_price_20XX anchor points
        """
        row = self.dataset.policy_scenarios.get(scenario_name)
        if not row:
            raise ValueError(f"Transition scenario '{scenario_name}' not found")

        # Get carbon scenario name from policy.csv (if present)
        carbon_scenario_name = row.get('carbon_scenario', None)

        scenario = TransitionScenario(
            name=scenario_name,
            dispatch_priority_penalty=float(row.get('dispatch_penalty', 0)),
            retirement_years=int(float(row.get('retirement_years', 40))),
            carbon_price_2025=float(row.get('carbon_price_2025', 0)),
            carbon_price_2030=float(row.get('carbon_price_2030', 0)),
            carbon_price_2040=float(row.get('carbon_price_2040', 0)),
            carbon_price_2050=float(row.get('carbon_price_2050', 0)),
            carbon_scenario_name=carbon_scenario_name,
        )

        # Link detailed carbon pricing scenario if available
        if carbon_scenario_name and carbon_scenario_name in self.carbon_scenarios:
            scenario.set_carbon_scenario(self.carbon_scenarios[carbon_scenario_name])

        return scenario

    def _load_physical_scenario(self, scenario_name: str) -> PhysicalScenario | CLIMADAHazardData:
        """Load physical scenario from CSV or CLIMADA data."""
        # Check CLIMADA first
        if scenario_name in self.climada_hazards:
            return self.climada_hazards[scenario_name]

        # Override for specific hardcoded scenarios if not in CSV
        if scenario_name == "severe_drought":
            # Force 50% water availability
            return PhysicalScenario(
                name="severe_drought",
                wildfire_outage_rate=0.05,
                drought_derate=0.05,
                cooling_temp_penalty=0.02,
                water_availability_pct=50.0
            )

        # Check for dynamic levels first
        if scenario_name.lower() in ["low", "medium", "high", "extreme"]:
            return get_physical_risk_scenario(scenario_name)

        row = self.dataset.physical_risks.get(scenario_name)
        if not row:
            # Fallback to baseline if not found
            return get_physical_risk_scenario("Low")

        return PhysicalScenario(
            name=scenario_name,
            wildfire_outage_rate=float(row.get('wildfire_outage_rate', 0)),
            drought_derate=float(row.get('drought_derate', 0)),
            cooling_temp_penalty=float(row.get('cooling_temp_penalty', 0)),
            water_availability_pct=float(row.get('water_availability_pct', 100.0)),
        )

    def _load_market_scenario(self, scenario_name: str) -> MarketScenario:
        """Load market scenario (demand/price)."""
        # For now, create default or simple variations since we don't have a CSV for this yet
        # In a real app, this would load from data/raw/market_scenarios.csv
        if scenario_name == "low_demand":
            return MarketScenario(name="low_demand", demand_growth_pct=-1.0, price_sensitivity=0.5)
        elif scenario_name == "high_demand":
            return MarketScenario(name="high_demand", demand_growth_pct=2.0, price_sensitivity=0.5)
        else:
            return MarketScenario(name="baseline", demand_growth_pct=1.0, price_sensitivity=0.5)

    def run_scenario(
        self,
        scenario_name: str,
        transition_scenario_name: str = "baseline",
        physical_scenario_name: str = "baseline",
        market_scenario_name: str = "baseline",
        power_plan_name: str | None = None,
    ) -> ScenarioResult:
        """Run a single scenario."""
        plant_params = self._get_plant_params()

        transition_scenario = self._load_transition_scenario(transition_scenario_name)
        physical_data = self._load_physical_scenario(physical_scenario_name)
        market_scenario = self._load_market_scenario(market_scenario_name)

        # Load Korea Power Plan if specified
        korea_plan = None
        if power_plan_name and power_plan_name in self.power_plans:
            korea_plan = self.power_plans[power_plan_name]

        transition_adj = apply_transition(
            plant_params, 
            transition_scenario,
            korea_plan_scenario=korea_plan
        )
        
        # Handle CLIMADA vs Standard Physical Scenario
        if isinstance(physical_data, CLIMADAHazardData):
            # Create a dummy base scenario for the signature, but pass climada_hazard
            dummy_scenario = PhysicalScenario("CLIMADA", 0, 0, 0)
            physical_adj = apply_physical(plant_params, dummy_scenario, climada_hazard=physical_data)
        else:
            physical_adj = apply_physical(plant_params, physical_data)

        cashflow = compute_cashflows_timeseries(
            plant_params,
            transition_scenario,
            transition_adj,
            physical_adj,
            market_scenario,
        )

        metrics = calculate_metrics(cashflow, plant_params)

        # Calculate credit rating based on average annual performance
        avg_ebitda = float(cashflow.ebitda.mean())
        capacity_mw = plant_params.get('capacity_mw', 2000)
        total_capex = plant_params.get('total_capex_million', 3200) * 1e6
        debt_fraction = plant_params.get('debt_fraction', 0.70)
        equity_fraction = plant_params.get('equity_fraction', 0.30)
        debt_interest = plant_params.get('debt_interest_rate', 0.05)

        # Estimate balance sheet items
        fixed_assets = total_capex  # Simplified: assume fixed assets = capex
        total_debt = total_capex * debt_fraction
        total_equity = total_capex * equity_fraction
        total_assets = total_capex
        interest_expense = total_debt * debt_interest
        cash_and_equivalents = avg_ebitda * 0.1  # Assume 10% of EBITDA in cash

        rating_metrics = calculate_rating_metrics_from_financials(
            capacity_mw=capacity_mw,
            ebitda=avg_ebitda,
            fixed_assets=fixed_assets,
            interest_expense=interest_expense,
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents,
            total_equity=total_equity,
            total_assets=total_assets,
            dscr=metrics.avg_dscr,  # Use DSCR from financial metrics
        )

        credit_rating = assess_credit_rating(rating_metrics)

        # Calculate counterfactual-based CRP
        counterfactual_result = assess_rating_with_counterfactual(rating_metrics)

        return ScenarioResult(
            scenario_name=scenario_name,
            cashflow=cashflow,
            metrics=metrics,
            credit_rating=credit_rating,
            counterfactual_crp=counterfactual_result,
        )

    def run_multi_scenario(
        self,
        scenarios: List[Dict[str, str]] = None,
    ) -> Dict[str, ScenarioResult]:
        """
        Run multiple scenarios and calculate financing impacts.

        Args:
            scenarios: List of dicts with keys: name, transition, physical
                      If None, runs default scenarios
        """
        if scenarios is None:
            scenarios = [
                # No carbon pricing baseline (for educational comparison)
                {"name": "no_carbon_baseline", "transition": "no_carbon_baseline", "physical": "baseline"},
                # Standard scenarios
                {"name": "baseline", "transition": "baseline", "physical": "baseline"},
                {"name": "moderate_transition", "transition": "moderate_transition", "physical": "baseline"},
                {"name": "aggressive_transition", "transition": "aggressive_transition", "physical": "baseline"},
                {"name": "moderate_physical", "transition": "baseline", "physical": "moderate_physical"},
                {"name": "high_physical", "transition": "baseline", "physical": "high_physical"},
                {"name": "combined_moderate", "transition": "moderate_transition", "physical": "moderate_physical"},
                {"name": "combined_aggressive", "transition": "aggressive_transition", "physical": "high_physical"},
                # Additional scenarios
                {"name": "low_demand", "transition": "baseline", "physical": "baseline", "market": "low_demand"},
                {"name": "severe_drought", "transition": "baseline", "physical": "severe_drought", "market": "baseline"},
            ]

        results = {}
        baseline_result = None

        # Run all scenarios
        for scenario_spec in scenarios:
            market_name = scenario_spec.get("market", "baseline")
            power_plan_name = scenario_spec.get("power_plan", None)
            
            result = self.run_scenario(
                scenario_spec["name"],
                scenario_spec["transition"],
                scenario_spec["physical"],
                market_name,
                power_plan_name,
            )
            results[scenario_spec["name"]] = result

            if scenario_spec["name"] == "baseline":
                baseline_result = result

        # Calculate financing impacts using counterfactual baseline
        # Counterfactual = A-rated (no-carbon world) for all scenarios including baseline
        plant_params = self._get_plant_params()
        financing_params = self._get_financing_params()
        total_capex = plant_params.get('total_capex_million', 3200) * 1e6

        # Get counterfactual rating (A = no carbon world)
        counterfactual_rating = get_counterfactual_baseline_rating()
        counterfactual_spread = counterfactual_rating.to_spread_bps()
        counterfactual_notch = counterfactual_rating.value

        for name, result in results.items():
            # Calculate counterfactual NPV loss (vs. no-carbon world)
            # For now, use baseline NPV as proxy for counterfactual NPV
            counterfactual_npv = baseline_result.metrics.npv if baseline_result else result.metrics.npv
            npv_loss = counterfactual_npv - result.metrics.npv

            if result.credit_rating:
                scenario_spread = result.credit_rating.overall_rating.to_spread_bps()
                scenario_notch = result.credit_rating.overall_rating.value

                result.financing = calculate_financing_with_counterfactual(
                    scenario_spread_bps=scenario_spread,
                    counterfactual_spread_bps=counterfactual_spread,
                    npv_loss=max(0, npv_loss),  # Floor at 0
                    total_capex=total_capex,
                    params=financing_params,
                    scenario_notch=scenario_notch,
                    counterfactual_notch=counterfactual_notch,
                )
            else:
                # Fallback to old linear model if no rating (shouldn't happen)
                el_pct = calculate_expected_loss(counterfactual_npv, result.metrics.npv, total_capex)
                result.financing = map_expected_loss_to_spreads(el_pct, npv_loss, financing_params)

        return results

    def export_results(
        self,
        results: Dict[str, ScenarioResult],
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Export scenario results to CSV files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Export cashflow time series for each scenario
        for name, result in results.items():
            cf_df = pd.DataFrame(result.cashflow.to_dict())
            cf_path = output_dir / f"cashflow_{name}.csv"
            cf_df.to_csv(cf_path, index=False)
            paths[f"cashflow_{name}"] = cf_path

        # Export summary metrics
        metrics_rows = []
        for name, result in results.items():
            row = {"scenario": name}
            row.update(result.metrics.to_dict())
            if result.financing:
                row.update(result.financing.to_dict())
            if result.credit_rating:
                row.update(result.credit_rating.to_dict())
            # Add counterfactual CRP data
            if result.counterfactual_crp:
                row["counterfactual_rating"] = result.counterfactual_crp.get("counterfactual_rating")
                row["counterfactual_spread_bps"] = result.counterfactual_crp.get("counterfactual_spread_bps")
                row["scenario_rating_new"] = result.counterfactual_crp.get("scenario_rating")
                row["scenario_spread_bps_new"] = result.counterfactual_crp.get("scenario_spread_bps")
                row["rating_migration"] = result.counterfactual_crp.get("rating_migration")
                row["notch_change"] = result.counterfactual_crp.get("notch_change")
                row["counterfactual_crp_bps"] = result.counterfactual_crp.get("crp_bps")
                row["is_investment_grade"] = result.counterfactual_crp.get("is_investment_grade")
                row["is_distressed"] = result.counterfactual_crp.get("is_distressed")
            metrics_rows.append(row)

        metrics_df = pd.DataFrame(metrics_rows)
        metrics_path = output_dir / "scenario_comparison.csv"
        metrics_df.to_csv(metrics_path, index=False)
        paths["scenario_comparison"] = metrics_path

        # Export credit rating summary
        rating_rows = []
        for name, result in results.items():
            if result.credit_rating:
                row = {"scenario": name}
                row.update(result.credit_rating.to_dict())
                rating_rows.append(row)

        if rating_rows:
            rating_df = pd.DataFrame(rating_rows)
            rating_path = output_dir / "credit_ratings.csv"
            rating_df.to_csv(rating_path, index=False)
            paths["credit_ratings"] = rating_path

        return paths
