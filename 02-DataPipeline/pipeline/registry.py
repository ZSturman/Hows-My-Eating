"""Local model registry helpers."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def make_model_id(dataset_hash: str | None = None, prefix: str = "chewnet") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if dataset_hash:
        return f"{prefix}-{timestamp}-{dataset_hash[:8]}"
    return f"{prefix}-{timestamp}"


def registry_root(repo_root: Path) -> Path:
    return Path(repo_root) / "02-DataPipeline" / "model_registry" / "runs"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(value, f, indent=2)


def _load_json_or_path(value: dict | Path | None) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    with open(value, "r") as f:
        return json.load(f)


def register_model(
    model_path: Path,
    repo_root: Path,
    config: Any,
    dataset_manifest: dict | Path | None = None,
    split_manifest: dict | Path | None = None,
    metrics: dict | None = None,
    model_id: str | None = None,
    coreml_path: Path | None = None,
) -> Path:
    """Create/update a local model registry entry."""
    model_path = Path(model_path)
    repo_root = Path(repo_root)

    dataset_data = _load_json_or_path(dataset_manifest)
    split_data = _load_json_or_path(split_manifest)
    dataset_hash = None
    if dataset_data:
        dataset_hash = dataset_data.get("dataset_hash")

    if model_id is None:
        model_id = make_model_id(dataset_hash)

    run_dir = registry_root(repo_root) / model_id
    run_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(model_path, run_dir / "chewnet.pth")
    if dataset_data is not None:
        _write_json(run_dir / "dataset_manifest.json", dataset_data)
    if split_data is not None:
        _write_json(run_dir / "split_manifest.json", split_data)
    if metrics is not None:
        _write_json(run_dir / "metrics.json", metrics)
    _write_json(run_dir / "runtime_config.json", config.to_dict().get("runtime", {}))

    export_status = {"normalization": "not_attempted", "coreml": "not_attempted"}
    try:
        from .export import export_normalization_json, generate_swift_constants

        export_normalization_json(model_path, run_dir / "chewnet_norm.json")
        generate_swift_constants(
            model_path,
            run_dir / "NormalizationConstants.swift",
            model_id=model_id,
        )
        export_status["normalization"] = "ok"
    except Exception as exc:  # Keep registry useful even without export tooling.
        export_status["normalization"] = f"failed: {exc}"

    if coreml_path and Path(coreml_path).exists():
        dest = run_dir / "ChewNet.mlpackage"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(coreml_path, dest)
        export_status["coreml"] = "copied"

    metadata = {
        "model_id": model_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_path": str(model_path),
        "dataset_hash": dataset_hash,
        "registry_dir": str(run_dir),
        "export_status": export_status,
    }
    _write_json(run_dir / "metadata.json", metadata)
    return run_dir


def latest_registry_entry(repo_root: Path) -> Path | None:
    root = registry_root(repo_root)
    if not root.exists():
        return None
    entries = [p for p in root.iterdir() if p.is_dir()]
    if not entries:
        return None
    return max(entries, key=lambda p: p.name)
