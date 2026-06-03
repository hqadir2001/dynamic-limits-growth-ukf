"""Small I/O and provenance utilities."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "run"


def write_json(path: str | Path, obj: Any) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    return out


def write_text(path: str | Path, text: str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def write_csv(path: str | Path, frame: pd.DataFrame) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    return out


def package_versions(names: list[str] | None = None) -> dict[str, str]:
    names = names or ["numpy", "pandas", "matplotlib", "PyYAML"]
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def current_commit(project_root: str | Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(project_root),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_run_manifest(
    *,
    run_tag: str,
    project_root: str | Path,
    input_panel_path: str | Path,
    config_path: str | Path,
    outputs: dict[str, str],
    warnings: list[str],
    stability_status: str,
) -> dict[str, Any]:
    return {
        "run_tag": run_tag,
        "created_utc": utc_now(),
        "code_commit": current_commit(project_root),
        "input_panel_sha256": sha256_file(input_panel_path),
        "config_sha256": sha256_file(config_path) if config_path else "NO_CONFIG_FILE",
        "python_version": platform.python_version(),
        "package_versions": package_versions(["numpy", "pandas", "matplotlib"]),
        "outputs": outputs,
        "warnings": warnings,
        "stability_status": stability_status,
    }

