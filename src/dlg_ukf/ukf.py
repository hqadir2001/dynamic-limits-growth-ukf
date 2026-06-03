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


def psd_project(matrix: np.ndarray, eps: float = 1.0e-9) -> tuple[np.ndarray, bool]:
    """Return a symmetric positive semi-definite matrix."""
    sym = 0.5 * (np.asarray(matrix, dtype=float) + np.asarray(matrix, dtype=float).T)
    vals, vecs = np.linalg.eigh(sym)
    repaired = bool(np.any(vals < eps))
    vals = np.maximum(vals, eps)
    return (vecs @ np.diag(vals) @ vecs.T + (vecs @ np.diag(vals) @ vecs.T).T) * 0.5, repaired


def chol_solve_logdet(matrix: np.ndarray, rhs: np.ndarray, eps: float = 1.0e-9) -> tuple[np.ndarray, float, bool]:
    mat, repaired = psd_project(matrix, eps)
    jitter = eps
    for _ in range(6):
        try:
            chol = np.linalg.cholesky(mat + np.eye(mat.shape[0]) * jitter)
            y = np.linalg.solve(chol, rhs)
            x = np.linalg.solve(chol.T, y)
            logdet = 2.0 * float(np.sum(np.log(np.diag(chol))))
            return x, logdet, repaired
        except np.linalg.LinAlgError:
            jitter *= 10.0
            repaired = True
    return np.linalg.pinv(mat) @ rhs, float(np.linalg.slogdet(mat)[1]), True


def sigma_points(
    x: np.ndarray,
    P: np.ndarray,
    alpha: float = 1.0e-3,
    beta: float = 2.0,
    kappa: float = 0.0,
    psd_eps: float = 1.0e-9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    n = len(x)
    lam = alpha * alpha * (n + kappa) - n
    scale = n + lam
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
    mean = Wm @ sigmas
    diff = sigmas - mean
    cov = diff.T @ (diff * Wc[:, None])
    if noise is not None:
        cov = cov + noise
    return mean, cov


def predict_step(x: np.ndarray, P: np.ndarray, t: int, spec: ModelSpec, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
    ukf_cfg = config.get("ukf", {})
    sigmas, Wm, Wc, repaired_sigma = sigma_points(
        x,
        P,
        float(ukf_cfg.get("alpha", 1.0e-3)),
        float(ukf_cfg.get("beta", 2.0)),
        float(ukf_cfg.get("kappa", 0.0)),
        float(ukf_cfg.get("psd_epsilon", 1.0e-9)),
    )
    propagated = np.asarray([transition(s, t, spec.params) for s in sigmas])
    x_pred, P_pred = _weighted_mean_cov(propagated, Wm, Wc, spec.Q)
    P_pred, repaired_pred = psd_project(P_pred, float(ukf_cfg.get("psd_epsilon", 1.0e-9)))
    dx = sigmas - x
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
    mask = np.isfinite(y_obs)
    yhat_full = measurement(x_pred, t, spec)
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
    zsig = np.asarray([measurement(s, t, spec) for s in sigmas])
    z_pred, S_full = _weighted_mean_cov(zsig, Wm, Wc, spec.R)
    S = S_full[np.ix_(mask, mask)]
    dx = sigmas - x_pred
    dz = zsig[:, mask] - z_pred[mask]
    Pxz = dx.T @ (dz * Wc[:, None])
    innovation = y_obs[mask] - z_pred[mask]
    solved, logdet, repaired_s = chol_solve_logdet(S, innovation, eps)
    K = Pxz @ np.linalg.pinv(S)
    x_new = x_pred + K @ innovation
    P_new = P_pred - K @ S @ K.T
    P_new, repaired_p = psd_project(P_new, eps)
    nis = float(innovation.T @ solved)
    ll = -0.5 * (len(innovation) * np.log(2.0 * np.pi) + logdet + nis)
    yhat = measurement(x_new, t, spec)
    resid = y_obs - yhat
    repairs = {"update_S": int(repaired_s or repaired_sigma), "update_P": int(repaired_p)}
    return x_new, P_new, yhat, resid, nis, float(ll), repairs


def run_filter(panel: pd.DataFrame, spec: ModelSpec, config: dict[str, Any]) -> UKFResult:
    obs = panel[spec.obs_physical].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    periods = panel["period"].astype(str).tolist()
    n_t = len(panel)
    n_x = len(spec.state_names)
    n_y = len(spec.obs_physical)
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
    x = spec.x0
    P = spec.P0
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
        metadata={"update_logic": "single observed block with missing-observation masking", "stage_A_stage_B": "not split in package smoke pipeline"},
    )

