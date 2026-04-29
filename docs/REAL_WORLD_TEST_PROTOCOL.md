# Real-World Test Protocol

Use this protocol when checking whether a deployed model works outside the training pipeline.

## Setup

1. Pair supported AirPods with motion sensors.
2. Open the canonical testing app: `ChewSenseDebuggingModel`.
3. Confirm the app displays the deployed model metadata.
4. Enter a short scenario name, such as `apple chewing`, `talking while idle`, or `walking no food`.
5. Tap `Start`.

## Test Blocks

Run short focused blocks instead of one long vague recording:

| Block | Duration | Purpose |
| --- | ---: | --- |
| Quiet idle | 1-2 min | Baseline false-positive check. |
| Talking | 1-2 min | Common false-positive source. |
| Walking/head movement | 1-2 min | Motion robustness. |
| Chewing soft food | 1-3 min | Recall on subtle chewing. |
| Chewing crunchy food | 1-3 min | Recall on stronger chewing. |
| Drinking/no chewing | 1 min | Sensitivity around mouth movement. |

## Marking Feedback

Use the app buttons as the model runs:

| Button | Use when | Corrected label |
| --- | --- | --- |
| `False Positive` | App says chewing but you are not chewing. | Not chewing |
| `Missed Chew` | You are chewing but app stays idle or too low. | Chewing |
| `Correct` | The app is right in the current moment. | Current predicted state |

Add a note when the context matters, for example `talking`, `walking`, `gum`, `left AirPod loose`, or `small bite`.

Each feedback entry is tied to the current prediction window and the nearby motion samples, so it can become training data.

## Export

At the end of a block:

1. Tap `Stop`.
2. Tap `Share Session Bundle`.
3. Save or AirDrop the exported folder.
4. Place the folder under:

```text
02-DataPipeline/data/user/field_tests/
```

Then import:

```bash
cd 02-DataPipeline
python main_new.py from-field-test --input data/user/field_tests
```

## What Good Logs Contain

A useful field-test bundle has:
- enough `motion.csv` rows around each feedback event,
- `predictions.csv` rows with probability and smoothed state,
- `feedback.csv` entries with event type and corrected state,
- `session_metadata.json` with model id, dataset hash, runtime config, platform, and scenario.
