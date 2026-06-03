"""Repository path resolution."""

from __future__ import annotations

import os
from pathlib import Path


def infer_project_root(project_root: str | Path | None = None) -> Path:
    """Infer the project root, honoring explicit input and ``SPROJ_ROOT``."""
    if project_root:
        return Path(project_root).resolve()
    if os.environ.get("SPROJ_ROOT"):
        return Path(os.environ["SPROJ_ROOT"]).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data").exists() and (parent / "notebooks").exists():
            return parent
    return Path.cwd().resolve()


def resolve_data_path(project_root: str | Path | None = None, data_path: str | Path | None = None) -> Path:
    """Resolve the canonical panel path."""
    root = infer_project_root(project_root)
    if data_path:
        return Path(data_path).resolve()
    return root / "data" / "processed" / "master_panel_canonical.csv"


def resolve_results_dir(project_root: str | Path | None = None, results_dir: str | Path | None = None) -> Path:
    """Resolve and create the results directory."""
    root = infer_project_root(project_root)
    path = Path(results_dir).resolve() if results_dir else root / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path

