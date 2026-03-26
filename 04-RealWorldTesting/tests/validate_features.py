#!/usr/bin/env python3
"""
Feature Parity Validation

Compares Python and Swift feature extraction to ensure they produce
similar results. This is critical for model accuracy since the model
was trained on Python-extracted features.

Usage:
    python validate_features.py --csv path/to/sample.csv
    python validate_features.py --generate-test-data

Tolerance: 5% relative error (configurable via --tolerance)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "02-DataPipeline"))

from pipeline.features import (
    extract_features,
    FEATURE_NAMES,
    detect_sampling_rate,
    accel_magnitude,
)


TOLERANCE = 0.05  # 5% relative error


def load_csv_window(csv_path: Path, window_sec: float = 0.75) -> tuple[pd.DataFrame, float]:
    """Load first window of data from CSV."""
    df = pd.read_csv(csv_path)
    
    # Detect timestamp column
    ts_col = None
    for c in ["timestamp", "time", "ts", "datetime"]:
        if c in df.columns:
            ts_col = c
            break
    
    if ts_col is None:
        raise ValueError(f"No timestamp column found in {csv_path}")
    
    # Get sampling rate
    if not np.issubdtype(df[ts_col].dtype, np.number):
        t = pd.to_datetime(df[ts_col]).astype("int64") / 1e9
    else:
        t = df[ts_col].astype(float).values
    
    fs = detect_sampling_rate(t)
    
    # Get first window
    window_samples = int(window_sec * fs)
    window = df.iloc[:window_samples]
    
    return window, fs


def extract_python_features(window: pd.DataFrame, fs: float) -> list[float]:
    """Extract features using Python implementation."""
    return extract_features(window, fs)


def generate_test_data(csv_path: Path, output_path: Path) -> None:
    """
    Generate test data JSON for Swift validation.
    
    Output format:
    {
        "samples": [{"ax": float, "ay": float, ...}, ...],
        "sampling_rate": float,
        "expected_features": [float, ...]
    }
    """
    window, fs = load_csv_window(csv_path)
    
    # Extract raw samples
    samples = []
    for _, row in window.iterrows():
        sample = {
            "ax": float(row["ax"]),
            "ay": float(row["ay"]),
            "az": float(row["az"]),
            "gx": float(row.get("gx", 0)),
            "gy": float(row.get("gy", 0)),
            "gz": float(row.get("gz", 0)),
        }
        samples.append(sample)
    
    # Extract features
    features = extract_python_features(window, fs)
    
    data = {
        "samples": samples,
        "sampling_rate": fs,
        "expected_features": features,
        "feature_names": FEATURE_NAMES,
    }
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Generated test data: {output_path}")
    print(f"   Samples: {len(samples)}")
    print(f"   Sampling rate: {fs:.2f} Hz")
    print(f"   Features: {len(features)}")


def compare_features(
    python_features: list[float],
    swift_features: list[float],
    tolerance: float = TOLERANCE,
) -> tuple[bool, list[dict]]:
    """
    Compare Python and Swift features.
    
    Returns:
        (all_pass, list of comparison results)
    """
    assert len(python_features) == len(swift_features) == 12
    
    results = []
    all_pass = True
    
    for i, (py, sw) in enumerate(zip(python_features, swift_features)):
        abs_diff = abs(py - sw)
        
        # Relative error (handle zero case)
        if abs(py) > 1e-10:
            rel_error = abs_diff / abs(py)
        else:
            rel_error = abs_diff  # Absolute for near-zero values
        
        passed = rel_error <= tolerance
        
        if not passed:
            all_pass = False
        
        results.append({
            "feature": FEATURE_NAMES[i],
            "python": py,
            "swift": sw,
            "abs_diff": abs_diff,
            "rel_error": rel_error,
            "passed": passed,
        })
    
    return all_pass, results


def print_comparison_results(results: list[dict]) -> None:
    """Print comparison results in a formatted table."""
    print("\nFeature Comparison Results")
    print("=" * 80)
    print(f"{'Feature':<25} {'Python':>12} {'Swift':>12} {'RelErr':>10} {'Status':>8}")
    print("-" * 80)
    
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{r['feature']:<25} {r['python']:>12.6f} {r['swift']:>12.6f} {r['rel_error']:>10.4f} {status:>8}")
    
    print("-" * 80)
    
    passed = sum(1 for r in results if r["passed"])
    print(f"Passed: {passed}/12 features")


def validate_from_swift_output(
    python_features: list[float],
    swift_output_path: Path,
    tolerance: float = TOLERANCE,
) -> bool:
    """
    Validate against Swift output file.
    
    Swift test should write features to a JSON file like:
    {"features": [0.123, 0.456, ...]}
    """
    with open(swift_output_path, "r") as f:
        data = json.load(f)
    
    swift_features = data["features"]
    
    all_pass, results = compare_features(python_features, swift_features, tolerance)
    print_comparison_results(results)
    
    return all_pass


def main():
    parser = argparse.ArgumentParser(description="Validate feature parity between Python and Swift")
    
    parser.add_argument(
        "--csv", type=Path,
        help="CSV file to extract features from"
    )
    parser.add_argument(
        "--generate-test-data", action="store_true",
        help="Generate test data JSON for Swift validation"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("test_data.json"),
        help="Output path for generated test data"
    )
    parser.add_argument(
        "--swift-output", type=Path,
        help="Path to Swift feature output JSON for comparison"
    )
    parser.add_argument(
        "--tolerance", type=float, default=TOLERANCE,
        help=f"Relative error tolerance (default: {TOLERANCE})"
    )
    
    args = parser.parse_args()
    
    if args.generate_test_data:
        if not args.csv:
            # Use sample data
            sample_dir = Path(__file__).parent.parent.parent / "02-DataPipeline" / "data" / "sample"
            csvs = list(sample_dir.glob("*/*.csv"))
            if not csvs:
                print("❌ No sample CSV found. Use --csv to specify a file.")
                return 1
            args.csv = csvs[0]
        
        generate_test_data(args.csv, args.output)
        return 0
    
    if args.csv:
        window, fs = load_csv_window(args.csv)
        python_features = extract_python_features(window, fs)
        
        print(f"Python features from: {args.csv}")
        print(f"Sampling rate: {fs:.2f} Hz")
        print(f"Window samples: {len(window)}")
        print("\nFeatures:")
        for i, (name, val) in enumerate(zip(FEATURE_NAMES, python_features)):
            print(f"  {i+1:2d}. {name:<25}: {val:.6f}")
        
        if args.swift_output:
            success = validate_from_swift_output(
                python_features,
                args.swift_output,
                args.tolerance,
            )
            return 0 if success else 1
        
        return 0
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
