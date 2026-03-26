"""
Ingest stage: Validate raw CSVs and compute dataset manifest/hash.

This stage ensures data quality before processing and provides
reproducibility via dataset hashing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


TIMESTAMP_CANDIDATES = ("timestamp", "time", "ts", "datetime")
REQUIRED_ACCEL_COLS = ("ax", "ay", "az")


@dataclass
class SessionInfo:
    """Information about a validated session."""
    path: Path
    csv_path: Path
    label: str  # "eating" or "not-eating"
    rows: int
    duration_sec: float
    sampling_rate_hz: float
    hash: str


@dataclass
class DatasetManifest:
    """Manifest of all sessions in a dataset."""
    sessions: list[SessionInfo]
    total_rows: int
    total_duration_sec: float
    eating_count: int
    not_eating_count: int
    dataset_hash: str


def autodetect_timestamp_col(df: pd.DataFrame) -> Optional[str]:
    """Auto-detect timestamp column from common names."""
    for c in TIMESTAMP_CANDIDATES:
        if c in df.columns:
            return c
    return None


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]  # Truncated for readability


def validate_csv(
    csv_path: Path,
    label_col: str = "label",
    timestamp_col: Optional[str] = None,
) -> tuple[str, pd.DataFrame]:
    """
    Validate a raw CSV file.
    
    Args:
        csv_path: Path to the CSV file
        label_col: Name of the label column
        timestamp_col: Name of timestamp column (auto-detect if None)
    
    Returns:
        Tuple of (detected_timestamp_col, dataframe)
    
    Raises:
        ValueError: If validation fails
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {csv_path}\nError: {e}")
    
    # Check required columns
    missing = [c for c in REQUIRED_ACCEL_COLS if c not in df.columns]
    if label_col not in df.columns:
        missing.append(label_col)
    if missing:
        raise ValueError(
            f"CSV missing required columns: {csv_path}\n"
            f"Missing: {missing}\n"
            f"Required accelerometer columns: {REQUIRED_ACCEL_COLS}\n"
            f"Required label column: {label_col}"
        )
    
    # Check row count
    if len(df) < 10:
        raise ValueError(
            f"CSV has too few rows: {csv_path} (rows={len(df)})\n"
            "Need at least 10 rows for meaningful processing."
        )
    
    # Auto-detect or validate timestamp column
    ts_col = timestamp_col
    if ts_col is None:
        ts_col = autodetect_timestamp_col(df)
        if ts_col is None:
            raise ValueError(
                f"No timestamp column detected in: {csv_path}\n"
                f"Tried: {TIMESTAMP_CANDIDATES}\n"
                "Fix: rename your timestamp column or pass --timestamp_col"
            )
    elif ts_col not in df.columns:
        raise ValueError(
            f"Timestamp column '{ts_col}' not found in: {csv_path}"
        )
    
    # Validate label column can be cast to int
    try:
        _ = df[label_col].astype(int)
    except Exception as e:
        raise ValueError(
            f"Label column '{label_col}' cannot be cast to int: {csv_path}\n"
            f"Error: {e}\n"
            "Labels must be 0 or 1."
        )
    
    return ts_col, df


def get_session_info(
    session_dir: Path,
    label_col: str = "label",
    timestamp_col: Optional[str] = None,
) -> SessionInfo:
    """
    Get information about a session directory.
    
    Args:
        session_dir: Path to session directory containing CSV
        label_col: Name of label column
        timestamp_col: Timestamp column (auto-detect if None)
    
    Returns:
        SessionInfo with validated session data
    """
    # Find CSV in session directory
    csvs = list(session_dir.glob("*.csv"))
    if len(csvs) == 0:
        raise ValueError(f"No CSV file found in: {session_dir}")
    if len(csvs) > 1:
        raise ValueError(f"Multiple CSV files in: {session_dir}. Expected one.")
    
    csv_path = csvs[0]
    
    # Validate
    ts_col, df = validate_csv(csv_path, label_col, timestamp_col)
    
    # Determine label from folder name
    folder_name = session_dir.name.lower()
    if folder_name.startswith("eating"):
        label = "eating"
    elif folder_name.startswith("not-eating") or folder_name.startswith("noteating"):
        label = "not-eating"
    else:
        # Infer from data
        label_mean = df[label_col].mean()
        label = "eating" if label_mean > 0.5 else "not-eating"
    
    # Compute duration and sampling rate
    if not pd.api.types.is_numeric_dtype(df[ts_col]):
        t = pd.to_datetime(df[ts_col]).astype("int64") / 1e9
    else:
        t = df[ts_col].astype(float).values
    
    dt = t.diff().dropna() if hasattr(t, 'diff') else pd.Series(t).diff().dropna()
    dt = dt[(dt > 0) & (dt < dt.quantile(0.95))]
    sampling_rate = 1.0 / dt.median() if len(dt) > 0 else 100.0
    duration = (t.max() - t.min()) if hasattr(t, 'max') else (t[-1] - t[0])
    
    return SessionInfo(
        path=session_dir,
        csv_path=csv_path,
        label=label,
        rows=len(df),
        duration_sec=float(duration),
        sampling_rate_hz=float(sampling_rate),
        hash=compute_file_hash(csv_path),
    )


def validate_sessions(
    input_dir: Path,
    label_col: str = "label",
    timestamp_col: Optional[str] = None,
) -> list[SessionInfo]:
    """
    Validate all sessions in a directory.
    
    Args:
        input_dir: Directory containing session folders
        label_col: Name of label column
        timestamp_col: Timestamp column (auto-detect if None)
    
    Returns:
        List of validated SessionInfo objects
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    sessions = []
    
    # Find session directories (folders containing CSVs)
    for item in sorted(input_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            csvs = list(item.glob("*.csv"))
            if csvs:
                try:
                    info = get_session_info(item, label_col, timestamp_col)
                    sessions.append(info)
                except ValueError as e:
                    print(f"Warning: Skipping {item.name}: {e}")
    
    # Also check for loose CSVs in input_dir itself
    for csv_path in sorted(input_dir.glob("*.csv")):
        try:
            ts_col, df = validate_csv(csv_path, label_col, timestamp_col)
            
            # Determine label from filename
            name = csv_path.stem.lower()
            if "eating" in name and "not" not in name:
                label = "eating"
            else:
                label = "not-eating"
            
            # Compute stats
            if not pd.api.types.is_numeric_dtype(df[ts_col]):
                t = pd.to_datetime(df[ts_col]).astype("int64") / 1e9
            else:
                t = df[ts_col].astype(float).values
            
            dt = pd.Series(t).diff().dropna()
            dt = dt[(dt > 0) & (dt < dt.quantile(0.95))]
            sampling_rate = 1.0 / dt.median() if len(dt) > 0 else 100.0
            duration = t[-1] - t[0] if len(t) > 1 else 0
            
            sessions.append(SessionInfo(
                path=csv_path.parent,
                csv_path=csv_path,
                label=label,
                rows=len(df),
                duration_sec=float(duration),
                sampling_rate_hz=float(sampling_rate),
                hash=compute_file_hash(csv_path),
            ))
        except ValueError as e:
            print(f"Warning: Skipping {csv_path.name}: {e}")
    
    if not sessions:
        raise ValueError(f"No valid sessions found in: {input_dir}")
    
    return sessions


def compute_dataset_hash(sessions: list[SessionInfo]) -> str:
    """
    Compute a hash representing the entire dataset.
    
    This can be used for W&B logging to track which exact data was used.
    """
    hasher = hashlib.sha256()
    for s in sorted(sessions, key=lambda x: x.csv_path.name):
        hasher.update(s.hash.encode())
    return hasher.hexdigest()[:16]


def create_manifest(sessions: list[SessionInfo]) -> DatasetManifest:
    """Create a manifest summarizing the dataset."""
    total_rows = sum(s.rows for s in sessions)
    total_duration = sum(s.duration_sec for s in sessions)
    eating = sum(1 for s in sessions if s.label == "eating")
    not_eating = len(sessions) - eating
    dataset_hash = compute_dataset_hash(sessions)
    
    return DatasetManifest(
        sessions=sessions,
        total_rows=total_rows,
        total_duration_sec=total_duration,
        eating_count=eating,
        not_eating_count=not_eating,
        dataset_hash=dataset_hash,
    )


def save_manifest(manifest: DatasetManifest, output_path: Path) -> None:
    """Save manifest to JSON file."""
    data = {
        "dataset_hash": manifest.dataset_hash,
        "total_rows": manifest.total_rows,
        "total_duration_sec": manifest.total_duration_sec,
        "eating_count": manifest.eating_count,
        "not_eating_count": manifest.not_eating_count,
        "sessions": [
            {
                "csv_path": str(s.csv_path),
                "label": s.label,
                "rows": s.rows,
                "duration_sec": s.duration_sec,
                "sampling_rate_hz": s.sampling_rate_hz,
                "hash": s.hash,
            }
            for s in manifest.sessions
        ],
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
