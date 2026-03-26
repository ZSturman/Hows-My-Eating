"""
Feature extraction stage: Extract 12-feature vectors from transformed CSVs.

Features (must match Swift implementation):
1. mean_accel_mag     - Mean of acceleration magnitude
2. var_accel_mag      - Variance of acceleration magnitude
3. rms_accel_mag      - RMS of acceleration magnitude
4. mean_gyro_mag      - Mean of gyroscope magnitude
5. rms_gyro_mag       - RMS of gyroscope magnitude
6. rms_jerk           - RMS of acceleration jerk (derivative)
7. zcr_accel_mag      - Zero-crossing rate of acceleration magnitude
8. chew_bandpower_1_3 - Bandpower in 1-3 Hz (primary chewing frequency)
9. bandpower_0_8_1_5  - Bandpower in 0.8-1.5 Hz
10. bandpower_2_4     - Bandpower in 2-4 Hz
11. spectral_centroid - Power-weighted mean frequency
12. spectral_rolloff  - 85th percentile frequency
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.signal import welch

from .config import FeaturesConfig, MouthShapeConfig


FEATURE_NAMES = [
    "mean_accel_mag",
    "var_accel_mag",
    "rms_accel_mag",
    "mean_gyro_mag",
    "rms_gyro_mag",
    "rms_jerk",
    "zcr_accel_mag",
    "chew_bandpower_1_3hz",
    "bandpower_0_8_1_5hz",
    "bandpower_2_4hz",
    "spectral_centroid",
    "spectral_rolloff_0_85",
]


def accel_magnitude(ax: np.ndarray, ay: np.ndarray, az: np.ndarray) -> np.ndarray:
    """Compute acceleration magnitude."""
    return np.sqrt(ax**2 + ay**2 + az**2)


def rms(x: np.ndarray) -> float:
    """Compute root mean square."""
    return float(np.sqrt(np.mean(x**2)))


def zero_crossing_rate(x: np.ndarray) -> float:
    """Compute zero-crossing rate."""
    if len(x) < 2:
        return 0.0
    return float(np.mean(np.diff(np.signbit(x))))


def jerk(x: np.ndarray) -> np.ndarray:
    """Compute jerk (first derivative)."""
    return np.diff(x, prepend=x[0])


def bandpower(x: np.ndarray, fs: float, fmin: float, fmax: float) -> float:
    """
    Compute bandpower in a frequency range using Welch's method.
    
    Args:
        x: Signal
        fs: Sampling frequency
        fmin: Minimum frequency
        fmax: Maximum frequency
    
    Returns:
        Integrated power in the frequency band
    """
    f, Pxx = welch(x, fs=fs, nperseg=min(256, len(x)))
    mask = (f >= fmin) & (f <= fmax)
    if mask.sum() == 0:
        return 0.0
    return float(np.trapezoid(Pxx[mask], f[mask]))


def spectral_centroid(x: np.ndarray, fs: float) -> float:
    """
    Compute spectral centroid (power-weighted mean frequency).
    
    Args:
        x: Signal
        fs: Sampling frequency
    
    Returns:
        Spectral centroid in Hz
    """
    f, Pxx = welch(x, fs=fs, nperseg=min(256, len(x)))
    denom = np.sum(Pxx)
    if denom == 0:
        return 0.0
    return float(np.sum(f * Pxx) / denom)


def spectral_rolloff(x: np.ndarray, fs: float, threshold: float = 0.85) -> float:
    """
    Compute spectral rolloff (frequency below which threshold% of power is contained).
    
    Args:
        x: Signal
        fs: Sampling frequency
        threshold: Cumulative power threshold (default 0.85 = 85%)
    
    Returns:
        Rolloff frequency in Hz
    """
    f, Pxx = welch(x, fs=fs, nperseg=min(256, len(x)))
    cumsum = np.cumsum(Pxx)
    if cumsum[-1] == 0:
        return 0.0
    thresh_val = threshold * cumsum[-1]
    idx = np.searchsorted(cumsum, thresh_val)
    if idx >= len(f):
        idx = len(f) - 1
    return float(f[idx])


def extract_features(window: pd.DataFrame, fs: float) -> list[float]:
    """
    Extract 12 features from a window of sensor data.
    
    Args:
        window: DataFrame with ax, ay, az (and optionally gx, gy, gz)
        fs: Sampling frequency
    
    Returns:
        List of 12 feature values
    """
    ax = window["ax"].values
    ay = window["ay"].values
    az = window["az"].values
    
    # Gyro (use zeros if missing)
    gx = window.get("gx")
    gy = window.get("gy")
    gz = window.get("gz")
    
    if gx is None or gy is None or gz is None:
        gx = np.zeros_like(ax)
        gy = np.zeros_like(ay)
        gz = np.zeros_like(az)
    else:
        gx = gx.values
        gy = gy.values
        gz = gz.values
    
    amag = accel_magnitude(ax, ay, az)
    gmag = accel_magnitude(gx, gy, gz)
    j = jerk(amag)
    
    # Time-domain features (7)
    mean_acc = float(np.mean(amag))
    var_acc = float(np.var(amag))
    rms_acc = rms(amag)
    mean_g = float(np.mean(gmag))
    rms_g = rms(gmag)
    rms_j = rms(j)
    zcr_acc = zero_crossing_rate(amag)
    
    # Frequency-domain features (5)
    chew_bp = bandpower(amag, fs, fmin=1.0, fmax=3.0)
    bp_0_8_1_5 = bandpower(amag, fs, fmin=0.8, fmax=1.5)
    bp_2_4 = bandpower(amag, fs, fmin=2.0, fmax=4.0)
    spec_cent = spectral_centroid(amag, fs)
    spec_rolloff = spectral_rolloff(amag, fs, threshold=0.85)
    
    return [
        mean_acc,
        var_acc,
        rms_acc,
        mean_g,
        rms_g,
        rms_j,
        zcr_acc,
        chew_bp,
        bp_0_8_1_5,
        bp_2_4,
        spec_cent,
        spec_rolloff,
    ]


def detect_sampling_rate(t: np.ndarray) -> float:
    """Detect sampling rate from timestamps."""
    dt = np.diff(t)
    dt = dt[(dt > 0) & (dt < np.percentile(dt, 95))]
    if len(dt) == 0:
        return 100.0
    return 1.0 / np.median(dt)


def extract_features_from_csv(
    csv_path: Path,
    config: FeaturesConfig,
    label_col: str = "chewing_soft",
    timestamp_col: Optional[str] = None,
    mouth_shape_config: Optional[MouthShapeConfig] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract features from a transformed CSV.
    
    Args:
        csv_path: Path to transformed CSV (with chewing_soft column)
        config: Feature extraction configuration
        label_col: Label column name (used in binary mode)
        timestamp_col: Timestamp column (auto-detect if None)
        mouth_shape_config: If provided and enabled, extract multi-dim mouth
                            shape labels instead of scalar chewing_soft.
    
    Returns:
        Tuple of (X, y) arrays.
        Binary mode: y shape (n_windows,)
        Mouth shape mode: y shape (n_windows, num_outputs)
    """
    df = pd.read_csv(csv_path)
    
    # Auto-detect timestamp
    if timestamp_col is None:
        for c in ["timestamp", "time", "ts", "datetime"]:
            if c in df.columns:
                timestamp_col = c
                break
        if timestamp_col is None:
            raise ValueError(f"No timestamp column in {csv_path}")
    
    # Get sampling rate
    if not np.issubdtype(df[timestamp_col].dtype, np.number):
        t = pd.to_datetime(df[timestamp_col]).astype("int64") / 1e9
    else:
        t = df[timestamp_col].astype(float).values
    
    fs = detect_sampling_rate(t)
    
    window_samples = int(config.window_sec * fs)
    step_samples = int(config.step_sec * fs)
    
    # Determine label mode
    use_mouth_shape = (
        mouth_shape_config is not None
        and mouth_shape_config.enabled
        and all(col in df.columns for col in mouth_shape_config.parameters)
    )
    
    X_list = []
    y_list = []
    
    for start in range(0, len(df) - window_samples, step_samples):
        end = start + window_samples
        window = df.iloc[start:end]
        
        features = extract_features(window, fs)
        X_list.append(features)
        
        if use_mouth_shape:
            # Multi-output: average each mouth shape param over window
            label_vec = [window[col].mean() for col in mouth_shape_config.parameters]
            y_list.append(label_vec)
        else:
            y_list.append(window[label_col].mean())
    
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    return X, y


def extract_features_directory(
    input_dir: Path,
    output_dir: Path,
    config: FeaturesConfig,
    label_col: str = "chewing_soft",
    timestamp_col: Optional[str] = None,
    mouth_shape_config: Optional[MouthShapeConfig] = None,
) -> tuple[Path, Path, Path]:
    """
    Extract features from all transformed CSVs in a directory.
    
    Args:
        input_dir: Directory containing transformed CSVs
        output_dir: Directory for feature outputs
        config: Feature extraction configuration
        label_col: Label column name (binary mode)
        timestamp_col: Timestamp column (auto-detect if None)
        mouth_shape_config: If provided and enabled, extract multi-dim labels.
    
    Returns:
        Tuple of (X.npy path, y.npy path, feature_names.txt path)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    X_all = []
    y_all = []
    
    csv_files = sorted(input_dir.glob("*.csv"))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in: {input_dir}")
    
    for csv_path in csv_files:
        print(f"Extracting features: {csv_path.name}")
        
        try:
            X, y = extract_features_from_csv(
                csv_path=csv_path,
                config=config,
                label_col=label_col,
                timestamp_col=timestamp_col,
                mouth_shape_config=mouth_shape_config,
            )
            X_all.append(X)
            y_all.append(y)
        except Exception as e:
            print(f"  Error: {e}")
    
    if not X_all:
        raise ValueError("No features extracted from any files")
    
    X = np.concatenate(X_all, axis=0)
    y = np.concatenate(y_all, axis=0)
    
    # Save outputs
    x_path = output_dir / "X.npy"
    y_path = output_dir / "y.npy"
    names_path = output_dir / "feature_names.txt"
    
    np.save(x_path, X)
    np.save(y_path, y)
    
    with open(names_path, "w") as f:
        for name in FEATURE_NAMES:
            f.write(name + "\n")
    
    print(f"✅ Feature extraction complete")
    print(f"   X shape: {X.shape}")
    print(f"   y shape: {y.shape}")
    print(f"   Output: {output_dir}")
    
    # Save label names for multi-output mode
    use_mouth_shape = (
        mouth_shape_config is not None
        and mouth_shape_config.enabled
    )
    if use_mouth_shape:
        label_names_path = output_dir / "label_names.txt"
        with open(label_names_path, "w") as f:
            for name in mouth_shape_config.parameters:
                f.write(name + "\n")
        print(f"   Label names: {label_names_path}")
    
    return x_path, y_path, names_path
