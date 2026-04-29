# User Data

This directory is for your own collected sessions. It is **git-ignored** to keep your personal data private.

## Directory Structure

```
user/
├── raw_sessions/          # Place exported sessions from the app here
│   ├── Eating-20250101-120000/
│   │   ├── Eating-20250101-120000.csv
│   │   ├── Eating-20250101-120000.mov  (optional, git-ignored)
│   │   └── _metadata.txt
│   └── Not-eating-20250101-130000/
│       └── ...
├── field_tests/           # Place real-world test-session bundles here
└── README.md              # This file
```

## How to Collect Data

1. **Install the app**: Download [ChewSense Data Collection](https://apps.apple.com/us/app/chew-sense-collect-and-label/id6755277802) on your iPhone.

2. **Connect AirPods**: Ensure AirPods Pro, AirPods Max, or AirPods 4 (with motion sensors) are connected.

3. **Record sessions**: Use the app to record eating and not-eating sessions. Label them appropriately.

4. **Export sessions**: Use the app's share/export feature to get the session folders.

5. **Transfer to this directory**: Copy the exported session folders into `raw_sessions/`.

## Running the Pipeline

Once you have sessions in `raw_sessions/`:

```bash
# If you have fresh labeled CSVs from the app
python main.py from-raw --input data/user/raw_sessions

# The pipeline will:
# 1. Validate CSVs
# 2. Transform (add soft labels)
# 3. Extract features
# 4. Train model
# 5. Optionally export to CoreML
```

For real-world app test bundles:

```bash
# Convert false positives/missed chews into curated training sessions
python main_new.py from-field-test --input data/user/field_tests
```

## Notes

- Video files (`.mov`) are large and git-ignored. The pipeline only needs CSVs.
- Field-test bundles should contain `session_metadata.json`, `motion.csv`, `predictions.csv`, and `feedback.csv`.
- Keep a backup of your raw sessions before processing.
- Processed CSVs will be moved to `data/derived/` after transformation.
