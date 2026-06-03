from pathlib import Path

import pandas as pd

from dlg_ukf.config import load_config
from dlg_ukf.data_validation import panel_window
from dlg_ukf.model_spec import compile_model_spec, measurement, transition


ROOT = Path(__file__).resolve().parents[1]


def _spec():
    cfg = load_config(ROOT / "configs" / "baseline.yaml")
    df = pd.read_csv(ROOT / "data" / "processed" / "master_panel_canonical.csv")
    panel = panel_window(df, "2003Q4", "2025Q2").head(5)
    return compile_model_spec(panel, cfg)


def test_transition_shape():
    spec = _spec()
    assert transition(spec.x0, 0, spec.params).shape == (18,)


def test_measurement_shape():
    spec = _spec()
    assert measurement(spec.x0, 0, spec).shape == (len(spec.obs_physical),)

