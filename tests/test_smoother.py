from pathlib import Path

import numpy as np
import pandas as pd

from dlg_ukf.config import load_config
from dlg_ukf.data_validation import panel_window
from dlg_ukf.model_spec import compile_model_spec
from dlg_ukf.smoother import rts_smoother
from dlg_ukf.ukf import run_filter


ROOT = Path(__file__).resolve().parents[1]


def test_smoother():
    cfg = load_config(ROOT / "configs" / "baseline.yaml")
    df = pd.read_csv(ROOT / "data" / "sample" / "master_panel_sample.csv")
    panel = panel_window(df, "2003Q4", "2006Q3").head(5)
    spec = compile_model_spec(panel, cfg)
    result = run_filter(panel, spec, cfg)
    smooth = rts_smoother(result)
    assert smooth.smoothed_means.shape == result.filtered_means.shape
    assert np.isfinite(smooth.smoothed_means).all()
    assert "smoother_type" in smooth.metadata
    assert not smooth.metadata["mirrors_filtered_states"]

