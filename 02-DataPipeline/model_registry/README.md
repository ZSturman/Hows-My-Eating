# Local Model Registry

Each training run can create a local registry entry:

```text
model_registry/runs/<model_id>/
  chewnet.pth
  metrics.json
  dataset_manifest.json
  split_manifest.json
  runtime_config.json
  chewnet_norm.json
  NormalizationConstants.swift
  ChewNet.mlpackage/        # when CoreML export succeeds
```

Registry run contents are git-ignored because they are generated and can be large. The directory exists so deployed app metadata can be traced back to a local model bundle even when W&B is disabled.
