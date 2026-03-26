import torch
import torch.nn as nn
import coremltools as ct

# ---- 1) Define the same model as in train_pytorch.py ----

class ChewNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),   # logit
        )

    def forward(self, x):
        # x: [B, D]
        return self.net(x).squeeze(-1)  # [B]


# ---- 2) Load checkpoint ----

CHECKPOINT_PATH = "chewnet.pth"

ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)

input_dim = ckpt["input_dim"]
hidden_dim = ckpt["hidden_dim"]

model = ChewNet(input_dim=input_dim, hidden_dim=hidden_dim)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

# Option A: let CoreML output the logit, and apply sigmoid in Swift
wrapped = model

# Option B: append sigmoid so CoreML outputs probability directly:
# wrapped = nn.Sequential(model, nn.Sigmoid())
# wrapped.eval()

# ---- 3) Trace the model ----

example_input = torch.randn(1, input_dim)  # shape [1, 12]
traced = torch.jit.trace(wrapped, example_input)
traced.eval()

# ---- 4) Convert to CoreML ----

# Input name will be "input" with shape [1, input_dim]
mlmodel = ct.convert(
    traced,
    inputs=[ct.TensorType(name="input", shape=example_input.shape)],
)

# Optional: rename output to "logit" or "prob"
# Note: for mlprogram models, we must reconstruct with weights_dir.
spec = mlmodel.get_spec()
print("Output feature name(s):")
for out in spec.description.output:
    print(" -", out.name)

# Example of renaming first output to "logit" (or use "prob" if you prefer)
old_name = spec.description.output[0].name
ct.utils.rename_feature(spec, old_name, "logit")

# Rebuild the MLModel with the associated weights directory
mlmodel_renamed = ct.models.MLModel(spec, weights_dir=mlmodel.weights_dir)
mlmodel_renamed.save("ChewNet.mlpackage")
print("Saved CoreML model as ChewNet.mlpackage")