"""Session-based split manifest helpers.

Locked split manifests keep validation and test sessions stable while new
reviewed data is added to training by default.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

from .ingest import SessionInfo


SPLIT_VERSION = 1


def session_id_from_path(path: Path) -> str:
    """Return the stable session id used across raw and transformed files."""
    stem = Path(path).stem
    if stem.endswith("_transformed"):
        stem = stem[: -len("_transformed")]
    return stem


def session_id_from_info(session: SessionInfo) -> str:
    return session_id_from_path(session.csv_path)


def _stable_order(session_ids: Iterable[str], seed: str = "chewsense") -> list[str]:
    return sorted(
        set(session_ids),
        key=lambda sid: hashlib.sha256(f"{seed}:{sid}".encode()).hexdigest(),
    )


def load_split_manifest(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def save_split_manifest(manifest: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return path


def create_or_update_split_manifest(
    sessions: list[SessionInfo],
    output_path: Path,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.1,
    field_regression_session_ids: Iterable[str] | None = None,
) -> dict:
    """Create or update a locked split manifest.

    Existing validation/test assignments are preserved. New sessions default to
    train so routine field-test imports do not churn validation metrics.
    """
    output_path = Path(output_path)
    current_ids = {session_id_from_info(s) for s in sessions}
    now = datetime.now(timezone.utc).isoformat()

    if output_path.exists():
        manifest = load_split_manifest(output_path)
        splits = manifest.setdefault("splits", {})
        train = set(splits.get("train", [])) & current_ids
        validation = set(splits.get("validation_locked", [])) & current_ids
        test = set(splits.get("test_locked", [])) & current_ids
        assigned = train | validation | test
        train |= current_ids - assigned
        if current_ids and (not validation or not test) and len(current_ids) >= 3:
            ordered = _stable_order(train)
            if not test:
                n_test = max(1, int(round(len(current_ids) * test_ratio)))
                test = set(ordered[:n_test])
                train -= test
                ordered = [sid for sid in ordered if sid not in test]
            if not validation:
                n_val = max(1, int(round(len(current_ids) * validation_ratio)))
                validation = set(ordered[:n_val])
                train -= validation
        manifest["updated_at"] = now
    else:
        ordered = _stable_order(current_ids)
        n_total = len(ordered)
        n_test = max(1, int(round(n_total * test_ratio))) if n_total >= 3 else 0
        n_val = max(1, int(round(n_total * validation_ratio))) if n_total >= 3 else 0
        test = set(ordered[:n_test])
        validation = set(ordered[n_test : n_test + n_val])
        train = set(ordered[n_test + n_val :])
        manifest = {
            "version": SPLIT_VERSION,
            "created_at": now,
            "updated_at": now,
            "policy": {
                "unit": "session",
                "new_sessions_default": "train",
                "validation_ratio_on_first_create": validation_ratio,
                "test_ratio_on_first_create": test_ratio,
            },
        }

    field_regression = set(
        manifest.get("splits", {}).get("field_regression", [])
    ) & current_ids
    if field_regression_session_ids:
        field_regression |= set(field_regression_session_ids) & current_ids

    manifest["splits"] = {
        "train": sorted(train),
        "validation_locked": sorted(validation),
        "test_locked": sorted(test),
        "field_regression": sorted(field_regression),
    }
    save_split_manifest(manifest, output_path)
    return manifest


def indices_for_split(
    features_dir: Path,
    split_manifest_path: Path | None,
    split_name: str,
) -> np.ndarray | None:
    """Return feature-row indices for a split, or None when unavailable."""
    if split_name == "all":
        return None
    if split_manifest_path is None:
        return None

    features_dir = Path(features_dir)
    session_ids_path = features_dir / "session_ids.npy"
    if not session_ids_path.exists() or not Path(split_manifest_path).exists():
        return None

    session_ids = np.load(session_ids_path, allow_pickle=True).astype(str)
    manifest = load_split_manifest(Path(split_manifest_path))
    wanted = set(manifest.get("splits", {}).get(split_name, []))
    if not wanted:
        return np.array([], dtype=int)

    return np.flatnonzero(np.isin(session_ids, list(wanted)))
