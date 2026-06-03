import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dlg_ukf.counterfactuals import parse_window
from dlg_ukf.historical_decomposition import build_historical_decomposition


ROOT = Path(__file__).resolve().parents[1]


def test_no_nonfinite_outputs(tmp_path):
    cmd = [sys.executable, str(ROOT / "scripts" / "run_pipeline.py"), "--config", "configs/baseline.yaml", "--smoke", "--results-dir", str(tmp_path)]
    subprocess.run(cmd, cwd=ROOT, check=True)
    run_dir = tmp_path / "baseline_smoke"
    for pattern in ["filtered_states_*.csv", "smoothed_states_*.csv", "fitted_values_*.csv", "residuals_*.csv"]:
        path = next(run_dir.glob(pattern))
        numeric = pd.read_csv(path).select_dtypes(include=["number"]).to_numpy(dtype=float)
        assert np.isfinite(numeric).all()
    assert (run_dir / "run_manifest.json").exists()
    assert json.loads((run_dir / "run_manifest.json").read_text())["outputs"]["smoothed_states"]


def test_counterfactual_window_parsing():
    assert parse_window("2020Q2", "2021Q4") == ("2020Q2", "2021Q4")
    with pytest.raises(ValueError):
        parse_window("2021Q4", "2020Q2")


def test_historical_decomp_reconciliation():
    fitted = pd.DataFrame({"period": ["2003Q4"], "x": [1.0]})
    _, report = build_historical_decomposition(["2003Q4"], fitted)
    assert report["status"] == "pass"

