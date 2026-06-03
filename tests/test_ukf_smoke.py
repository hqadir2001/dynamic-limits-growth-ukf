from pathlib import Path

import numpy as np
import pandas as pd

from dlg_ukf.config import load_config
from dlg_ukf.data_validation import panel_window
from dlg_ukf.model_spec import compile_model_spec
from dlg_ukf.ukf import psd_project, run_filter, sigma_points


ROOT = Path(__file__).resolve().parents[1]


def test_sigma_points():
    x = np.zeros(4)
    P = np.eye(4)
    sig, *_ = sigma_points(x, P)
    assert sig.shape == (9, 4)


def test_psd_project():
    M, _ = psd_project(np.array([[1.0, 2.0], [2.0, 1.0]]))
    assert np.allclose(M, M.T)
    assert np.linalg.eigvalsh(M).min() >= -1.0e-12


def test_ukf_smoke():
    cfg = load_config(ROOT / "configs" / "baseline.yaml")
    df = pd.read_csv(ROOT / "data" / "sample" / "master_panel_sample.csv")
    panel = panel_window(df, "2003Q4", "2006Q3").head(5)
    spec = compile_model_spec(panel, cfg)
    result = run_filter(panel, spec, cfg)
    assert result.filtered_means.shape == (5, 18)
    assert np.isfinite(result.filtered_means).all()

