import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_absolute_error,
    r2_score,
)

# -------------------------
# Load model
# -------------------------

CHECKPOINT_PATH = "chewnet.pth"

checkpoint = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)

input_dim = checkpoint["input_dim"]
hidden_dim = checkpoint["hidden_dim"]
num_outputs = checkpoint.get("num_outputs", 1)
mode = checkpoint.get("mode", "binary")
mean = checkpoint["mean"]
std = checkpoint["std"]

class ChewNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=32, num_outputs=1):
        super().__init__()
        self.num_outputs = num_outputs
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_outputs)
        )

    def forward(self, x):
        out = self.net(x)
        if self.num_outputs == 1:
            return out.squeeze(-1)
        return out

model = ChewNet(input_dim, hidden_dim, num_outputs)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# -------------------------
# Load *TEST* data
# -------------------------

X = np.load("features_output/X.npy").astype(np.float32)
y = np.load("features_output/y.npy").astype(np.float32)

# IMPORTANT: use SAME normalization as training
X = (X - mean) / std

X_t = torch.from_numpy(X)

# -------------------------
# Run inference
# -------------------------

with torch.no_grad():
    output = model(X_t)

# -------------------------
# Metrics
# -------------------------

if mode == "mouth_shape" and num_outputs > 1:
    preds = output.numpy()
    label_names = checkpoint.get("label_names", [f"output_{i}" for i in range(num_outputs)])

    print("\nMOUTH SHAPE EVALUATION RESULTS")
    print("-------------------------------")
    for i, name in enumerate(label_names):
        mae = mean_absolute_error(y[:, i], preds[:, i])
        rmse = np.sqrt(np.mean((y[:, i] - preds[:, i]) ** 2))
        r2 = r2_score(y[:, i], preds[:, i])
        print(f"  {name:25s}  MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}")

    overall_mae = mean_absolute_error(y, preds)
    print(f"\n  {'Overall':25s}  MAE={overall_mae:.4f}")

else:
    logits = output.numpy()
    probs = 1 / (1 + np.exp(-logits))  # sigmoid
    preds = (probs >= 0.5).astype(np.int32)

    acc = accuracy_score(y, preds)
    auc = roc_auc_score(y, probs)
    prec = precision_score(y, preds)
    rec = recall_score(y, preds)
    f1 = f1_score(y, preds)
    cm = confusion_matrix(y, preds)

    print("\nEVALUATION RESULTS")
    print("------------------")
    print(f"Accuracy:  {acc:.4f}")
    print(f"ROC AUC:   {auc:.4f}")
    print(f"Precision:{prec:.4f}")
    print(f"Recall:   {rec:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print("\nConfusion Matrix:")
    print(cm)