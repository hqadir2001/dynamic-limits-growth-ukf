"""UKF/RTS-style backward smoother.

This module implements a backward Rauch--Tung--Striebel-style smoother for
the additive-noise UKF output produced by :mod:`dlg_ukf.ukf`.

The smoother is not a filtered-state mirror: it uses the stored predicted
means/covariances and filtered-to-predicted cross-covariances from the
forward pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .ukf import UKFResult, psd_project, solve_right_psd


@dataclass
class SmootherResult:
    """Container for smoothed state paths and covariance matrices."""

    smoothed_means: np.ndarray
    smoothed_covariances: np.ndarray
    metadata: dict[str, Any]


def _validate_ukf_result(result: UKFResult) -> tuple[int, int]:
    """Validate that a UKFResult contains the arrays needed for smoothing."""
    arrays = {
        "filtered_means": result.filtered_means,
        "predicted_means": result.predicted_means,
        "filtered_covariances": result.filtered_covariances,
        "predicted_covariances": result.predicted_covariances,
        "cross_covariances": result.cross_covariances,
    }

    for name, arr in arrays.items():
        if not isinstance(arr, np.ndarray):
            raise TypeError(f"{name} must be a numpy array")
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} contains non-finite values")

    if result.filtered_means.ndim != 2:
        raise ValueError("filtered_means must have shape (T, n_state)")
    if result.predicted_means.shape != result.filtered_means.shape:
        raise ValueError("predicted_means shape must match filtered_means")

    T, n = result.filtered_means.shape
    expected_cov_shape = (T, n, n)
    for name in ("filtered_covariances", "predicted_covariances", "cross_covariances"):
        if arrays[name].shape != expected_cov_shape:
            raise ValueError(f"{name} must have shape {expected_cov_shape}, got {arrays[name].shape}")

    if T < 1:
        raise ValueError("Cannot smooth an empty filter result")
    return T, n


def rts_smoother(result: UKFResult, psd_eps: float = 1.0e-9) -> SmootherResult:
    """Run an additive-noise unscented RTS backward pass.

    The backward gain is

    ``G_t = C_t P_{t+1|t}^{-1}``

    where ``C_t`` is the stored filtered-to-predicted cross-covariance and
    ``P_{t+1|t}`` is the predicted covariance. The implementation solves this
    system with a PSD-projected Cholesky solve and only falls back to a
    pseudo-inverse inside ``solve_right_psd`` if needed.
    """
    T, _ = _validate_ukf_result(result)

    xs = result.filtered_means.copy()
    Ps = result.filtered_covariances.copy()

    repairs = 0
    solve_repairs = 0

    for t in range(T - 2, -1, -1):
        P_pred, repaired_pred = psd_project(result.predicted_covariances[t + 1], psd_eps)
        repairs += int(repaired_pred)

        gain, P_pred_stable, repaired_solve = solve_right_psd(
            P_pred,
            result.cross_covariances[t + 1],
            psd_eps,
        )
        solve_repairs += int(repaired_solve)

        innovation = xs[t + 1] - result.predicted_means[t + 1]
        xs[t] = result.filtered_means[t] + gain @ innovation

        cov_delta = Ps[t + 1] - P_pred_stable
        Ps[t] = result.filtered_covariances[t] + gain @ cov_delta @ gain.T
        Ps[t], repaired_ps = psd_project(Ps[t], psd_eps)
        repairs += int(repaired_ps)

    max_abs_delta = float(np.max(np.abs(xs - result.filtered_means))) if xs.size else 0.0
    mirrored = bool(np.allclose(xs, result.filtered_means, atol=1.0e-12, rtol=1.0e-12))

    return SmootherResult(
        smoothed_means=xs,
        smoothed_covariances=Ps,
        metadata={
            "smoother_type": "additive-noise-ukf-rts",
            "stored_full_covariance": bool(result.filtered_covariances.ndim == 3),
            "psd_repairs": int(repairs),
            "linear_solve_repairs": int(solve_repairs),
            "mirrors_filtered_states": mirrored,
            "max_abs_smoothed_minus_filtered": max_abs_delta,
            "algorithm_note": (
                "Backward RTS pass using UKF-predicted covariance and stored "
                "filtered-to-predicted cross-covariance. Uses PSD-projected "
                "Cholesky right-solve for the smoother gain."
            ),
        },
    )
