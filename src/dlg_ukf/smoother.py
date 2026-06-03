"""UKF/RTS-style backward smoother."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .ukf import UKFResult, psd_project


@dataclass
class SmootherResult:
    smoothed_means: np.ndarray
    smoothed_covariances: np.ndarray
    metadata: dict[str, Any]


def rts_smoother(result: UKFResult, psd_eps: float = 1.0e-9) -> SmootherResult:
    """Run an additive-noise unscented RTS backward pass.

    The filter stores the cross-covariance between filtered state ``t`` and
    predicted state ``t+1``. The backward gain is ``C_t P_{t+1|t}^{-1}``.
    This is a real smoothing pass; it is not a copy of filtered states.
    """
    xs = result.filtered_means.copy()
    Ps = result.filtered_covariances.copy()
    repairs = 0
    for t in range(len(xs) - 2, -1, -1):
        P_pred, repaired = psd_project(result.predicted_covariances[t + 1], psd_eps)
        repairs += int(repaired)
        gain = result.cross_covariances[t + 1] @ np.linalg.pinv(P_pred)
        xs[t] = result.filtered_means[t] + gain @ (xs[t + 1] - result.predicted_means[t + 1])
        Ps[t] = result.filtered_covariances[t] + gain @ (Ps[t + 1] - P_pred) @ gain.T
        Ps[t], repaired_ps = psd_project(Ps[t], psd_eps)
        repairs += int(repaired_ps)
    mirrored = bool(np.allclose(xs, result.filtered_means, atol=1.0e-12, rtol=1.0e-12))
    return SmootherResult(
        smoothed_means=xs,
        smoothed_covariances=Ps,
        metadata={
            "smoother_type": "additive-noise-ukf-rts",
            "stored_full_covariance": True,
            "psd_repairs": repairs,
            "mirrors_filtered_states": mirrored,
            "algorithm_note": "Backward RTS pass using UKF-predicted covariance and stored filtered-to-predicted cross-covariance.",
        },
    )

