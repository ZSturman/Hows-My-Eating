# Data Pipeline

This stage transforms raw motion sensor data into a trained, deployable CoreML model with full experiment tracking.

## Pipeline Overview

```
Raw CSV Files (data/raw_sessions/)
    ↓
[1] Transform: Add soft continuous labels
    ↓
Transformed CSVs (data/transformed/)
    ↓
[2] Feature Extraction: 12 time/frequency features per 0.75s window
    ↓
Feature Arrays (data/features/X.npy, y.npy)
    ↓
[3] Model Training: 3-layer MLP with W&B experiment tracking
    ↓
Trained Model (models/chewnet.pth)
    ↓
[4] Export: CoreML model + normalization constants
    ↓
Deployable Model (exports/ChewNet.mlpackage)
```

## Quick Start

**Prerequisites**:
```bash
pip install -r requirements.txt
wandb login  # First-time only (free account at wandb.ai)
```

**Run full pipeline**:
```bash
python main.py --stats
```

This executes all 4 steps and prompts for training/evaluation/export.

## Step-by-Step Usage

### 1. Transform Raw Data

Add soft continuous labels to raw labeled CSVs:

```bash
python main.py
```

**What it does**:
- Reads raw CSVs from `data/raw_sessions/`
- Generates smooth [0, 1] labels using transition ramps
- Writes transformed CSVs to `data/transformed/`
- Moves processed files to `data/raw_sessions/processed/`

**Parameters**:
- `--transition-sec 0.6`: Short chew transition window
- `--long-chew-sec 3.0`: Threshold for long chew detection
- `--long-ramp-sec 1.5`: Ramp time for long chews

### 2. Extract Features

Generate feature arrays for training:

```bash
# Automatically runs after transform in main.py
```

**What it does**:
- Reads transformed CSVs
- Extracts 12 features per 0.75s window (0.1s step)
- Writes `X.npy`, `y.npy`, `feature_names.txt` to `data/features/`

**Features (12 total)**:
1. Mean acceleration magnitude
2. Variance of acceleration magnitude
3. RMS acceleration magnitude
4. Mean gyroscope magnitude
5. RMS gyroscope magnitude
6. RMS jerk
7. Zero crossing rate
8. Chew bandpower (1-3 Hz)
9. Bandpower (0.8-1.5 Hz)
10. Bandpower (2-4 Hz)
11. Spectral centroid
12. Spectral rolloff (85%)

**Parameters**:
- `--window-sec 0.75`: Feature window size
- `--step-sec 0.1`: Sliding window step

### 3. Train Model

Train the neural network with W&B tracking:

```bash
# Prompted after feature extraction in main.py
# Or run directly:
cd training
python train_pytorch.py --input_dir ../data/features --output_model ../models/chewnet.pth
```

**What it does**:
- Loads `X.npy` and `y.npy`
- Splits into train/val (80/20)
- Computes normalization from training set
- Trains 3-layer MLP with early stopping
- Logs all metrics to Weights & Biases
- Saves best model to `models/chewnet.pth`

**Hyperparameters**:
```bash
--batch-size 256          # Training batch size
--lr 1e-3                 # Learning rate
--epochs 50               # Max epochs
--val-ratio 0.2           # Validation split
--hidden-dim 32           # Hidden layer size
--patience 5              # Early stopping patience
```

**W&B Logging**:
- Project: `chewsense` (private by default)
- Tracked: All hyperparameters, loss, accuracy per epoch
- Artifacts: Model checkpoint + normalization JSON
- Traceability: Run ID embedded in model file

### 4. Export Model

Convert PyTorch model to CoreML and dump normalization:

```bash
# Prompted after training in main.py
# Or run directly:
python scripts/export_coreML.py
python scripts/dump_norm.py
```

**What it does**:
- `export_coreML.py`: PyTorch → CoreML (`exports/ChewNet.mlpackage`)
- `dump_norm.py`: Extract mean/std to JSON (`exports/chewnet_norm.json`)

**Generate Swift constants** (for app integration):
```bash
python scripts/generate_swift_constants.py
```

This creates `../04-RealWorldTesting/Generated/NormalizationConstants.swift` with:
- `FEATURE_MEAN` array (12 values)
- `FEATURE_STD` array (12 values)
- W&B run ID in header comments for traceability

## Dataset Information

**Current dataset**: See [`DATASET.md`](DATASET.md)
- 24 sessions (~1 hour total)
- 7 eating, 17 not-eating
- All AirPods Pro motion data

**Regenerate dataset documentation**:
```bash
python scripts/generate_dataset_metadata.py
```

## Configuration & Tuning

All parameters exposed via CLI in `main.py`:

**Soft Label Generation**:
```bash
--transition-sec 0.6      # Short chew transition window
--long-chew-sec 3.0       # Threshold for long chew detection  
--long-ramp-sec 1.5       # Ramp time for long chews
```

**Feature Extraction**:
```bash
--window-sec 0.75         # Feature window size
--step-sec 0.1            # Sliding window step
```

**Detection Thresholds** (logged to W&B, used in evaluation):
```bash
--chew-threshold 0.5      # Binarize soft labels for eval
--pred-threshold 0.5      # Model probability → binary
--alpha 0.4               # EMA smoothing factor
--high-threshold 0.6      # Start chewing episode
--low-threshold 0.4       # End chewing episode
--min-start-windows 3     # Consecutive windows to trigger
--min-end-windows 2       # Consecutive windows to exit
```

**Training**:
```bash
--batch-size 256
--lr 1e-3
--epochs 50
--val-ratio 0.2
--hidden-dim 32
--patience 5
```

## Experiment Tracking

All training runs logged to **Weights & Biases**:

**View experiments**:
```bash
wandb login  # If not already logged in
# Then view at: https://wandb.ai/<your-username>/chewsense
```

**Logged metrics**:
- Hyperparameters (all CLI args + thresholds)
- Per-epoch: train_loss, val_loss
- Final: best_val_loss, final_epoch
- Model artifacts: `chewnet.pth`, `chewnet_norm.json`

**Traceability**:
- Each model checkpoint contains `wandb_run_id` and `wandb_run_url`
- Swift constants file includes W&B run ID in header
- Enables tracking deployed models back to training runs

## New Pipeline CLI (`main_new.py`)

A modular CLI is available for more flexible pipeline control:

```bash
# Full pipeline from sample data (ships with repo)
python main_new.py sample

# Full pipeline from data exported from iOS app
python main_new.py from-app

# Full pipeline from raw CSV files
python main_new.py from-raw --input-dir data/raw_sessions

# Resume from existing feature files
python main_new.py from-features

# Deploy model to Xcode project
python main_new.py deploy
```

### Subcommands

| Command | Description |
|---------|-------------|
| `sample` | Run pipeline using sample data in `data/sample/` |
| `from-app` | Process data exported from ChewSense Data Collection app |
| `from-raw` | Process raw CSV files from specified directory |
| `from-features` | Skip extraction, train from existing `X.npy`/`y.npy` |
| `deploy` | Copy model + constants to Xcode project |

### Configuration File

Use `--config` to override defaults:
```bash
python main_new.py sample --config config/my_experiment.yaml
```

Default configuration: [`config/defaults.yaml`](config/defaults.yaml)

### New Directory Structure

```
data/
├── sample/      # Sample CSVs (git-tracked, for demos)
├── user/        # User data (git-ignored)
└── derived/     # Pipeline outputs (git-ignored)
    ├── transformed/
    ├── features/
    ├── models/
    └── exports/
```

---

## Directory Structure

```
02-DataPipeline/
├── main.py                      # Orchestration script (full pipeline)
├── requirements.txt             # Python dependencies (includes wandb)
├── DATASET.md                   # Dataset documentation (auto-generated)
│
├── data/
│   ├── raw_sessions/            # Raw CSV files from data collection app
│   │   └── processed/           # Archived after processing
│   ├── transformed/             # CSVs with soft labels added
│   └── features/                # X.npy, y.npy, feature_names.txt
│
├── scripts/
│   ├── get_features.py          # Feature extraction logic
│   ├── dataset_stats.py         # Dataset statistics computation
│   ├── export_coreML.py         # PyTorch → CoreML conversion
│   ├── dump_norm.py             # Extract normalization to JSON
│   ├── generate_swift_constants.py      # Auto-generate Swift code
│   ├── generate_dataset_metadata.py     # Create DATASET.md
│   └── server.py                # FastAPI inference server (optional)
│
├── training/
│   └── train_pytorch.py         # Model training with W&B integration
│
├── models/
│   └── chewnet.pth              # Trained model checkpoint
│
├── exports/
│   ├── ChewNet.mlpackage/       # CoreML model for iOS/macOS
│   └── chewnet_norm.json        # Normalization parameters
│
└── logs/
    └── runs/                    # Per-run logs (pipeline.log, run_config.json)
```

## Troubleshooting

**Issue**: `wandb not found`
```bash
pip install wandb
wandb login
```

**Issue**: No raw CSV files found
- Place CSVs in `data/raw_sessions/`
- Or use data collection app to generate new sessions

**Issue**: Training crashes with CUDA out of memory
```bash
python main.py --batch-size 128  # Reduce batch size
```

**Issue**: Model performance poor
- Check dataset balance (eating vs. not-eating ratio)
- Increase dataset size
- Tune hyperparameters via W&B sweeps

**Issue**: Swift constants out of sync
- Regenerate after every training run:
```bash
python scripts/generate_swift_constants.py
```

## Next Steps

1. **Train the model**: Run `python main.py`
2. **Evaluate performance**: Check W&B dashboard for metrics
3. **Deploy to app**: Copy exports to `04-RealWorldTesting/`
4. **Test in real-time**: Build and run iOS/macOS app

See [`../03-ModelEvaluation/README.md`](../03-ModelEvaluation/README.md) for offline evaluation.
See [`../04-RealWorldTesting/README.md`](../04-RealWorldTesting/README.md) for deployment.

---

**Questions?** See main [README.md](../README.md) or check `ProjectHistory/` for development evolution.
