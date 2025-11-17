"""
Class-based orchestration for CRP runs using CSV inputs and CSV/plot outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

from src.data import load_inputs, get_param_value
from src.scenarios import TransitionScenario, PhysicalScenario
from src.risk import apply_transition, apply_physical, map_expected_loss_to_spreads, calculate_expected_loss, FinancingImpact
from src.financials import compute_cashflows_timeseries, calculate_metrics, CashFlowTimeSeries, FinancialMetrics


@dataclass
class ScenarioResult:
    """Results for a single scenario."""
    scenario_name: str
    cashflow: CashFlowTimeSeries
    metrics: FinancialMetrics
    financing: FinancingImpact | None = None  # Only for risk scenarios


class CRPModelRunner:
    """
    Orchestrates loading CSV inputs, applying risk adjustments, and exporting outputs.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.dataset = load_inputs(self.base_dir)

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
        """Load transition scenario from CSV."""
        row = self.dataset.policy_scenarios.get(scenario_name)
        if not row:
            raise ValueError(f"Transition scenario '{scenario_name}' not found")

        return TransitionScenario(
            name=scenario_name,
            dispatch_priority_penalty=float(row.get('dispatch_penalty', 0)),
            retirement_years=int(float(row.get('retirement_years', 40))),
            carbon_price_2025=float(row.get('carbon_price_2025', 0)),
            carbon_price_2030=float(row.get('carbon_price_2030', 0)),
            carbon_price_2040=float(row.get('carbon_price_2040', 0)),
            carbon_price_2050=float(row.get('carbon_price_2050', 0)),
        )

    def _load_physical_scenario(self, scenario_name: str) -> PhysicalScenario:
        """Load physical scenario from CSV."""
        row = self.dataset.physical_risks.get(scenario_name)
        if not row:
            raise ValueError(f"Physical scenario '{scenario_name}' not found")

        return PhysicalScenario(
            name=scenario_name,
            wildfire_outage_rate=float(row.get('wildfire_outage_rate', 0)),
            drought_derate=float(row.get('drought_derate', 0)),
            cooling_temp_penalty=float(row.get('cooling_temp_penalty', 0)),
        )

    def run_scenario(
        self,
        scenario_name: str,
        transition_scenario_name: str = "baseline",
        physical_scenario_name: str = "baseline",
    ) -> ScenarioResult:
        """Run a single scenario."""
        plant_params = self._get_plant_params()

        transition_scenario = self._load_transition_scenario(transition_scenario_name)
        physical_scenario = self._load_physical_scenario(physical_scenario_name)

        transition_adj = apply_transition(plant_params, transition_scenario)
        physical_adj = apply_physical(plant_params, physical_scenario)

        cashflow = compute_cashflows_timeseries(
            plant_params,
            transition_scenario,
            transition_adj,
            physical_adj,
        )

        metrics = calculate_metrics(cashflow, plant_params)

        return ScenarioResult(
            scenario_name=scenario_name,
            cashflow=cashflow,
            metrics=metrics,
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
                {"name": "baseline", "transition": "baseline", "physical": "baseline"},
                {"name": "moderate_transition", "transition": "moderate_transition", "physical": "baseline"},
                {"name": "aggressive_transition", "transition": "aggressive_transition", "physical": "baseline"},
                {"name": "moderate_physical", "transition": "baseline", "physical": "moderate_physical"},
                {"name": "high_physical", "transition": "baseline", "physical": "high_physical"},
                {"name": "combined_moderate", "transition": "moderate_transition", "physical": "moderate_physical"},
                {"name": "combined_aggressive", "transition": "aggressive_transition", "physical": "high_physical"},
            ]

        results = {}
        baseline_result = None

        # Run all scenarios
        for scenario_spec in scenarios:
            result = self.run_scenario(
                scenario_spec["name"],
                scenario_spec["transition"],
                scenario_spec["physical"],
            )
            results[scenario_spec["name"]] = result

            if scenario_spec["name"] == "baseline":
                baseline_result = result

        # Calculate financing impacts for risk scenarios
        if baseline_result:
            plant_params = self._get_plant_params()
            financing_params = self._get_financing_params()
            total_capex = plant_params.get('total_capex_million', 3200) * 1e6
            baseline_npv = baseline_result.metrics.npv

            for name, result in results.items():
                if name != "baseline":
                    risk_npv = result.metrics.npv
                    el_pct = calculate_expected_loss(baseline_npv, risk_npv, total_capex)
                    npv_loss = baseline_npv - risk_npv
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
            metrics_rows.append(row)

        metrics_df = pd.DataFrame(metrics_rows)
        metrics_path = output_dir / "scenario_comparison.csv"
        metrics_df.to_csv(metrics_path, index=False)
        paths["scenario_comparison"] = metrics_path

        return paths
