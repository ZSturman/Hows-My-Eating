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
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler

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


class FocalLoss(nn.Module):
    """Binary focal loss on logits. Reduces the weight of easy examples."""

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0,
                 pos_weight: torch.Tensor | None = None):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.pos_weight = pos_weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(
            logits, targets, reduction="none", pos_weight=self.pos_weight
        )
        p = torch.sigmoid(logits)
        p_t = p * targets + (1.0 - p) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        loss = alpha_t * (1.0 - p_t).clamp(min=1e-8).pow(self.gamma) * bce
        return loss.mean()


class _NoisyTensorDataset(torch.utils.data.Dataset):
    """Wrap a tensor pair and add Gaussian noise to features at training time."""

    def __init__(self, X: torch.Tensor, y: torch.Tensor, noise_std: float):
        self.X = X
        self.y = y
        self.noise_std = noise_std

    def __len__(self) -> int:
        return self.X.size(0)

    def __getitem__(self, idx: int):
        x = self.X[idx]
        if self.noise_std > 0:
            x = x + torch.randn_like(x) * self.noise_std
        return x, self.y[idx]


def _resolve_pos_weight(pos_weight_cfg: str, y_bin: np.ndarray) -> float | None:
    """Return scalar pos_weight or None to disable."""
    if pos_weight_cfg is None:
        return None
    s = str(pos_weight_cfg).strip().lower()
    if s in {"none", "off", "false", "0", ""}:
        return None
    if s == "auto":
        n_pos = float((y_bin >= 0.5).sum())
        n_neg = float((y_bin < 0.5).sum())
        if n_pos < 1:
            print("   ⚠️  No positives in training set; pos_weight disabled.")
            return None
        return n_neg / n_pos
    try:
        return float(s)
    except ValueError:
        print(f"   ⚠️  Unrecognized pos_weight={pos_weight_cfg!r}; disabling.")
        return None


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

    session_ids_path = features_dir / "session_ids.npy"
    have_session_ids = session_ids_path.exists()

    if split_manifest_path and have_session_ids:
        with open(split_manifest_path, "r") as f:
            split_manifest = json.load(f)
        splits = split_manifest.get("splits", {})
        train_sessions = set(splits.get("train", []))
        val_sessions = set(splits.get("validation_locked", []))
        session_ids = np.load(session_ids_path, allow_pickle=True).astype(str)
        train_idx = np.flatnonzero(np.isin(session_ids, list(train_sessions)))
        val_idx = np.flatnonzero(np.isin(session_ids, list(val_sessions)))

        # Reject single-class train or validation splits — they break
        # learning (single-class train) or make val_loss uninformative
        # (single-class val). Fall back to a session-aware random split.
        train_single_class = False
        val_single_class = False
        if len(train_idx) > 0:
            yt = (y[train_idx] >= 0.5).astype(np.int32)
            train_single_class = (yt.sum() == 0) or (yt.sum() == len(yt))
        if len(val_idx) > 0:
            yv = (y[val_idx] >= 0.5).astype(np.int32)
            val_single_class = (yv.sum() == 0) or (yv.sum() == len(yv))

        if (
            len(train_idx) > 0
            and len(val_idx) > 0
            and not train_single_class
            and not val_single_class
        ):
            train_idx = np.random.permutation(train_idx)
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            split_name = "locked_session_split"
            split_train_sessions = sorted(train_sessions)
            split_val_sessions = sorted(val_sessions)
        else:
            if train_single_class:
                yt_sum = int((y[train_idx] >= 0.5).sum())
                print(
                    "⚠️  Locked TRAIN split is single-class "
                    f"(train pos={yt_sum}/{len(train_idx)}); "
                    "cannot learn from it. Falling back to session-aware split."
                )
            elif val_single_class:
                yv_sum = int((y[val_idx] >= 0.5).sum())
                print(
                    "⚠️  Locked validation split is single-class "
                    f"(val pos={yv_sum}/{len(val_idx)}); "
                    "falling back to session-aware split."
                )
            else:
                print("Locked split unavailable or empty; falling back to session-aware split.")
            split_manifest_path = None

    if split_name == "random_row_split":
        # Fallback: session-aware random split (no within-session leakage).
        # Prefer a split where train has both classes (essential for learning)
        # and val also has both classes (essential for meaningful val_loss).
        # If train cannot be made two-class with any seed, we have a data
        # problem and warn the user explicitly.
        if have_session_ids:
            session_ids = np.load(session_ids_path, allow_pickle=True).astype(str)
            unique_sessions = np.array(sorted(set(session_ids)))
            n_val_sessions = max(1, int(len(unique_sessions) * tc.val_ratio))
            best: tuple[np.ndarray, np.ndarray, set, int] | None = None  # +score
            for seed in range(64):
                rng = np.random.default_rng(42 + seed)
                order = rng.permutation(len(unique_sessions))
                val_set = set(unique_sessions[order[:n_val_sessions]])
                v_idx = np.flatnonzero(np.isin(session_ids, list(val_set)))
                t_idx = np.flatnonzero(~np.isin(session_ids, list(val_set)))
                if len(t_idx) == 0 or len(v_idx) == 0:
                    continue
                yv = (y[v_idx] >= 0.5).astype(np.int32)
                yt = (y[t_idx] >= 0.5).astype(np.int32)
                two_class_val = 0 < int(yv.sum()) < len(yv)
                two_class_train = 0 < int(yt.sum()) < len(yt)
                # Score: train-two-class is worth 2; val-two-class is worth 1.
                score = (2 if two_class_train else 0) + (1 if two_class_val else 0)
                if best is None or score > best[3]:
                    best = (t_idx, v_idx, val_set, score)
                if score == 3:
                    break
            if best is not None:
                train_idx, val_idx, val_set, score = best
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                split_name = "session_aware_random_split"
                if score < 3:
                    print(
                        "⚠️  Best session-aware split has score "
                        f"{score}/3 (train two-class={(score & 2) != 0}, "
                        f"val two-class={(score & 1) != 0}). "
                        "Add more sessions of the under-represented class to fix this."
                    )

        if split_name == "random_row_split":
            if not tc.allow_unsplit and split_manifest_path is None:
                # Caller asked for locked split but we ended up with no session info.
                # Still allow training (no hard abort) but warn loudly.
                print(
                    "   ⚠️  No session_ids.npy and no locked split — training with row-level "
                    "shuffle. Consider rerunning feature extraction or passing "
                    "training.allow_unsplit=true to silence."
                )
            n_val = int(n_samples * tc.val_ratio)
            n_train_count = n_samples - n_val
            indices = np.random.permutation(n_samples)
            X = X[indices]
            y = y[indices]
            X_train, X_val = X[:n_train_count], X[n_train_count:]
            y_train, y_val = y[:n_train_count], y[n_train_count:]

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
    feature_noise = float(getattr(tc, "feature_noise_std", 0.0)) if not use_mouth_shape else 0.0
    train_X_t = torch.from_numpy(X_train_norm)
    train_y_t = torch.from_numpy(y_train)
    val_X_t = torch.from_numpy(X_val_norm)
    val_y_t = torch.from_numpy(y_val)

    train_ds: torch.utils.data.Dataset
    if feature_noise > 0:
        train_ds = _NoisyTensorDataset(train_X_t, train_y_t, feature_noise)
    else:
        train_ds = TensorDataset(train_X_t, train_y_t)
    val_ds = TensorDataset(val_X_t, val_y_t)

    # Class-balanced sampler for binary mode
    sampler = None
    pos_weight_value: float | None = None
    if not use_mouth_shape:
        y_train_bin = (y_train >= config.evaluation.chew_threshold).astype(np.int64)
        n_pos_train = int(y_train_bin.sum())
        n_neg_train = int(len(y_train_bin) - n_pos_train)
        n_pos_val = int((y_val >= config.evaluation.chew_threshold).sum())
        n_neg_val = int(len(y_val) - n_pos_val)
        print("\nDATASET BALANCE")
        print("---------------")
        print(f"  train: pos={n_pos_train}  neg={n_neg_train}  "
              f"pos_pct={100.0 * n_pos_train / max(1, len(y_train_bin)):.1f}%")
        print(f"    val: pos={n_pos_val}  neg={n_neg_val}  "
              f"pos_pct={100.0 * n_pos_val / max(1, len(y_val)):.1f}%")

        pos_weight_value = _resolve_pos_weight(tc.pos_weight, y_train_bin)
        if pos_weight_value is not None:
            print(f"  pos_weight: {pos_weight_value:.3f}")

        if tc.use_weighted_sampler and n_pos_train > 0 and n_neg_train > 0:
            class_w = np.where(y_train_bin == 1,
                               1.0 / max(n_pos_train, 1),
                               1.0 / max(n_neg_train, 1)).astype(np.float64)
            sampler = WeightedRandomSampler(
                weights=torch.from_numpy(class_w),
                num_samples=len(class_w),
                replacement=True,
            )
            print("  weighted sampler: ON")
        else:
            print("  weighted sampler: OFF")

    if sampler is not None:
        train_loader = DataLoader(train_ds, batch_size=tc.batch_size, sampler=sampler)
    else:
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
        pw_tensor = (
            torch.tensor([pos_weight_value], dtype=torch.float32, device=device)
            if pos_weight_value is not None else None
        )
        if tc.loss == "focal":
            criterion = FocalLoss(
                alpha=tc.focal_alpha, gamma=tc.focal_gamma, pos_weight=pw_tensor
            )
            print(f"  loss: focal(alpha={tc.focal_alpha}, gamma={tc.focal_gamma})")
        else:
            criterion = nn.BCEWithLogitsLoss(pos_weight=pw_tensor)
            print(f"  loss: bce_with_logits"
                  + (f"(pos_weight={pos_weight_value:.3f})" if pw_tensor is not None else ""))
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
        "loss": getattr(tc, "loss", "bce"),
        "pos_weight_used": pos_weight_value if not use_mouth_shape else None,
        "weighted_sampler_used": (sampler is not None) if not use_mouth_shape else False,
        "feature_noise_std": feature_noise,
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
