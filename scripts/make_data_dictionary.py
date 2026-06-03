"""Generate scaffolded data dictionaries from the canonical panel."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dlg_ukf.config import DEFAULT_REQUIRED_OBSERVABLES
from dlg_ukf.identity_anchors import IDENTITY_ANCHORS


def build_dictionary(panel_path: Path) -> pd.DataFrame:
    cols = pd.read_csv(panel_path, nrows=1).columns.tolist()
    required_physical = set(IDENTITY_ANCHORS.values())
    required_logical = set(DEFAULT_REQUIRED_OBSERVABLES)
    rows = []
    for col in cols:
        required_status = "required_identity_anchor" if col in required_physical else "required_observable" if col in required_logical else "supporting_or_derived"
        rows.append(
            {
                "column": col,
                "description": "TODO_VERIFY",
                "unit": "TODO_VERIFY",
                "source": "TODO_VERIFY",
                "transformation": "TODO_VERIFY",
                "required_status": required_status,
                "notes": "Generated scaffold; verify source/unit/description before citation.",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    panel = ROOT / "data" / "processed" / "master_panel_canonical.csv"
    frame = build_dictionary(panel)
    for out in [ROOT / "data" / "data_dictionary.csv", ROOT / "docs" / "DATA_DICTIONARY.csv"]:
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(out, index=False)
    print(f"Wrote {len(frame)} rows")


if __name__ == "__main__":
    main()

