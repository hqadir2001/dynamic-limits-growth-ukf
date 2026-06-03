"""YAML configuration loading and validation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REQUIRED_OBSERVABLES = [
    "logY_obs__sc",
    "y_gap_obs__sc",
    "pi_obs__sc",
    "U_obs__sc",
    "rS_obs__sc",
    "term_obs__sc",
    "hy_oas_obs__sc",
    "nfci_obs__sc",
    "vix_obs__sc",
    "debt_obs__sc",
    "pb_obs__sc",
    "nxY_obs__sc",
    "nfa_y_obs__sc",
    "cb_assets_obs__sc",
]


DEFAULT_CONFIG: dict[str, Any] = {
    "evaluation_window": {"start": "2003Q4", "end": "2025Q2"},
    "required_observables": DEFAULT_REQUIRED_OBSERVABLES,
    "identity_anchors": {
        "debt_obs__sc": "D_G_Y",
        "pb_obs__sc": "PB_GDP",
        "nxY_obs__sc": "NX_Y",
        "nfa_y_obs__sc": "NFA_to_Y",
        "cb_assets_obs__sc": "cb_assets_Y",
    },
    "ukf": {
        "alpha": 1.0e-3,
        "beta": 2.0,
        "kappa": 0.0,
        "q_scale": 0.02,
        "r_scale": 0.05,
        "p0_scale": 0.2,
        "psd_epsilon": 1.0e-9,
        "store_full_covariance": True,
    },
    "smoother": {"enabled": True, "type": "additive-noise-ukf-rts"},
    "outputs": {"run_tag": "baseline", "write_full_covariance": False},
    "freeze": {"FREEZE_REFRESH_MODE": False},
}


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def validate_config(config: dict[str, Any]) -> None:
    if "evaluation_window" not in config:
        raise ValueError("Config requires evaluation_window")
    for key in ["start", "end"]:
        if key not in config["evaluation_window"]:
            raise ValueError(f"Config requires evaluation_window.{key}")
    if not config.get("required_observables"):
        raise ValueError("Config requires required_observables")
    if config.get("freeze", {}).get("FREEZE_REFRESH_MODE") is True and not config.get("refresh_freeze_confirmed"):
        raise ValueError("FREEZE_REFRESH_MODE requires explicit refresh_freeze_confirmed opt-in")


def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if path:
        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        config = _merge(config, loaded)
    if overrides:
        config = _merge(config, overrides)
    validate_config(config)
    return config

