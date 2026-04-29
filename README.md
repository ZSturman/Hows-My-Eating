# ChewSense: Hierarchical Eating Behavior Analysis

**From chew detection to meal intelligence—building a complete understanding of eating patterns through AirPods motion sensors.**

---

## 🎯 Project Vision

ChewSense is evolving from simple binary chewing detection into a comprehensive **hierarchical eating behavior analysis system** that understands:
- **Individual chews** → Detected in real-time
- **Bite events** → Clustered from chew sequences
- **Meal structure** → Pace, duration, and patterns
- **Eating quality** → Scientifically-grounded health metrics
- **Real-time feedback** → Actionable interventions during eating

The system provides researchers, health professionals, and individuals with unprecedented insight into eating behavior through a non-invasive, always-available wearable sensor.

---

## ⚠️ Hardware Requirements

**REQUIRED**: AirPods Pro (1st, 2nd, or 3rd generation) or AirPods Max

These models include motion sensors (accelerometer + gyroscope) necessary for chewing detection. Standard AirPods and older generations **will not work**.

---

## 🏗️ Project Structure

This repository is organized into **5 lifecycle stages** representing the complete pipeline from data collection to deployment:

```
ChewSense/
├── 01-DataCollection/          ✅ COMPLETE - iOS app for data gathering
├── 02-DataPipeline/             🚧 ACTIVE - Transform, train, evaluate, registry, deploy
├── 03-ModelEvaluation/          ✅ COMPLETE - Offline metrics and analysis
├── 04-RealWorldTesting/         🚧 ACTIVE - Canonical iOS/macOS inference + field-test logging
├── 05-FutureStages/             📋 PLANNED - Hierarchical analysis roadmap
├── docs/                        📚 WORKFLOWS - Organization and model iteration guides
└── ProjectHistory/              📚 ARCHIVE - Development evolution
```

Each stage is self-contained with its own README explaining purpose, current state, and next steps.

---

## 🚀 Quick Start

### Stage 1: Data Collection (Optional)

**Option A**: Use the existing dataset (included in `02-DataPipeline/data/raw_sessions/`)

**Option B**: Collect your own data
1. Download [ChewSense Data Collection](https://apps.apple.com/us/app/chew-sense-collect-and-label/id6755277802) from the App Store
2. Record eating and not-eating sessions
3. Export sessions and place in `02-DataPipeline/data/raw_sessions/`

See [`01-DataCollection/README.md`](01-DataCollection/ChewSense-DataCollection/README.md) for details.

---

### Stage 2: Train the Model

**Prerequisites**:
```bash
cd 02-DataPipeline
pip install -r requirements.txt
wandb login  # First-time setup (free account at wandb.ai)
```

**Run the pipeline**:
```bash
python main.py --stats
```

This will:
1. Transform raw CSVs (add soft labels)
2. Extract 12 features per 0.75s window
3. Prompt to train the model
4. Log all experiments to Weights & Biases
5. Export CoreML model + normalization constants

**Optional**: Generate Swift constants for app integration
```bash
python scripts/generate_swift_constants.py
```

See [`02-DataPipeline/README.md`](02-DataPipeline/README.md) for advanced configuration.

**New modular CLI**:
```bash
python main_new.py sample --no-wandb
python main_new.py evaluate --model models/chewnet.pth
python main_new.py from-field-test --input data/user/field_tests
python main_new.py registry --latest
```

---

### Stage 3: Evaluate Performance

```bash
cd 03-ModelEvaluation
python evaluate.py --model ../02-DataPipeline/models/chewnet.pth
```

Generates:
- Accuracy, AUC, precision, recall, F1 score
- Confusion matrix
- ROC curve visualization

---

### Stage 4: Real-World Testing

**iOS Testing**:
1. Open `04-RealWorldTesting/ChewSense-RealTime/ChewSenseDebuggingModel.xcodeproj` in Xcode
2. Connect AirPods Pro/Max
3. Build and run on iPhone/iPad
4. Start chewing—see live detection!

**macOS Testing** (requires Mac Catalyst support—see TODO):
1. Select "My Mac (Designed for iPad)" as target
2. Build and run
3. Live detection on macOS

The canonical app is `ChewSenseDebuggingModel`. It displays:
- Real-time chewing probability
- Smoothed state (idle/chewing)
- False-positive, missed-chew, and correct feedback controls
- Exportable field-test session bundles for retraining

See [`04-RealWorldTesting/README.md`](04-RealWorldTesting/README.md) for details.

For the full improvement loop, see:
- [`docs/PROJECT_ORGANIZATION.md`](docs/PROJECT_ORGANIZATION.md)
- [`docs/MODEL_ITERATION_WORKFLOW.md`](docs/MODEL_ITERATION_WORKFLOW.md)
- [`docs/REAL_WORLD_TEST_PROTOCOL.md`](docs/REAL_WORLD_TEST_PROTOCOL.md)

---

## 📊 Current Capabilities

### ✅ What Works Today

| Feature | Status | Description |
|---------|--------|-------------|
| **Data Collection** | ✅ Complete | iOS app for labeled motion+video recording |
| **Soft Label Generation** | ✅ Complete | Smooth continuous labels for training |
| **Feature Extraction** | ✅ Complete | 12 time/frequency features |
| **Model Training** | ✅ Complete | 3-layer MLP with early stopping |
| **W&B Integration** | ✅ Complete | Full experiment tracking |
| **CoreML Export** | ✅ Complete | Deployable iOS/macOS model |
| **Real-Time Detection** | ✅ Complete | Live binary chewing classification |
| **State Machine** | ✅ Complete | Hysteresis-based episode detection |
| **Field-Test Import** | ✅ Added | App feedback windows can become curated sessions |
| **Local Model Registry** | ✅ Added | Model id, manifests, metrics, constants |

### 🚧 In Progress

| Feature | Status | Timeline |
|---------|--------|----------|
| **Real-world accuracy tuning** | 🚧 Active | Needs repeated app tests and retraining |
| **Locked split discipline** | 🚧 Active | Split manifests added; more regression data needed |
| **Device validation** | 🚧 Active | Requires physical iPhone/Mac + AirPods test passes |

### 📋 Planned Future Stages

See [`05-FutureStages/README.md`](05-FutureStages/README.md) for the complete roadmap.

**Stage 02**: [Bite Segmentation](05-FutureStages/02-BiteSegmentation/README.md)
- Temporal clustering to extract individual bites
- Bite timestamps, durations, chew counts
- ~1-2 weeks implementation

**Stage 03**: [Meal Structure Analysis](05-FutureStages/03-MealStructure/README.md)
- Meal boundary detection
- Eating pace and rhythm metrics
- Inter-bite interval analysis
- ~2-3 weeks implementation

**Stage 04**: [Quality Evaluation](05-FutureStages/04-QualityEvaluation/README.md)
- Science-backed quality scores (0-100)
- Pace, thoroughness, consistency, mindfulness
- Interpretable feedback generation
- ~4-5 weeks implementation

**Stage 05**: [Real-Time Feedback](05-FutureStages/05-RealtimeFeedback/README.md)
- Just-in-time interventions during eating
- Haptic/visual/audio modalities
- Behavior change tracking
- ~4-6 weeks implementation

---

## 🎓 Scientific Foundation

ChewSense is grounded in peer-reviewed research:

**Chewing & Eating Rate**:
- Zhu & Hollis (2014): 40 chews/bite reduces intake by 12%
- Ohkuma et al. (2015): Fast eating doubles obesity risk
- Robinson et al. (2014): Mindful eating reduces overconsumption

**Behavior Change**:
- Nahum-Shani et al. (2018): Just-in-time adaptive interventions
- Michie et al. (2013): Behavior change technique taxonomy

**Full references** in each stage's README.

---

## 📈 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       Data Collection                             │
│  AirPods Motion Sensors + Video → Labeled CSV                    │
│  (App Store: ChewSense Data Collection)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Data Pipeline (Python)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Transform │→ │ Features │→ │  Train   │→ │  Export  │        │
│  │(Soft     │  │(12 time/ │  │  (3-MLP  │  │ (CoreML) │        │
│  │ Labels)  │  │  freq)   │  │  +W&B)   │  │          │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Real-Time Testing (Swift/iOS/macOS)                  │
│  AirPods → Features → CoreML Inference → State Machine           │
│           → Live UI (probability, state, logs)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Future: Hierarchical Analysis                  │
│  Chews → Bites → Meals → Quality Scores → Real-Time Feedback    │
│  (Planned stages 02-05, see 05-FutureStages/)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration & Tuning

All detection parameters are exposed via CLI for experimentation:

**Soft Label Generation** (`main.py`):
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

**Detection Thresholds**:
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
--patience 5              # Early stopping patience
```

---

## 📚 Dataset

**Current tracked dataset**: 24 sessions (~1 hour total)
- 7 eating sessions
- 17 not-eating sessions
- All AirPods Pro motion data + labels

New personal recordings and field-test bundles should go under `02-DataPipeline/data/user/` and remain git-ignored. Reviewed imports go under `02-DataPipeline/data/curated/`.

**Format**:
- CSV: `timestamp, ax, ay, az, gx, gy, gz, label`
- Videos excluded from git (see `.gitignore`)

**Generate metadata**:
```bash
cd 02-DataPipeline
python scripts/generate_dataset_metadata.py
```

See [`DATASET.md`](02-DataPipeline/DATASET.md) for session details.

---

## 🤝 Contributing

We welcome contributions at any stage:

**Data Collection**:
- Record diverse eating scenarios (different foods, environments)
- Improve labeling precision

**Model Development**:
- Experiment with architectures (CNN, LSTM, Transformer)
- Hyperparameter tuning
- Cross-validation

**Feature Engineering**:
- New time/frequency features
- Food-type specific features

**Swift Implementation**:
- Complete FFT parity with Python
- Optimize performance
- Add macOS support

**Future Stages**:
- Implement bite segmentation algorithms
- Build meal analysis tools
- Design quality evaluation metrics

**Contribution process**:
1. Fork the repository
2. Create a feature branch
3. Run existing tests (when available)
4. Submit pull request with clear description

---

## 🔬 Research Use

This project is designed for research reproducibility:

- **W&B integration**: All experiments logged with hyperparameters
- **Versioned models**: Traceability from model → W&B run → training data
- **Open dataset**: Shareable motion+label data (videos optional)
- **Documented pipeline**: Every step from raw data → deployed model

**Citation**: If you use ChewSense in research, please cite this repository and reference the scientific papers in [`05-FutureStages/`](05-FutureStages/) READMEs.

---

## 📱 App Store

**Data Collection App**: [ChewSense: Collect and Label](https://apps.apple.com/us/app/chew-sense-collect-and-label/id6755277802)

This app is **finalized and published**. The code in `01-DataCollection/` reflects the production version.

---

## 📖 Project History

See [`ProjectHistory/README.md`](ProjectHistory/README.md) for the evolution of this project from initial prototype to current architecture. This shows the iterative development process and lessons learned.


---

## 🙏 Acknowledgments

- **Scientific community**: Research papers that inform our approach
- **Apple**: CoreML and AirPods motion API
- **Weights & Biases**: Experiment tracking platform
- **Open-source tools**: PyTorch, scikit-learn, pandas, numpy


---

## 🗺️ Roadmap Status

| Stage | Status | Completion |
|-------|--------|------------|
| **01-DataCollection** | ✅ Complete | 100% |
| **02-DataPipeline** | 🚧 Active | 90% |
| **03-ModelEvaluation** | ✅ Complete | 100% |
| **04-RealWorldTesting** | 🚧 Active | 90% |
| **05-BiteSegmentation** | 📋 Planned | 0% |
| **06-MealStructure** | 📋 Planned | 0% |
| **07-QualityEvaluation** | 📋 Planned | 0% |
| **08-RealtimeFeedback** | 📋 Planned | 0% |

**Last Updated**: April 28, 2026
