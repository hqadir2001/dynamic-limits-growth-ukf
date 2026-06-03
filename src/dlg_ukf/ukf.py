"""Unscented Kalman Filter implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .model_spec import ModelSpec, measurement, transition


@dataclass
class UKFResult:
    periods: list[str]
    filtered_means: np.ndarray
    filtered_covariances: np.ndarray
    predicted_means: np.ndarray
    predicted_covariances: np.ndarray
    cross_covariances: np.ndarray
    fitted_values: np.ndarray
    residuals: np.ndarray
    nis: np.ndarray
    log_likelihood: float
    psd_repairs: dict[str, int]
    metadata: dict[str, Any]


def _as_square_matrix(matrix: np.ndarray, name: str) -> np.ndarray:
    mat = np.asarray(matrix, dtype=float)
    if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
        raise ValueError(f"{name} must be square, got shape {mat.shape}")
    if not np.isfinite(mat).all():
        raise ValueError(f"{name} contains non-finite values")
    return mat


def psd_project(matrix: np.ndarray, eps: float = 1.0e-9) -> tuple[np.ndarray, bool]:
    """Return a symmetric positive semi-definite matrix."""
    mat = _as_square_matrix(matrix, "matrix")
    sym = 0.5 * (mat + mat.T)
    vals, vecs = np.linalg.eigh(sym)
    repaired = bool(np.any(vals < eps))
    vals = np.maximum(vals, eps)
    out = vecs @ np.diag(vals) @ vecs.T
    out = 0.5 * (out + out.T)
    return out, repaired


def chol_factor(matrix: np.ndarray, eps: float = 1.0e-9) -> tuple[np.ndarray, np.ndarray, bool]:
    """Return Cholesky factor and stabilized matrix.

    The returned matrix is the exact matrix used for the factorization.
    """
    mat, repaired = psd_project(matrix, eps)
    eye = np.eye(mat.shape[0])
    jitter = 0.0

    for attempt in range(8):
        candidate = mat + eye * jitter
        try:
            chol = np.linalg.cholesky(candidate)
            return chol, candidate, bool(repaired or jitter > 0.0)
        except np.linalg.LinAlgError:
            jitter = eps if attempt == 0 else jitter * 10.0

    candidate = mat + eye * max(jitter, eps)
    chol = np.linalg.cholesky(candidate)
    return chol, candidate, True


def chol_solve_logdet(matrix: np.ndarray, rhs: np.ndarray, eps: float = 1.0e-9) -> tuple[np.ndarray, float, bool]:
    """Solve ``matrix x = rhs`` and return ``x``, log determinant, and repair flag."""
    rhs = np.asarray(rhs, dtype=float)
    chol, stable, repaired = chol_factor(matrix, eps)
    y = np.linalg.solve(chol, rhs)
    x = np.linalg.solve(chol.T, y)
    logdet = 2.0 * float(np.sum(np.log(np.diag(chol))))
    if not np.isfinite(x).all() or not np.isfinite(logdet):
        x = np.linalg.pinv(stable) @ rhs
        sign, ld = np.linalg.slogdet(stable)
        logdet = float(ld) if sign > 0 else float("nan")
        repaired = True
    return x, logdet, repaired


def solve_right_psd(matrix: np.ndarray, rhs_left: np.ndarray, eps: float = 1.0e-9) -> tuple[np.ndarray, np.ndarray, bool]:
    """Compute ``rhs_left @ inv(matrix)`` using a PSD-stabilized solve.

    Returns the solution, the stabilized matrix used, and whether any repair or
    fallback was required.
    """
    rhs = np.asarray(rhs_left, dtype=float)
    if rhs.ndim != 2:
        raise ValueError(f"rhs_left must be 2D, got {rhs.shape}")

    chol, stable, repaired = chol_factor(matrix, eps)
    if rhs.shape[1] != stable.shape[0]:
        raise ValueError(f"rhs_left shape {rhs.shape} incompatible with matrix shape {stable.shape}")

    try:
        tmp = np.linalg.solve(chol, rhs.T)
        sol_t = np.linalg.solve(chol.T, tmp)
        sol = sol_t.T
    except np.linalg.LinAlgError:
        sol = rhs @ np.linalg.pinv(stable)
        repaired = True

    if not np.isfinite(sol).all():
        sol = rhs @ np.linalg.pinv(stable)
        repaired = True

    return sol, stable, repaired


def sigma_points(
    x: np.ndarray,
    P: np.ndarray,
    alpha: float = 1.0e-3,
    beta: float = 2.0,
    kappa: float = 0.0,
    psd_eps: float = 1.0e-9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Construct Julier/Uhlmann sigma points."""
    x = np.asarray(x, dtype=float).reshape(-1)
    if not np.isfinite(x).all():
        raise ValueError("state vector contains non-finite values")

    P = _as_square_matrix(P, "P")
    if P.shape[0] != x.size:
        raise ValueError(f"P shape {P.shape} incompatible with state size {x.size}")

    n = x.size
    lam = alpha * alpha * (n + kappa) - n
    scale = n + lam
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError(f"Invalid UKF scaling: alpha={alpha}, kappa={kappa}, n={n}, scale={scale}")

    P_psd, repaired = psd_project(P, psd_eps)
    chol = np.linalg.cholesky(scale * P_psd)

    sigmas = np.empty((2 * n + 1, n), dtype=float)
    sigmas[0] = x
    for i in range(n):
        sigmas[i + 1] = x + chol[:, i]
        sigmas[n + i + 1] = x - chol[:, i]

    Wm = np.full(2 * n + 1, 1.0 / (2.0 * scale))
    Wc = Wm.copy()
    Wm[0] = lam / scale
    Wc[0] = lam / scale + (1.0 - alpha * alpha + beta)
    return sigmas, Wm, Wc, repaired


def _weighted_mean_cov(sigmas: np.ndarray, Wm: np.ndarray, Wc: np.ndarray, noise: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    sigmas = np.asarray(sigmas, dtype=float)
    Wm = np.asarray(Wm, dtype=float).reshape(-1)
    Wc = np.asarray(Wc, dtype=float).reshape(-1)

    if sigmas.ndim != 2:
        raise ValueError("sigmas must be 2D")
    if Wm.shape[0] != sigmas.shape[0] or Wc.shape[0] != sigmas.shape[0]:
        raise ValueError("weight lengths must match sigma count")

    mean = Wm @ sigmas
    diff = sigmas - mean
    cov = diff.T @ (diff * Wc[:, None])
    if noise is not None:
        cov = cov + _as_square_matrix(noise, "noise")
    return mean, 0.5 * (cov + cov.T)


def predict_step(x: np.ndarray, P: np.ndarray, t: int, spec: ModelSpec, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
    ukf_cfg = config.get("ukf", {})
    eps = float(ukf_cfg.get("psd_epsilon", 1.0e-9))

    sigmas, Wm, Wc, repaired_sigma = sigma_points(
        x,
        P,
        float(ukf_cfg.get("alpha", 1.0e-3)),
        float(ukf_cfg.get("beta", 2.0)),
        float(ukf_cfg.get("kappa", 0.0)),
        eps,
    )

    propagated = np.asarray([transition(s, t, spec.params) for s in sigmas], dtype=float)
    if propagated.shape != sigmas.shape:
        raise ValueError(f"transition returned shape {propagated.shape}, expected {sigmas.shape}")

    x_pred, P_pred = _weighted_mean_cov(propagated, Wm, Wc, spec.Q)
    P_pred, repaired_pred = psd_project(P_pred, eps)

    dx = sigmas - np.asarray(x, dtype=float).reshape(-1)
    dy = propagated - x_pred
    cross = dx.T @ (dy * Wc[:, None])

    repairs = {"predict_sigma": int(repaired_sigma), "predict_P": int(repaired_pred), "update_S": 0, "update_P": 0}
    return x_pred, P_pred, cross, repairs


def update_step(
    x_pred: np.ndarray,
    P_pred: np.ndarray,
    y_obs: np.ndarray,
    t: int,
    spec: ModelSpec,
    config: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float, dict[str, int]]:
    ukf_cfg = config.get("ukf", {})
    eps = float(ukf_cfg.get("psd_epsilon", 1.0e-9))

    x_pred = np.asarray(x_pred, dtype=float).reshape(-1)
    P_pred = _as_square_matrix(P_pred, "P_pred")
    y_obs = np.asarray(y_obs, dtype=float).reshape(-1)

    mask = np.isfinite(y_obs)
    yhat_full = measurement(x_pred, t, spec)
    if yhat_full.shape != y_obs.shape:
        raise ValueError(f"measurement shape {yhat_full.shape} does not match observation shape {y_obs.shape}")

    residual_full = y_obs - yhat_full
    if not mask.any():
        return x_pred, P_pred, yhat_full, residual_full, np.nan, 0.0, {"update_S": 0, "update_P": 0}

    sigmas, Wm, Wc, repaired_sigma = sigma_points(
        x_pred,
        P_pred,
        float(ukf_cfg.get("alpha", 1.0e-3)),
        float(ukf_cfg.get("beta", 2.0)),
        float(ukf_cfg.get("kappa", 0.0)),
        eps,
    )

    zsig = np.asarray([measurement(s, t, spec) for s in sigmas], dtype=float)
    if zsig.shape != (sigmas.shape[0], y_obs.size):
        raise ValueError(f"measurement sigma shape {zsig.shape} incompatible with observations {y_obs.size}")

    z_pred, S_full = _weighted_mean_cov(zsig, Wm, Wc, spec.R)
    S = S_full[np.ix_(mask, mask)]

    dx = sigmas - x_pred
    dz = zsig[:, mask] - z_pred[mask]
    Pxz = dx.T @ (dz * Wc[:, None])
    innovation = y_obs[mask] - z_pred[mask]

    solved, logdet, repaired_s_likelihood = chol_solve_logdet(S, innovation, eps)
    K, S_stable, repaired_s_gain = solve_right_psd(S, Pxz, eps)

    x_new = x_pred + K @ innovation
    P_new = P_pred - K @ S_stable @ K.T
    P_new, repaired_p = psd_project(P_new, eps)

    nis = float(innovation.T @ solved)
    ll = float(-0.5 * (len(innovation) * np.log(2.0 * np.pi) + logdet + nis))

    yhat = measurement(x_new, t, spec)
    resid = y_obs - yhat

    repairs = {
        "update_S": int(repaired_s_likelihood or repaired_s_gain or repaired_sigma),
        "update_P": int(repaired_p),
    }
    return x_new, P_new, yhat, resid, nis, ll, repairs


def run_filter(panel: pd.DataFrame, spec: ModelSpec, config: dict[str, Any]) -> UKFResult:
    obs = panel[spec.obs_physical].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    periods = panel["period"].astype(str).tolist()

    n_t = len(panel)
    n_x = len(spec.state_names)
    n_y = len(spec.obs_physical)

    if obs.shape != (n_t, n_y):
        raise ValueError(f"Observation matrix shape mismatch: {obs.shape}, expected {(n_t, n_y)}")

    xf = np.zeros((n_t, n_x))
    Pf = np.zeros((n_t, n_x, n_x))
    xp = np.zeros((n_t, n_x))
    Pp = np.zeros((n_t, n_x, n_x))
    C = np.zeros((n_t, n_x, n_x))
    fitted = np.zeros((n_t, n_y))
    resid = np.zeros((n_t, n_y))
    nis = np.full(n_t, np.nan)

    repairs = {"predict_sigma": 0, "predict_P": 0, "update_S": 0, "update_P": 0, "total": 0}
    ll = 0.0

    x = np.asarray(spec.x0, dtype=float).reshape(-1).copy()
    P = np.asarray(spec.P0, dtype=float).copy()

    if x.size != n_x:
        raise ValueError(f"Initial state size {x.size} does not match n_state {n_x}")
    if P.shape != (n_x, n_x):
        raise ValueError(f"Initial covariance shape {P.shape} does not match {(n_x, n_x)}")

    for t in range(n_t):
        if t == 0:
            x_pred, P_pred, cross = x, P, np.zeros_like(P)
            step_repairs = {"predict_sigma": 0, "predict_P": 0}
        else:
            x_pred, P_pred, cross, step_repairs = predict_step(x, P, t - 1, spec, config)

        x, P, yhat, err, nis_t, ll_t, update_repairs = update_step(x_pred, P_pred, obs[t], t, spec, config)

        xp[t], Pp[t], C[t] = x_pred, P_pred, cross
        xf[t], Pf[t] = x, P
        fitted[t], resid[t], nis[t] = yhat, err, nis_t

        if np.isfinite(ll_t):
            ll += ll_t

        for key, val in {**step_repairs, **update_repairs}.items():
            repairs[key] = repairs.get(key, 0) + int(val)

    repairs["total"] = sum(v for k, v in repairs.items() if k != "total")

    return UKFResult(
        periods=periods,
        filtered_means=xf,
        filtered_covariances=Pf,
        predicted_means=xp,
        predicted_covariances=Pp,
        cross_covariances=C,
        fitted_values=fitted,
        residuals=resid,
        nis=nis,
        log_likelihood=float(ll),
        psd_repairs=repairs,
        metadata={
            "update_logic": "single observed block with missing-observation masking",
            "stage_A_stage_B": "not split in modular scaffold; legacy notebook contains richer staged update logic",
            "stores_full_covariance": True,
        },
    )
