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

---

## 🔴 High Priority

### 1. Run End-to-End Pipeline Test
**Purpose**: Validate the refactored pipeline works correctly

**Steps**:
1. Run `python main_new.py sample` to test with sample data
2. Verify model trains successfully
3. Run `python main_new.py deploy` to copy to Xcode project
4. Build and run iOS app
5. Verify real-time detection works

**Estimated Effort**: 1-2 hours

---

### 2. Add Sample Data Files
**Purpose**: Enable `main_new.py sample` to work out-of-the-box

**Steps**:
1. Copy representative eating/not-eating CSVs to `data/sample/`
2. Update `data/sample/README.md` with file descriptions
3. Test `main_new.py sample` works

**Estimated Effort**: 30 minutes

---

### 3. Enable Mac Catalyst in Xcode
**Purpose**: Allow running on macOS

**Steps**:
1. Open `ChewSenseDebuggingModel.xcodeproj`
2. In target settings, add "Mac (Mac Catalyst)" to Supported Destinations
3. Build and test on macOS

See [MACOS_SETUP.md](04-RealWorldTesting/ChewSense-RealTime/MACOS_SETUP.md) for details.

**Estimated Effort**: 30 minutes

---

### 4. Add New Swift Files to Xcode Project
**Purpose**: New modular files need to be added to Xcode target

**Files to add**:
- `Features/FeatureExtractor.swift`
- `Features/FrequencyFeatures.swift`
- `Features/TimeFeatures.swift`
- `Managers/ChewDetector.swift`
- `Managers/MotionManager.swift`
- `Models/ChewModel.swift`
- `Views/MainContentView.swift`
- `Views/ConfigurationView.swift`
- `Generated/NormalizationConstants.swift`

**Steps**:
1. Open Xcode project
2. Drag folders into project navigator
3. Ensure all files are added to main target
4. Build and fix any compilation errors

**Estimated Effort**: 30-60 minutes

---

## 🟡 Medium Priority

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
- Task #4: Add Swift files to Xcode project
- Task #1: Run end-to-end pipeline test
- Task #2: Add sample data files

### Following Session (~4 hours)
- Task #3: Enable Mac Catalyst
- Task #6: Add unit tests for pipeline
- Fix any issues from end-to-end testing

---

*Last updated: After refactor completion*
*See IMPLEMENTATION_STATUS.md for detailed implementation notes*
