import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

## TO RUN: 
""" 
uvicorn server:app --host 0.0.0.0 --port 8000 --reload 
""" 


# =========================
# Model definition (same as training)
# =========================

class ChewNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)  # logits
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)  # [B]

# =========================
# Load checkpoint
# =========================

CHECKPOINT_PATH = "chewnet.pth"

checkpoint = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)

input_dim = checkpoint["input_dim"]
hidden_dim = checkpoint["hidden_dim"]
mean = checkpoint["mean"]          # numpy array, shape [input_dim]
std = checkpoint["std"]            # numpy array, shape [input_dim]
std[std == 0] = 1.0                # safety, same as training

model = ChewNet(input_dim=input_dim, hidden_dim=hidden_dim)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

device = torch.device("cpu")
model.to(device)

# convert normalization stats to torch tensors
mean_t = torch.from_numpy(mean).to(device)
std_t = torch.from_numpy(std).to(device)

# =========================
# FastAPI app + schema
# =========================

app = FastAPI(title="ChewNet API")

class PredictRequest(BaseModel):
    # Single feature vector, e.g. 7 floats
    features: List[float]

class PredictResponse(BaseModel):
    probability: float  # model's P(chew)
    label: int          # 0 or 1 based on threshold

class PredictWithLabelRequest(BaseModel):
    features: List[float]
    true_label: int  # 0 or 1

class PredictWithLabelResponse(BaseModel):
    probability: float
    label: int
    true_label: int
    correct: bool

class BatchTestRequest(BaseModel):
    chewing: List[List[float]]
    # use JSON key "not-chewing" to match test.json
    not_chewing: List[List[float]] = Field(alias="not-chewing")

class BatchTestResponse(BaseModel):
    total_samples: int
    total_correct: int
    accuracy: float
    chewing_correct: int
    chewing_total: int
    not_chewing_correct: int
    not_chewing_total: int

class ThresholdMetrics(BaseModel):
    threshold: float
    accuracy: float
    chewing_recall: float
    not_chewing_recall: float

class ThresholdEvalRequest(BaseModel):
    thresholds: List[float]
    chewing: List[List[float]]
    not_chewing: List[List[float]] = Field(alias="not-chewing")

class ThresholdEvalResponse(BaseModel):
    results: List[ThresholdMetrics]

# =========================
# Helper
# =========================

def predict_single(features: List[float], threshold: float = 0.5):
    if len(features) != input_dim:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {input_dim} features, got {len(features)}"
        )

    x = torch.tensor(features, dtype=torch.float32, device=device)  # [D]
    # normalize with same mean/std as training
    x = (x - mean_t) / std_t
    x = x.unsqueeze(0)  # [1, D]

    with torch.no_grad():
        logits = model(x)          # [1]
        prob = torch.sigmoid(logits)[0].item()

    label = int(prob >= threshold)
    return prob, label

# =========================
# Routes
# =========================

@app.get("/")
def root():
    return {"message": "ChewNet server is running."}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    prob, label = predict_single(req.features)
    return PredictResponse(probability=prob, label=label)

@app.post("/predict_with_label", response_model=PredictWithLabelResponse)
def predict_with_label(req: PredictWithLabelRequest):
    prob, pred_label = predict_single(req.features)
    correct = pred_label == req.true_label
    return PredictWithLabelResponse(
        probability=prob,
        label=pred_label,
        true_label=req.true_label,
        correct=correct,
    )

@app.post("/evaluate_batch", response_model=BatchTestResponse)
def evaluate_batch(req: BatchTestRequest):
    chewing_total = len(req.chewing)
    not_chewing_total = len(req.not_chewing)

    chewing_correct = 0
    not_chewing_correct = 0

    # Label 1 for chewing
    for feats in req.chewing:
        _, pred = predict_single(feats)
        if pred == 1:
            chewing_correct += 1

    # Label 0 for not-chewing
    for feats in req.not_chewing:
        _, pred = predict_single(feats)
        if pred == 0:
            not_chewing_correct += 1

    total_samples = chewing_total + not_chewing_total
    total_correct = chewing_correct + not_chewing_correct
    accuracy = float(total_correct) / total_samples if total_samples > 0 else 0.0

    return BatchTestResponse(
        total_samples=total_samples,
        total_correct=total_correct,
        accuracy=accuracy,
        chewing_correct=chewing_correct,
        chewing_total=chewing_total,
        not_chewing_correct=not_chewing_correct,
        not_chewing_total=not_chewing_total,
    )

@app.post("/evaluate_thresholds", response_model=ThresholdEvalResponse)
def evaluate_thresholds(req: ThresholdEvalRequest):
    # Precompute probabilities for all samples
    chewing_probs: List[float] = []
    not_chewing_probs: List[float] = []

    for feats in req.chewing:
        prob, _ = predict_single(feats, threshold=0.5)
        chewing_probs.append(prob)

    for feats in req.not_chewing:
        prob, _ = predict_single(feats, threshold=0.5)
        not_chewing_probs.append(prob)

    results: List[ThresholdMetrics] = []

    total_chewing = len(chewing_probs)
    total_not = len(not_chewing_probs)
    total_samples = total_chewing + total_not

    for thr in req.thresholds:
        # Chewing recall (TPR): fraction of chewing samples with prob >= thr
        tp = sum(1 for p in chewing_probs if p >= thr)
        chewing_recall = tp / total_chewing if total_chewing > 0 else 0.0

        # Not-chewing recall (TNR): fraction of not-chewing samples with prob < thr
        tn = sum(1 for p in not_chewing_probs if p < thr)
        not_chewing_recall = tn / total_not if total_not > 0 else 0.0

        total_correct = tp + tn
        accuracy = total_correct / total_samples if total_samples > 0 else 0.0

        results.append(
            ThresholdMetrics(
                threshold=thr,
                accuracy=accuracy,
                chewing_recall=chewing_recall,
                not_chewing_recall=not_chewing_recall,
            )
        )

    return ThresholdEvalResponse(results=results)