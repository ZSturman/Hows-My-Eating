import os
import argparse
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    print("Warning: wandb not available. Install with: pip install wandb")


# ============================================================
# MODEL
# ============================================================

class ChewNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),  # BCEWithLogitsLoss expects logits
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, D]
        return self.net(x).squeeze(-1)  # [B]


# ============================================================
# TRAINING
# ============================================================

def train(
    input_dir: str,
    output_path: str,
    batch_size: int = 256,
    lr: float = 1e-3,
    epochs: int = 50,
    val_ratio: float = 0.2,
    hidden_dim: int = 32,
    patience: int = 5,
    use_wandb: bool = True,
    wandb_project: str = "chewsense",
    wandb_run_name: Optional[str] = None,
    config: Optional[dict] = None,
) -> None:
    """Train ChewNet on precomputed features stored in X.npy, y.npy.

    Args:
        input_dir: Directory containing X.npy and y.npy.
        output_path: Path to save the trained model checkpoint (chewnet.pth).
        batch_size: Training batch size.
        lr: Learning rate for Adam optimizer.
        epochs: Max number of epochs to train.
        val_ratio: Fraction of data to use for validation.
        hidden_dim: Hidden layer size for ChewNet.
        patience: Early stopping patience (epochs without improvement).
        use_wandb: Whether to log to Weights & Biases.
        wandb_project: W&B project name.
        wandb_run_name: Optional W&B run name.
        config: Additional config dict to log to W&B (e.g., threshold parameters).
    """

    # -------------------------
    # Initialize W&B
    # -------------------------
    if use_wandb and WANDB_AVAILABLE:
        wandb_config = {
            "batch_size": batch_size,
            "lr": lr,
            "epochs": epochs,
            "val_ratio": val_ratio,
            "hidden_dim": hidden_dim,
            "patience": patience,
            "architecture": "3-layer MLP",
        }
        if config:
            wandb_config.update(config)
        
        wandb.init(
            project=wandb_project,
            name=wandb_run_name,
            config=wandb_config,
        )
    elif use_wandb and not WANDB_AVAILABLE:
        print("Warning: W&B logging requested but wandb not installed. Continuing without logging.")
        use_wandb = False

    # -------------------------
    # Load data
    # -------------------------
    X_path = os.path.join(input_dir, "X.npy")
    y_path = os.path.join(input_dir, "y.npy")

    X = np.load(X_path).astype(np.float32)
    y = np.load(y_path).astype(np.float32)

    n_samples, input_dim = X.shape
    print(f"Loaded X: {X.shape}, y: {y.shape}")

    # -------------------------
    # Train/val split
    # -------------------------
    n_val = int(n_samples * val_ratio)
    n_train = n_samples - n_val

    # Shuffle before split
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    X_train, X_val = X[:n_train], X[n_train:]
    y_train, y_val = y[:n_train], y[n_train:]

    # -------------------------
    # Normalization (train only)
    # -------------------------
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1.0  # avoid division by zero

    X_train_norm = (X_train - mean) / std
    X_val_norm = (X_val - mean) / std

    # -------------------------
    # Dataloaders
    # -------------------------
    train_ds = TensorDataset(
        torch.from_numpy(X_train_norm), torch.from_numpy(y_train)
    )
    val_ds = TensorDataset(
        torch.from_numpy(X_val_norm), torch.from_numpy(y_val)
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # -------------------------
    # Model / loss / optimizer
    # -------------------------
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = ChewNet(input_dim=input_dim, hidden_dim=hidden_dim).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_loss = float("inf")
    best_state = None
    epochs_no_improve = 0

    # -------------------------
    # Training loop
    # -------------------------
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)

            optimizer.zero_grad()
            logits = model(xb)  # [B]
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
                xb = xb.to(device)
                yb = yb.to(device)
                logits = model(xb)
                loss = criterion(logits, yb)
                val_loss += loss.item() * xb.size(0)

        val_loss /= n_val

        print(
            f"Epoch {epoch:03d} | "
            f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f}"
        )

        # Log to W&B
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
            if epochs_no_improve >= patience:
                print("Early stopping triggered.")
                break

    # -------------------------
    # Save best model + normalization
    # -------------------------
    if best_state is None:
        best_state = model.state_dict()

    checkpoint = {
        "model_state_dict": best_state,
        "input_dim": input_dim,
        "hidden_dim": hidden_dim,
        "mean": mean,
        "std": std,
        "best_val_loss": best_val_loss,
    }
    
    if use_wandb:
        checkpoint["wandb_run_id"] = wandb.run.id
        checkpoint["wandb_run_url"] = wandb.run.get_url()
    
    torch.save(checkpoint, output_path)

    print(f"Saved model to: {output_path}")
    print(f"Best val loss: {best_val_loss:.4f}")

    # Log to W&B
    if use_wandb:
        # Save model as W&B artifact
        artifact = wandb.Artifact(
            name="chewnet-model",
            type="model",
            description="ChewNet binary chewing detection model",
        )
        artifact.add_file(output_path)
        wandb.log_artifact(artifact)
        
        # Log final metrics
        wandb.summary["best_val_loss"] = best_val_loss
        wandb.summary["final_epoch"] = epoch
        
        wandb.finish()


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True, help="Directory with X.npy, y.npy")
    parser.add_argument("--output_model", default="chewnet.pth")

    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--hidden_dim", type=int, default=32)
    parser.add_argument("--patience", type=int, default=5)

    args = parser.parse_args()

    train(
        input_dir=args.input_dir,
        output_path=args.output_model,
        batch_size=args.batch_size,
        lr=args.lr,
        epochs=args.epochs,
        val_ratio=args.val_ratio,
        hidden_dim=args.hidden_dim,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()