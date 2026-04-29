"""Import real-world app field-test bundles as labeled training sessions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_MOTION_COLUMNS = ["timestamp", "ax", "ay", "az", "gx", "gy", "gz"]
LABELED_MOTION_FILE = "labeled_motion.csv"


@dataclass
class ImportedFieldSession:
    session_id: str
    output_dir: Path
    csv_path: Path
    event_type: str
    corrected_state: str
    rows: int
    source_bundle: Path


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    slug = slug.strip("-")
    return slug or "session"


def _find_bundles(input_dir: Path) -> list[Path]:
    input_dir = Path(input_dir)
    if _is_bundle(input_dir):
        return [input_dir]
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_dir() and _is_bundle(p)
    )


def _is_bundle(path: Path) -> bool:
    return (path / LABELED_MOTION_FILE).exists() or (
        (path / "motion.csv").exists() and (path / "feedback.csv").exists()
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _truth_from_feedback(row: pd.Series) -> bool | None:
    corrected = str(row.get("corrected_state", "")).strip().lower()
    event_type = str(row.get("event_type", "")).strip().lower()

    if corrected in {"chewing", "chew", "true", "1"}:
        return True
    if corrected in {"idle", "not_chewing", "not-chewing", "false", "0"}:
        return False
    if event_type == "false_positive":
        return False
    if event_type == "missed_chew":
        return True
    if event_type == "correct":
        predicted = str(row.get("predicted_state", "")).strip().lower()
        if predicted == "chewing":
            return True
        if predicted in {"idle", "not_chewing", "not-chewing"}:
            return False
    return None


def _label_series_to_bool(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    truthy = {"true", "1", "yes", "y", "chewing", "chew"}
    falsy = {"false", "0", "no", "n", "idle", "not_chewing", "not-chewing"}

    def parse(value: str) -> bool:
        if value in truthy:
            return True
        if value in falsy:
            return False
        try:
            return bool(float(value))
        except Exception as exc:
            raise ValueError(f"Unrecognized label value: {value!r}") from exc

    return normalized.map(parse)


def _window_bounds(row: pd.Series, padding_sec: float) -> tuple[float | None, float | None]:
    try:
        start = float(row.get("window_start"))
        end = float(row.get("window_end"))
        if end >= start:
            return start, end
    except Exception:
        pass

    try:
        ts = float(row.get("motion_timestamp"))
        return ts - padding_sec, ts + padding_sec
    except Exception:
        return None, None


def import_field_test_bundles(
    input_dir: Path,
    output_dir: Path,
    manifest_dir: Path,
    padding_sec: float = 0.75,
) -> dict[str, Any]:
    """Convert app feedback windows into labeled session folders."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    manifest_dir = Path(manifest_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    bundles = _find_bundles(input_dir) if input_dir.exists() else []
    imported: list[ImportedFieldSession] = []
    skipped: list[dict[str, Any]] = []

    for bundle in bundles:
        metadata = _read_json(bundle / "session_metadata.json")

        labeled_motion_path = bundle / LABELED_MOTION_FILE
        if labeled_motion_path.exists():
            labeled_motion = pd.read_csv(labeled_motion_path)
            required = REQUIRED_MOTION_COLUMNS + ["label"]
            missing = [c for c in required if c not in labeled_motion.columns]
            if missing:
                skipped.append({
                    "bundle": str(bundle),
                    "reason": f"{LABELED_MOTION_FILE} missing columns: {missing}",
                })
                continue

            reviewed = labeled_motion[required].copy()
            reviewed["timestamp"] = reviewed["timestamp"].astype(float)
            try:
                reviewed["label"] = _label_series_to_bool(reviewed["label"])
            except ValueError as exc:
                skipped.append({
                    "bundle": str(bundle),
                    "reason": str(exc),
                })
                continue

            bundle_slug = _safe_slug(metadata.get("session_id") or bundle.name)
            prefix = "Eating" if reviewed["label"].mean() > 0.5 else "Not-eating"
            session_id = _safe_slug(f"{prefix}-field-reviewed-{bundle_slug}")
            session_dir = output_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            csv_path = session_dir / f"{session_id}.csv"
            reviewed.to_csv(csv_path, index=False)

            event_metadata = {
                "session_id": session_id,
                "source_bundle": str(bundle),
                "source_metadata": metadata,
                "source_file": LABELED_MOTION_FILE,
                "rows": int(len(reviewed)),
                "label_mean": float(reviewed["label"].mean()),
                "imported_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(session_dir / "_metadata.txt", "w") as f:
                f.write(json.dumps(event_metadata, indent=2))

            imported.append(ImportedFieldSession(
                session_id=session_id,
                output_dir=session_dir,
                csv_path=csv_path,
                event_type="reviewed_session",
                corrected_state="mixed",
                rows=len(reviewed),
                source_bundle=bundle,
            ))
            continue

        motion = pd.read_csv(bundle / "motion.csv")
        feedback = pd.read_csv(bundle / "feedback.csv")

        missing = [c for c in REQUIRED_MOTION_COLUMNS if c not in motion.columns]
        if missing:
            skipped.append({
                "bundle": str(bundle),
                "reason": f"motion.csv missing columns: {missing}",
            })
            continue

        if feedback.empty:
            skipped.append({"bundle": str(bundle), "reason": "feedback.csv has no rows"})
            continue

        motion = motion[REQUIRED_MOTION_COLUMNS].copy()
        motion["timestamp"] = motion["timestamp"].astype(float)

        bundle_slug = _safe_slug(metadata.get("session_id") or bundle.name)
        for idx, row in feedback.iterrows():
            truth = _truth_from_feedback(row)
            start, end = _window_bounds(row, padding_sec)
            event_type = _safe_slug(str(row.get("event_type", "feedback")).lower())

            if truth is None or start is None or end is None:
                skipped.append({
                    "bundle": str(bundle),
                    "row": int(idx),
                    "reason": "missing corrected state or window bounds",
                })
                continue

            window = motion[(motion["timestamp"] >= start) & (motion["timestamp"] <= end)].copy()
            if window.empty:
                skipped.append({
                    "bundle": str(bundle),
                    "row": int(idx),
                    "reason": "no motion rows in feedback window",
                })
                continue

            prefix = "Eating" if truth else "Not-eating"
            session_id = f"{prefix}-field-{bundle_slug}-{idx + 1:03d}-{event_type}"
            session_id = _safe_slug(session_id)
            session_dir = output_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            window["label"] = bool(truth)
            csv_path = session_dir / f"{session_id}.csv"
            window.to_csv(csv_path, index=False)

            event_metadata = {
                "session_id": session_id,
                "source_bundle": str(bundle),
                "source_metadata": metadata,
                "feedback_row": {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()},
                "window_start": start,
                "window_end": end,
                "corrected_label": bool(truth),
                "imported_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(session_dir / "_metadata.txt", "w") as f:
                f.write(json.dumps(event_metadata, indent=2))

            imported.append(ImportedFieldSession(
                session_id=session_id,
                output_dir=session_dir,
                csv_path=csv_path,
                event_type=event_type,
                corrected_state="chewing" if truth else "idle",
                rows=len(window),
                source_bundle=bundle,
            ))

    manifest = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "bundles_found": len(bundles),
        "imported_count": len(imported),
        "skipped": skipped,
        "imported_sessions": [
            {
                "session_id": item.session_id,
                "csv_path": str(item.csv_path),
                "event_type": item.event_type,
                "corrected_state": item.corrected_state,
                "rows": item.rows,
                "source_bundle": str(item.source_bundle),
            }
            for item in imported
        ],
    }

    manifest_path = manifest_dir / f"field_test_import_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
