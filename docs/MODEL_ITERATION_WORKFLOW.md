# ChewSense Model Iteration Workflow

This is the repeatable loop that turns app field-tests into a better deployed
model and back into the app. Once everything is set up, **one full iteration
is three commands** in `02-DataPipeline/`:

```bash
python main_new.py from-field-test     # ingest + retrain
python main_new.py compare             # report vs previous model
python main_new.py deploy --force      # ship to Xcode
```

Then in Xcode: **Product → Clean Build Folder (⇧⌘K)** and run the app.

---

## 0. One-time environment setup

The `coremltools` export step on macOS arm64 currently segfaults with
`torch>=2.8`. Use the pinned export venv from
[02-DataPipeline/requirements-export.txt](../02-DataPipeline/requirements-export.txt):

```bash
cd 02-DataPipeline
python3 -m venv .venv-export
source .venv-export/bin/activate
pip install -r requirements-export.txt
```

The same venv handles training **and** export, so you don't need a second one.
Activate it before every command in this doc.

---

## 1. Record + correct in the app (stage 04)

1. Open `04-RealWorldTesting/ChewSense-RealTime/ChewSenseDebuggingModel.xcodeproj`.
2. Build and run on iPhone or Mac with AirPods connected.
3. Hit **New** to start a recording. The app saves a session bundle that
   contains `motion.csv`, `predictions.csv`, optional `*.mov`, and
   `session_metadata.json`.
4. Open the recording in the review pane. Drag review segments to mark
   missed chews, false positives, or "the prediction was correct here." On
   finalize, the app writes **`labeled_motion.csv`** — every motion sample
   in the session with a per-row `label` resolved from the model's
   predictions plus your corrections.
5. Open the **Recording Configuration** inspector and confirm the
   **Bundled Model** section shows the `MODEL_ID` and short SHA you expect.
   That's how you'll know when a new model has actually landed in step 6.
6. Export the bundle (Files / Finder share sheet) and drop the folder into:

   ```
   02-DataPipeline/data/user/field_tests/
   ```

> **All sessions count as training data.** `labeled_motion.csv` is written
> for every reviewed session, whether you changed labels or not. The
> pipeline always prefers `labeled_motion.csv` over the legacy
> `motion.csv + feedback.csv` pair, so a "correct" review still contributes
> a fully-labeled session to the next training run.

---

## 2. Ingest + retrain (stage 02)

```bash
cd 02-DataPipeline
source .venv-export/bin/activate
python main_new.py from-field-test --input data/user/field_tests
```

What this does:

1. Reads every bundle under `data/user/field_tests/` (skipping anything
   already inside `_archive/`).
2. Writes labeled session CSVs into
   `data/curated/accepted_sessions/Eating-field-reviewed-…/`. **Curated
   sessions accumulate forever** — every iteration adds new ones, and
   training in step 3 uses the entire curated directory.
3. **Archives the source bundle** to
   `data/user/field_tests/_archive/<timestamp>/<bundle>/`. This guarantees
   the next iteration only ingests *new* bundles, not duplicates of past
   ones, while still keeping a copy of the raw data on disk.
4. Validates curated sessions, transforms them, extracts features, trains a
   new `models/chewnet.pth`, and writes a registry entry under
   `model_registry/runs/<model_id>/`.

Useful flags:

- `--no-archive` — keep bundles in `field_tests/` after ingest (will be
  re-imported next iteration; usually not what you want).
- `--strip-archive-mov` — delete the bulky `.mov`/`.mp4` files inside the
  archived bundle. Labels live in CSV/JSON, so this is lossless for
  training but reclaims most of the disk.

---

## 3. Compare against the previous model (stage 03)

```bash
python main_new.py compare
```

This calls [03-ModelEvaluation/compare.py](../03-ModelEvaluation/compare.py),
which loads the **two newest registry entries**, diffs their
`metrics.json` per split (`validation_locked`, `field_regression`,
`all`), and writes a markdown report:

```
03-ModelEvaluation/reports/<timestamp>_compare.md
```

The report ends with a verdict — `improved`, `neutral`, or `regressed`
(neutral band ±0.005 on accuracy/AUC/precision/recall/F1). The deploy
command in step 4 reads the same verdict and refuses to ship a regressed
model unless you pass `--force`.

To pin specific models for the comparison:

```bash
python main_new.py compare --baseline chewnet-2026… --candidate chewnet-2026…
```

---

## 4. Deploy to the app (stage 02 → 04)

```bash
python main_new.py deploy --force
```

What this does:

1. Runs the comparator gate (skip with `--skip-compare`).
2. Prints the resolved versions of `python`/`torch`/`coremltools`/`numpy`
   so you can spot a bad env immediately.
3. Runs the CoreML conversion in an **isolated subprocess** so a native
   crash inside `coremltools` no longer takes down the whole CLI; instead
   you get a clear error and remediation hint.
4. Writes:
   - `02-DataPipeline/exports/ChewNet.mlpackage`
   - `04-RealWorldTesting/ChewSense-RealTime/ChewNet.mlpackage`
   - `04-RealWorldTesting/ChewSense-RealTime/ChewSenseDebuggingModel/Generated/NormalizationConstants.swift`
   - `02-DataPipeline/exports/chewnet_norm.json`
5. Prints a **before → after diff table** for the seven identity fields
   (`MODEL_ID`, `DATASET_HASH`, `DATASET_STATUS`, `MODEL_PACKAGE_SHA256`,
   `WANDB_RUN_ID`, `GENERATED_AT`).
6. **Exits with code 3** if `MODEL_PACKAGE_SHA256` is unchanged — that's
   the loud signal that the deploy was a no-op (typically because the
   checkpoint wasn't retrained).

Useful flags:

- `--force` — bypass the regression gate and overwrite existing artifacts.
- `--skip-coreml` — reuse the existing `exports/ChewNet.mlpackage` (debug
  the Swift constants without paying for the conversion).
- `--skip-compare` — skip the regression gate.

---

## 5. Rebuild the app (stage 04)

In Xcode:

1. **Product → Clean Build Folder (⇧⌘K)** — required because the
   `.mlpackage` compilation is cached aggressively.
2. Build and run.
3. Open **Recording Configuration → Bundled Model** and verify:
   - `MODEL_ID` matches the value the deploy step printed.
   - The short SHA matches the new `MODEL_PACKAGE_SHA256`.
   - `GENERATED_AT` is the most recent run.

If those values still show the old model, you forgot the clean build.

---

## 6. Loop again

Record more sessions in the app, drop the new bundles into
`data/user/field_tests/`, and re-run steps 2–5. Each iteration:

- Adds new labeled sessions to `data/curated/accepted_sessions/` (training
  data **strictly grows**; nothing the user has ever recorded is dropped).
- Archives the imported bundles so they aren't re-ingested.
- Produces a new comparison report and a new registry entry.
- Replaces the deployed `.mlpackage` and `NormalizationConstants.swift`.

---

## Disk hygiene: `clean` subcommand

The loop produces four kinds of accumulating artifact. Run this whenever
you notice disk pressure (everything except curated training data is
disposable):

```bash
python main_new.py clean --dry-run        # preview
python main_new.py clean                  # actually prune
python main_new.py clean --strip-archive-mov   # also drop .mov/.mp4 from archived bundles
```

Defaults keep the most recent:

| Path | Default keep | What's pruned |
|---|---:|---|
| `data/derived/runs/` | 3 | per-iteration features + transformed CSVs |
| `model_registry/runs/` | 5 | per-train registry entries (full checkpoint copies) |
| `wandb/` | 3 | local W&B run dirs |
| `data/user/field_tests/_archive/` | 5 | timestamped archives of already-imported bundles |

Override with `--keep-runs N`, `--keep-registry N`, `--keep-wandb N`,
`--keep-archive N`. **Never pruned**: `data/curated/`, split manifests,
`models/chewnet.pth`, the active export under
`02-DataPipeline/exports/`, the deployed Xcode artifacts, and any
non-archived field-test bundles.

---

## Invariants for the loop

- **Raw data is preserved.** Bundles are archived, not deleted. The
  curated CSVs that feed training are kept indefinitely.
- **Validation/test splits are stable.** Locked validation/test sessions
  in `data/manifests/splits/locked_splits.json` carry across retraining.
- **Every deployed model is traceable.** `MODEL_ID`, `DATASET_HASH`, the
  W&B run id, and the package SHA-256 are all visible in the app.
- **A no-op deploy is loud.** Unchanged SHA returns exit code 3 and prints
  a warning, so a forgotten retrain can't masquerade as a successful
  deploy.
