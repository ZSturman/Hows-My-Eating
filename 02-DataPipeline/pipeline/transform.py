"""
Transform stage: Add soft labels to raw CSVs.

Converts hard 0/1 labels to soft continuous labels (0.0-1.0) using
transition ramps. This helps the model learn smoother boundaries.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .config import SoftLabelsConfig, MouthShapeConfig


def detect_sampling_rate(t: np.ndarray) -> float:
    """Detect sampling rate from timestamps."""
    dt = np.diff(t)
    dt = dt[(dt > 0) & (dt < np.percentile(dt, 95))]
    if len(dt) == 0:
        return 100.0  # Default fallback
    return 1.0 / np.median(dt)


def compute_soft_labels(
    labels: np.ndarray,
    sampling_rate: float,
    config: SoftLabelsConfig,
) -> np.ndarray:
    """
    Compute soft continuous labels from hard 0/1 labels.
    
    Args:
        labels: Binary labels (0/1)
        sampling_rate: Sampling rate in Hz
        config: Soft label configuration
    
    Returns:
        Soft labels (0.0 to 1.0)
    """
    n = len(labels)
    
    soft_ramp_samples = int(config.transition_sec * sampling_rate)
    long_chew_samples = int(config.long_chew_sec * sampling_rate)
    long_ramp_samples = int(config.long_ramp_sec * sampling_rate)
    
    chewing_soft = np.zeros(n)
    
    # Find chewing segments
    segments = []
    in_segment = False
    start = 0
    
    for i in range(n):
        if labels[i] == 1 and not in_segment:
            start = i
            in_segment = True
        elif labels[i] == 0 and in_segment:
            segments.append((start, i))
            in_segment = False
    
    if in_segment:
        segments.append((start, n))
    
    # Apply soft label logic
    for start, end in segments:
        length = end - start
        
        if length < long_chew_samples:
            # Short chews: symmetric ramp up/down
            ramp = max(length // 2, 1)
            
            for i in range(start, start + ramp):
                chewing_soft[i] = (i - start) / ramp
            
            for i in range(start + ramp, end):
                chewing_soft[i] = (end - i) / ramp
        else:
            # Long chews: ramp up, plateau, ramp down
            ramp = min(long_ramp_samples, length // 2)
            ramp = max(ramp, 1)
            
            for i in range(start, start + ramp):
                chewing_soft[i] = (i - start) / ramp
            
            for i in range(start + ramp, end - ramp):
                chewing_soft[i] = 1.0
            
            for i in range(end - ramp, end):
                chewing_soft[i] = (end - i) / ramp
    
    return chewing_soft


def transform_csv(
    input_path: Path,
    output_path: Path,
    config: SoftLabelsConfig,
    label_col: str = "label",
    timestamp_col: Optional[str] = None,
) -> Path:
    """
    Transform a raw CSV by adding soft labels.
    
    Args:
        input_path: Path to input CSV
        output_path: Path for output CSV
        config: Soft label configuration
        label_col: Name of the label column
        timestamp_col: Timestamp column (auto-detect if None)
    
    Returns:
        Path to the output CSV
    """
    df = pd.read_csv(input_path)
    
    # Auto-detect timestamp column
    if timestamp_col is None:
        for c in ["timestamp", "time", "ts", "datetime"]:
            if c in df.columns:
                timestamp_col = c
                break
        if timestamp_col is None:
            raise ValueError(f"No timestamp column found in {input_path}")
    
    # Get timestamps for sampling rate detection
    if not np.issubdtype(df[timestamp_col].dtype, np.number):
        t = pd.to_datetime(df[timestamp_col]).astype("int64") / 1e9
    else:
        t = df[timestamp_col].astype(float).values
    
    sampling_rate = detect_sampling_rate(t)
    
    # Compute soft labels
    labels = df[label_col].astype(int).values
    soft_labels = compute_soft_labels(labels, sampling_rate, config)
    
    # Add to dataframe
    df["chewing_soft"] = soft_labels
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    return output_path


def transform_directory(
    input_dir: Path,
    output_dir: Path,
    config: SoftLabelsConfig,
    archive_dir: Optional[Path] = None,
    label_col: str = "label",
    timestamp_col: Optional[str] = None,
    postfix: str = "_transformed",
) -> list[Path]:
    """
    Transform all CSVs in a directory.
    
    Args:
        input_dir: Directory containing raw CSVs or session folders
        output_dir: Directory for transformed CSVs
        config: Soft label configuration
        archive_dir: If set, move originals here after processing
        label_col: Name of label column
        timestamp_col: Timestamp column (auto-detect if None)
        postfix: Postfix to add to output filenames
    
    Returns:
        List of paths to transformed CSVs
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if archive_dir:
        archive_dir = Path(archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)
    
    transformed = []
    
    # Find all CSVs (in session folders or directly in input_dir)
    csv_files = []
    
    for item in input_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Session folder - find CSV inside
            csvs = list(item.glob("*.csv"))
            csv_files.extend(csvs)
        elif item.is_file() and item.suffix.lower() == ".csv":
            csv_files.append(item)
    
    for csv_path in sorted(csv_files):
        print(f"Transforming: {csv_path.name}")
        
        # Output name
        out_name = f"{csv_path.stem}{postfix}{csv_path.suffix}"
        out_path = output_dir / out_name
        
        if out_path.exists():
            print(f"  Skipping (already exists): {out_path}")
            transformed.append(out_path)
            continue
        
        try:
            transform_csv(
                input_path=csv_path,
                output_path=out_path,
                config=config,
                label_col=label_col,
                timestamp_col=timestamp_col,
            )
            transformed.append(out_path)
            
            # Archive original if requested
            if archive_dir:
                dest = archive_dir / csv_path.name
                if not dest.exists():
                    shutil.copy2(csv_path, dest)
                    print(f"  Archived to: {dest}")
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"✅ Transformed {len(transformed)} files to: {output_dir}")
    return transformed


def smooth_mouth_shape(
    csv_path: Path,
    output_path: Path,
    config: MouthShapeConfig,
) -> Path:
    """
    Apply optional temporal smoothing to mouth shape columns in an aligned CSV.

    If temporal_smooth_sigma is 0, the file is copied unchanged.

    Args:
        csv_path: Path to aligned CSV (with mouth shape columns)
        output_path: Path for smoothed output CSV
        config: Mouth shape configuration

    Returns:
        Path to the output CSV
    """
    from scipy.ndimage import gaussian_filter1d

    df = pd.read_csv(csv_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if config.temporal_smooth_sigma > 0:
        for col in config.parameters:
            if col in df.columns:
                df[col] = gaussian_filter1d(
                    df[col].values.astype(float),
                    sigma=config.temporal_smooth_sigma,
                )

    df.to_csv(output_path, index=False)
    return output_path
