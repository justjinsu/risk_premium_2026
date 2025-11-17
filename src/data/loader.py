"""
Data loading and validation helpers for CSV inputs.
Replace placeholder logic with real schemas when inputs are defined.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
import csv


@dataclass
class Dataset:
    """Container for loaded input tables."""
    plant_params: Dict[str, Any]
    policy_scenarios: Dict[str, Any]
    physical_risks: Dict[str, Any]
    financing_params: Dict[str, Any]


def load_csv(path: Path, key_field: str | None = None) -> Dict[str, Any]:
    with path.open() as f:
        reader = csv.DictReader(f)
        if key_field:
            return {row[key_field]: row for row in reader}
        return {i: row for i, row in enumerate(reader)}


def load_inputs(base_dir: Path) -> Dataset:
    """
    Load baseline input CSV files.
    Expected files:
      - data/raw/plant.csv
      - data/raw/policy.csv
      - data/raw/physical.csv
      - data/raw/financing.csv
    """
    plant = load_csv(base_dir / "data" / "raw" / "plant.csv", key_field="parameter")
    policy = load_csv(base_dir / "data" / "raw" / "policy.csv", key_field="scenario")
    physical = load_csv(base_dir / "data" / "raw" / "physical.csv", key_field="scenario")
    financing = load_csv(base_dir / "data" / "raw" / "financing.csv", key_field="parameter")
    return Dataset(
        plant_params=plant,
        policy_scenarios=policy,
        physical_risks=physical,
        financing_params=financing
    )


def get_param_value(params: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """Helper to extract numeric value from parameter dict."""
    if key not in params:
        return default
    val = params[key].get("value", default)
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
