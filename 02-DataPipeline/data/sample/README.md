# Sample Data

This directory contains sample CSV sessions for testing the pipeline without collecting your own data.

## Contents

These sessions are provided as CSV-only (no video files) for git-friendliness:

- `Eating-sample-01/` — A sample eating session (~30 seconds)
- `Not-eating-sample-01/` — A sample not-eating session (~30 seconds)

## Usage

To run the full pipeline with sample data:

```bash
python main.py sample
```

This will:
1. Transform the sample CSVs (add soft labels)
2. Extract features
3. Train a model
4. Optionally export to CoreML

## Note

Sample data provides minimal training data and is intended for:
- Testing pipeline functionality
- Learning the workflow
- Smoke tests and CI

For production models, collect your own data using the [ChewSense Data Collection app](https://apps.apple.com/us/app/chew-sense-collect-and-label/id6755277802).
