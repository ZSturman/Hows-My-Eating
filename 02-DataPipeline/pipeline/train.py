"""
Training stage: Train ChewNet model with W&B logging.

This module wraps the existing train_pytorch.py with better W&B integration
and config management.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from .config import PipelineConfig

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False


class ChewNet(nn.Module):
    """MLP for chewing detection or mouth shape regression.
    
    Binary mode (num_outputs=1): outputs single logit for chewing probability.
    Mouth shape mode (num_outputs>1): outputs continuous mouth shape parameters.
    """
    
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_outputs: int = 1):
        super().__init__()
        self.num_outputs = num_outputs
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_outputs),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.net(x)
        if self.num_outputs == 1:
            return out.squeeze(-1)
        return out


def compute_data_hash(X: np.ndarray, y: np.ndarray) -> str:
    """Compute hash of training data for reproducibility tracking."""
    hasher = hashlib.sha256()
    hasher.update(X.tobytes())
    hasher.update(y.tobytes())
    return hasher.hexdigest()[:16]


def train_model(
    features_dir: Path,
    output_path: Path,
    config: PipelineConfig,
    dataset_hash: Optional[str] = None,
    data_source: str = "unknown",
    split_manifest_path: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Train ChewNet model on precomputed features.
    
    Args:
        features_dir: Directory containing X.npy and y.npy
        output_path: Path to save model checkpoint
        config: Pipeline configuration
        dataset_hash: Optional hash from ingest stage (for W&B)
        data_source: "sample" or "user" (for W&B)
    
    Returns:
        Dictionary with training results and W&B run info
    """
    features_dir = Path(features_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    X = np.load(features_dir / "X.npy").astype(np.float32)
    y = np.load(features_dir / "y.npy").astype(np.float32)
    
    n_samples, input_dim = X.shape
    
    # Determine mode: binary classification or mouth shape regression
    ms_config = config.mouth_shape
    use_mouth_shape = ms_config.enabled and y.ndim == 2
    num_outputs = ms_config.num_outputs if use_mouth_shape else 1
    
    print(f"Loaded X: {X.shape}, y: {y.shape}")
    if use_mouth_shape:
        print(f"Mode: mouth shape regression ({num_outputs} outputs)")
    else:
        print(f"Mode: binary chewing classification")
    
    # Compute data hash if not provided
    if dataset_hash is None:
        dataset_hash = compute_data_hash(X, y)
    
    # Training config
    tc = config.training
    
    # Initialize W&B
    wandb_run_id = None
    wandb_run_url = None
    use_wandb = config.wandb.enabled and WANDB_AVAILABLE
    
    if use_wandb:
        wandb_config = {
            **config.to_dict(),
            "dataset_hash": dataset_hash,
            "data_source": data_source,
            "n_samples": n_samples,
            "input_dim": input_dim,
            "num_outputs": num_outputs,
            "mode": "mouth_shape" if use_mouth_shape else "binary",
            "architecture": "3-layer MLP",
        }
        
        wandb.init(
            project=config.wandb.project,
            entity=config.wandb.entity,
            config=wandb_config,
        )
        wandb_run_id = wandb.run.id
        wandb_run_url = wandb.run.get_url()
        print(f"W&B run: {wandb_run_url}")
    
    # Train/val split. Prefer locked session splits when available.
    split_name = "random_row_split"
    split_train_sessions: list[str] = []
    split_val_sessions: list[str] = []

    X_train: np.ndarray
    X_val: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray

    if split_manifest_path and (features_dir / "session_ids.npy").exists():
        with open(split_manifest_path, "r") as f:
            split_manifest = json.load(f)
        splits = split_manifest.get("splits", {})
        train_sessions = set(splits.get("train", []))
        val_sessions = set(splits.get("validation_locked", []))
        session_ids = np.load(features_dir / "session_ids.npy", allow_pickle=True).astype(str)
        train_idx = np.flatnonzero(np.isin(session_ids, list(train_sessions)))
        val_idx = np.flatnonzero(np.isin(session_ids, list(val_sessions)))

        if len(train_idx) > 0 and len(val_idx) > 0:
            train_idx = np.random.permutation(train_idx)
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            split_name = "locked_session_split"
            split_train_sessions = sorted(train_sessions)
            split_val_sessions = sorted(val_sessions)
        else:
            print("Locked split unavailable or empty; falling back to random row split.")
            split_manifest_path = None

    if not split_manifest_path or split_name == "random_row_split":
        n_val = int(n_samples * tc.val_ratio)
        n_train = n_samples - n_val
        indices = np.random.permutation(n_samples)
        X = X[indices]
        y = y[indices]
        X_train, X_val = X[:n_train], X[n_train:]
        y_train, y_val = y[:n_train], y[n_train:]

    n_train = len(X_train)
    n_val = len(X_val)
    
    # Normalization (from training data only)
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1.0
    
    X_train_norm = (X_train - mean) / std
    X_val_norm = (X_val - mean) / std
    
    # Label normalization for mouth shape mode
    label_mean = None
    label_std = None
    if use_mouth_shape:
        label_mean = y_train.mean(axis=0)
        label_std = y_train.std(axis=0)
        label_std[label_std == 0] = 1.0
    
    # Dataloaders
    train_ds = TensorDataset(torch.from_numpy(X_train_norm), torch.from_numpy(y_train))
    val_ds = TensorDataset(torch.from_numpy(X_val_norm), torch.from_numpy(y_val))
    
    train_loader = DataLoader(train_ds, batch_size=tc.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=tc.batch_size, shuffle=False)
    
    # Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ChewNet(
        input_dim=input_dim, hidden_dim=tc.hidden_dim, num_outputs=num_outputs
    ).to(device)
    
    if use_mouth_shape:
        criterion = nn.SmoothL1Loss()
    else:
        criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=tc.lr)
    
    best_val_loss = float("inf")
    best_state = None
    epochs_no_improve = 0
    
    # Training loop
    for epoch in range(1, tc.epochs + 1):
        model.train()
        train_loss = 0.0
        
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * xb.size(0)
        
        train_loss /= n_train
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                logits = model(xb)
                loss = criterion(logits, yb)
                val_loss += loss.item() * xb.size(0)
        
        val_loss /= n_val
        
        print(f"Epoch {epoch:03d} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f}")
        
        if use_wandb:
            wandb.log({
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
            })
        
        # Early stopping
        if val_loss < best_val_loss - 1e-4:
            best_val_loss = val_loss
            best_state = model.state_dict()
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= tc.patience:
                print("Early stopping triggered.")
                break
    
    if best_state is None:
        best_state = model.state_dict()
    
    model_id = f"chewnet-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{dataset_hash[:8]}"

    # Save checkpoint with all metadata
    checkpoint = {
        "model_id": model_id,
        "model_state_dict": best_state,
        "input_dim": input_dim,
        "hidden_dim": tc.hidden_dim,
        "num_outputs": num_outputs,
        "mean": mean,
        "std": std,
        "best_val_loss": float(best_val_loss),
        "dataset_hash": dataset_hash,
        "config": config.to_dict(),
        "data_source": data_source,
        "split_name": split_name,
        "split_manifest_path": str(split_manifest_path) if split_manifest_path else None,
        "split_train_sessions": split_train_sessions,
        "split_validation_sessions": split_val_sessions,
    }
    
    if use_mouth_shape:
        checkpoint["label_names"] = ms_config.parameters
        checkpoint["label_mean"] = label_mean
        checkpoint["label_std"] = label_std
        checkpoint["mode"] = "mouth_shape"
    else:
        checkpoint["mode"] = "binary"
    
    if use_wandb:
        checkpoint["wandb_run_id"] = wandb_run_id
        checkpoint["wandb_run_url"] = wandb_run_url
    
    torch.save(checkpoint, output_path)
    print(f"Saved model to: {output_path}")
    print(f"Model ID: {model_id}")
    print(f"Best val loss: {best_val_loss:.4f}")
    
    # Log to W&B
    if use_wandb:
        artifact = wandb.Artifact(
            name="chewnet-model",
            type="model",
            description="ChewNet binary chewing detection model",
            metadata={
                "best_val_loss": best_val_loss,
                "dataset_hash": dataset_hash,
                "model_id": model_id,
                "split_name": split_name,
            },
        )
        artifact.add_file(str(output_path))
        wandb.log_artifact(artifact)
        
        wandb.summary["best_val_loss"] = best_val_loss
        wandb.summary["final_epoch"] = epoch
        
        wandb.finish()
    
    return {
        "output_path": output_path,
        "model_id": model_id,
        "best_val_loss": best_val_loss,
        "final_epoch": epoch,
        "wandb_run_id": wandb_run_id,
        "wandb_run_url": wandb_run_url,
        "mean": mean.tolist(),
        "std": std.tolist(),
    }
