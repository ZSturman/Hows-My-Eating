# CI/CD Testing Documentation

## Overview

This document describes the testing strategy for ensuring feature parity between Python and Swift implementations.

## Test Categories

### 1. Unit Tests (Swift)

Location: `ChewSenseDebuggingModelTests/FeatureExtractionTests.swift`

Run with Xcode:
```bash
xcodebuild test -scheme ChewSenseDebuggingModel -destination 'platform=iOS Simulator,name=iPhone 15'
```

Tests cover:
- FFT implementation correctness (sine wave peak detection)
- Bandpower calculation in frequency ranges
- Spectral centroid and rolloff
- Time-domain features (mean, variance, RMS, ZCR)
- Feature vector integration

### 2. Feature Parity Validation (Python)

Location: `04-RealWorldTesting/tests/validate_features.py`

#### Generate Test Data
```bash
cd 04-RealWorldTesting/tests
python validate_features.py --generate-test-data --csv ../../02-DataPipeline/data/sample/Eating-sample-01/*.csv
```

This creates `test_data.json` containing:
- Raw sensor samples
- Sampling rate
- Expected features (from Python)
- Feature names

#### Run Comparison
After extracting features in Swift and saving to `swift_output.json`:
```bash
python validate_features.py --csv <sample.csv> --swift-output swift_output.json
```

### 3. Tolerance

Default tolerance: **5% relative error**

This accounts for differences in:
- FFT implementations (vDSP vs scipy)
- Window functions (Hanning implementation details)
- Numerical precision (Float32 vs Float64)

Override with `--tolerance` flag:
```bash
python validate_features.py --tolerance 0.10  # 10% tolerance
```

## Continuous Integration

### GitHub Actions Workflow (Suggested)

```yaml
name: Feature Parity Check

on: [push, pull_request]

jobs:
  python-features:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r 02-DataPipeline/requirements.txt
      - name: Generate test data
        run: |
          cd 04-RealWorldTesting/tests
          python validate_features.py --generate-test-data
      - name: Upload test data
        uses: actions/upload-artifact@v3
        with:
          name: test-data
          path: 04-RealWorldTesting/tests/test_data.json

  swift-tests:
    runs-on: macos-latest
    needs: python-features
    steps:
      - uses: actions/checkout@v3
      - name: Download test data
        uses: actions/download-artifact@v3
        with:
          name: test-data
          path: 04-RealWorldTesting/tests/
      - name: Run Swift tests
        run: |
          cd 04-RealWorldTesting/ChewSense-RealTime
          xcodebuild test -scheme ChewSenseDebuggingModel -destination 'platform=iOS Simulator,name=iPhone 15'
```

## Manual Validation Workflow

1. **Train a model** (Python):
   ```bash
   cd 02-DataPipeline
   python main.py sample
   ```

2. **Generate test data**:
   ```bash
   cd 04-RealWorldTesting/tests
   python validate_features.py --generate-test-data
   ```

3. **Run Swift tests**:
   - Open `ChewSenseDebuggingModel.xcodeproj`
   - Product → Test (⌘U)

4. **Compare outputs**:
   - Add test that exports Swift features to JSON
   - Run comparison script

## Known Differences

| Feature | Difference | Impact |
|---------|------------|--------|
| FFT Windowing | vDSP uses single segment | < 2% on bandpower |
| Spectral Rolloff | Index vs interpolation | < 1% typically |
| Zero handling | Different epsilon values | Negligible |

## Passing Criteria

- All 7 time-domain features: < 1% relative error
- All 5 frequency-domain features: < 5% relative error
- Overall: 12/12 features pass tolerance check
