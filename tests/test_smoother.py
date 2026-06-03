from pathlib import Path

import numpy as np
import pandas as pd

from dlg_ukf.config import load_config
from dlg_ukf.data_validation import panel_window
from dlg_ukf.model_spec import compile_model_spec
from dlg_ukf.smoother import rts_smoother
from dlg_ukf.ukf import UKFResult, run_filter


ROOT = Path(__file__).resolve().parents[1]


def test_smoother_smoke_pipeline():
    cfg = load_config(ROOT / "configs" / "baseline.yaml")
    df = pd.read_csv(ROOT / "data" / "sample" / "master_panel_sample.csv")
    panel = panel_window(df, "2003Q4", "2006Q3").head(5)
    spec = compile_model_spec(panel, cfg)
    result = run_filter(panel, spec, cfg)
    smooth = rts_smoother(result)

    assert smooth.smoothed_means.shape == result.filtered_means.shape
    assert smooth.smoothed_covariances.shape == result.filtered_covariances.shape
    assert np.isfinite(smooth.smoothed_means).all()
    assert np.isfinite(smooth.smoothed_covariances).all()
    assert "smoother_type" in smooth.metadata
    assert not smooth.metadata["mirrors_filtered_states"]


def test_smoother_matches_manual_one_dimensional_backward_pass():
    periods = ["2000Q1", "2000Q2", "2000Q3"]
    filtered_means = np.array([[0.0], [1.0], [2.0]])
    filtered_covariances = np.array([[[1.0]], [[0.5]], [[0.25]]])
    predicted_means = np.array([[0.0], [0.2], [1.5]])
    predicted_covariances = np.array([[[1.0]], [[0.8]], [[0.6]]])
    cross_covariances = np.array([[[0.0]], [[0.4]], [[0.3]]])

    result = UKFResult(
        periods=periods,
        filtered_means=filtered_means,
        filtered_covariances=filtered_covariances,
        predicted_means=predicted_means,
        predicted_covariances=predicted_covariances,
        cross_covariances=cross_covariances,
        fitted_values=np.zeros((3, 1)),
        residuals=np.zeros((3, 1)),
        nis=np.zeros(3),
        log_likelihood=0.0,
        psd_repairs={"total": 0},
        metadata={},
    )

    smooth = rts_smoother(result, psd_eps=1.0e-12)

    # Manual scalar RTS equations:
    # t=1: G1 = 0.3 / 0.6 = 0.5; x1s = 1 + 0.5 * (2 - 1.5) = 1.25
    # t=0: G0 = 0.4 / 0.8 = 0.5; x0s = 0 + 0.5 * (1.25 - 0.2) = 0.525
    expected = np.array([[0.525], [1.25], [2.0]])
    assert np.allclose(smooth.smoothed_means, expected, atol=1.0e-10)
    assert not smooth.metadata["mirrors_filtered_states"]
    assert smooth.metadata["max_abs_smoothed_minus_filtered"] > 0.0
