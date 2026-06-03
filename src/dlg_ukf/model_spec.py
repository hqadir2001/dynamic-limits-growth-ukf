"""Semi-structural model specification used by the UKF pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .identity_anchors import resolve_observable_aliases


STATE_NAMES = [
    "logY",
    "y_gap",
    "pi",
    "U",
    "rS",
    "term",
    "hy_oas",
    "nfci",
    "vix",
    "debt",
    "pb",
    "nx",
    "nfa",
    "cb_assets",
    "growth_limit",
    "fragility",
    "policy_rigidity",
    "complacency",
]


@dataclass(frozen=True)
class ModelParams:
    """Calibrated/semi-structural parameters for the state transition."""

    rho_macro: float = 0.86
    rho_financial: float = 0.78
    rho_anchor: float = 0.90
    debt_feedback: float = 0.015
    pb_feedback: float = 0.010
    stress_feedback: float = 0.025
    cb_feedback: float = 0.012


@dataclass(frozen=True)
class ModelSpec:
    state_names: list[str]
    obs_logical: list[str]
    obs_physical: list[str]
    alias_map: dict[str, str]
    params: ModelParams
    x0: np.ndarray
    Q: np.ndarray
    R: np.ndarray
    P0: np.ndarray


def _z(value: Any, fallback: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return fallback
    return out if np.isfinite(out) else fallback


def initial_state(panel: pd.DataFrame, alias_map: dict[str, str]) -> np.ndarray:
    first = panel.iloc[0]
    by_state = {
        "logY": alias_map.get("logY_obs__sc", "logY_obs__sc"),
        "y_gap": alias_map.get("y_gap_obs__sc", "y_gap_obs__sc"),
        "pi": alias_map.get("pi_obs__sc", "pi_obs__sc"),
        "U": alias_map.get("U_obs__sc", "U_obs__sc"),
        "rS": alias_map.get("rS_obs__sc", "rS_obs__sc"),
        "term": alias_map.get("term_obs__sc", "term_obs__sc"),
        "hy_oas": alias_map.get("hy_oas_obs__sc", "hy_oas_obs__sc"),
        "nfci": alias_map.get("nfci_obs__sc", "nfci_obs__sc"),
        "vix": alias_map.get("vix_obs__sc", "vix_obs__sc"),
        "debt": alias_map.get("debt_obs__sc", "D_G_Y"),
        "pb": alias_map.get("pb_obs__sc", "PB_GDP"),
        "nx": alias_map.get("nxY_obs__sc", "NX_Y"),
        "nfa": alias_map.get("nfa_y_obs__sc", "NFA_to_Y"),
        "cb_assets": alias_map.get("cb_assets_obs__sc", "cb_assets_Y"),
    }
    values = [_z(first.get(by_state.get(name, ""), 0.0)) for name in STATE_NAMES[:14]]
    stress = float(np.nanmean(np.abs(values[1:9])))
    values.extend([values[1] - values[9], stress, values[13], -stress])
    return np.asarray(values, dtype=float)


def transition(x: np.ndarray, t: int, params: ModelParams) -> np.ndarray:
    """Nonlinear 18-state transition preserving the notebook's semi-structural intent."""
    y = np.asarray(x, dtype=float).copy()
    out = y.copy()
    out[0] = y[0] + 0.02 * y[1] - 0.01 * y[15]
    out[1] = params.rho_macro * y[1] - 0.04 * y[3] - params.stress_feedback * y[15]
    out[2] = params.rho_macro * y[2] + 0.03 * y[1] - 0.01 * y[10]
    out[3] = params.rho_macro * y[3] - 0.03 * y[1] + 0.02 * y[15]
    out[4] = params.rho_macro * y[4] + 0.02 * y[2]
    out[5] = params.rho_macro * y[5] + 0.01 * y[16]
    out[6] = params.rho_financial * y[6] + 0.05 * y[15]
    out[7] = params.rho_financial * y[7] + 0.04 * y[15]
    out[8] = params.rho_financial * y[8] + 0.03 * abs(y[15])
    out[9] = params.rho_anchor * y[9] - params.pb_feedback * y[10] + params.debt_feedback * y[16]
    out[10] = params.rho_anchor * y[10] + 0.02 * y[1] - 0.01 * (y[9] - np.nanmedian([y[9], 0.0]))
    out[11] = params.rho_anchor * y[11] + 0.01 * y[1]
    out[12] = params.rho_anchor * y[12] + 0.03 * y[11]
    out[13] = params.rho_anchor * y[13] + params.cb_feedback * y[15]
    out[14] = 0.92 * y[14] - 0.03 * y[9] + 0.02 * y[11]
    out[15] = 0.80 * y[15] + 0.04 * y[6] + 0.04 * y[7] + 0.02 * y[8]
    out[16] = 0.88 * y[16] + 0.02 * y[9] + 0.02 * y[13]
    out[17] = 0.84 * y[17] - 0.02 * y[15] + 0.01 * y[1]
    return out


def measurement(x: np.ndarray, t: int, spec: ModelSpec) -> np.ndarray:
    """Map state vector to the observable vector."""
    del t, spec
    return np.asarray(x[:14], dtype=float)


def measurement_consistency_residuals(x: np.ndarray, observed: np.ndarray, spec: ModelSpec) -> dict[str, float]:
    fitted = measurement(x, 0, spec)
    return {
        f"res_{logical}": float(obs - fit)
        for logical, obs, fit in zip(spec.obs_logical, observed, fitted)
        if np.isfinite(obs)
    }


def compile_model_spec(panel: pd.DataFrame, config: dict[str, Any], params: ModelParams | None = None) -> ModelSpec:
    params = params or ModelParams()
    obs_logical = list(config["required_observables"])
    alias_map = resolve_observable_aliases(obs_logical, panel.columns.tolist())
    obs_physical = [alias_map[name] for name in obs_logical]
    x0 = initial_state(panel, alias_map)
    ukf_cfg = config.get("ukf", {})
    q = float(ukf_cfg.get("q_scale", 0.02))
    r = float(ukf_cfg.get("r_scale", 0.05))
    p0 = float(ukf_cfg.get("p0_scale", 0.2))
    return ModelSpec(
        state_names=list(STATE_NAMES),
        obs_logical=obs_logical,
        obs_physical=obs_physical,
        alias_map=alias_map,
        params=params,
        x0=x0,
        Q=np.eye(len(STATE_NAMES)) * q,
        R=np.eye(len(obs_logical)) * r,
        P0=np.eye(len(STATE_NAMES)) * p0,
    )

