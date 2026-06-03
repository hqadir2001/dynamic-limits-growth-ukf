from pathlib import Path

import pandas as pd

from dlg_ukf.config import DEFAULT_REQUIRED_OBSERVABLES
from dlg_ukf.data_validation import validate_canonical_panel, validate_pb_identity


ROOT = Path(__file__).resolve().parents[1]


def test_panel_window():
    df = pd.read_csv(ROOT / "data" / "processed" / "master_panel_canonical.csv")
    result = validate_canonical_panel(df, start="2003Q4", end="2025Q2", required_observables=DEFAULT_REQUIRED_OBSERVABLES)
    assert result.rows == 87
    assert result.start == "2003Q4"
    assert result.end == "2025Q2"


def test_pb_identity():
    df = pd.read_csv(ROOT / "data" / "processed" / "master_panel_canonical.csv")
    validate_pb_identity(df)


def test_required_obs_complete():
    df = pd.read_csv(ROOT / "data" / "processed" / "master_panel_canonical.csv")
    validate_canonical_panel(df, start="2003Q4", end="2025Q2", required_observables=DEFAULT_REQUIRED_OBSERVABLES)

