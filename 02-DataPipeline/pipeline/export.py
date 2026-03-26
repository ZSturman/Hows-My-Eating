"""
Export stage: Export trained model to CoreML and generate Swift constants.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
import torch.nn as nn

from .train import ChewNet
from .features import FEATURE_NAMES

try:
    import coremltools as ct
    COREML_AVAILABLE = True
except ImportError:
    COREML_AVAILABLE = False


def export_coreml(
    model_path: Path,
    output_path: Path,
) -> Path:
    """
    Export PyTorch model to CoreML format.
    
    Supports both binary (1-output) and mouth shape (multi-output) models.
    
    Args:
        model_path: Path to PyTorch checkpoint
        output_path: Path for CoreML output (should end in .mlpackage)
    
    Returns:
        Path to the exported model
    """
    if not COREML_AVAILABLE:
        raise RuntimeError(
            "coremltools is required for CoreML export.\n"
            "Install with: pip install coremltools"
        )
    
    model_path = Path(model_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    
    input_dim = ckpt["input_dim"]
    hidden_dim = ckpt["hidden_dim"]
    num_outputs = ckpt.get("num_outputs", 1)
    
    model = ChewNet(input_dim=input_dim, hidden_dim=hidden_dim, num_outputs=num_outputs)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    # Trace model
    example_input = torch.randn(1, input_dim)
    traced = torch.jit.trace(model, example_input)
    traced.eval()
    
    # Convert to CoreML
    mlmodel = ct.convert(
        traced,
        inputs=[ct.TensorType(name="input", shape=example_input.shape)],
    )
    
    # Rename output
    spec = mlmodel.get_spec()
    old_name = spec.description.output[0].name
    output_name = "mouth_shape" if num_outputs > 1 else "logit"
    ct.utils.rename_feature(spec, old_name, output_name)
    
    # Rebuild with weights
    mlmodel_renamed = ct.models.MLModel(spec, weights_dir=mlmodel.weights_dir)
    mlmodel_renamed.save(str(output_path))
    
    print(f"✅ Exported CoreML model: {output_path} (outputs={num_outputs})")
    return output_path


def export_normalization_json(
    model_path: Path,
    output_path: Path,
) -> Path:
    """
    Export normalization constants to JSON.
    
    Args:
        model_path: Path to PyTorch checkpoint
        output_path: Path for JSON output
    
    Returns:
        Path to the JSON file
    """
    model_path = Path(model_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    
    data = {
        "feature_mean": ckpt["mean"].tolist(),
        "feature_std": ckpt["std"].tolist(),
        "feature_names": FEATURE_NAMES,
        "input_dim": ckpt["input_dim"],
        "hidden_dim": ckpt["hidden_dim"],
        "num_outputs": ckpt.get("num_outputs", 1),
        "mode": ckpt.get("mode", "binary"),
    }
    
    # Mouth shape specific metadata
    if ckpt.get("mode") == "mouth_shape":
        data["label_names"] = ckpt.get("label_names", [])
        if ckpt.get("label_mean") is not None:
            data["label_mean"] = ckpt["label_mean"].tolist()
            data["label_std"] = ckpt["label_std"].tolist()
    
    # Include W&B info if available
    if "wandb_run_id" in ckpt:
        data["wandb_run_id"] = ckpt["wandb_run_id"]
    if "wandb_run_url" in ckpt:
        data["wandb_run_url"] = ckpt["wandb_run_url"]
    if "dataset_hash" in ckpt:
        data["dataset_hash"] = ckpt["dataset_hash"]
    if "config" in ckpt:
        data["runtime_config"] = ckpt["config"].get("runtime", {})
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Exported normalization JSON: {output_path}")
    return output_path


def format_swift_array(values: list[float], indent: str = "    ") -> str:
    """Format a list of floats as a Swift array literal."""
    formatted = [f"{v:.10f}" for v in values]
    return f"[\n{indent}    " + f",\n{indent}    ".join(formatted) + f"\n{indent}]"


def generate_swift_constants(
    model_path: Path,
    output_path: Path,
    runtime_config: Optional[dict] = None,
) -> Path:
    """
    Generate Swift normalization constants from trained model.
    
    This file should be imported into the iOS/macOS app and replaces
    any hardcoded normalization arrays.
    
    Args:
        model_path: Path to PyTorch checkpoint
        output_path: Path for Swift output
        runtime_config: Optional runtime config to include
    
    Returns:
        Path to the Swift file
    """
    model_path = Path(model_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    
    mean = ckpt["mean"].tolist()
    std = ckpt["std"].tolist()
    num_outputs = ckpt.get("num_outputs", 1)
    mode = ckpt.get("mode", "binary")
    label_names = ckpt.get("label_names", [])
    
    # Get W&B info for traceability
    wandb_run_id = ckpt.get("wandb_run_id")
    wandb_run_url = ckpt.get("wandb_run_url")
    dataset_hash = ckpt.get("dataset_hash")
    
    # Get runtime config from checkpoint or parameter
    if runtime_config is None and "config" in ckpt:
        runtime_config = ckpt["config"].get("runtime", {})
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build Swift file
    swift_code = f'''//
//  NormalizationConstants.swift
//  ChewSense
//
//  AUTO-GENERATED by pipeline/export.py
//  Do not edit manually - regenerate from pipeline after training.
//
//  Generated: {timestamp}
'''
    
    if wandb_run_id:
        swift_code += f"//  W&B Run ID: {wandb_run_id}\n"
    if wandb_run_url:
        swift_code += f"//  W&B Run URL: {wandb_run_url}\n"
    if dataset_hash:
        swift_code += f"//  Dataset Hash: {dataset_hash}\n"
    
    swift_code += '''//

import Foundation

/// Normalization constants for ChewNet feature preprocessing.
/// These values are computed from the training set and must match the model.
struct NormalizationConstants {
    
    /// Feature means from training data (12 features)
    /// Order: mean_accel_mag, var_accel_mag, rms_accel_mag, mean_gyro_mag, rms_gyro_mag,
    ///        rms_jerk, zcr_accel_mag, chew_bandpower_1_3hz, bandpower_0_8_1_5hz,
    ///        bandpower_2_4hz, spectral_centroid, spectral_rolloff_0_85
'''
    
    swift_code += f"    static let FEATURE_MEAN: [Double] = {format_swift_array(mean)}\n\n"
    swift_code += "    /// Feature standard deviations from training data (12 features)\n"
    swift_code += f"    static let FEATURE_STD: [Double] = {format_swift_array(std)}\n\n"
    
    # Add output metadata
    swift_code += f"    /// Number of model outputs\n"
    swift_code += f"    static let NUM_OUTPUTS: Int = {num_outputs}\n\n"
    swift_code += f"    /// Model mode: \"binary\" or \"mouth_shape\"\n"
    swift_code += f'    static let MODE: String = "{mode}"\n\n'
    
    if mode == "mouth_shape" and label_names:
        swift_code += "    /// Output parameter names (order matches model output)\n"
        names_swift = ', '.join(f'"{n}"' for n in label_names)
        swift_code += f"    static let OUTPUT_NAMES: [String] = [{names_swift}]\n\n"
    
    swift_code += '''    /// Normalize features using training statistics
    /// - Parameter features: Raw feature vector (12 elements)
    /// - Returns: Normalized feature vector
    static func normalize(_ features: [Double]) -> [Double] {
        guard features.count == FEATURE_MEAN.count else {
            fatalError("Expected \(FEATURE_MEAN.count) features, got \\(features.count)")
        }
        return zip(zip(features, FEATURE_MEAN), FEATURE_STD).map { (($0.0 - $0.1) / $1) }
    }
}

'''
    
    # Add runtime config if provided
    if runtime_config:
        swift_code += '''/// Runtime detection parameters.
/// These control the chewing state machine behavior and can be tuned without retraining.
struct RuntimeConfig {
'''
        alpha = runtime_config.get("alpha", 0.4)
        high = runtime_config.get("high_threshold", 0.6)
        low = runtime_config.get("low_threshold", 0.4)
        min_start = runtime_config.get("min_start_windows", 3)
        min_end = runtime_config.get("min_end_windows", 2)
        
        swift_code += f'''    /// EMA smoothing factor (0 = no smoothing, 1 = no memory)
    static let alpha: Double = {alpha}
    
    /// Probability threshold to START a chewing episode
    static let highThreshold: Double = {high}
    
    /// Probability threshold to END a chewing episode
    static let lowThreshold: Double = {low}
    
    /// Consecutive windows above highThreshold to confirm chewing start
    static let minStartWindows: Int = {min_start}
    
    /// Consecutive windows below lowThreshold to confirm chewing end
    static let minEndWindows: Int = {min_end}
}}
'''
    
    with open(output_path, "w") as f:
        f.write(swift_code)
    
    print(f"✅ Generated Swift constants: {output_path}")
    return output_path
