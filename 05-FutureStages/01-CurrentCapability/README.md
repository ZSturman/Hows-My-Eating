# Current Capability: Binary Chewing Detection

## Overview

This stage represents the **currently implemented** capability of the ChewSense system: binary classification of chewing vs. non-chewing states using motion sensor data from AirPods.

## Status: ✅ IMPLEMENTED

The binary chewing detection model is fully functional and deployed in the real-time testing application.

## Technical Details

### Model Architecture
- **Type**: 3-layer Multi-Layer Perceptron (MLP)
- **Input**: 12 time-domain and frequency-domain features
- **Output**: Binary probability (chewing vs. not-chewing)
- **Framework**: PyTorch → CoreML

### Features (12 total)
1. **Mean acceleration magnitude**: Average magnitude of acceleration vector
2. **Variance of acceleration magnitude**: Variability in acceleration
3. **RMS acceleration magnitude**: Root mean square of acceleration
4. **Mean gyroscope magnitude**: Average angular velocity magnitude
5. **RMS gyroscope magnitude**: Root mean square of angular velocity
6. **RMS jerk**: Rate of change of acceleration
7. **Zero crossing rate**: Frequency of signal polarity changes
8. **Chew bandpower (1-3 Hz)**: Power in typical chewing frequency range
9. **Bandpower (0.8-1.5 Hz)**: Lower frequency movement detection
10. **Bandpower (2-4 Hz)**: Higher frequency chewing patterns
11. **Spectral centroid**: Center of mass of power spectrum
12. **Spectral rolloff (85%)**: Frequency below which 85% of power is contained

### Temporal State Machine
The raw model predictions are smoothed and processed through a state machine to reduce false positives:

```
Parameters:
- alpha: 0.4 (EMA smoothing factor)
- high_threshold: 0.6 (probability to start chewing episode)
- low_threshold: 0.4 (probability to end chewing episode)
- min_start_windows: 3 (consecutive high predictions to trigger)
- min_end_windows: 2 (consecutive low predictions to exit)
```

This hysteresis approach prevents rapid flickering between states.

## Performance Metrics

Current model performance on validation set:
- **Accuracy**: ~XX% (update after training)
- **AUC**: ~XX (update after training)
- **Precision**: ~XX% (update after training)
- **Recall**: ~XX% (update after training)
- **F1 Score**: ~XX (update after training)

*(Run `python main.py` and evaluate to populate metrics)*

## Soft Label Generation

The system uses a sophisticated soft-label approach for training that handles both short and long chewing episodes:

- **Short chews** (<3 seconds): Linear ramp over 0.6s transition
- **Long chews** (≥3 seconds): Linear ramp over 1.5s for more gradual transitions

This produces targets in [0, 1] rather than hard {0, 1} labels, allowing the model to learn temporal smoothness.

## Real-World Application

The model runs in real-time on iOS/macOS devices with AirPods:
- **Input**: 0.75s sliding window (step: 0.1s)
- **Processing**: Feature extraction → normalization → inference
- **Output**: Smoothed chewing probability and binary state
- **Latency**: ~10ms per inference on modern iPhone/Mac

## Limitations

Current limitations that motivate future stages:

1. **No bite-level information**: Cannot distinguish individual bites or count them
2. **No meal structure**: Cannot identify meal boundaries or eating episodes
3. **No quality metrics**: Cannot assess eating speed, thoroughness, or patterns
4. **Binary only**: Outputs chewing vs. not-chewing, nothing more granular
5. **Limited feedback**: No actionable information for behavior change

## Hardware Requirements

**REQUIRED**: AirPods Pro (1st/2nd/3rd gen) or AirPods Max with motion sensor support

Not all AirPods models include motion sensors. Standard AirPods and older generations will not work.

## Code Location

- **Training**: `02-DataPipeline/training/train_pytorch.py`
- **Feature Extraction**: `02-DataPipeline/scripts/get_features.py`
- **Real-Time Inference**: `04-RealWorldTesting/ChewSense-RealTime/InferenceEngine.swift`
- **Model Export**: `02-DataPipeline/scripts/export_coreML.py`

## Next Stage

See [02-BiteSegmentation](../02-BiteSegmentation/) for the next evolutionary step: extracting individual bite events from continuous chewing detection.
