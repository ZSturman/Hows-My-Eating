"""
Evaluation stage: Compute metrics on the trained model.

Supports both binary classification (chewing detection) and
multi-output regression (mouth shape estimation).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from .config import PipelineConfig
from .train import ChewNet
from .splits import indices_for_split

try:
    from sklearn.metrics import (
        accuracy_score,
        roc_auc_score,
        precision_score,
        recall_score,
        f1_score,
        confusion_matrix,
        mean_absolute_error,
        mean_squared_error,
        r2_score,
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def evaluate_model(
    features_dir: Path,
    model_path: Path,
    config: PipelineConfig,
    split_manifest_path: Path | None = None,
    split_name: str = "all",
) -> dict[str, Any]:
    """
    Evaluate trained model on feature data.
    
    Automatically detects binary vs mouth shape mode from the checkpoint.
    
    Args:
        features_dir: Directory containing X.npy and y.npy
        model_path: Path to trained model checkpoint
        config: Pipeline configuration
    
    Returns:
        Dictionary with evaluation metrics
    """
    if not SKLEARN_AVAILABLE:
        raise RuntimeError(
            "scikit-learn is required for evaluation.\n"
            "Install with: pip install scikit-learn"
        )
    
    features_dir = Path(features_dir)
    model_path = Path(model_path)
    
    # Load model
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    mean = ckpt["mean"]
    std = ckpt["std"]
    num_outputs = ckpt.get("num_outputs", 1)
    mode = ckpt.get("mode", "binary")
    
    model = ChewNet(
        input_dim=ckpt["input_dim"],
        hidden_dim=ckpt["hidden_dim"],
        num_outputs=num_outputs,
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    # Load data
    X = np.load(features_dir / "X.npy").astype(np.float32)
    y = np.load(features_dir / "y.npy").astype(np.float32)

    split_indices = indices_for_split(features_dir, split_manifest_path, split_name)
    if split_indices is not None:
        if len(split_indices) == 0:
            raise ValueError(f"Split '{split_name}' has no feature rows")
        X = X[split_indices]
        y = y[split_indices]
        print(f"Evaluating split '{split_name}' ({len(split_indices)} rows)")
    
    # Normalize and predict
    X_norm = (X - mean) / std
    X_t = torch.from_numpy(X_norm)
    
    with torch.no_grad():
        output = model(X_t).numpy()
    
    if mode == "mouth_shape" and num_outputs > 1:
        metrics = _evaluate_regression(y, output, ckpt)
    else:
        metrics = _evaluate_binary(y, output, config)
    metrics["split"] = split_name
    metrics["split_manifest_path"] = str(split_manifest_path) if split_manifest_path else None
    return metrics


def _evaluate_binary(
    y_soft: np.ndarray,
    logits: np.ndarray,
    config: PipelineConfig,
) -> dict[str, Any]:
    """Evaluate binary chewing classification."""
    ec = config.evaluation
    y = (y_soft >= ec.chew_threshold).astype(np.int32)
    
    probs = 1.0 / (1.0 + np.exp(-logits))  # sigmoid
    preds = (probs >= ec.pred_threshold).astype(np.int32)
    
    acc = accuracy_score(y, preds)
    auc = roc_auc_score(y, probs)
    prec = precision_score(y, preds, zero_division=0)
    rec = recall_score(y, preds, zero_division=0)
    f1 = f1_score(y, preds, zero_division=0)
    cm = confusion_matrix(y, preds)
    
    print("\nEVALUATION RESULTS (Binary Classification)")
    print("-------------------------------------------")
    print(f"Accuracy:   {acc:.4f}")
    print(f"ROC AUC:    {auc:.4f}")
    print(f"Precision:  {prec:.4f}")
    print(f"Recall:     {rec:.4f}")
    print(f"F1 Score:   {f1:.4f}")
    print("Confusion Matrix:")
    print(cm)
    
    return {
        "mode": "binary",
        "accuracy": float(acc),
        "roc_auc": float(auc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "confusion_matrix": cm.tolist(),
        "n_samples": len(y),
        "n_positive": int(y.sum()),
        "n_negative": int(len(y) - y.sum()),
    }


def _evaluate_regression(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    ckpt: dict,
) -> dict[str, Any]:
    """Evaluate multi-output mouth shape regression."""
    label_names = ckpt.get("label_names", [f"output_{i}" for i in range(y_true.shape[1])])
    
    print("\nEVALUATION RESULTS (Mouth Shape Regression)")
    print("--------------------------------------------")
    
    per_param: dict[str, dict[str, float]] = {}
    
    for i, name in enumerate(label_names):
        yt = y_true[:, i]
        yp = y_pred[:, i]
        
        mae = mean_absolute_error(yt, yp)
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        r2 = r2_score(yt, yp)
        
        per_param[name] = {"mae": mae, "rmse": rmse, "r2": r2}
        print(f"  {name:25s}  MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}")
    
    # Aggregate
    all_mae = mean_absolute_error(y_true, y_pred)
    all_rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    
    print(f"\n  {'OVERALL':25s}  MAE={all_mae:.4f}  RMSE={all_rmse:.4f}")
    
    return {
        "mode": "mouth_shape",
        "per_parameter": per_param,
        "overall_mae": float(all_mae),
        "overall_rmse": float(all_rmse),
        "n_samples": len(y_true),
        "label_names": label_names,
    }
