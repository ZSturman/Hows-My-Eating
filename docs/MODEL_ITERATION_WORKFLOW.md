# ChewSense Model Iteration Workflow

This is the repeatable loop for improving chewing detection accuracy.

## 1. Collect Or Import Data

For controlled labeled data:

```bash
cd 02-DataPipeline
python main_new.py from-app
```

For real-world model failures:

1. Run the canonical app in `04-RealWorldTesting/ChewSense-RealTime`.
2. Start a real-world test session on iPhone or macOS.
3. Mark `False Positive`, `Missed Chew`, or `Correct` while testing.
4. Export the field-test bundle.
5. Place exported folders in:

```text
02-DataPipeline/data/user/field_tests/
```

## 2. Import Field Tests

```bash
cd 02-DataPipeline
python main_new.py from-field-test --input data/user/field_tests
```

This converts feedback windows into labeled CSV sessions under:

```text
data/curated/accepted_sessions/
```

Each imported event becomes a small labeled session so false positives and missed chewing can be reused during training.

## 3. Train With Locked Splits

Routine retraining should use session-based split manifests:

```bash
python main_new.py from-raw --input data/curated/accepted_sessions --no-wandb
```

The pipeline writes or updates split manifests in:

```text
data/manifests/splits/
```

Locked `validation_locked` and `test_locked` sessions stay stable across retraining. New reviewed data defaults to `train`, while known field failures are also tracked in `field_regression`.

## 4. Evaluate In The CLI

```bash
python main_new.py evaluate --model models/chewnet.pth
```

Use this before deploying to check accuracy, AUC, precision, recall, F1, and confusion matrix.

## 5. Register And Deploy

Every training run should produce a local registry entry under:

```text
02-DataPipeline/model_registry/runs/<model_id>/
```

View the latest registered model:

```bash
python main_new.py registry --latest
```

Deploy to the app:

```bash
python main_new.py deploy --model models/chewnet.pth --force
```

The deployed Swift constants should include model id, dataset hash, W&B metadata when available, and runtime thresholds.

## 6. Test On Device

Run the canonical app on iPhone or Mac with AirPods connected. Export the resulting field-test bundle, place it in `data/user/field_tests/`, and repeat the loop.

The loop is expected to run many times. The important invariants are:
- raw data is preserved,
- validation/test splits are stable,
- app feedback is tied to model metadata,
- every deployed model can be traced back to a registry entry.
