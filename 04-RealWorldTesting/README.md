# Real-World Testing

This stage contains the iOS/macOS app for real-time chewing detection using AirPods motion sensors.

## Overview

The canonical **ChewSenseDebuggingModel** app runs the trained ChewNet model in real-time on your device, providing:
- Live chewing probability display
- Temporal state machine (idle/chewing detection)
- Field-test session bundle export for analysis and retraining
- False-positive, missed-chew, and correct feedback capture
- Runtime configuration tuning

## Project Structure

```
ChewSense-RealTime/
├── ChewSenseDebuggingModel/
│   ├── Features/             # Feature extraction (FFT, time-domain)
│   │   ├── FeatureExtractor.swift    # Combined 12-feature extraction
│   │   ├── FrequencyFeatures.swift   # vDSP-based FFT, Welch PSD, bandpower
│   │   └── TimeFeatures.swift        # Mean, variance, RMS, ZCR, jerk
│   │
│   ├── Managers/             # Business logic
│   │   ├── ChewDetector.swift        # State machine with hysteresis
│   │   └── MotionManager.swift       # AirPods motion data handling
│   │
│   ├── Models/               # CoreML wrapper
│   │   └── ChewModel.swift           # Prediction interface
│   │
│   ├── Views/                # SwiftUI UI
│   │   ├── MainContentView.swift     # Main debugging interface
│   │   └── ConfigurationView.swift   # Runtime parameter tuning
│   │
│   ├── Generated/            # Auto-generated from pipeline
│   │   └── NormalizationConstants.swift  # Feature normalization
│   │
│   ├── ContentView.swift     # Legacy wrapper (forwards to MainContentView)
│   └── ChewSenseDebuggingModelApp.swift
│
├── ChewNet.mlpackage/        # CoreML model
├── MACOS_SETUP.md            # macOS Catalyst setup guide
└── tests/                    # Feature validation
    ├── validate_features.py  # Python-Swift comparison
    └── TODO_CI.md            # CI/CD documentation
```

## Hardware Requirements

- **Required**: AirPods Pro (1st/2nd gen), AirPods Max, or AirPods 4
- **Platform**: iOS 14+ or macOS 14+ (via Mac Catalyst)
- These models include motion sensors (accelerometer + gyroscope)

## Quick Start

### 1. Open the Project
```bash
cd ChewSense-RealTime
open ChewSenseDebuggingModel.xcodeproj
```

### 2. Connect AirPods
- Pair AirPods with your device
- Put them in your ears

### 3. Build and Run
- Select your device (or "My Mac" for Mac Catalyst)
- Press ⌘R to build and run

### 4. Start Detection
- Tap "Start" to begin motion updates
- Watch the probability bar update in real-time
- "CHEWING" indicator appears when chewing is detected

## Configuration

Tap the ⚙️ button to access runtime configuration:

| Parameter | Default | Description |
|-----------|---------|-------------|
| **EMA Alpha** | 0.4 | Smoothing factor (0=slow, 1=no smoothing) |
| **High Threshold** | 0.6 | Probability to start chewing episode |
| **Low Threshold** | 0.4 | Probability to end chewing episode |
| **Min Start Windows** | 3 | Consecutive high predictions to trigger |
| **Min End Windows** | 2 | Consecutive low predictions to exit |

You can export the current configuration as JSON for reproducibility.

## Feature Extraction

The app extracts 12 features per 0.75s window, matching the Python pipeline:

### Time-Domain Features (7)
1. Mean acceleration magnitude
2. Variance of acceleration magnitude
3. RMS acceleration magnitude
4. Mean gyroscope magnitude
5. RMS gyroscope magnitude
6. RMS jerk
7. Zero crossing rate

### Frequency-Domain Features (5)
8. Chew bandpower (1-3 Hz)
9. Bandpower (0.8-1.5 Hz)
10. Bandpower (2-4 Hz)
11. Spectral centroid
12. Spectral rolloff (85%)

FFT features are computed using Apple's Accelerate framework (vDSP) with Welch-style power spectral density estimation.

## Model Deployment

To update the model from the pipeline:

```bash
cd ../02-DataPipeline
python main_new.py deploy
```

This copies:
- `ChewNet.mlpackage` → `ChewSense-RealTime/`
- Generated `NormalizationConstants.swift` → `Generated/`

## Field-Test Session Bundles

Each app test run creates a session folder containing:

- `session_metadata.json` - model id, dataset hash, W&B metadata when available, platform, app version, runtime config, and scenario
- `motion.csv` - raw AirPods motion samples
- `predictions.csv` - per-window probability, smoothed state, and raw feature vector
- `feedback.csv` - false positives, missed chews, and correct confirmations
- `config.json` - exported runtime settings when available

Import exported bundles into the training loop:

```bash
cd ../02-DataPipeline
python main_new.py from-field-test --input data/user/field_tests
```

## macOS Support

The app can run on macOS via Mac Catalyst. See [MACOS_SETUP.md](MACOS_SETUP.md) for setup instructions.

## Validation

### Feature Parity Testing

Ensure Swift features match Python reference:

```bash
cd tests
python validate_features.py --generate-test-data
# Then run Swift tests in Xcode
```

Target: < 5% relative error on all features.

### XCTest Suite

Run the test target `ChewSenseDebuggingModelTests` in Xcode:
- FFT peak frequency validation
- Bandpower range isolation
- Spectral centroid accuracy
- Time-domain feature correctness

## Troubleshooting

### "Headphone motion not available"
- Ensure AirPods are connected (not just paired)
- Check System Settings → Bluetooth shows AirPods connected
- Try removing and reinserting AirPods

### Low probability even when chewing
- Ensure AirPods are properly seated in ears
- Check that you're using AirPods Pro/Max/4 (standard AirPods lack motion sensors)
- Try adjusting EMA alpha lower (e.g., 0.3) for more smoothing

### High false positive rate
- Increase high threshold (e.g., 0.7)
- Increase min start windows (e.g., 4)
- Try lowering EMA alpha for more smoothing

## Files Not in Source Control

The following are generated/ignored:
- `*.xcuserdata/` - Xcode user settings
- `DerivedData/` - Build artifacts
- `ChewNet.mlmodelc/` - Compiled CoreML model (generated by Xcode)

## Related Documentation

- [02-DataPipeline/README.md](../02-DataPipeline/README.md) - Training pipeline
- [05-FutureStages/](../05-FutureStages/) - Planned hierarchical analysis
