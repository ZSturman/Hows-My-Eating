"""
Alignment stage: Align video-derived mouth shape labels with motion CSV data.

The data collection app records video (~30fps) and motion CSV (~100Hz)
simultaneously. This module interpolates the lower-rate mouth shape
parameters onto the higher-rate motion timestamps so every motion sample
has a corresponding mouth shape label.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .mouth_shape import MOUTH_SHAPE_COLUMNS


def align_mouth_shape_to_motion(
    motion_csv: Path,
    mouth_shape_csv: Path,
    output_csv: Path,
    timestamp_col: Optional[str] = None,
) -> Path:
    """
    Align mouth shape labels to motion CSV via linear interpolation.

    Both recordings start simultaneously from the data collection app.
    Video mouth shape has ~30fps timestamps; motion CSV has ~100Hz timestamps.
    We interpolate mouth shape values to match each motion sample.

    Args:
        motion_csv: Path to motion CSV (timestamp, ax, ay, az, gx, gy, gz, label)
        mouth_shape_csv: Path to mouth shape CSV from extract_and_save()
        output_csv: Path for aligned output CSV
        timestamp_col: Timestamp column in motion CSV (auto-detect if None)

    Returns:
        Path to the aligned CSV
    """
    motion_df = pd.read_csv(motion_csv)
    shape_df = pd.read_csv(mouth_shape_csv)

    # Auto-detect timestamp column
    if timestamp_col is None:
        for c in ("timestamp", "time", "ts", "datetime"):
            if c in motion_df.columns:
                timestamp_col = c
                break
        if timestamp_col is None:
            raise ValueError(f"No timestamp column found in {motion_csv}")

    # Convert motion timestamps to relative seconds from first sample
    if not np.issubdtype(motion_df[timestamp_col].dtype, np.number):
        motion_t = pd.to_datetime(motion_df[timestamp_col]).astype("int64") / 1e9
    else:
        motion_t = motion_df[timestamp_col].astype(float).values

    t0 = motion_t[0] if hasattr(motion_t, '__getitem__') else motion_t.iloc[0]
    motion_rel = np.asarray(motion_t) - t0

    # Mouth shape timestamps are already relative seconds (from frame_idx / fps)
    shape_t = shape_df["timestamp_sec"].values

    # Validate overlap
    if len(shape_t) < 2:
        raise ValueError(
            f"Mouth shape CSV has fewer than 2 frames: {mouth_shape_csv}"
        )

    motion_duration = motion_rel[-1]
    shape_duration = shape_t[-1]
    overlap = min(motion_duration, shape_duration)

    if overlap < 1.0:
        raise ValueError(
            f"Insufficient overlap between motion ({motion_duration:.1f}s) "
            f"and mouth shape ({shape_duration:.1f}s) data"
        )

    # Linear interpolation of each mouth shape parameter
    for col in MOUTH_SHAPE_COLUMNS:
        if col not in shape_df.columns:
            raise ValueError(f"Missing column '{col}' in {mouth_shape_csv}")

        values = shape_df[col].values
        interpolated = np.interp(motion_rel, shape_t, values)

        # Samples beyond the video duration get the last known value
        # (np.interp already handles this via edge clamping)
        motion_df[col] = interpolated

    # Save
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    motion_df.to_csv(output_csv, index=False)

    print(f"  Aligned: {len(motion_df)} motion samples with mouth shape")
    print(f"  Motion duration: {motion_duration:.1f}s, Video duration: {shape_duration:.1f}s")
    print(f"  Saved: {output_csv}")
    return output_csv


def align_session(
    session_dir: Path,
    mouth_shape_dir: Path,
    output_dir: Path,
    timestamp_col: Optional[str] = None,
) -> Optional[Path]:
    """
    Align a single session's motion CSV with its mouth shape CSV.

    Expects:
      - session_dir/ contains one .csv (motion data)
      - mouth_shape_dir/ contains a matching CSV (by session folder name)

    Args:
        session_dir: Path to session directory with motion CSV
        mouth_shape_dir: Directory containing mouth shape CSVs
        output_dir: Directory for aligned output CSVs
        timestamp_col: Timestamp column (auto-detect if None)

    Returns:
        Path to aligned CSV, or None if mouth shape data not found
    """
    # Find motion CSV
    motion_csvs = list(session_dir.glob("*.csv"))
    if not motion_csvs:
        print(f"  No motion CSV in {session_dir.name}, skipping")
        return None
    motion_csv = motion_csvs[0]

    # Find corresponding mouth shape CSV
    shape_csv_name = f"{session_dir.name}_mouth_shape.csv"
    shape_csv = mouth_shape_dir / shape_csv_name
    if not shape_csv.exists():
        print(f"  No mouth shape CSV for {session_dir.name}, skipping")
        return None

    output_csv = Path(output_dir) / f"{session_dir.name}_aligned.csv"
    return align_mouth_shape_to_motion(
        motion_csv=motion_csv,
        mouth_shape_csv=shape_csv,
        output_csv=output_csv,
        timestamp_col=timestamp_col,
    )


def align_directory(
    sessions_dir: Path,
    mouth_shape_dir: Path,
    output_dir: Path,
    timestamp_col: Optional[str] = None,
) -> list[Path]:
    """
    Align all sessions in a directory.

    Args:
        sessions_dir: Directory containing session subdirectories
        mouth_shape_dir: Directory containing mouth shape CSVs
        output_dir: Directory for aligned output CSVs
        timestamp_col: Timestamp column (auto-detect if None)

    Returns:
        List of paths to aligned CSVs
    """
    sessions_dir = Path(sessions_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    aligned = []

    for session_dir in sorted(sessions_dir.iterdir()):
        if not session_dir.is_dir() or session_dir.name.startswith("."):
            continue

        print(f"Aligning session: {session_dir.name}")
        result = align_session(
            session_dir=session_dir,
            mouth_shape_dir=mouth_shape_dir,
            output_dir=output_dir,
            timestamp_col=timestamp_col,
        )
        if result is not None:
            aligned.append(result)

    print(f"\n✅ Aligned {len(aligned)} sessions")
    return aligned


def process_videos_and_align(
    sessions_dir: Path,
    output_dir: Path,
    timestamp_col: Optional[str] = None,
) -> list[Path]:
    """
    End-to-end: extract mouth shapes from session videos and align with motion.

    Each session directory should contain:
      - One .csv file (motion data)
      - One .mov file (video for face landmark extraction)

    Args:
        sessions_dir: Directory containing session subdirectories
        output_dir: Base output directory (will create mouth_shape/ and aligned/ subdirs)
        timestamp_col: Timestamp column (auto-detect if None)

    Returns:
        List of paths to aligned CSVs
    """
    from .mouth_shape import extract_and_save

    sessions_dir = Path(sessions_dir)
    output_dir = Path(output_dir)

    mouth_shape_dir = output_dir / "mouth_shape"
    aligned_dir = output_dir / "aligned"
    mouth_shape_dir.mkdir(parents=True, exist_ok=True)
    aligned_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract mouth shape from each session's video
    for session_dir in sorted(sessions_dir.iterdir()):
        if not session_dir.is_dir() or session_dir.name.startswith("."):
            continue

        videos = list(session_dir.glob("*.mov")) + list(session_dir.glob("*.mp4"))
        if not videos:
            print(f"  No video in {session_dir.name}, skipping mouth shape extraction")
            continue

        video_path = videos[0]
        shape_csv = mouth_shape_dir / f"{session_dir.name}_mouth_shape.csv"

        if shape_csv.exists():
            print(f"  Mouth shape already extracted: {session_dir.name}")
            continue

        try:
            extract_and_save(video_path, shape_csv)
        except Exception as e:
            print(f"  Error extracting {session_dir.name}: {e}")

    # Step 2: Align all extracted mouth shapes with motion data
    return align_directory(
        sessions_dir=sessions_dir,
        mouth_shape_dir=mouth_shape_dir,
        output_dir=aligned_dir,
        timestamp_col=timestamp_col,
    )
