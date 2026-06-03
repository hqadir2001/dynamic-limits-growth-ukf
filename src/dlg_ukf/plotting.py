"""Matplotlib plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_fit(fitted: pd.DataFrame, residuals: pd.DataFrame, out_dir: str | Path, tag: str) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for col in [c for c in fitted.columns if c != "period"][:4]:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(fitted["period"], fitted[col], label="fitted")
        ax.plot(residuals["period"], residuals[col], label="residual", alpha=0.7)
        ax.set_title(col)
        ax.tick_params(axis="x", labelrotation=90)
        ax.legend()
        fig.tight_layout()
        path = out / f"fit_{col}_{tag}.png"
        fig.savefig(path, dpi=140)
        plt.close(fig)
        paths.append(str(path))
    return paths

