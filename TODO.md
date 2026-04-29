# TODO: Remaining Work

This file tracks remaining work for the ChewSense project.

---

## ✅ Recently Completed (Refactor Phase)

These tasks were completed in the comprehensive refactor:

- [x] **Pipeline module** - Created `02-DataPipeline/pipeline/` with modular components
- [x] **New CLI** - `main_new.py` with subcommands (sample, from-app, from-raw, from-features, deploy)
- [x] **Config system** - YAML-based configuration in `config/defaults.yaml`
- [x] **Data directory restructure** - `data/sample/`, `data/user/`, `data/derived/`
- [x] **W&B integration** - Dataset hash, artifacts, run ID in Swift constants
- [x] **Deploy script** - `pipeline/deploy.py` copies model + generates Swift constants
- [x] **Swift FFT features** - `FrequencyFeatures.swift` with vDSP-based implementation
- [x] **Feature parity validation** - `tests/validate_features.py` + XCTest suite
- [x] **macOS support** - Platform conditionals, `MACOS_SETUP.md` guide
- [x] **ContentView refactor** - Modular structure (Features/, Managers/, Models/, Views/, Generated/)
- [x] **Runtime config UI** - `ConfigurationView.swift` with sliders and JSON export
- [x] **Future stage scaffolds** - Python scaffolds + DESIGN.md for all future stages
- [x] **Documentation** - Updated READMEs for 02-DataPipeline, 04-RealWorldTesting
- [x] **Field-test loop** - App session bundles, feedback import, CLI evaluate, local registry
- [x] **Canonical app target** - Xcode project/scheme points at modular `ChewSenseDebuggingModel`

---

## 🔴 High Priority

### 1. Run End-to-End Pipeline Test
**Purpose**: Validate the refactored pipeline works correctly

**Steps**:
1. Run `python main_new.py sample --no-wandb` to test with sample data
2. Verify model trains successfully
3. Run `python main_new.py evaluate --model models/chewnet.pth`
4. Run `python main_new.py deploy --force` to copy to Xcode project
5. Build and run iOS app
6. Verify real-time detection works

**Estimated Effort**: 1-2 hours

---

### 2. Real-World Field-Test Pass
**Purpose**: Capture false positives and missed chewing from the deployed model

**Steps**:
1. Run the canonical `ChewSenseDebuggingModel` app on iPhone with AirPods
2. Complete the scenarios in `docs/REAL_WORLD_TEST_PROTOCOL.md`
3. Export the session bundle
4. Place it under `02-DataPipeline/data/user/field_tests/`
5. Run `python main_new.py from-field-test --input data/user/field_tests`

**Estimated Effort**: 1-2 hours

---

### 3. Enable/Verify Mac Catalyst in Xcode
**Purpose**: Allow running on macOS

**Steps**:
1. Open `ChewSenseDebuggingModel.xcodeproj`
2. In target settings, add "Mac (Mac Catalyst)" to Supported Destinations
3. Build and test on macOS

See [MACOS_SETUP.md](04-RealWorldTesting/ChewSense-RealTime/MACOS_SETUP.md) for details.

**Estimated Effort**: 30 minutes

---

## 🟡 Medium Priority

### 4. Add Unit Tests for Field-Test Import
**Location**: `02-DataPipeline/tests/`

**Tests needed**:
- Import a fixture bundle with `motion.csv`, `predictions.csv`, and `feedback.csv`
- Verify false positives become `label=false`
- Verify missed chews become `label=true`
- Verify empty/malformed bundles are skipped with manifest notes

**Estimated Effort**: 2-3 hours

---

### 5. Implement Chew Count Estimation
**Location**: `Features/FrequencyFeatures.swift`, `05-FutureStages/02-BiteSegmentation/bite_detector.py`

**Purpose**: Count individual chews within bites for quality metrics

**Approach**:
- Peak detection in acceleration magnitude
- Filter for chewing frequency range (1-3 Hz)
- Count peaks within bite boundaries

**Estimated Effort**: 4-6 hours

---

### 6. Add Unit Tests for Pipeline Modules
**Location**: `02-DataPipeline/tests/`

**Tests needed**:
- `test_ingest.py` - CSV validation, manifest generation
- `test_transform.py` - Soft label generation
- `test_features.py` - Feature extraction accuracy
- `test_export.py` - CoreML export, Swift constants
- `test_splits.py` - Locked validation/test preservation
- `test_registry.py` - Registry metadata and artifact creation

**Estimated Effort**: 4-6 hours

---

### 7. Set Up GitHub Actions CI
**Location**: `.github/workflows/`

**Workflows**:
- Python tests (pytest)
- Swift tests (xcodebuild)
- Feature parity validation

See [04-RealWorldTesting/tests/TODO_CI.md](04-RealWorldTesting/tests/TODO_CI.md) for specs.

**Estimated Effort**: 3-4 hours

---

## 🟢 Nice-to-Have

### 8. Improve FFT Accuracy
**Current**: Simplified single-segment FFT
**Goal**: True Welch averaging with multiple overlapping segments

**Estimated Effort**: 3-4 hours

---

### 9. Add Model Comparison Dashboard
**Location**: W&B

**Purpose**: Automatically compare new training runs against baseline

**Estimated Effort**: 2-3 hours

---

### 10. Implement Bite Segmentation
**Location**: `05-FutureStages/02-BiteSegmentation/`

See [02-BiteSegmentation/README.md](05-FutureStages/02-BiteSegmentation/README.md) and [DESIGN.md](05-FutureStages/02-BiteSegmentation/DESIGN.md).

**Estimated Effort**: 1-2 weeks

---

## 🔵 Future Work

See `05-FutureStages/` for planned hierarchical analysis capabilities:

| Stage | Description | Status |
|-------|-------------|--------|
| 02-BiteSegmentation | Segment chewing into individual bites | Scaffold ready |
| 03-MealStructure | Analyze meal patterns and pace | Scaffold ready |
| 04-QualityEvaluation | Score chewing quality | Scaffold ready |
| 05-RealtimeFeedback | Provide live eating feedback | Scaffold ready |

---

## 📋 Session Planning

### Next Session (~2 hours)
- Task #1: Run end-to-end pipeline test
- Task #2: Complete one real-world field-test pass on device
- Task #3: Verify Mac Catalyst build/run

### Following Session (~4 hours)
- Task #4: Add field-test import unit tests
- Task #6: Add unit tests for pipeline
- Fix any issues from end-to-end testing

---

*Last updated: After refactor completion*
*See IMPLEMENTATION_STATUS.md for detailed implementation notes*
