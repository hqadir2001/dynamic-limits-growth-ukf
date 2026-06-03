"""Diagnostics and output tables for UKF runs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .smoother import SmootherResult
from .ukf import UKFResult


def states_frame(periods: list[str], state_names: list[str], values: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(values, columns=state_names)
    frame.insert(0, "period", periods)
    return frame


def covariance_diag_frame(periods: list[str], state_names: list[str], covariances: np.ndarray) -> pd.DataFrame:
    diag = np.asarray([np.diag(cov) for cov in covariances])
    frame = pd.DataFrame(diag, columns=[f"{name}_var" for name in state_names])
    frame.insert(0, "period", periods)
    return frame


def observable_frame(periods: list[str], obs_names: list[str], values: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(values, columns=obs_names)
    frame.insert(0, "period", periods)
    return frame


def residual_summary(residuals: pd.DataFrame, obs_names: list[str]) -> pd.DataFrame:
    rows = []
    for col in obs_names:
        values = pd.to_numeric(residuals[col], errors="coerce").to_numpy(dtype=float)
        rows.append(
            {
                "observable": col,
                "mean": float(np.nanmean(values)),
                "std": float(np.nanstd(values)),
                "rmse": float(np.sqrt(np.nanmean(values * values))),
                "max_abs": float(np.nanmax(np.abs(values))),
            }
        )
    return pd.DataFrame(rows)


def residual_acf(residuals: pd.DataFrame, obs_names: list[str], max_lag: int = 4) -> pd.DataFrame:
    rows = []
    for col in obs_names:
        values = pd.to_numeric(residuals[col], errors="coerce").to_numpy(dtype=float)
        values = values - np.nanmean(values)
        for lag in range(1, max_lag + 1):
            left = values[:-lag]
            right = values[lag:]
            if len(values) <= lag or len(left) < 2 or np.nanstd(left) == 0.0 or np.nanstd(right) == 0.0:
                acf = 0.0
            else:
                acf = float(np.corrcoef(left, right)[0, 1])
            rows.append({"observable": col, "lag": lag, "acf": acf})
    return pd.DataFrame(rows)


def outlier_quarters(residuals: pd.DataFrame, obs_names: list[str], top_n: int = 25) -> pd.DataFrame:
    rows = []
    for _, row in residuals.iterrows():
        for col in obs_names:
            rows.append({"period": row["period"], "observable": col, "abs_residual": abs(float(row[col]))})
    return pd.DataFrame(rows).sort_values("abs_residual", ascending=False).head(top_n)


def stability_report(result: UKFResult, smoother: SmootherResult) -> dict[str, object]:
    filtered_finite = bool(np.isfinite(result.filtered_means).all())
    smoothed_finite = bool(np.isfinite(smoother.smoothed_means).all())
    cov_finite = bool(np.isfinite(result.filtered_covariances).all() and np.isfinite(smoother.smoothed_covariances).all())

    nis_values = result.nis[np.isfinite(result.nis)]
    max_nis = float(np.max(nis_values)) if len(nis_values) else np.nan
    mean_nis = float(np.mean(nis_values)) if len(nis_values) else np.nan

    smoother_mirrors = bool(smoother.metadata.get("mirrors_filtered_states", False))
    psd_total = int(result.psd_repairs.get("total", 0)) + int(smoother.metadata.get("psd_repairs", 0))

    warnings = []
    if smoother_mirrors and len(result.periods) > 1:
        warnings.append("Smoother output mirrors filtered states on a multi-period run.")
    if psd_total > 0:
        warnings.append(f"PSD repairs occurred: total={psd_total}")
    if np.isfinite(max_nis) and max_nis > 1.0e4:
        warnings.append(f"Very large NIS detected: max_nis={max_nis}")

    status = "pass" if (filtered_finite and smoothed_finite and cov_finite and not smoother_mirrors) else "fail"
    if status == "pass" and warnings:
        status = "warn"

    return {
        "status": status,
        "filtered_finite": filtered_finite,
        "smoothed_finite": smoothed_finite,
        "covariance_finite": cov_finite,
        "log_likelihood": result.log_likelihood,
        "nis_count": int(len(nis_values)),
        "nis_mean": mean_nis,
        "nis_max": max_nis,
        "psd_repairs_filter": result.psd_repairs,
        "psd_repairs_smoother": int(smoother.metadata.get("psd_repairs", 0)),
        "smoother_metadata": smoother.metadata,
        "warnings": warnings,
    }


def nis_summary(result: UKFResult) -> pd.DataFrame:
    values = result.nis[np.isfinite(result.nis)]
    return pd.DataFrame(
        [
            {
                "count": int(len(values)),
                "mean": float(np.mean(values)) if len(values) else np.nan,
                "max": float(np.max(values)) if len(values) else np.nan,
                "p95": float(np.percentile(values, 95)) if len(values) else np.nan,
            }
        ]
    )


def output_integrity_check(frames: dict[str, pd.DataFrame]) -> list[str]:
    warnings: list[str] = []
    for name, frame in frames.items():
        numeric = frame.select_dtypes(include=["number"])
        if not np.isfinite(numeric.to_numpy(dtype=float)).all():
            warnings.append(f"Non-finite values detected in {name}")
    return warnings
