# ChewSense Project Organization

ChewSense is organized as a lifecycle pipeline. Each numbered top-level folder owns one phase of the model loop, and generated artifacts should be kept separate from source-of-truth data and code.

## Top-Level Folders

| Path | Owns | Current status |
| --- | --- | --- |
| `01-DataCollection/` | iOS data collection and video labeling app. Produces labeled AirPods motion CSVs plus optional video. | Production app exists. Use it for new carefully labeled recordings. |
| `02-DataPipeline/` | Python ingest, transform, feature extraction, training, evaluation, CoreML export, deployment, and model registry. | Active model-development surface. |
| `03-ModelEvaluation/` | Legacy/offline evaluation scripts. | Useful reference, but the modular pipeline now owns routine evaluation. |
| `04-RealWorldTesting/` | iPhone/macOS real-time inference app for testing deployed models with AirPods. | Canonical app is `ChewSenseDebuggingModel`; legacy monolithic files should not be used for new testing. |
| `05-FutureStages/` | Planned bite, meal, quality, and feedback capabilities. | Design/scaffold only. |
| `ProjectHistory/` | Archived prototypes and notes. | Reference only. |

## Data Ownership

Use this default data layout:

```text
02-DataPipeline/data/
  sample/                  # Tiny tracked smoke-test data
  user/
    raw_sessions/           # Data collection app exports, git-ignored
    field_tests/            # Real-world app test bundles, git-ignored
  curated/
    accepted_sessions/      # Reviewed/imported labeled sessions, git-ignored except docs
    rejected_sessions/      # Unusable sessions with notes, git-ignored except docs
  manifests/
    datasets/               # Dataset manifests and import summaries
    splits/                 # Locked split manifests
  derived/                  # Transformed/features/logs, git-ignored
```

Rules:
- Raw data is immutable. Do not rewrite app exports in place.
- `sample/` is the only place for tracked example recordings.
- `user/`, `curated/*_sessions/`, and `derived/` may contain personal or generated data and are ignored by git.
- Manifests are small enough to track when they describe public/sample data; user-specific manifests can remain local.

## Source Of Truth Vs Generated

Source of truth:
- Python pipeline code and configs.
- Swift app source files.
- Sample CSVs.
- Documentation and schema descriptions.
- Locked split manifests for public/sample data.

Generated:
- `data/derived/**`
- `model_registry/runs/**`
- CoreML exports regenerated from a checkpoint.
- Swift normalization constants regenerated from a checkpoint.
- App-exported field-test bundles.

## Canonical App

The canonical real-world testing app is:

```text
04-RealWorldTesting/ChewSense-RealTime/ChewSenseDebuggingModel/
```

It should own:
- real-time AirPods motion capture,
- Swift feature extraction,
- CoreML inference,
- test-session bundle logging,
- feedback capture for false positives and missed chewing.

The legacy `ChewSense Model/` folder is kept only for historical comparison and should not be used for new testing.
